"""WinPeek software inventory + account management.

Tables:
  winpeek_software         — installed software registry (path, version, launch)
  winpeek_software_account  — user accounts on platforms (auth tokens, multi-account)

Uses winpeek-db2 MySQL. No passwords stored — auth_type + auth_value model.
"""

import json as _json
import logging
from datetime import datetime

from .db import get_conn

logger = logging.getLogger(__name__)

_DDL_OK = False


def ensure_tables():
    """Idempotent DDL — add missing columns to existing tables."""
    global _DDL_OK
    if _DDL_OK:
        return
    conn = get_conn()
    if conn is None:
        logger.warning("software ensure_tables: DB unavailable")
        return
    try:
        with conn.cursor() as cur:
            # ── winpeek_software columns (add if missing) ──
            _add_col(cur, "winpeek_software", "name", "varchar(128) NOT NULL")
            _add_col(cur, "winpeek_software", "install_path", "text")
            _add_col(cur, "winpeek_software", "launch_args", "text")
            _add_col(cur, "winpeek_software", "description", "text")
            _add_col(cur, "winpeek_software", "company", "varchar(128)")
            _add_col(cur, "winpeek_software", "version", "varchar(32)")
            _add_col(cur, "winpeek_software", "latest_version", "varchar(32)")
            _add_col(cur, "winpeek_software", "registry_info", "text")
            _add_col(cur, "winpeek_software", "category", "varchar(64)")
            _add_col(cur, "winpeek_software", "platform", "varchar(64)")
            _add_col(cur, "winpeek_software", "exe_path", "text")
            _add_col(cur, "winpeek_software", "icon_path", "text")
            _add_col(cur, "winpeek_software", "last_launched_at", "datetime")
            _add_col(cur, "winpeek_software", "exit_normal", "tinyint")
            _add_col(cur, "winpeek_software", "created_at", "datetime DEFAULT CURRENT_TIMESTAMP")
            _add_col(cur, "winpeek_software", "updated_at", "datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")

            # ── winpeek_software_account columns ──
            _add_col(cur, "winpeek_software_account", "software_id", "int")
            _add_col(cur, "winpeek_software_account", "uid", "int")
            _add_col(cur, "winpeek_software_account", "wxid", "varchar(128)")
            _add_col(cur, "winpeek_software_account", "nickname", "varchar(256)")
            _add_col(cur, "winpeek_software_account", "auth_type", "varchar(32)")
            _add_col(cur, "winpeek_software_account", "auth_value", "text")
            _add_col(cur, "winpeek_software_account", "priority", "int DEFAULT 0")
            _add_col(cur, "winpeek_software_account", "meta", "text")
            _add_col(cur, "winpeek_software_account", "is_active", "int DEFAULT 0")
            _add_col(cur, "winpeek_software_account", "created_at", "datetime DEFAULT CURRENT_TIMESTAMP")
            _add_col(cur, "winpeek_software_account", "updated_at", "datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")

            conn.commit()
        _DDL_OK = True
        logger.info("software tables ready")
    except Exception as e:
        logger.warning(f"ensure_tables failed: {e}")
    finally:
        conn.close()


def _add_col(cur, table: str, col: str, col_type: str):
    """Add column if not exists. col_type includes type only, not the name."""
    # Skip if column exists
    cur.execute(
        "SELECT 1 FROM information_schema.COLUMNS "
        "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s AND COLUMN_NAME = %s",
        (table, col),
    )
    if cur.fetchone():
        return
    try:
        cur.execute(
            f"ALTER TABLE `{table}` ADD COLUMN `{col}` {col_type}")
    except Exception:
        pass  # column may already exist via race


# ═══════════════════════════════════════════════════════
#  SOFTWARE CRUD
# ═══════════════════════════════════════════════════════

def list_softwares() -> list[dict]:
    """List all registered software."""
    conn = get_conn()
    if conn is None:
        return []
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM winpeek_software ORDER BY name")
            rows = cur.fetchall()
            return [_row_to_dict(r) for r in rows]
    except Exception as e:
        logger.warning(f"list_softwares: {e}")
        return []
    finally:
        conn.close()


def get_software(software_id: int) -> dict | None:
    conn = get_conn()
    if conn is None:
        return None
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM winpeek_software WHERE id = %s", (software_id,))
            r = cur.fetchone()
            return _row_to_dict(r) if r else None
    finally:
        conn.close()


def upsert_software(name: str, **fields) -> dict:
    """Insert or update a software entry. 'slug' is the unique key, derived from name."""
    ensure_tables()
    conn = get_conn()
    if conn is None:
        return {"ok": False, "error": "DB unavailable"}
    # Generate slug from name
    slug = name.lower().replace(" ", "_").replace("-", "_").replace(".", "")
    # Map name→slug for common software
    slug_map = {
        "微信": "wechat", "wechat": "wechat", "企业微信": "wework",
        "抖音": "douyin", "小红书": "xiaohongshu", "快手": "kuaishou",
        "钉钉": "dingtalk", "飞书": "feishu", "qq": "qq",
        "visual studio code": "vscode", "vs code": "vscode",
    }
    slug = slug_map.get(name.lower(), slug)[:64]
    if not slug:
        slug = name[:64]

    allowed = {"name", "install_path", "exe_path", "launch_args", "description",
               "company", "version", "latest_version", "registry_info", "icon_path",
               "category", "platform", "last_launched_at", "exit_normal", "machine_id"}
    vals = {"slug": slug, "name": name}
    for k in allowed:
        if k in fields and fields[k] is not None:
            vals[k] = fields[k]
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    vals["updated_at"] = now
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM winpeek_software WHERE slug = %s", (slug,))
            existing = cur.fetchone()
            if existing:
                sid = existing["id"]
                # remove slug from update set — it's the lookup key
                update_vals = {k: v for k, v in vals.items() if k != "slug"}
                if update_vals:
                    set_clause = ", ".join(f"`{k}` = %s" for k in update_vals)
                    params = list(update_vals.values()) + [sid]
                    cur.execute(
                        f"UPDATE winpeek_software SET {set_clause} WHERE id = %s",
                        params,
                    )
            else:
                vals.setdefault("created_at", now)
                cols = ", ".join(f"`{k}`" for k in vals)
                placeholders = ", ".join("%s" for _ in vals)
                cur.execute(
                    f"INSERT INTO winpeek_software ({cols}) VALUES ({placeholders})",
                    list(vals.values()),
                )
                sid = cur.lastrowid
            conn.commit()
        return {"ok": True, "id": sid}
    except Exception as e:
        logger.warning(f"upsert_software: {e}")
        return {"ok": False, "error": str(e)}
    finally:
        conn.close()


# ═══════════════════════════════════════════════════════
#  SOFTWARE ACCOUNT CRUD
# ═══════════════════════════════════════════════════════

def list_accounts(uid: int = 0, software_id: int = 0) -> list[dict]:
    """List software accounts. Filter by uid and/or software_id."""
    conn = get_conn()
    if conn is None:
        return []
    try:
        with conn.cursor() as cur:
            sql = "SELECT * FROM winpeek_software_account WHERE 1=1"
            params = []
            if uid:
                sql += " AND uid = %s"
                params.append(uid)
            if software_id:
                sql += " AND software_id = %s"
                params.append(software_id)
            sql += " ORDER BY priority DESC, is_active DESC"
            cur.execute(sql, params)
            return [_row_to_dict(r) for r in cur.fetchall()]
    except Exception as e:
        logger.warning(f"list_accounts: {e}")
        return []
    finally:
        conn.close()


def get_account(account_id: int) -> dict | None:
    conn = get_conn()
    if conn is None:
        return None
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM winpeek_software_account WHERE id = %s",
                (account_id,))
            r = cur.fetchone()
            return _row_to_dict(r) if r else None
    finally:
        conn.close()


def upsert_account(**fields) -> dict:
    """Insert or update a software account."""
    ensure_tables()
    conn = get_conn()
    if conn is None:
        return {"ok": False, "error": "DB unavailable"}
    allowed = {"software_id", "uid", "wxid", "nickname", "auth_type",
               "auth_value", "priority", "meta", "is_active"}
    vals = {}
    for k in allowed:
        if k in fields and fields[k] is not None:
            vals[k] = fields[k]
    if "meta" in vals and isinstance(vals["meta"], dict):
        vals["meta"] = _json.dumps(vals["meta"], ensure_ascii=False)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    vals.setdefault("created_at", now)
    vals["updated_at"] = now
    try:
        with conn.cursor() as cur:
            account_id = fields.get("id")
            if account_id:
                cur.execute(
                    "SELECT id FROM winpeek_software_account WHERE id = %s",
                    (account_id,))
                if cur.fetchone():
                    set_clause = ", ".join(f"`{k}` = %s" for k in vals)
                    params = list(vals.values()) + [account_id]
                    cur.execute(
                        f"UPDATE winpeek_software_account SET {set_clause} WHERE id = %s",
                        params,
                    )
                    conn.commit()
                    return {"ok": True, "id": account_id}
            # insert
            cols = ", ".join(f"`{k}`" for k in vals)
            placeholders = ", ".join("%s" for _ in vals)
            cur.execute(
                f"INSERT INTO winpeek_software_account ({cols}) VALUES ({placeholders})",
                list(vals.values()),
            )
            conn.commit()
        return {"ok": True, "id": cur.lastrowid or account_id}
    except Exception as e:
        logger.warning(f"upsert_account: {e}")
        return {"ok": False, "error": str(e)}
    finally:
        conn.close()


def set_active_account(account_id: int, uid: int) -> dict:
    """Set one account active, deactivate others for same software."""
    conn = get_conn()
    if conn is None:
        return {"ok": False, "error": "DB unavailable"}
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT software_id FROM winpeek_software_account WHERE id = %s",
                (account_id,))
            r = cur.fetchone()
            if not r:
                return {"ok": False, "error": "Account not found"}
            sid = r["software_id"]
            cur.execute(
                "UPDATE winpeek_software_account SET is_active = 0 "
                "WHERE software_id = %s AND uid = %s",
                (sid, uid))
            cur.execute(
                "UPDATE winpeek_software_account SET is_active = 1 "
                "WHERE id = %s", (account_id,))
            conn.commit()
        return {"ok": True}
    except Exception as e:
        logger.warning(f"set_active_account: {e}")
        return {"ok": False, "error": str(e)}
    finally:
        conn.close()


def delete_account(account_id: int) -> dict:
    conn = get_conn()
    if conn is None:
        return {"ok": False, "error": "DB unavailable"}
    try:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM winpeek_software_account WHERE id = %s",
                (account_id,))
            conn.commit()
        return {"ok": True}
    except Exception as e:
        logger.warning(f"delete_account: {e}")
        return {"ok": False, "error": str(e)}
    finally:
        conn.close()


# ── helpers ──

def _row_to_dict(r) -> dict:
    d = {}
    for k in r.keys():
        v = r[k]
        if isinstance(v, datetime):
            v = v.strftime("%Y-%m-%d %H:%M:%S")
        d[k] = v
    return d
