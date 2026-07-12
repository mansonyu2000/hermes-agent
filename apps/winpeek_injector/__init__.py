"""WinPeek Agent Injector — daemon + engine.

Auto-started by hub_bridge.try_load_hub() when WINPEEK_HUB_ENABLED=1.
Scans local AI agents, registers them, injects MCP config, maintains heartbeat.

Also provides the delivery pipeline:
  MIM message arrives via MQTT → chat.py enqueue → deliver_to_agent()
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
