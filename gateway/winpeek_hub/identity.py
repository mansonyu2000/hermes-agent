"""
identity.py — WinPeek MIM identity management with MySQL persistence.

Uses winpeek-db2.users table (shared with PeekabooWin).
Provides: register, login, get_identity, list_all.
"""

import time
import logging
from typing import Optional

from .db import get_conn

logger = logging.getLogger(__name__)

ROLES = ["Developer", "Architect", "Ops", "QA", "PM", "Director", "Boss"]


def _next_uid() -> int:
    """获取下一个可用 UID（max + 1，最小 2001）。"""
    conn = get_conn()
    if not conn:
        return 2001
    try:
        cur = conn.cursor()
        cur.execute("SELECT COALESCE(MAX(uid), 2000) + 1 FROM users")
        return cur.fetchone()[0]
    finally:
        conn.close()


def register(nickname: str, role: str = "Developer", host: str = "local") -> dict | None:
    """
    Register a new identity. Returns the created identity, or None if nickname taken.
    """
    if role not in ROLES:
        role = "Developer"

    conn = get_conn()
    if not conn:
        return None

    try:
        cur = conn.cursor()

        # check duplicate nickname
        cur.execute("SELECT uid, nickname, role, created_at FROM users WHERE nickname = %s", (nickname,))
        existing = cur.fetchone()
        if existing:
            return None

        uid = _next_uid()
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ")
        cur.execute(
            "INSERT INTO users (uid, nickname, role, agent_type, status, created_at, hostname) VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (uid, nickname, role, "winpeek", 1, now, host),
        )
        conn.commit()
        return {"uid": uid, "nickname": nickname, "role": role, "host": host, "created_at": now}

    except Exception as e:
        logger.error(f"register failed: {e}")
        return None
    finally:
        conn.close()


def login(nickname: str) -> dict | None:
    """Login by nickname. Returns identity if found."""
    conn = get_conn()
    if not conn:
        return None
    try:
        cur = conn.cursor()
        cur.execute("SELECT uid, nickname, role, hostname AS host, created_at FROM users WHERE nickname = %s", (nickname,))
        row = cur.fetchone()
        if row:
            return {"uid": row[0], "nickname": row[1], "role": row[2], "host": row[3], "created_at": str(row[4])}
        return None
    finally:
        conn.close()


def get_by_uid(uid: int) -> Optional[dict]:
    """Get identity by uid."""
    conn = get_conn()
    if not conn:
        return None
    try:
        cur = conn.cursor()
        cur.execute("SELECT uid, nickname, role, hostname AS host, created_at FROM users WHERE uid = %s", (uid,))
        row = cur.fetchone()
        if row:
            return {"uid": row[0], "nickname": row[1], "role": row[2], "host": row[3], "created_at": str(row[4])}
        return None
    finally:
        conn.close()


def list_all() -> list[dict]:
    """List all registered identities."""
    conn = get_conn()
    if not conn:
        return []
    try:
        cur = conn.cursor()
        cur.execute("SELECT uid, nickname, role, hostname AS host, created_at FROM users WHERE status = 1 ORDER BY uid")
        rows = cur.fetchall()
        return [{"uid": r[0], "nickname": r[1], "role": r[2], "host": r[3], "created_at": str(r[4])} for r in rows]
    finally:
        conn.close()
"""
identity.py — WinPeek MIM identity management with JSONL persistence.

Stores identities at ~/.hermes/winpeek/identities.jsonl.
Provides: register, login, get_identity, list_identities.
"""
import json
import os
import time
from pathlib import Path
from typing import Optional

IDENTITIES_PATH = Path.home() / ".hermes" / "winpeek" / "identities.jsonl"

ROLES = ["Developer", "Architect", "Ops", "QA", "PM", "Director", "Boss"]


def _ensure_dir():
    IDENTITIES_PATH.parent.mkdir(parents=True, exist_ok=True)


def _read_all() -> list[dict]:
    """Read all identities from JSONL file."""
    _ensure_dir()
    if not IDENTITIES_PATH.exists():
        return []
    results = []
    with open(IDENTITIES_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    results.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return results


def _append(entry: dict):
    """Append one identity to JSONL file."""
    _ensure_dir()
    with open(IDENTITIES_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def register(nickname: str, role: str = "Developer", host: str = "local") -> dict | None:
    """
    Register a new identity. Returns the created identity, or None if nickname taken.
    """
    if role not in ROLES:
        role = "Developer"

    all_ids = _read_all()
    for entry in all_ids:
        if entry.get("nickname", "").lower() == nickname.lower():
            return None  # already exists

    uid = 2000 + len(all_ids) + 1
    identity = {
        "uid": uid,
        "nickname": nickname,
        "role": role,
        "host": host,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    _append(identity)
    return identity


def login(nickname: str) -> dict | None:
    """
    Login by nickname. Returns identity if found.
    """
    all_ids = _read_all()
    for entry in all_ids:
        if entry.get("nickname", "").lower() == nickname.lower():
            return entry
    return None


def get_by_uid(uid: int) -> Optional[dict]:
    """Get identity by uid."""
    for entry in _read_all():
        if entry.get("uid") == uid:
            return entry
    return None


def list_all() -> list[dict]:
    """List all registered identities."""
    return _read_all()
