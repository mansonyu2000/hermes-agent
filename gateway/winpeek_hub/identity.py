"""
identity.py — WinPeek MIM identity management with MySQL persistence.

Uses winpeek-db2.users table (192.168.3.23:3306).
Provides: register, login, get_identity, list_identities.
"""

import hashlib
import logging
import secrets
import socket
import time
from collections import defaultdict
from typing import Optional

from .db import get_conn

logger = logging.getLogger(__name__)

# ── Password hashing (PBKDF2 with SHA256 fallback) ────────────────────────

_PBKDF2_ITERATIONS = 100_000
_PBKDF2_PREFIX = "pbkdf2:sha256:"

# ── Rate limiting (in-memory, per-process) ─────────────────────────────────

_FAILURES: dict[str, list[float]] = defaultdict(list)  # key → list of failure timestamps
_MAX_FAILURES = 5       # max failures before cooldown
_COOLDOWN_SECONDS = 60  # cooldown period

def _rate_limit_check(key: str) -> bool:
    """Return True if this key is rate-limited (too many recent failures)."""
    now = time.time()
    cutoff = now - _COOLDOWN_SECONDS
    timestamps = [t for t in _FAILURES.get(key, []) if t > cutoff]
    _FAILURES[key] = timestamps
    return len(timestamps) >= _MAX_FAILURES

def _rate_limit_record(key: str) -> None:
    """Record a failed attempt for this key."""
    _FAILURES[key].append(time.time())

def _rate_limit_key(ip: str, nickname: str) -> str:
    return f"{ip}|{nickname}"

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
    """Legacy SHA256 hash — kept for backward compatibility with existing users.

    New passwords use _hash_password_pbkdf2() instead.
    """
    return hashlib.sha256(password.encode()).hexdigest()


def _hash_password_pbkdf2(password: str) -> str:
    """PBKDF2-HMAC-SHA256 with random 16-byte salt, 100k iterations.

    Format: pbkdf2:sha256:100000:<salt_hex>:<hash_hex>
    This is the default for new passwords; old SHA256 hashes are auto-migrated on login.
    """
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _PBKDF2_ITERATIONS)
    return f"{_PBKDF2_PREFIX}{_PBKDF2_ITERATIONS}:{salt.hex()}:{dk.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Verify a password against a stored hash (PBKDF2 or legacy SHA256)."""
    if not stored_hash:
        return not password  # empty hash → only empty password accepted
    if stored_hash.startswith(_PBKDF2_PREFIX):
        # PBKDF2 format: pbkdf2:sha256:iterations:salt:hash
        try:
            _, _, iterations_str, salt_hex, hash_hex = stored_hash.split(":")
            salt = bytes.fromhex(salt_hex)
            iterations = int(iterations_str)
            dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations)
            return dk.hex() == hash_hex
        except (ValueError, AttributeError):
            return False
    # Legacy SHA256 (64 hex chars)
    if len(stored_hash) == 64 and all(c in "0123456789abcdef" for c in stored_hash):
        return _hash_password(password) == stored_hash
    return False


def _needs_migration(stored_hash: str) -> bool:
    """Return True if this is a legacy SHA256 hash that should be migrated to PBKDF2."""
    return bool(stored_hash) and not stored_hash.startswith(_PBKDF2_PREFIX) \
        and len(stored_hash) == 64


def _migrate_password(uid: int, password: str) -> None:
    """Upgrade a legacy SHA256 hash to PBKDF2 (best-effort, silent on failure)."""
    try:
        conn = get_conn()
        if conn is None:
            return
        new_hash = _hash_password_pbkdf2(password)
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET password_hash = %s WHERE uid = %s",
                (new_hash, uid))
            conn.commit()
        conn.close()
        logger.info("password migrated to PBKDF2: uid=%d", uid)
    except Exception:
        pass  # migration is best-effort


def set_password(uid: int, password: str) -> bool:
    """Set or change the password for an existing user by uid."""
    conn = get_conn()
    if conn is None:
        return False
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET password_hash = %s WHERE uid = %s",
                (_hash_password_pbkdf2(password), uid))
            conn.commit()
        return True
    except Exception as e:
        logger.exception(f"set_password failed for uid={uid}: {e}")
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

            now = time.strftime("%Y-%m-%dT%H:%M:%SZ")
            pw_hash = _hash_password_pbkdf2(password) if password else ""

            # Atomic INSERT … SELECT (avoids MAX(uid)+1 race condition)
            cur.execute(
                """INSERT INTO users (uid, nickname, role, hostname, created_at, updated_at, is_active, identity_type, status, password_hash)
                   SELECT COALESCE(MAX(uid), 1999) + 1, %s, %s, %s, %s, %s, 1, 'mim', 1, %s
                   FROM users WHERE uid >= 2000""",
                (nickname, role, host, now, now, pw_hash),
            )
            conn.commit()
            cur.execute("SELECT MAX(uid) as uid FROM users WHERE nickname = %s", (nickname,))
            next_uid = int(cur.fetchone()["uid"])

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


def get_by_nickname(nickname: str) -> Optional[dict]:
    """Look up identity by nickname WITHOUT password check (token-auth world).

    MIM 客户端身份已由 /api/ws token 认证, 不再需要密码登录。
    winpeek_mim_login 用它按 nickname 解析身份 (不存在则走 register)。
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
            return _row_to_dict(row) if row else None
    finally:
        conn.close()


def login(nickname: str, password: str = "", client_ip: str = "") -> dict | None:
    """
    Login by nickname + password. Returns identity if found and password matches.
    Supports PBKDF2 (new) and SHA256 (legacy) hashes with auto-migration.
    Rate-limited: 5 failures per (ip, nickname) → 60s cooldown.
    """
    # Rate limit check
    rl_key = _rate_limit_key(client_ip, nickname)
    if _rate_limit_check(rl_key):
        logger.warning("rate-limited login attempt: nickname=%s ip=%s", nickname, client_ip)
        return None

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
            if not row:
                _rate_limit_record(rl_key)  # user enumeration hardening
                return None

            stored_hash = row.get("password_hash") or ""
            if not stored_hash:
                # Empty hash (daemon legacy): only allow empty password
                if password:
                    _rate_limit_record(rl_key)
                    return None  # prevents hijacking
            else:
                # Verify with PBKDF2 (new) or SHA256 (legacy) fallback
                if not verify_password(password, stored_hash):
                    _rate_limit_record(rl_key)
                    return None  # wrong password

            # Auto-migrate legacy SHA256 → PBKDF2
            if _needs_migration(stored_hash):
                _migrate_password(row["uid"], password)

            return _row_to_dict(row)
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

            now = time.strftime("%Y-%m-%dT%H:%M:%SZ")
            pw_hash = _hash_password_pbkdf2(password)

            # Atomic INSERT … SELECT (avoids MAX(uid)+1 race condition)
            cur.execute(
                """INSERT INTO users (uid, nickname, role, hostname, created_at, updated_at,
                   is_active, identity_type, status, password_hash, gender)
                   SELECT COALESCE(MAX(uid), 1999) + 1, %s, %s, %s, %s, %s, 1, 'mim-user', 1, %s, %s
                   FROM users WHERE uid >= 2000""",
                (name, "Developer", host, now, now, pw_hash, gender),
            )
            conn.commit()
            cur.execute("SELECT MAX(uid) as uid FROM users WHERE nickname = %s", (name,))
            next_uid = int(cur.fetchone()["uid"])

            identity = {
                "uid": next_uid, "nickname": name, "role": "Developer",
                "host": host, "identity_type": "mim-user", "gender": gender,
                "created_at": now,
            }
            logger.info(f"MIM User registered: uid={next_uid} name={name}")
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
        logger.exception(f"register_device failed for hostname={hostname}: {e}")
        return None
    finally:
        conn.close()
