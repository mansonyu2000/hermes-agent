"""WinPeek org hierarchy — squad → person → device → winpeek → agent.

Tables:
  squads           — 组织 (company/team)
  persons          — 真人, 属于一个 squad
  machines         — Device (pc/laptop/phone/container/vm), 属于 person 或 squad
  winpeek_accounts — person 与 users.uid 的关联 (一人可有多个winpeek账号)
  ai_agents        — AI Agent, 属于 person/device/squad

Relations:
  squad 1──N persons
  squad 1──N machines (组织级设备)
  person 1──N machines (个人设备)
  person 1──N winpeek_accounts (winpeek uid)
  person 1──N ai_agents
  machine 1──1 winpeek_uid (主账号)
  machine 1──N ai_agents (运行在此设备上的agent)
  machine 1──N winpeek_software (安装的软件)
"""

import json as _json
import logging
import secrets
import socket
from datetime import datetime
from typing import Any

from .db import get_conn

logger = logging.getLogger(__name__)

# Per-uid failed invite-code attempt counter (process-local, resets on restart)
_invite_fail_count: dict[int, int] = {}

_DDL_OK = False


def ensure_tables():
    global _DDL_OK
    if _DDL_OK:
        return
    conn = get_conn()
    if conn is None:
        return
    try:
        with conn.cursor() as cur:
            # ── squads ──
            cur.execute("""
                CREATE TABLE IF NOT EXISTS squads (
                  id          INT AUTO_INCREMENT PRIMARY KEY,
                  name        VARCHAR(128) NOT NULL,
                  description TEXT,
                  meta        TEXT COMMENT 'JSON扩展',
                  created_at  DATETIME DEFAULT NOW(),
                  updated_at  DATETIME DEFAULT NOW() ON UPDATE NOW(),
                  UNIQUE KEY uk_squad_name (name)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            _ensure_cols(cur, "squads", {
                "description": "TEXT", "meta": "TEXT",
                "updated_at": "DATETIME DEFAULT NOW() ON UPDATE NOW()",
            })

            # ── persons ──
            cur.execute("""
                CREATE TABLE IF NOT EXISTS persons (
                  id          INT AUTO_INCREMENT PRIMARY KEY,
                  name        VARCHAR(128) NOT NULL,
                  squad_id    INT,
                  email       VARCHAR(128),
                  phone       VARCHAR(32),
                  notes       TEXT COMMENT '备注',
                  meta        TEXT COMMENT 'JSON扩展',
                  created_at  DATETIME DEFAULT NOW(),
                  updated_at  DATETIME DEFAULT NOW() ON UPDATE NOW(),
                  FOREIGN KEY (squad_id) REFERENCES squads(id) ON DELETE SET NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            _ensure_cols(cur, "persons", {
                "email": "VARCHAR(128)", "phone": "VARCHAR(32)",
                "notes": "TEXT", "meta": "TEXT",
                "approval_status": "VARCHAR(16) DEFAULT 'pending'",
                "approved_by": "INT", "approved_at": "DATETIME",
                "updated_at": "DATETIME DEFAULT NOW() ON UPDATE NOW()",
            })

            # ── machines ──
            cur.execute("""
                CREATE TABLE IF NOT EXISTS machines (
                  id           INT AUTO_INCREMENT PRIMARY KEY,
                  hostname     VARCHAR(128) NOT NULL,
                  squad_id     INT,
                  person_id    INT,
                  winpeek_uid  INT COMMENT '关联 users.uid',
                  os_name      VARCHAR(64),
                  os_version   VARCHAR(64),
                  cpu_model    VARCHAR(256),
                  cpu_cores    INT,
                  ram_gb       DECIMAL(6,1),
                  gpu_models   TEXT COMMENT 'JSON array',
                  disks_json   TEXT COMMENT 'JSON [{\"drive\":\"C:\",\"total_gb\":512}]',
                  ip_address   VARCHAR(64),
                  mac_address  VARCHAR(64),
                  last_seen    DATETIME,
                  meta         TEXT COMMENT 'JSON扩展',
                  created_at   DATETIME DEFAULT NOW(),
                  updated_at   DATETIME DEFAULT NOW() ON UPDATE NOW(),
                  UNIQUE KEY uk_hostname (hostname),
                  FOREIGN KEY (person_id) REFERENCES persons(id) ON DELETE SET NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            _ensure_cols(cur, "machines", {
                "squad_id": "INT", "device_type": "VARCHAR(32)",
                "os_name": "VARCHAR(64)", "os_version": "VARCHAR(64)",
                "cpu_model": "VARCHAR(256)", "cpu_cores": "INT",
                "ram_gb": "DECIMAL(6,1)", "gpu_models": "TEXT",
                "disks_json": "TEXT", "ip_address": "VARCHAR(64)",
                "mac_address": "VARCHAR(64)", "meta": "TEXT",
                "winpeek_uid": "INT",
                "approval_status": "VARCHAR(16) DEFAULT 'pending'",
                "approved_by": "INT", "approved_at": "DATETIME",
                "updated_at": "DATETIME DEFAULT NOW() ON UPDATE NOW()",
            })

            # ── squads.owner_person_id ──
            _ensure_cols(cur, "squads", {"owner_person_id": "INT", "invite_code": "VARCHAR(8)",
                # Organization profile fields
                "address": "TEXT", "industry": "VARCHAR(64)",
                "founded_at": "VARCHAR(16)", "legal_person": "VARCHAR(64)",
                "contact_phone": "VARCHAR(32)", "website": "VARCHAR(256)",
                "contact_email": "VARCHAR(128)", "managed_by_uid": "INT",
            })

            # ── winpeek_accounts: person ↔ users.uid ──
            cur.execute("""
                CREATE TABLE IF NOT EXISTS winpeek_accounts (
                  id        INT AUTO_INCREMENT PRIMARY KEY,
                  person_id INT NOT NULL,
                  uid       INT NOT NULL COMMENT 'users.uid',
                  is_main   TINYINT DEFAULT 0 COMMENT '主账号',
                  created_at DATETIME DEFAULT NOW(),
                  UNIQUE KEY uk_person_uid (person_id, uid),
                  FOREIGN KEY (person_id) REFERENCES persons(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)

            # ── ai_agents: AI agent registry ──
            cur.execute("""
                CREATE TABLE IF NOT EXISTS ai_agents (
                  id          INT AUTO_INCREMENT PRIMARY KEY,
                  name        VARCHAR(128) NOT NULL,
                  agent_type  VARCHAR(64) COMMENT 'hermes/qoder/cc...',
                  uid         INT COMMENT 'users.uid',
                  person_id   INT,
                  squad_id    INT,
                  machine_id  INT,
                  role        VARCHAR(64),
                  status      VARCHAR(32) DEFAULT 'active',
                  config_json TEXT COMMENT 'JSON配置',
                  created_at  DATETIME DEFAULT NOW(),
                  updated_at  DATETIME DEFAULT NOW() ON UPDATE NOW(),
                  FOREIGN KEY (machine_id) REFERENCES machines(id) ON DELETE SET NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)

            # ── FK ──
            _ensure_cols(cur, "winpeek_software", {"machine_id": "INT"})
            _ensure_cols(cur, "winpeek_software_account", {"machine_id": "INT"})

            conn.commit()
        _DDL_OK = True
        logger.info("organization tables ready: squads + persons + machines")
    except Exception as e:
        logger.warning(f"ensure_tables failed: {e}")
    finally:
        conn.close()


def _ensure_cols(cur, table: str, cols: dict[str, str]):
    """Add columns if not present."""
    for col, col_type in cols.items():
        cur.execute(
            "SELECT 1 FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s AND COLUMN_NAME = %s",
            (table, col),
        )
        if cur.fetchone():
            continue
        try:
            cur.execute(f"ALTER TABLE `{table}` ADD COLUMN `{col}` {col_type}")
        except Exception:
            pass


def _get_user_squad_ids(uid: int) -> set[int]:
    """Get all squad IDs a user belongs to (via machines.squad_id or persons.squad_id)."""
    if not uid:
        return set()
    conn = get_conn()
    if conn is None:
        return set()
    ids: set[int] = set()
    try:
        with conn.cursor() as cur:
            # via machine registration
            cur.execute(
                "SELECT DISTINCT squad_id FROM machines WHERE winpeek_uid = %s AND squad_id IS NOT NULL",
                (uid,))
            for r in cur.fetchall():
                ids.add(r["squad_id"])
            # via person link
            cur.execute("""
                SELECT DISTINCT p.squad_id FROM persons p
                INNER JOIN winpeek_accounts wa ON p.id = wa.person_id
                WHERE wa.uid = %s AND p.squad_id IS NOT NULL
            """, (uid,))
            for r in cur.fetchall():
                ids.add(r["squad_id"])
    finally:
        conn.close()
    return ids


def _can_access_squad(uid: int, squad_id: int) -> bool:
    """Check if uid belongs to a squad (or is 0=unlinked)."""
    if not uid or not squad_id:
        return True  # allow unlinked users (backward compat)
    return squad_id in _get_user_squad_ids(uid)


# ═══════════════════════════════════════════════════════
#  SQUAD CRUD
# ═══════════════════════════════════════════════════════

def list_squads() -> list[dict]:
    conn = get_conn()
    if conn is None: return []
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM squads ORDER BY name")
            return [_row(r) for r in cur.fetchall()]
    finally:
        conn.close()


def upsert_squad(name: str, **fields) -> dict:
    ensure_tables()
    conn = get_conn()
    if conn is None: return {"ok": False, "error": "DB unavailable"}
    allowed = {"description", "meta", "address", "industry", "founded_at",
               "legal_person", "contact_phone", "website", "contact_email", "managed_by_uid"}
    vals = {"name": name}
    for k in allowed:
        if k in fields and fields[k] is not None:
            vals[k] = fields[k]
    now = _now()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM squads WHERE name = %s", (name,))
            existing = cur.fetchone()
            if existing:
                sid = existing["id"]
                sets = ", ".join(f"`{k}` = %s" for k in vals)
                cur.execute(f"UPDATE squads SET {sets}, updated_at = %s WHERE id = %s",
                            list(vals.values()) + [now, sid])
            else:
                vals["created_at"] = now; vals["updated_at"] = now
                cols = ", ".join(f"`{k}`" for k in vals)
                ph = ", ".join("%s" for _ in vals)
                cur.execute(f"INSERT INTO squads ({cols}) VALUES ({ph})", list(vals.values()))
                sid = cur.lastrowid
            conn.commit()
        return {"ok": True, "id": sid}
    except Exception as e:
        return {"ok": False, "error": str(e)}
    finally:
        conn.close()


# ═══════════════════════════════════════════════════════
#  PERSON CRUD
# ═══════════════════════════════════════════════════════

def list_persons(squad_id: int = 0) -> list[dict]:
    conn = get_conn()
    if conn is None: return []
    try:
        with conn.cursor() as cur:
            if squad_id:
                cur.execute("""
                    SELECT p.*, s.name AS squad_name
                    FROM persons p LEFT JOIN squads s ON p.squad_id = s.id
                    WHERE p.squad_id = %s ORDER BY p.name
                """, (squad_id,))
            else:
                cur.execute("""
                    SELECT p.*, s.name AS squad_name
                    FROM persons p LEFT JOIN squads s ON p.squad_id = s.id
                    ORDER BY p.name
                """)
            return [_row(r) for r in cur.fetchall()]
    finally:
        conn.close()


def upsert_person(name: str, requester_uid: int = 0, **fields) -> dict:
    ensure_tables()
    conn = get_conn()
    if conn is None: return {"ok": False, "error": "DB unavailable"}
    allowed = {"squad_id", "email", "phone", "notes", "meta"}
    vals = {"name": name}
    for k in allowed:
        if k in fields and fields[k] is not None:
            vals[k] = fields[k]
    now = _now()
    try:
        with conn.cursor() as cur:
            pid = fields.get("id")
            if pid:
                cur.execute("SELECT id, squad_id FROM persons WHERE id = %s", (pid,))
                existing = cur.fetchone()
                if existing:
                    # Auth: requester must be in same squad
                    if requester_uid and existing.get("squad_id"):
                        if not _can_access_squad(requester_uid, existing["squad_id"]):
                            return {"ok": False, "error": "Permission denied"}
                    sets = ", ".join(f"`{k}` = %s" for k in vals)
                    cur.execute(f"UPDATE persons SET {sets}, updated_at = %s WHERE id = %s",
                                list(vals.values()) + [now, pid])
                    conn.commit()
                    return {"ok": True, "id": pid}
            vals["created_at"] = now; vals["updated_at"] = now
            cols = ", ".join(f"`{k}`" for k in vals)
            ph = ", ".join("%s" for _ in vals)
            cur.execute(f"INSERT INTO persons ({cols}) VALUES ({ph})", list(vals.values()))
            conn.commit()
        return {"ok": True, "id": cur.lastrowid}
    except Exception as e:
        return {"ok": False, "error": str(e)}
    finally:
        conn.close()


# ═══════════════════════════════════════════════════════
#  MACHINE CRUD
# ═══════════════════════════════════════════════════════

def list_machines(person_id: int = 0) -> list[dict]:
    conn = get_conn()
    if conn is None: return []
    try:
        with conn.cursor() as cur:
            if person_id:
                cur.execute("""
                    SELECT m.*, p.name AS person_name, s.name AS squad_name
                    FROM machines m
                    LEFT JOIN persons p ON m.person_id = p.id
                    LEFT JOIN squads s ON p.squad_id = s.id
                    WHERE m.person_id = %s ORDER BY m.hostname
                """, (person_id,))
            else:
                cur.execute("""
                    SELECT m.*, p.name AS person_name, s.name AS squad_name
                    FROM machines m
                    LEFT JOIN persons p ON m.person_id = p.id
                    LEFT JOIN squads s ON p.squad_id = s.id
                    ORDER BY m.last_seen DESC
                """)
            return [_row(r) for r in cur.fetchall()]
    finally:
        conn.close()


def upsert_machine(hostname: str, **fields) -> dict:
    """Upsert a machine. hostname is the unique key."""
    ensure_tables()
    conn = get_conn()
    if conn is None: return {"ok": False, "error": "DB unavailable"}
    allowed = {"squad_id", "device_type", "person_id", "winpeek_uid",
               "os_name", "os_version",
               "cpu_model", "cpu_cores", "ram_gb", "gpu_models",
               "disks_json", "ip_address", "mac_address", "meta"}
    vals = {"hostname": hostname, "last_seen": _now()}
    for k in allowed:
        if k in fields and fields[k] is not None:
            vals[k] = fields[k]
    now = _now()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM machines WHERE hostname = %s", (hostname,))
            existing = cur.fetchone()
            if existing:
                mid = existing["id"]
                sets = ", ".join(f"`{k}` = %s" for k in vals)
                cur.execute(f"UPDATE machines SET {sets}, updated_at = %s WHERE id = %s",
                            list(vals.values()) + [now, mid])
            else:
                vals["created_at"] = now; vals["updated_at"] = now
                cols = ", ".join(f"`{k}`" for k in vals)
                ph = ", ".join("%s" for _ in vals)
                cur.execute(f"INSERT INTO machines ({cols}) VALUES ({ph})", list(vals.values()))
                mid = cur.lastrowid
            conn.commit()
        return {"ok": True, "id": mid}
    except Exception as e:
        return {"ok": False, "error": str(e)}
    finally:
        conn.close()


def get_machine_detail(machine_id: int, requester_uid: int = 0) -> dict | None:
    conn = get_conn()
    if conn is None: return None
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT m.*, p.name AS person_name, p.email AS person_email,
                       s.name AS squad_name, s.id AS squad_id
                FROM machines m
                LEFT JOIN persons p ON m.person_id = p.id
                LEFT JOIN squads s ON p.squad_id = s.id
                WHERE m.id = %s
            """, (machine_id,))
            r = cur.fetchone()
            if not r: return None
            # Auth: requester must be machine owner or same squad
            msid = r.get("squad_id")
            mowner = r.get("winpeek_uid")
            if requester_uid and msid and mowner and requester_uid != mowner:
                if not _can_access_squad(requester_uid, msid):
                    return None
            data = _row(r)
            # load software on this machine
            cur.execute(
                "SELECT * FROM winpeek_software WHERE machine_id = %s ORDER BY name",
                (machine_id,))
            data["softwares"] = [_row(s) for s in cur.fetchall()]
            return data
    finally:
        conn.close()


def get_org_status(winpeek_uid: int) -> dict:
    """Check if a uid's machine is linked to a squad. Returns options for frontend."""
    conn = get_conn()
    if conn is None: return {"linked": False, "squads": []}
    try:
        with conn.cursor() as cur:
            # find machine for this uid
            cur.execute("SELECT id, squad_id, hostname FROM machines WHERE winpeek_uid = %s ORDER BY last_seen DESC LIMIT 1", (winpeek_uid,))
            m = cur.fetchone()
            if m and m["squad_id"]:
                cur.execute("SELECT * FROM squads WHERE id = %s", (m["squad_id"],))
                s = cur.fetchone()
                return {"linked": True, "machine_id": m["id"], "squad": _row(s) if s else None}
            # list available squads
            cur.execute("SELECT * FROM squads ORDER BY name")
            squads = [_row(s) for s in cur.fetchall()]
            return {"linked": False, "machine_id": m["id"] if m else None, "squads": squads,
                    "hostname": m["hostname"] if m else ""}
    finally:
        conn.close()


def join_squad(machine_id: int, squad_id: int, winpeek_uid: int,
               is_owner: bool = False) -> dict:
    """Link a machine to a squad. Auto-create person.
    is_owner=True → auto-approved; else → pending."""
    conn = get_conn()
    if conn is None: return {"ok": False, "error": "DB unavailable"}
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM machines WHERE id = %s AND winpeek_uid = %s",
                        (machine_id, winpeek_uid))
            if not cur.fetchone():
                return {"ok": False, "error": "Machine not found"}

            approval = "approved" if is_owner else "pending"

            cur.execute("SELECT nickname FROM users WHERE uid = %s", (winpeek_uid,))
            u = cur.fetchone()
            name = u["nickname"] if u else f"user_{winpeek_uid}"
            cur.execute("SELECT id FROM persons WHERE name = %s AND squad_id = %s", (name, squad_id))
            p = cur.fetchone()
            pid = None
            if not p:
                cur.execute("INSERT INTO persons (name, squad_id, approval_status) VALUES (%s, %s, %s)",
                            (name, squad_id, approval))
                pid = cur.lastrowid
            else:
                cur.execute("UPDATE persons SET squad_id = %s, approval_status = %s WHERE id = %s",
                            (squad_id, approval, p["id"]))
                pid = p["id"]

            cur.execute("UPDATE machines SET squad_id = %s, person_id = %s, approval_status = %s WHERE id = %s",
                        (squad_id, pid, approval, machine_id))

            cur.execute("INSERT INTO winpeek_accounts (person_id, uid, is_main) VALUES (%s, %s, 1) "
                        "ON DUPLICATE KEY UPDATE is_main = 1", (pid, winpeek_uid))

            if is_owner:
                cur.execute("UPDATE squads SET owner_person_id = %s WHERE id = %s", (pid, squad_id))

            conn.commit()
        return {"ok": True, "squad_id": squad_id, "person_id": pid, "approval_status": approval}
    except Exception as e:
        return {"ok": False, "error": str(e)}
    finally:
        conn.close()


def scan_and_register_machine(winpeek_uid: int, hostname: str = "") -> dict:
    """Auto-register current machine with hardware info, then scan software."""
    import platform as _plat, socket, os as _os

    if not hostname:
        hostname = _plat.node()

    # ── scan hardware ──
    from .scanner import get_hardware_info
    hw = get_hardware_info()

    # ── scan software ──
    from .scanner import scan_software
    sw = scan_software()

    # ── upsert machine ──
    disks = hw.get("disks", [])
    machine = upsert_machine(hostname,
        device_type="pc",
        winpeek_uid=winpeek_uid,
        os_name=hw.get("os", {}).get("system", ""),
        os_version=hw.get("os", {}).get("release", ""),
        cpu_model=hw.get("cpu", {}).get("name", ""),
        cpu_cores=hw.get("cpu", {}).get("cores", 0),
        ram_gb=_to_float(hw.get("memory", {}).get("total_gb", 0)),
        gpu_models=_json.dumps(hw.get("gpus", []), ensure_ascii=False),
        disks_json=_json.dumps(disks, ensure_ascii=False),
        ip_address=socket.gethostbyname(hostname) if hostname else "",
    )

    # ── tag software with machine_id ──
    if machine.get("ok") and machine.get("id"):
        mid = machine["id"]
        conn = get_conn()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE winpeek_software SET machine_id = %s WHERE machine_id IS NULL",
                        (mid,))
                    conn.commit()
            except Exception:
                pass
            finally:
                conn.close()

    return {"ok": True, "machine": machine, "hardware": hw, "software": sw}


# ═══════════════════════════════════════════════════════
#  HIERARCHY VIEW (full tree)
# ═══════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════
#  WINPEEK_ACCOUNTS (person ↔ users.uid)
# ═══════════════════════════════════════════════════════


def link_account(person_id: int, uid: int, is_main: int = 0) -> dict:
    ensure_tables()
    conn = get_conn()
    if conn is None: return {"ok": False, "error": "DB unavailable"}
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO winpeek_accounts (person_id, uid, is_main) VALUES (%s, %s, %s) "
                "ON DUPLICATE KEY UPDATE is_main = VALUES(is_main)",
                (person_id, uid, is_main))
            conn.commit()
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}
    finally:
        conn.close()


def list_accounts_for_person(person_id: int) -> list[dict]:
    conn = get_conn()
    if conn is None: return []
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT wa.*, u.nickname, u.role
                FROM winpeek_accounts wa
                LEFT JOIN users u ON wa.uid = u.uid
                WHERE wa.person_id = %s
            """, (person_id,))
            return [_row(r) for r in cur.fetchall()]
    finally:
        conn.close()


# ═══════════════════════════════════════════════════════
#  AI_AGENTS
# ═══════════════════════════════════════════════════════


def list_agents(squad_id: int = 0, machine_id: int = 0, requester_uid: int = 0) -> list[dict]:
    conn = get_conn()
    if conn is None: return []
    try:
        with conn.cursor() as cur:
            # Auth: scope to squads the requester belongs to
            if requester_uid and squad_id:
                if not _can_access_squad(requester_uid, squad_id):
                    return []
            sql = "SELECT * FROM ai_agents WHERE 1=1"
            params = []
            if squad_id: sql += " AND squad_id = %s"; params.append(squad_id)
            if machine_id: sql += " AND machine_id = %s"; params.append(machine_id)
            sql += " ORDER BY name"
            cur.execute(sql, params)
            return [_row(r) for r in cur.fetchall()]
    finally:
        conn.close()


def upsert_agent(name: str, requester_uid: int = 0, **fields) -> dict:
    ensure_tables()
    conn = get_conn()
    if conn is None: return {"ok": False, "error": "DB unavailable"}
    # Auth: requester must belong to target squad
    tsid = int(fields.get("squad_id") or 0)
    if requester_uid and tsid:
        if not _can_access_squad(requester_uid, tsid):
            return {"ok": False, "error": "Permission denied"}
    allowed = {"agent_type", "uid", "person_id", "squad_id", "machine_id",
               "role", "status", "config_json"}
    vals = {"name": name}
    for k in allowed:
        if k in fields and fields[k] is not None:
            vals[k] = fields[k]
    now = _now()
    try:
        with conn.cursor() as cur:
            aid = fields.get("id")
            if aid:
                cur.execute("SELECT id FROM ai_agents WHERE id = %s", (aid,))
                if cur.fetchone():
                    sets = ", ".join(f"`{k}` = %s" for k in vals)
                    cur.execute(f"UPDATE ai_agents SET {sets}, updated_at = %s WHERE id = %s",
                                list(vals.values()) + [now, aid])
                    conn.commit()
                    return {"ok": True, "id": aid}
            vals["created_at"] = now; vals["updated_at"] = now
            cols = ", ".join(f"`{k}`" for k in vals)
            ph = ", ".join("%s" for _ in vals)
            cur.execute(f"INSERT INTO ai_agents ({cols}) VALUES ({ph})", list(vals.values()))
            conn.commit()
        return {"ok": True, "id": cur.lastrowid}
    except Exception as e:
        return {"ok": False, "error": str(e)}
    finally:
        conn.close()


# ═══════════════════════════════════════════════════════
#  APPROVAL
# ═══════════════════════════════════════════════════════


def _is_squad_admin(uid: int, squad_id: int, cur) -> bool:
    """Check if uid is the squad owner (via owner_person_id → winpeek_accounts)."""
    cur.execute("SELECT owner_person_id FROM squads WHERE id = %s", (squad_id,))
    s = cur.fetchone()
    if not s:
        return False
    oid = s.get("owner_person_id")
    if not oid:
        return False
    cur.execute("SELECT 1 FROM winpeek_accounts WHERE person_id = %s AND uid = %s", (oid, uid))
    return bool(cur.fetchone())


def approve_person(person_id: int, action: str, requester_uid: int) -> dict:
    """Approve or reject a person registration. Only squad admin can do this."""
    if action not in ("approved", "rejected"):
        return {"ok": False, "error": "action must be 'approved' or 'rejected'"}
    conn = get_conn()
    if conn is None: return {"ok": False, "error": "DB unavailable"}
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT squad_id FROM persons WHERE id = %s", (person_id,))
            p = cur.fetchone()
            if not p:
                return {"ok": False, "error": "Person not found"}
            if not _is_squad_admin(requester_uid, p["squad_id"], cur):
                return {"ok": False, "error": "Permission denied — must be squad admin"}
            now = _now()
            cur.execute(
                "UPDATE persons SET approval_status = %s, approved_by = %s, approved_at = %s WHERE id = %s",
                (action, requester_uid, now, person_id))
            conn.commit()
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}
    finally:
        conn.close()


def approve_machine(machine_id: int, action: str, requester_uid: int) -> dict:
    """Approve or reject a device registration. Only squad admin can do this."""
    if action not in ("approved", "rejected"):
        return {"ok": False, "error": "action must be 'approved' or 'rejected'"}
    conn = get_conn()
    if conn is None: return {"ok": False, "error": "DB unavailable"}
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT squad_id, person_id FROM machines WHERE id = %s", (machine_id,))
            m = cur.fetchone()
            if not m:
                return {"ok": False, "error": "Machine not found"}

            # Auth: squad admin OR the machine owner
            is_authorized = False
            if requester_uid == (m.get("winpeek_uid") or 0):
                is_authorized = True
            elif m.get("squad_id") and _is_squad_admin(requester_uid, m["squad_id"], cur):
                is_authorized = True
            if not is_authorized:
                return {"ok": False, "error": "Permission denied"}

            now = _now()
            cur.execute(
                "UPDATE machines SET approval_status = %s, approved_by = %s, approved_at = %s WHERE id = %s",
                (action, requester_uid, now, machine_id))

            # auto-approve linked person
            if action == "approved" and m.get("person_id"):
                cur.execute(
                    "UPDATE persons SET approval_status = 'approved', approved_by = %s, approved_at = %s WHERE id = %s",
                    (requester_uid, now, m["person_id"]))
            conn.commit()
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}
    finally:
        conn.close()


def get_pending(squad_id: int = 0, requester_uid: int = 0) -> dict:
    """Get pending persons/machines. Scoped to squads the requester belongs to."""
    conn = get_conn()
    if conn is None: return {"persons": [], "machines": []}
    try:
        allowed = _get_user_squad_ids(requester_uid) if requester_uid else set()
        if requester_uid and not allowed:
            return {"persons": [], "machines": []}  # no squads → nothing to approve

        with conn.cursor() as cur:
            if squad_id:
                if requester_uid and squad_id not in allowed:
                    return {"persons": [], "machines": []}
                squad_list = [squad_id]
            elif requester_uid:
                squad_list = list(allowed)
            else:
                squad_list = []

            if squad_list:
                placeholders = ",".join(["%s"] * len(squad_list))
                sp = f"SELECT p.*, s.name AS squad_name FROM persons p LEFT JOIN squads s ON p.squad_id = s.id WHERE p.approval_status = 'pending' AND p.squad_id IN ({placeholders})"
                sm = f"SELECT m.*, s.name AS squad_name FROM machines m LEFT JOIN squads s ON m.squad_id = s.id WHERE m.approval_status = 'pending' AND m.squad_id IN ({placeholders})"
                cur.execute(sp, squad_list)
                persons = [_row(r) for r in cur.fetchall()]
                cur.execute(sm, squad_list)
                machines = [_row(r) for r in cur.fetchall()]
            else:
                persons, machines = [], []
        return {"persons": persons, "machines": machines}
    finally:
        conn.close()


def search_squads(q: str, max_results: int = 10) -> list[dict]:
    """Search squads by name (fuzzy match)."""
    conn = get_conn()
    if conn is None: return []
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, description, owner_person_id, created_at, updated_at "
                "FROM squads WHERE name LIKE %s ORDER BY name LIMIT %s",
                (f"%{q}%", max_results))
            return [_row(r) for r in cur.fetchall()]
    finally:
        conn.close()


def register_with_squad(uid: int, squad_id: int, is_new_squad: bool = False,
                        squad_name: str = "", squad_desc: str = "",
                        person_name: str = "", email: str = "",
                        phone: str = "", hostname: str = "",
                        invite_code: str = "") -> dict:
    """Complete one-call registration.

    - is_new_squad: creates squad, person=owner, auto-approved
    - else: join existing squad, person=pending
    """
    if not uid:
        return {"ok": False, "error": "uid required"}

    conn = get_conn()
    if conn is None: return {"ok": False, "error": "DB unavailable"}
    now = _now()

    try:
        with conn.cursor() as cur:
            # ── Step 1: squad ──
            if is_new_squad:
                if not squad_name:
                    return {"ok": False, "error": "squad_name required for new squad"}
                cur.execute("SELECT id FROM squads WHERE name = %s", (squad_name,))
                exist = cur.fetchone()
                if exist:
                    return {"ok": False, "error": f"Squad '{squad_name}' already exists"}
                # Generate 6-digit invite code (human-friendly, 10 retries for uniqueness)
                code = ''
                for _ in range(10):
                    code = f"{secrets.randbelow(1000000):06d}"
                    cur.execute("SELECT 1 FROM squads WHERE invite_code = %s", (code,))
                    if not cur.fetchone():
                        break
                cur.execute(
                    "INSERT INTO squads (name, description, invite_code, created_at, updated_at) VALUES (%s, %s, %s, %s, %s)",
                    (squad_name, squad_desc, code, now, now))
                sqid = cur.lastrowid
            else:
                sqid = 0
                if not squad_id:
                    if invite_code:
                        cur.execute("SELECT id FROM squads WHERE invite_code = %s", (invite_code,))
                        row = cur.fetchone()
                        if row:
                            sqid = row["id"]
                    if not sqid:  # still not found
                        return {"ok": False, "error": "squad_id or valid invite_code required"}
                else:
                    cur.execute("SELECT id FROM squads WHERE id = %s", (squad_id,))
                    if not cur.fetchone():
                        return {"ok": False, "error": "Squad not found"}
                    sqid = squad_id

            # ── Step 2: person name ──
            name = person_name
            if not name:
                cur.execute("SELECT nickname FROM users WHERE uid = %s", (uid,))
                u = cur.fetchone()
                name = u["nickname"] if u else f"user_{uid}"

            # Determine approval: owner→approved, invite_code match→approved, else→pending
            if is_new_squad:
                approval = "approved"
            elif invite_code:
                cur.execute(
                    "SELECT id, invite_code FROM squads WHERE invite_code = %s", (invite_code,))
                row = cur.fetchone()
                if row:
                    approval = "approved"
                    sqid = row["id"]
                    _invite_fail_count.pop(uid, None)
                else:
                    approval = "pending"
                    cnt = _invite_fail_count.get(uid, 0) + 1
                    _invite_fail_count[uid] = cnt
                    if cnt > 5:
                        return {"ok": False, "error": "Too many failed attempts. Try again later."}
            else:
                approval = "pending"

            cur.execute(
                "SELECT id FROM persons WHERE name = %s AND squad_id = %s",
                (name, sqid))
            p = cur.fetchone()
            if p:
                cur.execute(
                    "UPDATE persons SET email=%s, phone=%s, approval_status=%s WHERE id=%s",
                    (email, phone, approval, p["id"]))
                pid = p["id"]
            else:
                cur.execute(
                    "INSERT INTO persons (name, squad_id, email, phone, notes, approval_status) VALUES (%s, %s, %s, %s, '', %s)",
                    (name, sqid, email, phone, approval))
                pid = cur.lastrowid

            # ── Step 3: winpeek_account ──
            cur.execute(
                "INSERT INTO winpeek_accounts (person_id, uid, is_main) VALUES (%s, %s, 1) "
                "ON DUPLICATE KEY UPDATE is_main = 1", (pid, uid))

            # ── Step 4: machine ──
            hn = hostname or socket.gethostname()  # type: ignore
            cur.execute("SELECT id FROM machines WHERE hostname = %s", (hn,))
            m = cur.fetchone()
            if m:
                cur.execute(
                    "UPDATE machines SET squad_id=%s, person_id=%s, winpeek_uid=%s, approval_status=%s WHERE id=%s",
                    (sqid, pid, uid, approval, m["id"]))
                mid = m["id"]
            else:
                cur.execute(
                    "INSERT INTO machines (hostname, squad_id, person_id, winpeek_uid, device_type, approval_status) "
                    "VALUES (%s, %s, %s, %s, 'pc', %s)",
                    (hn, sqid, pid, uid, approval))
                mid = cur.lastrowid

            # ── Step 5: if owner, set squad.owner_person_id ──
            if is_new_squad:
                cur.execute("UPDATE squads SET owner_person_id = %s WHERE id = %s", (pid, sqid))

            # Read back invite_code
            cur.execute("SELECT invite_code FROM squads WHERE id = %s", (sqid,))
            srow = cur.fetchone()
            inv_code = srow["invite_code"] if srow else ""

            conn.commit()

        return {
            "ok": True,
            "squad_id": sqid,
            "person_id": pid,
            "machine_id": mid,
            "approval_status": approval,
            "invite_code": inv_code,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}
    finally:
        conn.close()


def get_org_tree() -> dict:
    """Return full hierarchy: squads → persons → machines → software count."""
    conn = get_conn()
    if conn is None: return {"squads": []}
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM squads ORDER BY name")
            squads = []
            for s in cur.fetchall():
                sd = _row(s)
                cur.execute("SELECT * FROM persons WHERE squad_id = %s ORDER BY name", (s["id"],))
                persons = []
                for p in cur.fetchall():
                    pd = _row(p)
                    cur.execute("""
                        SELECT m.*, (SELECT COUNT(*) FROM winpeek_software WHERE machine_id = m.id) AS software_count
                        FROM machines m WHERE m.person_id = %s ORDER BY m.hostname
                    """, (p["id"],))
                    pd["machines"] = [_row(m) for m in cur.fetchall()]
                    persons.append(pd)
                sd["persons"] = persons
                squads.append(sd)
        return {"squads": squads}
    finally:
        conn.close()


# ── helpers ──

def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _row(r) -> dict:
    d = {}
    for k in r.keys():
        v = r[k]
        if isinstance(v, datetime):
            v = v.strftime("%Y-%m-%d %H:%M:%S")
        d[k] = v
    return d


def _to_float(v: Any) -> float | None:
    try: return float(v)
    except (TypeError, ValueError): return None
