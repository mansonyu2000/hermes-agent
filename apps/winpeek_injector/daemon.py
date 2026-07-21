"""Agent Daemon — background service, auto-started with hermes serve.

Migrated from PeekabooWin agent-discovery.js + agent-launcher.js.
Scans local .claude/.hermes/.qoder config directories, registers agents
to identity DB, injects MIM MCP config, maintains heartbeat.

Runs silently — no window, no tray (yet). Started by hub_bridge.try_load_hub().
"""

import json, os, socket, stat, time, threading
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
        password = "123321"  # aligned with tool‑layer default

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

        results.append({
            "agent_type": agent_type,
            "name": name,
            "uid": uid,
            "config_injected": injected,
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

def get_local_state() -> dict:
    """Return daemon state snapshot (called by _handle_mim_local_agents)."""
    return _daemon_state

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

def start_daemon():
    """Start the injector daemon. Idempotent."""
    global _running
    if _running:
        return

    # 1. Register + inject
    results = register_and_inject()
    for r in results:
        print(f"[injector] {r['name']}: uid={r['uid']} injected={r['config_injected']}")

    # 2. Start heartbeat
    _running = True
    t = threading.Thread(target=_heartbeat_loop, daemon=True)
    t.start()
    print(f"[injector] daemon started ({len(results)} agents)")

def stop_daemon():
    global _running
    _running = False
