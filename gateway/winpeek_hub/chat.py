"""MIM message engine — send, receive, contacts, history.

Per-user SQLite at ~/.hermes/winpeek/data/uid{uid}/mim.db
Memory queue bridges MQTT incoming → frontend polling.
Each user's chat records stored independently — switch user, see own history.
"""

import json, sqlite3, time
from datetime import datetime
from pathlib import Path
from typing import Optional

DATA_ROOT = Path.home() / ".hermes" / "winpeek" / "data"

# ── Active session ────────────────────────────────

_active_uid: int = 0
_active_name: str = ""

def _user_dir(uid: int = None) -> Path:
    uid = uid if uid is not None else _active_uid
    return DATA_ROOT / f"uid{uid}" if uid else DATA_ROOT / "_default"

def _user_db(uid: int = None) -> Path:
    return _user_dir(uid) / "mim.db"

def set_active_session(uid: int, name: str = ""):
    global _active_uid, _active_name
    _active_uid = uid
    _active_name = name
    if uid:
        _db()  # init DB for this user on first switch

def active_uid() -> int:
    return _active_uid

def active_name() -> str:
    return _active_name

# ── DB (per-user) ─────────────────────────────────

def _db():
    db_path = _user_db()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
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
    conn.execute("CREATE INDEX IF NOT EXISTS idx_msg_peer ON messages(from_uid, to_uid)")
    conn.commit()
    return conn

# ── Memory queue ─────────────────────────────────

_pending: list[dict] = []

def enqueue(msg: dict):
    _pending.append(msg)

def poll_messages(to_uid: int) -> list[dict]:
    mine = [m for m in _pending if m.get("to_uid") == to_uid]
    _pending[:] = [m for m in _pending if m.get("to_uid") != to_uid]
    return mine

# ── Send ────────────────────────────────────────

def send_message(from_uid: int, from_name: str, to_uid: int, body: str) -> dict:
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
        pass

    return {"ok": True, "msg_ts": ts}

# ── History ─────────────────────────────────────

def get_history(uid: int, peer_uid: int, limit: int = 50) -> list[dict]:
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
    try:
        from gateway.winpeek_hub import identity
        return identity.list_all()
    except Exception:
        return []
