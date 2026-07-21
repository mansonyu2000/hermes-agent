"""Agent Daemon — background service, auto-started with hermes serve.

Migrated from PeekabooWin agent-discovery.js + agent-launcher.js.
Scans local .claude/.hermes/.qoder config directories, registers agents
to identity DB, injects MIM MCP config, maintains heartbeat.

Runs silently — no window, no tray (yet). Started by hub_bridge.try_load_hub().
"""

import json, os, secrets, socket, stat, time, threading
from datetime import datetime
from pathlib import Path

HOME = Path.home()

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

# Password file: ~/.hermes/winpeek/agent_passwords.json — {agent_name: password}
_PASSWORD_FILE = HOME / ".hermes" / "winpeek" / "agent_passwords.json"


def _get_or_create_agent_password(agent_name: str) -> str:
    """Retrieve or generate a unique CSPRNG password per agent.

    Passwords persisted to _PASSWORD_FILE with owner-only permissions (0o600).
    One password per agent name, generated once at registration time.
    """
    passwords: dict = {}
    if _PASSWORD_FILE.exists():
        try:
            passwords = json.loads(_PASSWORD_FILE.read_text(encoding="utf-8"))
        except Exception:
            passwords = {}
    if agent_name in passwords:
        return passwords[agent_name]
    # Generate new: 16 URL-safe random bytes → ~22 chars
    pw = secrets.token_urlsafe(16)
    passwords[agent_name] = pw
    _PASSWORD_FILE.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(_PASSWORD_FILE), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(passwords, f, indent=2, ensure_ascii=False)
    return pw


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

    for scanner in agents:
        name = scanner["name"]
        agent_type = scanner["agent_type"]

        # Generate or retrieve a unique per-agent password (CSPRNG, persisted)
        password = _get_or_create_agent_password(name)

        # Login or register
        existing = identity.login(name, password)
        if not existing:
            existing = identity.register(name, "Agent", hostname, password)
            # If register succeeds, login to get the full identity record
            if existing:
                existing = identity.login(name, password)

        uid = existing.get("uid") if existing else None

        # Inject MCP config (skip for types without config_file like traecli)
        injected = False
        if scanner.get("config_file"):
            injected = inject_mcp_config(scanner["config_file"])

        # Inject MIM identity block into agent prompt file
        prompt_injected = False
        if uid and scanner.get("agent_type"):
            prompt_injected = _inject_agent_prompt(uid, existing, scanner)

        # Initialize inbox for this agent
        if uid:
            _init_inbox(uid)

        results.append({
            "agent_type": agent_type,
            "name": name,
            "uid": uid,
            "config_injected": injected,
            "prompt_injected": prompt_injected,
            "config_file": str(scanner.get("config_file", "")),
        })

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
    "hermes": HOME / ".hermes" / "config.yaml",
    "qoder": HOME / ".qoder" / "AGENTS.md",
}


def _build_identity_block(uid: int, identity: dict, scanner: dict) -> str:
    """Build the MIM_IDENTITY_BLOCK markdown for an agent."""
    hostname = socket.gethostname()
    peeka_name = identity.get("peeka_name", f"agent{uid}-{hostname}-hotime.cn")
    role = identity.get("role", "Agent")
    name = identity.get("nickname", scanner.get("name", ""))
    squad = identity.get("squad_name", "")
    manager_uid = identity.get("manager_uid", 0)

    block = f"""
<!-- MIM_IDENTITY_BLOCK — auto‑injected by Peeka Daemon, do not edit manually -->

[MIM Identity]
uid: {uid}
name: {name}
role: {role}
peeka_name: {peeka_name}
squad: {squad or "(未加入组织)"}
manager_uid: {manager_uid or 0}
inbox_path: {HOME / '.hermes' / 'winpeek' / 'inbox' / str(uid)}
hostname: {hostname}

[MIM Commands]
- 发送回复: say <uid> "消息内容"
- 查阅收信箱: 查看 inbox_path/unread/ 目录
- 查看联系人: curl http://192.168.3.44:2000/api/contacts
- 有疑问: 先问本地 Daemon, 再问上级 (manager_uid={manager_uid})

[MIM Rules]
- 你是多 Agent 网络中的一员, Daemon 是你的本地管家
- 收到 [MIM] 开头的消息后, 自主用 LLM 判断是否回复
- 回复时执行 say <uid> "内容" 即可, Daemon 负责送达
- Daemon 可能会催问未回复的消息, 请及时处理
- 不必回复的消息: 广告(已过滤)、问候(Daemon 已代答)
<!-- /MIM_IDENTITY_BLOCK -->
"""
    return block.strip()


def _inject_agent_prompt(uid: int, identity: dict, scanner: dict) -> bool:
    """Write MIM_IDENTITY_BLOCK into the agent's prompt/config file.

    Idempotent — checks if block already exists before writing.
    Keeps existing file content intact outside the block.
    """
    prompt_file = AGENT_PROMPT_FILES.get(scanner.get("agent_type"))
    if not prompt_file:
        return False

    block = _build_identity_block(uid, identity, scanner)
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

def incr_politeness(from_uid: int, to_uid: int) -> int:
    """Increment politeness count and return new value."""
    key = (from_uid, to_uid)
    _politeness_count[key] = _politeness_count.get(key, 0) + 1
    return _politeness_count[key]

def get_politeness(from_uid: int, to_uid: int) -> int:
    """Read politeness count for a pair."""
    return _politeness_count.get((from_uid, to_uid), 0)

# ═══════════════════════════════════════════════
# Background thread — heartbeat
# ═══════════════════════════════════════════════

_running = False

def _heartbeat_loop(interval: int = 30):
    """Every N seconds, bump heartbeat for all registered identities."""
    global _running
    while _running:
        try:
            from gateway.winpeek_hub import hub, identity
            for entry in identity.list_all():
                uid = entry.get("uid")
                if uid:
                    hub.heartbeat(uid)
        except Exception:
            pass
        time.sleep(interval)

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

    print(f"[injector] daemon started ({len(results)} agents) + reliability scanner + inbox manager")

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


def stop_daemon():
    global _running
    _running = False
    _flush_audit()
    _audit_log("daemon_stop", {"machine": socket.gethostname()})
