"""Agent Daemon — background service, auto-started with hermes serve.

Migrated from PeekabooWin agent-discovery.js + agent-launcher.js.
Scans local .claude/.hermes/.qoder config directories, registers agents
to identity DB, injects MIM MCP config, maintains heartbeat.

Runs silently — no window, no tray (yet). Started by hub_bridge.try_load_hub().
"""

import json, os, stat, time, threading
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
# Scanner + injector
# ═══════════════════════════════════════════════

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
    if not config_path.exists():
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
    agents = scan_installed_agents()
    results = []

    try:
        from gateway.winpeek_hub import identity
    except ImportError:
        return results

    for scanner in agents:
        name = scanner["name"]
        agent_type = scanner["agent_type"]

        # Register identity if not exists
        existing = identity.login(name)
        if not existing:
            existing = identity.register(name, "Agent", agent_type)

        uid = existing.get("uid") if existing else None

        # Inject MCP config
        injected = False
        if scanner["config_file"]:
            injected = inject_mcp_config(scanner["config_file"])

        results.append({
            "agent_type": agent_type,
            "name": name,
            "uid": uid,
            "config_injected": injected,
            "config_file": str(scanner["config_file"]),
        })

    return results

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
