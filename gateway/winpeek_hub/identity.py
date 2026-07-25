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


def set_password(uid: int, password: str) -> bool:
    """Set or change the password for an existing user by uid."""
    conn = get_conn()
    if conn is None:
        return False
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET password_hash = %s WHERE uid = %s",
                (_hash_password(password), uid))
            conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()


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
                "SELECT uid, nickname, role, hostname, created_at, password_hash, title, bio, skills, manager_uid, identity_type, gender FROM users WHERE nickname = %s",
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
    identity_type = row.get("identity_type", "")
    gender = row.get("gender")
    return {
        "uid": row["uid"],
        "nickname": nickname,
        "role": row["role"],
        "host": host,
        "agent_type": agent_type,
        "identity_type": identity_type,
        "gender": gender,
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
                "SELECT uid, nickname, role, hostname, created_at, title, bio, skills, manager_uid, identity_type, gender FROM users WHERE uid = %s",
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
                "SELECT uid, nickname, role, hostname, created_at, title, bio, skills, manager_uid, identity_type, gender FROM users WHERE is_active = 1 OR is_active IS NULL ORDER BY uid"
            )
            return [_row_to_dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


# ── User (真人) registration ──────────────────


def register_user(name: str, gender: str = "", password: str = "a@123321",
                  host: str = "local") -> dict | None:
    """Register a human User (真人). identity_type = 'mim-user'."""
    if gender not in ("male", "female"):
        return None  # gender required for human users

    conn = get_conn()
    if conn is None:
        return None
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT uid FROM users WHERE nickname = %s", (name,))
            if cur.fetchone():
                return None  # already exists

            cur.execute("SELECT COALESCE(MAX(uid), 1999) + 1 AS next_uid FROM users WHERE uid >= 2000")
            next_uid = cur.fetchone()["next_uid"]

            now = time.strftime("%Y-%m-%dT%H:%M:%SZ")
            pw_hash = _hash_password(password)
            cur.execute(
                """INSERT INTO users (uid, nickname, role, hostname, created_at, updated_at,
                   is_active, identity_type, status, password_hash, gender)
                   VALUES (%s, %s, %s, %s, %s, %s, 1, 'mim-user', 1, %s, %s)""",
                (next_uid, name, "Developer", host, now, now, pw_hash, gender),
            )
            conn.commit()

            identity = {
                "uid": next_uid, "nickname": name, "role": "Developer",
                "host": host, "identity_type": "mim-user", "gender": gender,
                "created_at": now,
            }
            logger.info(f"MIM User registered: uid={next_uid} name={name} gender={gender}")
            return identity
    except Exception as e:
        logger.warning(f"MIM User register failed: {e}")
        return None
    finally:
        conn.close()


# ── Device (电脑) management ──────────────────


def check_device(hostname: str) -> dict | None:
    """Check if a hostname is already registered in machines table.
    Returns machine info dict if found, None otherwise.
    """
    conn = get_conn()
    if conn is None:
        return None
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, hostname, person_id, winpeek_uid, os_name, os_version, "
                "cpu_model, cpu_cores, ram_gb, gpu_models, created_at, device_type "
                "FROM machines WHERE hostname = %s",
                (hostname,),
            )
            row = cur.fetchone()
            if row:
                return {
                    "id": row["id"], "hostname": row["hostname"],
                    "person_id": row.get("person_id"), "winpeek_uid": row.get("winpeek_uid"),
                    "os_name": row.get("os_name"), "os_version": row.get("os_version"),
                    "cpu_model": row.get("cpu_model"), "cpu_cores": row.get("cpu_cores"),
                    "ram_gb": float(row["ram_gb"]) if row.get("ram_gb") else None,
                    "gpu_models": row.get("gpu_models"), "device_type": row.get("device_type"),
                    "created_at": str(row.get("created_at", "")),
                }
            return None
    finally:
        conn.close()


def register_device(hostname: str, owner_uid: int, os_name: str = "",
                    os_version: str = "", cpu_model: str = "", cpu_cores: int = 0,
                    ram_gb: float = 0, gpu_models: str = "", ip_address: str = "",
                    device_type: str = "pc") -> dict | None:
    """Register a new device (电脑) to the machines table. Returns the machine record."""
    conn = get_conn()
    if conn is None:
        return None
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM machines WHERE hostname = %s", (hostname,))
            if cur.fetchone():
                return None  # already registered

            cur.execute(
                """INSERT INTO machines (hostname, person_id, winpeek_uid, os_name, os_version,
                   cpu_model, cpu_cores, ram_gb, gpu_models, ip_address, device_type)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (hostname, None, owner_uid, os_name, os_version,
                 cpu_model, cpu_cores, ram_gb, gpu_models, ip_address, device_type),
            )
            conn.commit()
            logger.info(f"Device registered: hostname={hostname} owner_uid={owner_uid}")
            return {"hostname": hostname, "winpeek_uid": owner_uid, "device_type": device_type}
    except Exception as e:
        logger.warning(f"Device register failed: {e}")
        return None
    finally:
        conn.close()
