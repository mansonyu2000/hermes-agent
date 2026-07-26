"""MIM Node Hub — register, heartbeat, dead detection.

Each agent is a 'node' with online status.
Heartbeat every 30s. Auto-offline after 120s without heartbeat.
"""

import json, time
from pathlib import Path
from datetime import datetime
from typing import Optional

STATE_PATH = Path.home() / ".hermes" / "winpeek" / "nodes.json"

# ── Persistence ─────────────────────────────────

def _read_state() -> dict:
    if not STATE_PATH.exists():
        return {"nodes": {}}
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"nodes": {}}

def _write_state(state: dict):
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")

# ── Register ─────────────────────────────────────

def register_node(uid: int, name: str, role: str = "Agent", host: str = "local") -> dict:
    """Register this agent as an online node."""
    state = _read_state()
    node_id = str(uid)
    now = datetime.now().isoformat()
    state["nodes"][node_id] = {
        "uid": uid,
        "name": name,
        "role": role,
        "host": host,
        "status": "online",
        "last_seen": now,
        "first_seen": state["nodes"].get(node_id, {}).get("first_seen", now),
    }
    _write_state(state)
    return state["nodes"][node_id]

def heartbeat(uid: int):
    """Update last_seen timestamp. Auto-register if not yet known."""
    state = _read_state()
    node_id = str(uid)
    if node_id not in state["nodes"]:
        # Lookup name from identity DB
        name = f"uid_{uid}"
        try:
            from gateway.winpeek_hub import identity
            user = identity.get_by_uid(uid)
            if user:
                name = user.get("nickname", name)
        except Exception:
            pass
        # Auto-register from MQTT activity
        state["nodes"][node_id] = {
            "uid": uid,
            "name": name,
            "role": "Agent",
            "host": "mqtt",
            "status": "online",
            "last_seen": datetime.now().isoformat(),
            "first_seen": datetime.now().isoformat(),
        }
    else:
        state["nodes"][node_id]["last_seen"] = datetime.now().isoformat()
        state["nodes"][node_id]["status"] = "online"
    _write_state(state)

def mark_offline(uid: int):
    """Mark a node as offline."""
    state = _read_state()
    node_id = str(uid)
    if node_id in state["nodes"]:
        state["nodes"][node_id]["status"] = "offline"
    _write_state(state)

# ── Dead detection ───────────────────────────────

def sweep_dead_nodes(timeout_seconds: int = 120) -> int:
    """Mark nodes offline if last_seen > timeout. Returns count of nodes swept."""
    state = _read_state()
    now = datetime.now()
    count = 0
    for node_id, node in list(state["nodes"].items()):
        if node["status"] == "online":
            try:
                last = datetime.fromisoformat(node["last_seen"])
                if (now - last).total_seconds() > timeout_seconds:
                    node["status"] = "offline"
                    count += 1
            except Exception:
                pass
    _write_state(state)
    return count

# ── Query ────────────────────────────────────────

def is_online(uid: int) -> bool:
    state = _read_state()
    node = state["nodes"].get(str(uid), {})
    return node.get("status") == "online"

def list_nodes() -> list[dict]:
    state = _read_state()
    return list(state["nodes"].values())
