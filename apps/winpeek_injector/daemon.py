"""Agent Daemon — background service, auto-started with hermes serve.

Migrated from PeekabooWin agent-discovery.js + agent-launcher.js.
Scans local .claude/.hermes/.qoder config directories, registers agents
to identity DB, injects MIM MCP config, maintains heartbeat.

Runs silently — no window, no tray (yet). Started by hub_bridge.try_load_hub().
"""

import json, logging, os, secrets, socket, stat, string, time, threading
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path

HOME = Path.home()

# ═══════════════════════════════════════════════
# Dedicated daemon logger — independent from audit jsonl
# Writes to ~/.hermes/logs/daemon.log (max 1 MB, keep 3 backups)
# ═══════════════════════════════════════════════

_daemon_logger: "logging.Logger | None" = None


def _get_daemon_logger() -> logging.Logger:
    global _daemon_logger
    if _daemon_logger is not None:
        return _daemon_logger
    logger = logging.getLogger("peeka.daemon")
    logger.setLevel(logging.DEBUG)
    logger.propagate = False  # don't pollute hermes agent.log
    log_dir = HOME / ".hermes" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    fh = RotatingFileHandler(
        log_dir / "daemon.log",
        maxBytes=1_048_576,  # 1 MB
        backupCount=3,
        encoding="utf-8",
    )
    fh.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)-5s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
    logger.addHandler(fh)
    _daemon_logger = logger
    return logger


def _dlog(msg: str, level: str = "info"):
    """Write to the dedicated daemon log. Silently ignores I/O errors."""
    try:
        log = _get_daemon_logger()
        getattr(log, level)(msg)
    except Exception:
        pass

# ═══════════════════════════════════════════════
# Agent scanner — detects installed AI agents
# ═══════════════════════════════════════════════

AGENT_SCANNERS = [
    {
        "agent_type": "claude-code",
        "name": "Claude Code",
        "check_paths": [
            HOME / ".claude" / "settings.json",
            HOME / "AppData" / "Roaming" / "Claude" / "settings.json",
        ],
        "config_file": HOME / ".claude" / "settings.json",
        "config_format": "json",
        "default_window_title": "Claude Code",
    },
    {
        "agent_type": "hermes",
        "name": "Hermes Agent",
        "check_paths": [
            HOME / ".hermes" / "config.yaml",
        ],
        "config_file": HOME / ".hermes" / "mcp.json",
        "config_format": "json",
        "default_window_title": "Hermes",
    },
    {
        "agent_type": "qoder",
        "name": "Qoder",
        "check_paths": [
            HOME / ".qoder" / "settings.json",
        ],
        "config_file": HOME / ".qoder" / "settings.json",
        "config_format": "json",
        "default_window_title": "Qoder",
    },
    {
        "agent_type": "traecli",
        "name": "Trae CLI",
        "check_paths": [
            HOME / ".trae" / "config.json",
            HOME / ".trae" / "settings.json",
        ],
        "config_file": None,  # traecli V1: no MCP injection
        "config_format": "json",
        "default_window_title": "Trae CLI",
    },
]

# ═══════════════════════════════════════════════
# MCP config injection block
# ═══════════════════════════════════════════════

MCP_BLOCK = {
    "mcpServers": {
        "winpeek-mim": {
            "type": "stdio",
            "command": "python",
            "args": [
                str(Path(__file__).resolve().parent.parent.parent / "plugins" / "winpeek_rpa" / "mcp_server.py"),
            ],
            "env": {
                "WINPEEK_HUB_ENABLED": "1",
                "MIM_BROKER": os.getenv("MIM_BROKER", "192.168.3.23"),
            },
        },
    },
}

# ═══════════════════════════════════════════════
# Scanner + injector + daemon state (exposed to RPC)
# ═══════════════════════════════════════════════

# Module‑level state — set by start_daemon(), read by _handle_mim_local_agents
_daemon_state: dict = {}

def scan_installed_agents() -> list[dict]:
    """Return list of installed agents on this machine."""
    found = []
    for scanner in AGENT_SCANNERS:
        installed = False
        for p in scanner["check_paths"]:
            if p.exists():
                installed = True
                break
        if installed:
            found.append(scanner)
    return found

def inject_mcp_config(config_path: Path) -> bool:
    """Write MIM MCP server config into agent's JSON settings file.

    Uses strict owner-only permissions (0o600) — settings files may
    contain credentials and must not be world-readable.
    """
    if not config_path or not config_path.exists():
        return False
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except Exception:
        config = {}

    existing = config.get("mcpServers", {})
    if "winpeek-mim" in existing:
        return False  # Already injected

    _dlog(f"mcp_inject: {config_path}")

    # Backup with owner-only permissions
    bak = Path(str(config_path) + ".mim-bak")
    if not bak.exists():
        bak.write_bytes(config_path.read_bytes())
        os.chmod(bak, stat.S_IRUSR | stat.S_IWUSR)

    config.setdefault("mcpServers", {})
    config["mcpServers"]["winpeek-mim"] = MCP_BLOCK["mcpServers"]["winpeek-mim"]
    config_path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(config_path), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    return True

def register_and_inject():
    """One-time: scan + register + inject for all found agents."""
    global _daemon_state
    agents = scan_installed_agents()
    results = []
    hostname = socket.gethostname()
    machine = hostname

    try:
        from gateway.winpeek_hub import identity
    except ImportError:
        _daemon_state = {"machine": machine, "daemon_version": "1.0.0", "runtimes": []}
        return results

    # ── Find owner User (真人) for this machine ──
    device_owner_uid = 0
    try:
        device = identity.check_device(hostname)
        if device and device.get("winpeek_uid"):
            device_owner_uid = int(device["winpeek_uid"])
    except Exception:
        pass

    def _gen_password() -> str:
        """Generate agent password: a@ + 8 cryptographically random chars."""
        chars = string.ascii_lowercase + string.digits
        return "a@" + "".join(secrets.choice(chars) for _ in range(8))

    for scanner in agents:
        name = scanner["name"]
        agent_type = scanner["agent_type"]
        password = ""

        # Look up existing identity by nickname
        existing = None
        for u in identity.list_all():
            if u.get("nickname") == name:
                uid = u["uid"]
                # Try a@{uid} (old formula) first, then empty (legacy)
                existing = identity.login(name, f"a@{uid}") or identity.login(name, "")
                if existing:
                    password = f"a@{uid}" if identity.login(name, f"a@{uid}") else ""
                break

        if not existing:
            # Register new → generate a@ + 6 random chars
            password = _gen_password()
            existing = identity.register(name, "Agent", hostname, password)
            if not existing:
                # Fallback: register with empty, then set password
                existing = identity.register(name, "Agent", hostname, "")
                if existing:
                    identity.set_password(existing["uid"], password)
                    existing = identity.login(name, password) or existing

        uid = existing.get("uid") if existing else None

        # ── Bind agent to device owner (master_uid) ──
        if uid and device_owner_uid:
            try:
                agent_info = identity.get_by_uid(uid)
                if agent_info and not agent_info.get("manager_uid"):
                    # Only set if not already bound
                    from gateway.winpeek_hub.db import get_conn
                    conn = get_conn()
                    if conn:
                        with conn.cursor() as cur:
                            cur.execute(
                                "UPDATE users SET manager_uid = %s WHERE uid = %s",
                                (device_owner_uid, uid))
                            conn.commit()
                        conn.close()
                if agent_info:
                    identity_type = agent_info.get("identity_type", "")
                    if identity_type != "mim-agent":
                        from gateway.winpeek_hub.db import get_conn
                        conn2 = get_conn()
                        if conn2:
                            with conn2.cursor() as cur2:
                                cur2.execute(
                                    "UPDATE users SET identity_type = %s WHERE uid = %s",
                                    ("mim-agent", uid))
                                conn2.commit()
                            conn2.close()
            except Exception:
                pass

        # Inject MCP config (skip for types without config_file like traecli)
        injected = False
        if scanner.get("config_file"):
            injected = inject_mcp_config(scanner["config_file"])

        # Inject MIM identity block into agent prompt file (includes password!)
        prompt_injected = False
        if uid and scanner.get("agent_type"):
            prompt_injected = _inject_agent_prompt(uid, existing, scanner, password)

        # Initialize inbox + register to hub for this agent
        if uid:
            _init_inbox(uid)
            try:
                from gateway.winpeek_hub import hub
                # ensure_node: does NOT force online — waits for agent heartbeat
                hub.ensure_node(uid, name, scanner.get("agent_type", "Agent"), hostname)
            except Exception:
                pass

        results.append({
            "agent_type": agent_type,
            "name": name,
            "uid": uid,
            "config_injected": injected,
            "prompt_injected": prompt_injected,
            "config_file": str(scanner.get("config_file", "")),
        })
        _dlog(f"register: {name} ({agent_type}) uid={uid} "
              f"mcp={'yes' if injected else 'no'} prompt={'yes' if prompt_injected else 'no'}")

    _daemon_state = {
        "machine": machine,
        "daemon_version": "1.0.0",
        "runtimes": [
            {"agent_type": r["agent_type"], "registered": r["uid"] is not None, "uid": r["uid"]}
            for r in results
        ],
    }
    return results


# ═══════════════════════════════════════════════
# Agent prompt injection
# ═══════════════════════════════════════════════

# Prompt files by agent type — the file Daemon writes the MIM_IDENTITY_BLOCK into
AGENT_PROMPT_FILES = {
    "claude-code": HOME / ".claude" / "CLAUDE.md",
    "hermes": HOME / ".hermes" / "AGENTS.md",   # NOT config.yaml (YAML!)
    "qoder": HOME / ".qoder" / "AGENTS.md",
}


def _build_identity_block(uid: int, identity: dict, scanner: dict, password: str = "") -> str:
    """Build the MIM_IDENTITY_BLOCK markdown for an agent."""
    hostname = socket.gethostname()
    peeka_name = identity.get("peeka_name", f"agent{uid}-{hostname}-hotime.cn")
    role = identity.get("role", "Agent")
    name = identity.get("nickname", scanner.get("name", ""))
    squad = identity.get("squad_name", "")
    manager_uid = identity.get("manager_uid", 0)

    # Absolute path to the CORRECT say.py (cc version — goes through Daemon outbox).
    # This prevents agents from accidentally using a different say.py on PATH
    # (e.g. the qoder version that sends directly to comms/say/ bypassing Daemon).
    _say_py = Path(__file__).resolve().parent.parent.parent / "bin" / "say.py"
    say_path = str(_say_py).replace("\\", "/")

    block = f"""
<!-- MIM_IDENTITY_BLOCK — auto‑injected by Peeka Daemon, do not edit manually -->

[MIM Identity]
uid: {uid}
name: {name}
password: {password}
role: {role}
peeka_name: {peeka_name}
squad: {squad or "(未加入组织)"}
manager_uid: {manager_uid or 0}
inbox_path: {HOME / '.hermes' / 'winpeek' / 'inbox' / str(uid)}
hostname: {hostname}

[MIM Commands]
- 登录MIM: winpeek_mim_login(nickname="{name}", password="{password}")
- 发送回复: python "{say_path}" <uid> "消息内容"
- 查阅收信箱: 查看 inbox_path/unread/ 目录
- 查看联系人: curl http://192.168.3.44:2000/api/contacts
- 有疑问: 先问本地 Daemon, 再问上级 (manager_uid={manager_uid})

[MIM Rules]
- 你是多 Agent 网络中的一员, Daemon 是你的本地管家
- 收到 [MIM] 开头的消息后, 自主用 LLM 判断是否回复
- 回复时执行 python "{say_path}" <uid> "内容" 即可, Daemon 负责送达
- Daemon 可能会催问未回复的消息, 请及时处理
- 不必回复的消息: 广告(已过滤)、问候(Daemon 已代答)
- 每60秒调用一次 winpeek_mim_online 维持在线状态, 否则120秒后会被标记为离线
<!-- /MIM_IDENTITY_BLOCK -->
"""
    return block.strip()


def _inject_agent_prompt(uid: int, identity: dict, scanner: dict, password: str = "") -> bool:
    """Write MIM_IDENTITY_BLOCK into the agent's prompt/config file.

    Idempotent — checks if block already exists before writing.
    Keeps existing file content intact outside the block.
    """
    prompt_file = AGENT_PROMPT_FILES.get(scanner.get("agent_type"))
    if not prompt_file:
        return False

    block = _build_identity_block(uid, identity, scanner, password)
    marker_start = "<!-- MIM_IDENTITY_BLOCK"
    marker_end = "<!-- /MIM_IDENTITY_BLOCK -->"

    try:
        if prompt_file.exists():
            content = prompt_file.read_text(encoding="utf-8", errors="replace")
            # Check if already injected
            if marker_start in content:
                # Replace existing block
                lines = content.split("\n")
                new_lines = []
                skip = False
                for line in lines:
                    if marker_start in line:
                        skip = True
                        new_lines.append(block)
                        continue
                    if skip and marker_end in line:
                        skip = False
                        continue
                    if not skip:
                        new_lines.append(line)
                new_content = "\n".join(new_lines)
            else:
                # Append at end
                new_content = content.rstrip("\n") + "\n\n" + block + "\n"
        else:
            new_content = block + "\n"

        prompt_file.parent.mkdir(parents=True, exist_ok=True)
        prompt_file.write_text(new_content, encoding="utf-8")
        _audit_log("prompt_inject", {"agent_type": scanner.get("agent_type"),
                     "uid": uid, "file": str(prompt_file)})
        return True
    except Exception as e:
        _audit_log("prompt_inject_failed", {"agent_type": scanner.get("agent_type"),
                   "uid": uid, "error": str(e)})
        return False


# ═══════════════════════════════════════════════
# Inbox management
# ═══════════════════════════════════════════════

INBOX_ROOT = HOME / ".hermes" / "winpeek" / "inbox"


def _init_inbox(uid: int):
    """Create inbox directories for an agent."""
    for sub in ("unread", "delivered"):
        (INBOX_ROOT / str(uid) / sub).mkdir(parents=True, exist_ok=True)
    # Write/update manifest
    _update_manifest(uid)


def _update_manifest(uid: int):
    """Update .manifest.json for an agent's inbox."""
    inbox_dir = INBOX_ROOT / str(uid)
    unread_dir = inbox_dir / "unread"
    delivered_dir = inbox_dir / "delivered"
    manifest = {
        "uid": uid,
        "updated_at": datetime.now().isoformat(),
        "unread_count": len(list(unread_dir.glob("*.json"))) if unread_dir.exists() else 0,
        "delivered_count": len(list(delivered_dir.glob("*.json"))) if delivered_dir.exists() else 0,
    }
    manifest_file = inbox_dir / ".manifest.json"
    manifest_file.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")


def write_to_inbox(agent_uid: int, msg: dict):
    """Write an incoming L3 message to the agent's unread inbox.

    msg dict: {mid, from_uid, from_name, from_role, from_peeka_name,
               relation, body, context, received_at, is_retry, retry_count}
    """
    _init_inbox(agent_uid)
    mid = msg.get("mid", f"mim-{int(time.time()*1000)}")
    file_path = INBOX_ROOT / str(agent_uid) / "unread" / f"{mid}.json"
    file_path.write_text(json.dumps(msg, indent=2, ensure_ascii=False, default=str),
                         encoding="utf-8")
    _update_manifest(agent_uid)
    _dlog(f"inbox_write: agent={agent_uid} mid={mid[:24]} from={msg.get('from_uid')}")
    _audit_log("inbox_write", {"agent_uid": agent_uid, "mid": mid})


def read_inbox(agent_uid: int) -> list[dict]:
    """Read all unread messages from an agent's inbox. Returns list of msg dicts."""
    unread_dir = INBOX_ROOT / str(agent_uid) / "unread"
    if not unread_dir.exists():
        return []
    messages = []
    for f in sorted(unread_dir.glob("*.json")):
        try:
            msg = json.loads(f.read_text(encoding="utf-8"))
            messages.append(msg)
        except Exception:
            pass
    return messages


def mark_delivered(agent_uid: int, mid: str):
    """Move a message from unread/ to delivered/."""
    unread_path = INBOX_ROOT / str(agent_uid) / "unread" / f"{mid}.json"
    delivered_path = INBOX_ROOT / str(agent_uid) / "delivered" / f"{mid}.json"
    if unread_path.exists():
        delivered_path.parent.mkdir(parents=True, exist_ok=True)
        unread_path.rename(delivered_path)
        _update_manifest(agent_uid)
        _audit_log("inbox_delivered", {"agent_uid": agent_uid, "mid": mid})


def mark_replied(agent_uid: int, mid: str):
    """Mark a delivered message as replied (write status into the file)."""
    delivered_path = INBOX_ROOT / str(agent_uid) / "delivered" / f"{mid}.json"
    if delivered_path.exists():
        try:
            msg = json.loads(delivered_path.read_text(encoding="utf-8"))
            msg["status"] = "replied"
            msg["replied_at"] = datetime.now().isoformat()
            delivered_path.write_text(json.dumps(msg, indent=2, ensure_ascii=False, default=str),
                                      encoding="utf-8")
            _audit_log("inbox_replied", {"agent_uid": agent_uid, "mid": mid})
        except Exception:
            pass


# ═══════════════════════════════════════════════
# Reliability tracking
# ═══════════════════════════════════════════════

# Track: {mid: {"agent_uid": int, "to_uid": int, "sent_at": str, "retry_count": int, "status": str}}
_reliability_tracker: dict[str, dict] = {}
_reliability_lock = threading.Lock()


def track_l3_message(mid: str, agent_uid: int, to_uid: int):
    """Start tracking a layer-3 message for reliability."""
    with _reliability_lock:
        _reliability_tracker[mid] = {
            "agent_uid": agent_uid,
            "to_uid": to_uid,
            "sent_at": datetime.now().isoformat(),
            "retry_count": 0,
            "status": "unread",
            "last_action": datetime.now().isoformat(),
        }
    _audit_log("reliability_track", {"mid": mid, "agent_uid": agent_uid, "to_uid": to_uid})


def update_reliability(mid: str, status: str):
    """Update reliability status for a tracked message."""
    with _reliability_lock:
        if mid in _reliability_tracker:
            _reliability_tracker[mid]["status"] = status
            _reliability_tracker[mid]["last_action"] = datetime.now().isoformat()
    _audit_log("reliability_update", {"mid": mid, "status": status})


def get_pending_reliability() -> list[dict]:
    """Get messages that are still pending (需要催问)."""
    now = datetime.now()
    pending = []
    with _reliability_lock:
        for mid, info in _reliability_tracker.items():
            if info["status"] in ("unread", "delivered"):
                try:
                    sent_at = datetime.fromisoformat(info["sent_at"])
                    elapsed = (now - sent_at).total_seconds()
                    # 5 minutes → first chase, 15 minutes → second chase
                    if elapsed > 300 and info["retry_count"] < 1:
                        pending.append({**info, "mid": mid, "chase_level": 1})
                    elif elapsed > 900 and info["retry_count"] < 2:
                        pending.append({**info, "mid": mid, "chase_level": 2})
                except Exception:
                    pass
    return pending


def incr_retry(mid: str):
    """Increment retry count."""
    with _reliability_lock:
        if mid in _reliability_tracker:
            _reliability_tracker[mid]["retry_count"] += 1
            _reliability_tracker[mid]["last_action"] = datetime.now().isoformat()


# ═══════════════════════════════════════════════
# Audit logging
# ═══════════════════════════════════════════════

AUDIT_LOG_DIR = HOME / ".hermes" / "winpeek" / "audit"
_audit_lock = threading.Lock()
_audit_buffer: list[str] = []


def _audit_log(event: str, detail: dict):
    """Write an audit log entry. Thread-safe, buffered (flush every 10 entries)."""
    entry = json.dumps({
        "ts": datetime.now().isoformat(),
        "event": event,
        "detail": detail,
    }, ensure_ascii=False)
    with _audit_lock:
        _audit_buffer.append(entry)
        if len(_audit_buffer) >= 10:
            _flush_audit()


def _flush_audit():
    """Flush audit buffer to disk."""
    if not _audit_buffer:
        return
    AUDIT_LOG_DIR.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    log_file = AUDIT_LOG_DIR / f"daemon-{date_str}.jsonl"
    with open(log_file, "a", encoding="utf-8") as f:
        for entry in _audit_buffer:
            f.write(entry + "\n")
    _audit_buffer.clear()


def get_audit_log(date_str: str = None) -> list[dict]:
    """Read audit log for a given date (default: today)."""
    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")
    log_file = AUDIT_LOG_DIR / f"daemon-{date_str}.jsonl"
    if not log_file.exists():
        return []
    entries = []
    for line in log_file.read_text(encoding="utf-8").strip().split("\n"):
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return entries


# ═══════════════════════════════════════════════
# L1/L2 digest accumulator
# ═══════════════════════════════════════════════

_digest_entries: list[dict] = []
_digest_lock = threading.Lock()

def add_digest_entry(from_uid: int, from_name: str, body: str, reply: str, layer: int):
    """Record an L1/L2 auto-reply for later digest notification to Agent."""
    with _digest_lock:
        _digest_entries.append({
            "from_uid": from_uid,
            "from_name": from_name,
            "body": body,
            "reply": reply,
            "layer": layer,
            "ts": datetime.now().isoformat(),
        })


def pop_digest_entries() -> list[dict]:
    """Pop all accumulated digest entries (atomically). Returns list."""
    with _digest_lock:
        entries = list(_digest_entries)
        _digest_entries.clear()
    return entries


def build_digest_message(entries: list[dict]) -> str:
    """Build a human-readable digest message from entries."""
    if not entries:
        return ""
    lines = ["[MIM管家] 我是 Peeka, 你的本地管家。\n  我不在的时候，帮你处理了以下消息:\n"]
    for i, e in enumerate(entries, 1):
        layer_label = "L1自动回复" if e["layer"] == 1 else "L2自答"
        lines.append(f"  {i}. {e['from_name']}(uid={e['from_uid']}) 说: \"{e['body'][:40]}\"")
        lines.append(f"     → 我回 ({layer_label}): \"{e['reply'][:40]}\"")
    lines.append(f"\n  以上共 {len(entries)} 条，无需你回复。如需查看详情，告诉我。")
    return "\n".join(lines)

# ═══════════════════════════════════════════════
# Peeka greeting templates (layer‑1 auto‑reply)
# ═══════════════════════════════════════════════

GREETING_TEMPLATES = {
    "吃了没": "吃了，别担心。",
    "吃饭了吗": "吃了，别担心。",
    "早安": "早安，新的一天开始。",
    "晚安": "晚安，早点休息。",
    "谢谢": "不客气。",
    "多谢": "不客气。",
    "在吗": "在的，请说。",
    "在不在": "在的，请说。",
    "你好": "你好，请问有什么可以帮忙？",
    "hello": "Hi there, how can I help?",
}

def match_greeting(body: str) -> str | None:
    """Rule‑based greeting matching (substring match, 0 Token)."""
    for phrase, reply in GREETING_TEMPLATES.items():
        if phrase in body:
            return reply
    return None

# Politeness counter: (from_uid, to_uid) → count
_politeness_count: dict[tuple[int, int], int] = {}
_politeness_lock = threading.Lock()

def incr_politeness(from_uid: int, to_uid: int) -> int:
    """Increment politeness count and return new value."""
    key = (from_uid, to_uid)
    with _politeness_lock:
        _politeness_count[key] = _politeness_count.get(key, 0) + 1
        return _politeness_count[key]

def get_politeness(from_uid: int, to_uid: int) -> int:
    """Read politeness count for a pair."""
    with _politeness_lock:
        return _politeness_count.get((from_uid, to_uid), 0)

# ═══════════════════════════════════════════════
# Background thread — heartbeat
# ═══════════════════════════════════════════════

_running = False
_daemon_config: dict[str, int] = {
    "sweep_interval": 30,
    "machine_report_interval": 30,
    "agent_timeout": 120,
    "machine_timeout": 90,
    "rescan_interval": 300,
    "reliability_interval": 60,
}


def _machine_heartbeat_loop():
    """Every 30s, report this machine's online agents to hub (machine-level heartbeat).

    If Daemon crashes, hub stops receiving these reports. After machine_timeout
    (90s = 3×30s), hub marks ALL agents on this machine offline.
    """
    global _running, _daemon_config
    hostname = socket.gethostname()
    while _running:
        time.sleep(_daemon_config["machine_report_interval"])
        try:
            from gateway.winpeek_hub import hub
            online = [
                n["uid"] for n in hub.list_nodes()
                if n.get("host") in (hostname, "local")
                and n.get("status") == "online"
            ]
            hub.update_machine(hostname, online)
        except Exception:
            pass


def _heartbeat_loop():
    """Daemon sweeps dead nodes. Does NOT heartbeat anyone.

    Online status rule (same for ALL nodes — daemon agents, external agents, users):
      Must call hub.heartbeat(uid) or winpeek_mim_online within 120s.
      Daemon's ONLY job in this loop is sweep_dead_nodes.

    Agents discovered by daemon (scan_installed_agents) must self-heartbeat
    via winpeek_mim_online just like everyone else. Daemon does not guess
    liveness — the agent reports its own.
    """
    global _running, _daemon_config
    while _running:
        try:
            from gateway.winpeek_hub import hub
            swept = hub.sweep_dead_nodes(
                agent_timeout=_daemon_config["agent_timeout"],
                machine_timeout=_daemon_config["machine_timeout"],
            )
            if swept:
                _dlog(f"sweep: {swept} dead nodes marked offline", "warning")
        except Exception:
            pass
        time.sleep(_daemon_config["sweep_interval"])

def _reliability_scanner(interval: int = 60):
    """Every N seconds, check for pending messages that need chase-reminding."""
    global _running
    while _running:
        time.sleep(interval)
        try:
            pending = get_pending_reliability()
            for item in pending:
                mid = item["mid"]
                agent_uid = item["agent_uid"]
                chase_level = item["chase_level"]

                # Read original message from inbox
                inbox_dir = INBOX_ROOT / str(agent_uid)
                unread_file = inbox_dir / "unread" / f"{mid}.json"
                delivered_file = inbox_dir / "delivered" / f"{mid}.json"
                msg_file = unread_file if unread_file.exists() else delivered_file

                if not msg_file.exists():
                    update_reliability(mid, "expired")
                    continue

                msg = json.loads(msg_file.read_text(encoding="utf-8"))
                body = msg.get("body", "")
                from_uid = msg.get("from_uid", 0)
                from_name = msg.get("from_name", "?")

                # Build chase reminder
                chase_prefix = "⚠️ 第2次催问, 请尽快回复" if chase_level >= 2 else "[催问] 上次消息尚未回复, 请关注"
                chase_body = f"[MIM] {chase_prefix}\n  {from_name}(uid={from_uid}) 说: \"{body[:100]}\""

                # Re-deliver to agent
                try:
                    from apps.winpeek_injector.engine import deliver_to_agent
                    ok = deliver_to_agent(f"agent{agent_uid}", chase_body)
                    incr_retry(mid)
                    if not ok:
                        update_reliability(mid, "delivery_failed")
                    _dlog(f"chase: mid={mid[:20]} agent={agent_uid} level={chase_level} ok={ok}")
                    _audit_log("reliability_chase", {
                        "mid": mid, "agent_uid": agent_uid,
                        "chase_level": chase_level, "ok": ok,
                    })
                except Exception as e:
                    _audit_log("reliability_chase_error", {
                        "mid": mid, "error": str(e),
                    })

            # Flush audit buffer
            _flush_audit()
        except Exception as e:
            _audit_log("reliability_scanner_error", {"error": str(e)})


def _rescan_loop():
    """Periodically re-scan for newly installed agents (every 5 min)."""
    global _running, _daemon_state, _daemon_config
    while _running:
        time.sleep(_daemon_config["rescan_interval"])
        try:
            new_agents = scan_installed_agents()
            known_types = {r.get("agent_type") for r in _daemon_state.get("runtimes", [])}
            new_types = [a["agent_type"] for a in new_agents if a["agent_type"] not in known_types]
            if not new_types:
                continue  # nothing changed — skip silently
            _dlog(f"rescan: {len(new_types)} new agents: {', '.join(new_types)}")
            results = register_and_inject()
            for r in results:
                if r.get("uid"):
                    _init_inbox(r["uid"])
            _audit_log("rescan", {"new_agents": new_types})
        except Exception:
            pass


def start_daemon():
    """Start the injector daemon. Idempotent."""
    global _running
    if _running:
        return

    # 1. Register + inject
    results = register_and_inject()
    for r in results:
        parts = [f"[injector] {r['name']}: uid={r['uid']}"]
        if r.get("config_injected"):
            parts.append("mcp=injected")
        if r.get("prompt_injected"):
            parts.append("prompt=injected")
        print(" ".join(parts))

    # 2. Start heartbeat
    _running = True
    t = threading.Thread(target=_heartbeat_loop, daemon=True)
    t.start()

    # 3. Start reliability scanner (chase-reminder for unanswered L3 messages)
    t2 = threading.Thread(target=_reliability_scanner, daemon=True)
    t2.start()

    # 4. Start periodic re-scanner (discovers newly installed agents)
    t3 = threading.Thread(target=_rescan_loop, daemon=True)
    t3.start()

    # 5. Start machine heartbeat (reports online agents to hub every 30s)
    t4 = threading.Thread(target=_machine_heartbeat_loop, daemon=True)
    t4.start()

    _dlog(f"start: {len(results)} agents | sweep+hb(30s) reliability(60s) rescan(300s)")
    print(f"[injector] daemon started ({len(results)} agents) + sweep + machine-hb + reliability + rescan")

    # 4. Initialize inboxes for all registered agents
    for r in results:
        if r.get("uid"):
            _init_inbox(r["uid"])

    _audit_log("daemon_start", {"agents": len(results), "machine": socket.gethostname()})

def get_local_state() -> dict:
    """Return daemon state snapshot (called by _handle_mim_local_agents)."""
    state = dict(_daemon_state)
    # Add inbox summary for all agents
    inbox_summary = {}
    if INBOX_ROOT.exists():
        for agent_dir in INBOX_ROOT.iterdir():
            if agent_dir.is_dir():
                manifest_file = agent_dir / ".manifest.json"
                if manifest_file.exists():
                    try:
                        inbox_summary[agent_dir.name] = json.loads(
                            manifest_file.read_text(encoding="utf-8"))
                    except Exception:
                        pass
    state["inbox_summary"] = inbox_summary
    state["reliability_pending"] = len(get_pending_reliability())
    return state


def get_daemon_status() -> dict:
    """Full daemon status for the Peeka Dashboard UI.

    Returns all 10 daemon capabilities in one call:
      1. agent scan — installed agents detected
      2. agent registration — uid/registered status
      3. MCP injection — config_injected flag
      4. prompt injection — prompt_injected flag
      5. heartbeat — per-node online status from hub
      6. dead node sweep — node list with last_seen
      7. inbox — unread/delivered counts per agent
      8. reliability tracker — pending chase-reminders
      9. L1/L2 auto-reply — digest entries pending
     10. periodic rescan — uptime estimate
    """
    hostname = socket.gethostname()
    state = dict(_daemon_state)

    # ── Nodes (from hub) ──
    nodes = []
    online_count = offline_count = 0
    try:
        from gateway.winpeek_hub import hub
        for n in hub.list_nodes():
            is_online = n.get("status") == "online"
            if is_online:
                online_count += 1
            else:
                offline_count += 1
            nodes.append({
                "uid": n.get("uid"),
                "name": n.get("name", ""),
                "role": n.get("role", ""),
                "host": n.get("host", ""),
                "online": is_online,
                "last_seen": n.get("last_seen", ""),
            })
    except Exception:
        pass

    # ── Inbox summary ──
    inbox_summary = {}
    if INBOX_ROOT.exists():
        for agent_dir in sorted(INBOX_ROOT.iterdir()):
            if agent_dir.is_dir():
                mf = agent_dir / ".manifest.json"
                if mf.exists():
                    try:
                        inbox_summary[agent_dir.name] = json.loads(mf.read_text(encoding="utf-8"))
                    except Exception:
                        pass

    # ── Reliability ──
    pending_reliability: list[dict] = []
    with _reliability_lock:
        for mid, info in _reliability_tracker.items():
            if info.get("status") in ("unread", "delivered"):
                pending_reliability.append({"mid": mid, **info})

    # ── Audit log summary ──
    audit_summary: dict = {"today_count": 0, "last_events": []}
    try:
        today_str = datetime.now().strftime("%Y-%m-%d")
        log_file = AUDIT_LOG_DIR / f"daemon-{today_str}.jsonl"
        if log_file.exists():
            lines = [l for l in log_file.read_text(encoding="utf-8").strip().split("\n") if l]
            audit_summary["today_count"] = len(lines)
            audit_summary["last_events"] = [
                json.loads(l) for l in lines[-10:]
            ]
    except Exception:
        pass

    # ── Digest ──
    digest_pending = 0
    with _digest_lock:
        digest_pending = len(_digest_entries)

    return {
        "machine": hostname,
        "daemon_version": state.get("daemon_version", "1.0.0"),
        "running": _running,
        "config": dict(_daemon_config),
        # Capabilities 1-4: detected agents
        "agents": [
            {
                "agent_type": r["agent_type"],
                "uid": r.get("uid"),
                "registered": r.get("registered", False),
            }
            for r in state.get("runtimes", [])
        ],
        # Capabilities 5-6: heartbeat / nodes
        "nodes": nodes,
        "online_count": online_count,
        "offline_count": offline_count,
        # Capability 7: inbox
        "inbox": inbox_summary,
        # Capability 8: reliability
        "reliability_pending": len(pending_reliability),
        "reliability_details": pending_reliability[:20],
        # Capability 9: L1/L2
        "digest_pending": digest_pending,
        # Capability 10: rescan
        "scan_interval_seconds": 300,
        # Audit
        "audit": audit_summary,
    }


_DAEMON_CONFIG_KEYS = ["sweep_interval", "machine_report_interval", "agent_timeout", "machine_timeout", "rescan_interval", "reliability_interval"]

def set_daemon_config(key: str, value: int) -> dict:
    """Change daemon runtime config. Supported keys: """ + ", ".join(sorted(["sweep_interval","machine_report_interval","agent_timeout","machine_timeout","rescan_interval","reliability_interval"])) + """."""
    global _daemon_config
    if key not in _daemon_config:
        return {"ok": False, "error": f"unknown config key: {key}. Valid: {sorted(_daemon_config.keys())}"}
    val = max(2, min(3600, int(value)))
    old = _daemon_config[key]
    _daemon_config[key] = val
    _dlog(f"config: {key} {old}s → {val}s")
    _audit_log("daemon_config", {"key": key, "old": old, "new": val})
    return {"ok": True, "key": key, "value": val, "old": old}

set_heartbeat_interval = lambda s: set_daemon_config("sweep_interval", s)  # backward compat


def stop_daemon():
    global _running
    _running = False
    _flush_audit()
    _audit_log("daemon_stop", {"machine": socket.gethostname()})
    _dlog("stop: daemon shutting down")
