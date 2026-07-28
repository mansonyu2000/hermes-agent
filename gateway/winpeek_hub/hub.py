"""MIM Node Hub — register, heartbeat, dead detection.

Each agent is a 'node' with online status.
Heartbeat every 30s. Auto-offline after 120s without heartbeat.
"""

import json, os, time, threading
from pathlib import Path
from datetime import datetime
from typing import Optional

STATE_PATH = Path.home() / ".hermes" / "winpeek" / "nodes.json"
_state_lock = threading.Lock()  # protect concurrent read-modify-write

# ── Persistence (thread-safe, 0o600) ────────────

def _read_state() -> dict:
    if not STATE_PATH.exists():
        return {"nodes": {}}
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"nodes": {}}

def _write_state(state: dict):
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(STATE_PATH), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

# ── Register ─────────────────────────────────────

def register_node(uid: int, name: str, role: str = "Agent", host: str = "local") -> dict:
    """Register this agent as an online node."""
    return _upsert_node(uid, name, role, host, overwrite=True)


def ensure_node(uid: int, name: str, role: str = "Agent", host: str = "local") -> dict:
    """Idempotent: register if not exists. register_node() for overwrite."""
    return _upsert_node(uid, name, role, host, overwrite=False)


def _upsert_node(uid: int, name: str, role: str, host: str, overwrite: bool) -> dict:
    with _state_lock:
        state = _read_state()
        node_id = str(uid)
        now = datetime.now().isoformat()
        existing = state["nodes"].get(node_id, {})
        if not existing:
            # New node — start offline, wait for first heartbeat
            state["nodes"][node_id] = {
                "uid": uid,
                "name": name,
                "role": role,
                "host": host,
                "status": "offline",
                "last_seen": now,
                "first_seen": now,
            }
        elif overwrite:
            state["nodes"][node_id].update({
                "name": name, "role": role, "host": host,
                "status": "online", "last_seen": now,
            })
        else:
            # ensure_node: keep existing state, don't touch status
            pass
        _write_state(state)
        return state["nodes"][node_id]

def heartbeat(uid: int):
    """Update last_seen timestamp."""
    with _state_lock:
        state = _read_state()
        node_id = str(uid)
        if node_id in state["nodes"]:
            state["nodes"][node_id]["last_seen"] = datetime.now().isoformat()
            state["nodes"][node_id]["status"] = "online"
        _write_state(state)

def mark_offline(uid: int):
    """Mark a node as offline."""
    with _state_lock:
        state = _read_state()
        node_id = str(uid)
        if node_id in state["nodes"]:
            state["nodes"][node_id]["status"] = "offline"
        _write_state(state)

# ── Machine heartbeat (Daemon → Hub aggregation) ──

_machine_heartbeats: dict[str, tuple[datetime, list[int]]] = {}  # hostname → (last_seen, [uid,...])
_machine_lock = threading.Lock()


def update_machine(hostname: str, online_uids: list[int]):
    """Daemon reports the full list of online agents on this machine."""
    with _machine_lock:
        _machine_heartbeats[hostname] = (datetime.now(), online_uids)


# ── Dead detection ───────────────────────────────

def mark_all_offline(host: str = ""):
    """Mark all (or host-specific) nodes offline. Called on shutdown."""
    with _state_lock:
        state = _read_state()
        for node_id, node in list(state["nodes"].items()):
            if node["status"] == "online" and (not host or node.get("host") == host):
                node["status"] = "offline"
        _write_state(state)


def sweep_dead_nodes(agent_timeout: int = 120, machine_timeout: int = 90) -> int:
    """Two-level dead detection.

    agent_timeout: node-level — agent's own heartbeat (winpeek_mim_online).
      If last_seen > agent_timeout, mark offline.

    machine_timeout: machine-level — Daemon's heartbeat (update_machine).
      If Daemon hasn't reported for machine_timeout, ALL agents on that
      machine are marked offline (Daemon crashed, all agents unreachable).
    """
    with _state_lock:
        state = _read_state()
        now = datetime.now()
        count = 0

        # Agent-level sweep
        for node_id, node in list(state["nodes"].items()):
            if node["status"] == "online":
                try:
                    last = datetime.fromisoformat(node["last_seen"])
                    if (now - last).total_seconds() > agent_timeout:
                        node["status"] = "offline"
                        count += 1
                except Exception:
                    pass

        # Machine-level sweep: Daemon stopped reporting → whole machine offline
        with _machine_lock:
            dead_machines = []
            for host, (ts, uids) in list(_machine_heartbeats.items()):
                if (now - ts).total_seconds() > machine_timeout:
                    dead_machines.append((host, uids))
                    del _machine_heartbeats[host]
        for host, uids in dead_machines:
            for uid in uids:
                if str(uid) in state["nodes"] and state["nodes"][str(uid)]["status"] == "online":
                    state["nodes"][str(uid)]["status"] = "offline"
                    count += 1

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
