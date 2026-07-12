"""MIM message engine — send, receive, contacts, history.

SQLite storage at ~/.hermes/winpeek/mim.db.
Memory queue bridges MQTT incoming → frontend polling.
"""

import json, sqlite3, time
from datetime import datetime
from pathlib import Path
from typing import Optional

DB_PATH = Path.home() / ".hermes" / "winpeek" / "mim.db"

# ── DB ──────────────────────────────────────────

def _db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_uid INTEGER NOT NULL,
            to_uid INTEGER NOT NULL,
            from_name TEXT,
            content TEXT NOT NULL,
            msg_ts TEXT NOT NULL DEFAULT (datetime('now','localtime'))
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_msg_to ON messages(to_uid)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_msg_from ON messages(from_uid)")
    conn.commit()
    return conn

# ── Memory queue ─────────────────────────────────

_pending: list[dict] = []

def enqueue(msg: dict):
    """Called by mqtt_adapter._on_message when MQTT message arrives."""
    _pending.append(msg)

def poll_messages(to_uid: int) -> list[dict]:
    """Called by winpeek_mim_poll every 3s. Returns + clears queue."""
    mine = [m for m in _pending if m.get("to_uid") == to_uid]
    _pending[:] = [m for m in _pending if m.get("to_uid") != to_uid]
    return mine

# ── Send ────────────────────────────────────────

def send_message(from_uid: int, from_name: str, to_uid: int, body: str) -> dict:
    """Persist to SQLite, then publish via MQTT."""
    conn = _db()
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        "INSERT INTO messages (from_uid, to_uid, from_name, content, msg_ts) VALUES (?,?,?,?,?)",
        (from_uid, to_uid, from_name, body, ts))
    conn.commit()
    conn.close()

    try:
        from gateway.winpeek_hub.mqtt_adapter import send_message as mqtt_send
        mqtt_send(to_uid, body, from_name)
    except Exception:
        pass  # MQTT is best-effort; message is already in SQLite

    return {"ok": True, "msg_ts": ts}

# ── History ─────────────────────────────────────

def get_history(uid: int, peer_uid: int, limit: int = 50) -> list[dict]:
    """Get conversation history between two uids."""
    conn = _db()
    rows = conn.execute(
        """SELECT from_uid, to_uid, from_name, content, msg_ts
           FROM messages
           WHERE (from_uid=? AND to_uid=?) OR (from_uid=? AND to_uid=?)
           ORDER BY id DESC LIMIT ?""",
        (uid, peer_uid, peer_uid, uid, limit)).fetchall()
    conn.close()
    return [dict(r) for r in reversed(rows)]

# ── Contacts ────────────────────────────────────

def get_contacts() -> list[dict]:
    """List all identities as contacts."""
    try:
        from gateway.winpeek_hub import identity
        return identity.list_all()
    except Exception:
        return []
