"""MIM message engine — send, receive, contacts, history.

Storage: MySQL winpeek-db2.chat + contacts tables (shared with PeekabooWin).
Memory queue bridges MQTT incoming → frontend polling.
"""

import json
import logging
from datetime import datetime
from uuid import uuid4

from .db import get_conn

logger = logging.getLogger(__name__)

# ── Active session ────────────────────────────────

_active_uid: int = 0
_active_name: str = ""


def set_active_session(uid: int, name: str = ""):
    global _active_uid, _active_name
    _active_uid = uid
    _active_name = name


def active_uid() -> int:
    return _active_uid


def active_name() -> str:
    return _active_name


# ── Memory queue (remains in-memory for poll) ────

_pending: list[dict] = []


def enqueue(msg: dict):
    _pending.append(msg)


def poll_messages(to_uid: int) -> list[dict]:
    mine = [m for m in _pending if m.get("to_uid") == to_uid]
    _pending[:] = [m for m in _pending if m.get("to_uid") != to_uid]
    return mine


# ── Helpers ───────────────────────────────────────

def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _mid() -> str:
    return uuid4().hex[:12]


# ── Send ────────────────────────────────────────

def send_message(from_uid: int, from_name: str, to_uid: int, body: str) -> dict:
    conn = get_conn()
    if not conn:
        return {"ok": False, "error": "database unavailable"}

    try:
        cur = conn.cursor()
        mid = _mid()
        now = _now()

        cur.execute(
            """INSERT INTO chat (mid, cid, from_uid, to_uid, role, content, created_at, direction)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
            (mid, f"mim:{from_uid}:{to_uid}", from_uid, to_uid, "user", body, now, "out"),
        )

        # upsert contact (sender's perspective)
        cur.execute(
            """INSERT INTO contacts (uid, c_uid, display_name, last_contact_at, last_message)
               VALUES (%s,%s,%s,%s,%s)
               ON DUPLICATE KEY UPDATE last_contact_at=%s, last_message=%s""",
            (from_uid, to_uid, from_name, now, body, now, body),
        )

        conn.commit()

        try:
            from gateway.winpeek_hub.mqtt_adapter import send_message as mqtt_send
            mqtt_send(to_uid, body, from_name)
        except Exception:
            pass

        return {"ok": True, "mid": mid, "msg_ts": now}

    except Exception as e:
        logger.error(f"send_message failed: {e}")
        return {"ok": False, "error": str(e)}
    finally:
        conn.close()


# ── History ─────────────────────────────────────

def get_history(uid: int, peer_uid: int, limit: int = 50) -> list[dict]:
    conn = get_conn()
    if not conn:
        return []
    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT from_uid, to_uid, role, content, created_at
               FROM chat
               WHERE (from_uid=%s AND to_uid=%s) OR (from_uid=%s AND to_uid=%s)
               ORDER BY id DESC LIMIT %s""",
            (uid, peer_uid, peer_uid, uid, limit),
        )
        rows = cur.fetchall()
        return [{"from_uid": r[0], "to_uid": r[1], "role": r[2], "content": r[3], "msg_ts": str(r[4])}
                for r in reversed(rows)]
    finally:
        conn.close()


# ── Contacts ────────────────────────────────────

def get_contacts(uid: int = None) -> list[dict]:
    """Get contacts for a user (or all if uid is None)."""
    conn = get_conn()
    if not conn:
        return []
    try:
        cur = conn.cursor()
        if uid:
            cur.execute(
                """SELECT c.c_uid, u.nickname, u.role, c.last_message, c.last_contact_at, c.unread_count
                   FROM contacts c JOIN users u ON c.c_uid = u.uid
                   WHERE c.uid = %s AND c.status = 1 ORDER BY c.last_contact_at DESC""",
                (uid,),
            )
        else:
            cur.execute(
                """SELECT c.c_uid, u.nickname, u.role, c.last_message, c.last_contact_at, c.unread_count
                   FROM contacts c JOIN users u ON c.c_uid = u.uid
                   WHERE c.status = 1 ORDER BY c.last_contact_at DESC"""
            )
        rows = cur.fetchall()
        return [{"uid": r[0], "name": r[1], "role": r[2], "last_message": r[3],
                  "last_time": str(r[4]) if r[4] else None, "unread": r[5] or 0} for r in rows]
    finally:
        conn.close()
