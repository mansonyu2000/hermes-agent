"""MIM message engine — send, receive, contacts, history.

Uses winpeek-db2 MySQL (chat, contacts tables).
Memory queue bridges MQTT incoming → frontend polling.
"""

import json
import logging
import os
import time
import uuid
from datetime import datetime
from typing import Optional

import pymysql
from pymysql.cursors import DictCursor

logger = logging.getLogger(__name__)

_DB_CONFIG = {
    "host": os.getenv("WINPEEK_DB_HOST", "192.168.3.23"),
    "port": int(os.getenv("WINPEEK_DB_PORT", "3306")),
    "user": os.getenv("WINPEEK_DB_USER", "winpeek"),
    "password": os.getenv("WINPEEK_DB_PASS", "Server33"),
    "database": os.getenv("WINPEEK_DB_NAME", "winpeek-db2"),
}


def _get_conn():
    return pymysql.connect(**_DB_CONFIG, cursorclass=DictCursor)


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


# ── Memory queue (MQTT → frontend polling bridge) ─

_pending: list[dict] = []


def enqueue(msg: dict):
    _pending.append(msg)


def poll_messages(to_uid: int) -> list[dict]:
    mine = [m for m in _pending if m.get("to_uid") == to_uid]
    _pending[:] = [m for m in _pending if m.get("to_uid") != to_uid]
    return mine


# ── Send ────────────────────────────────────────

def _next_mid() -> str:
    """Generate a message ID: mim-{timestamp}-{random}"""
    return f"mim-{int(time.time()*1000)}-{uuid.uuid4().hex[:8]}"


def send_message(from_uid: int, from_name: str, to_uid: int, body: str) -> dict:
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            mid = _next_mid()
            cid = str(uuid.uuid4().hex[:16])
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            cur.execute(
                """INSERT INTO chat
                   (mid, cid, from_uid, to_uid, role, content, from_type,
                    created_at, sent_at, direction, delivery_status)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (mid, cid, from_uid, to_uid, "user", body, "mim",
                 now, now, "outgoing", "sent"),
            )
            conn.commit()

            # Update or create contact
            cur.execute(
                "SELECT id FROM contacts WHERE uid = %s AND c_uid = %s",
                (from_uid, to_uid),
            )
            if cur.fetchone():
                cur.execute(
                    "UPDATE contacts SET last_message = %s, last_contact_at = %s WHERE uid = %s AND c_uid = %s",
                    (body, now, from_uid, to_uid),
                )
            else:
                # Get peer name
                cur.execute("SELECT nickname FROM users WHERE uid = %s", (to_uid,))
                peer = cur.fetchone()
                peer_name = peer["nickname"] if peer else f"user_{to_uid}"
                cur.execute(
                    "INSERT INTO contacts (uid, c_uid, display_name, last_message, last_contact_at, first_contact_at, status) "
                    "VALUES (%s, %s, %s, %s, %s, %s, 1)",
                    (from_uid, to_uid, peer_name, body, now, now),
                )
            conn.commit()
    except Exception as e:
        logger.warning(f"MIM send DB failed: {e}")
        return {"ok": False, "error": str(e)}
    finally:
        conn.close()

    # MQTT publish
    try:
        from gateway.winpeek_hub.mqtt_adapter import send_message as mqtt_send
        mqtt_send(to_uid, body, from_name)
    except Exception:
        pass

    return {"ok": True, "mid": mid}


# ── History ─────────────────────────────────────

def get_history(uid: int, peer_uid: int, limit: int = 50) -> list[dict]:
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT from_uid, to_uid, role, content, created_at
                   FROM chat
                   WHERE (from_uid = %s AND to_uid = %s)
                      OR (from_uid = %s AND to_uid = %s)
                   ORDER BY id DESC LIMIT %s""",
                (uid, peer_uid, peer_uid, uid, limit),
            )
            rows = list(reversed(cur.fetchall()))
            return [
                {
                    "from_uid": r["from_uid"],
                    "to_uid": r["to_uid"],
                    "from_name": "",
                    "content": r["content"],
                    "msg_ts": str(r.get("created_at", "")),
                }
                for r in rows
            ]
    finally:
        conn.close()


# ── Contacts ────────────────────────────────────

def get_contacts() -> list[dict]:
    """Get all users as contacts (identity.list_all equivalent)."""
    try:
        from gateway.winpeek_hub import identity
        return identity.list_all()
    except Exception:
        return []


def get_user_contacts(uid: int) -> list[dict]:
    """Get contacts for a specific user from contacts table."""
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT c.c_uid, c.display_name, c.last_message,
                          c.unread_count, c.last_contact_at, u.role, u.hostname
                   FROM contacts c
                   LEFT JOIN users u ON c.c_uid = u.uid
                   WHERE c.uid = %s
                   ORDER BY c.last_contact_at DESC""",
                (uid,),
            )
            return [
                {
                    "uid": r["c_uid"],
                    "nickname": r["display_name"],
                    "role": r.get("role", ""),
                    "host": r.get("hostname", ""),
                    "last_message": r.get("last_message", ""),
                    "unread": r.get("unread_count", 0),
                }
                for r in cur.fetchall()
            ]
    finally:
        conn.close()
