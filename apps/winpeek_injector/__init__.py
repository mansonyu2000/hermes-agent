"""WinPeek Agent Injector — daemon + engine + conpty.

Auto-started by hub_bridge.try_load_hub() when WINPEEK_HUB_ENABLED=1.
Scans local AI agents, registers them, injects MCP config, maintains heartbeat.

Three injection modes:
  rpa     — Clipboard paste (grabs keyboard)
  backend — SendInput batch (non-blocking)
  conpty  — ConPTY device-level (no focus, best for terminals)
"""

from .engine import (
    activate_window,
    inject_rpa,
    inject_backend,
    deliver_to_agent,
    list_windows,
    load_config,
    save_config,
)
from .daemon import (
    start_daemon,
    stop_daemon,
    scan_installed_agents,
    register_and_inject,
)
