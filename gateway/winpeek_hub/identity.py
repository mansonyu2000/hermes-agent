"""
identity.py — WinPeek MIM identity management with MySQL persistence.

Uses winpeek-db2.users table (192.168.3.23:3306).
Provides: register, login, get_identity, list_identities.
"""

import hashlib
import logging
import socket
import time
from typing import Optional

from .db import get_conn

logger = logging.getLogger(__name__)

ROLES = ["Developer", "Architect", "Ops", "QA", "PM", "Director", "Boss"]

# Agent type abbreviations for PeekaName
AGENT_TYPE_ABBR = {
    "claude-code": "CC",
    "hermes": "HM",
    "qoder": "QD",
    "traecli": "TC",
}

def _build_peeka_name(nickname: str, agent_type: str = "", hostname: str = "", ip: str = "") -> str:
    """Build PeekaName: {prefix}{abbr}-{hostname}{-ip}-hotime.cn

    e.g. pigCC-YU2-192.168.3.44-hotime.cn
    """
    abbr = AGENT_TYPE_ABBR.get(agent_type, "XX")
    # Extract prefix: remove the agent_type abbreviation suffix and machine suffix
    prefix = nickname
    for suffix in [f"-{abbr}", f"-{hostname}", abbr]:
        if prefix.endswith(suffix):
            prefix = prefix[: -len(suffix)]
            break
    if not hostname:
        hostname = socket.gethostname()
    ip_part = f"-{ip}" if ip else ""
    return f"{prefix}{abbr}-{hostname}{ip_part}-hotime.cn"


def _hash_password(password: str) -> str:
    """SHA256 hash of password."""
    return hashlib.sha256(password.encode()).hexdigest()


def register(nickname: str, role: str = "Developer", host: str = "local", password: str = "") -> dict | None:
    """
    Register a new identity. Returns the created identity, or None if nickname taken.
    """
    if role not in ROLES:
        role = "Developer"

    conn = get_conn()
    if conn is None:
        return None
    try:
        with conn.cursor() as cur:
            # Check duplicate nickname
            cur.execute("SELECT uid FROM users WHERE nickname = %s", (nickname,))
            if cur.fetchone():
                return None  # already exists

            # Generate next uid (keep in the 2000+ range for MIM users)
            cur.execute("SELECT COALESCE(MAX(uid), 1999) + 1 AS next_uid FROM users WHERE uid >= 2000")
            next_uid = cur.fetchone()["next_uid"]

            now = time.strftime("%Y-%m-%dT%H:%M:%SZ")
            pw_hash = _hash_password(password) if password else ""
            cur.execute(
                """INSERT INTO users (uid, nickname, role, hostname, created_at, updated_at, is_active, identity_type, status, password_hash)
                   VALUES (%s, %s, %s, %s, %s, %s, 1, 'mim', 1, %s)""",
                (next_uid, nickname, role, host, now, now, pw_hash),
            )
            conn.commit()

            identity = {
                "uid": next_uid,
                "nickname": nickname,
                "role": role,
                "host": host,
                "created_at": now,
            }
            logger.info(f"MIM identity registered: uid={next_uid} name={nickname}")
            return identity
    except Exception as e:
        logger.warning(f"MIM register failed: {e}")
        return None
    finally:
        conn.close()


def login(nickname: str, password: str = "") -> dict | None:
    """
    Login by nickname + password. Returns identity if found and password matches.
    """
    conn = get_conn()
    if conn is None:
        return None
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT uid, nickname, role, hostname, created_at, password_hash, title, bio, skills, manager_uid FROM users WHERE nickname = %s",
                (nickname,),
            )
            row = cur.fetchone()
            if row:
                stored_hash = row.get("password_hash") or ""
                # If user has no password set, allow login without password (backward compat)
                if stored_hash and _hash_password(password) != stored_hash:
                    return None  # wrong password
                return _row_to_dict(row)
            return None
    finally:
        conn.close()


def _row_to_dict(row: dict) -> dict:
    """Convert a DB row to the identity dict."""
    host = row.get("hostname", "local")
    nickname = row["nickname"]
    agent_type = row.get("agent_type", "")
    return {
        "uid": row["uid"],
        "nickname": nickname,
        "role": row["role"],
        "host": host,
        "agent_type": agent_type,
        "peeka_name": _build_peeka_name(nickname, agent_type, host),
        "title": row.get("title") or "",
        "bio": row.get("bio") or "",
        "skills": row.get("skills") or "",
        "manager_uid": int(row["manager_uid"]) if row.get("manager_uid") else 0,
        "created_at": str(row.get("created_at", "")),
    }


def get_by_uid(uid: int) -> Optional[dict]:
    """Get identity by uid."""
    conn = get_conn()
    if conn is None:
        return None
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT uid, nickname, role, hostname, created_at, title, bio, skills, manager_uid FROM users WHERE uid = %s",
                (uid,),
            )
            row = cur.fetchone()
            if row:
                return _row_to_dict(row)
            return None
    finally:
        conn.close()


def list_all() -> list[dict]:
    """List all registered identities."""
    conn = get_conn()
    if conn is None:
        return []
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT uid, nickname, role, hostname, created_at, title, bio, skills, manager_uid FROM users WHERE is_active = 1 OR is_active IS NULL ORDER BY uid"
            )
            return [_row_to_dict(row) for row in cur.fetchall()]
    finally:
        conn.close()
