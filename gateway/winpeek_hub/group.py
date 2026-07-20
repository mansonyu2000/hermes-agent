"""MIM group chat — CRUD for existing groups & group_members tables.

Tables already exist in winpeek-db2 MySQL (from PeekabooWin):
  groups:         gid, title, conversation_type, status, metadata, owner_id,
                  admins, description, avatar, created_at, updated_at
  group_members:  gid, uid, participant_type, joined_at
  chat:           gid column (NULL=单聊, <int>=群聊)
"""

import json as _json
import logging
from datetime import datetime

from .db import get_conn

logger = logging.getLogger(__name__)


def _is_owner_or_admin(gid: int, uid: int, cur) -> bool:
    """Check whether uid is owner or admin of gid. Uses the open cursor."""
    # 1) groups.owner_id
    cur.execute("SELECT owner_id, admins FROM `groups` WHERE gid = %s", (gid,))
    g = cur.fetchone()
    if not g:
        return False
    if str(g.get("owner_id", "")) == str(uid):
        return True
    try:
        admins = _json.loads(g.get("admins") or "[]")
        if str(uid) in [str(a) for a in admins]:
            return True
    except Exception:
        pass
    # 2) group_members.participant_type
    cur.execute(
        "SELECT participant_type FROM group_members WHERE gid = %s AND uid = %s",
        (gid, uid),
    )
    gm = cur.fetchone()
    if gm and gm.get("participant_type", "") in ("owner", "admin"):
        return True
    return False


# ── Create ──────────────────────────────────────

def create_group(owner_uid: int, title: str,
                 member_uids: list[int], description: str = "") -> dict:
    """Create a group. owner_uid is the group owner."""
    conn = get_conn()
    if conn is None:
        return {"ok": False, "error": "DB unavailable"}
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO `groups`
                   (title, conversation_type, owner_id, admins, description,
                    metadata, status, created_at, updated_at)
                   VALUES (%s, 'group', %s, '[]', %s, '{}', 1, %s, %s)""",
                (title, str(owner_uid), description, now, now),
            )
            gid = cur.lastrowid

            # owner
            cur.execute(
                "INSERT INTO group_members (gid, uid, participant_type, joined_at) "
                "VALUES (%s, %s, 'owner', %s)",
                (gid, owner_uid, now),
            )

            seen = {owner_uid}
            for muid in member_uids:
                if muid in seen:
                    continue
                seen.add(muid)
                cur.execute(
                    "INSERT INTO group_members (gid, uid, participant_type, joined_at) "
                    "VALUES (%s, %s, 'member', %s)",
                    (gid, muid, now),
                )

            conn.commit()
        return {"ok": True, "gid": gid}
    except Exception as e:
        logger.warning(f"create_group failed: {e}")
        return {"ok": False, "error": str(e)}
    finally:
        conn.close()


# ── Read ────────────────────────────────────────

def get_group_info(gid: int, requester_uid: int) -> dict | None:
    """Return group detail + member list. Caller must be a member."""
    conn = get_conn()
    if conn is None:
        return None
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM group_members WHERE gid = %s AND uid = %s",
                (gid, requester_uid),
            )
            if not cur.fetchone():
                return None
            cur.execute("SELECT * FROM `groups` WHERE gid = %s", (gid,))
            g = cur.fetchone()
            if not g:
                return None
            # Parse admins JSON
            admins = []
            try:
                admins = _json.loads(g.get("admins") or "[]")
            except Exception:
                pass
            cur.execute("""
                SELECT gm.uid, gm.participant_type, gm.joined_at,
                       u.nickname, u.role AS user_role
                FROM group_members gm
                LEFT JOIN users u ON gm.uid = u.uid
                WHERE gm.gid = %s
                ORDER BY gm.joined_at
            """, (gid,))
            members = [
                {
                    "uid": r["uid"],
                    "participant_type": r.get("participant_type", "member"),
                    "nickname": r.get("nickname", "") or f"user_{r['uid']}",
                    "user_role": r.get("user_role", ""),
                    "joined_at": str(r.get("joined_at", "")),
                }
                for r in cur.fetchall()
            ]
        return {
            "gid": g["gid"],
            "title": g["title"],
            "description": g.get("description") or "",
            "owner_id": g.get("owner_id", ""),
            "admins": admins,
            "metadata": g.get("metadata") or "{}",
            "status": g["status"],
            "created_at": str(g.get("created_at", "")),
            "members": members,
        }
    except Exception as e:
        logger.warning(f"get_group_info failed: {e}")
        return None
    finally:
        conn.close()


def get_my_groups(uid: int) -> list[dict]:
    """Return all active groups that uid belongs to, with last-message preview."""
    conn = get_conn()
    if conn is None:
        return []
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT g.gid, g.title, g.description, g.owner_id, g.status,
                       g.created_at, g.updated_at,
                       (SELECT COUNT(*)
                        FROM group_members WHERE gid = g.gid) AS member_count
                FROM `groups` g
                INNER JOIN group_members gm ON g.gid = gm.gid
                WHERE gm.uid = %s
                  AND g.status = 1
                  AND g.conversation_type = 'group'
                ORDER BY g.updated_at DESC
            """, (uid,))
            rows = cur.fetchall()

            # Last message per group
            cur.execute("""
                SELECT gid, content, created_at
                FROM chat
                WHERE gid IS NOT NULL
                  AND id IN (
                    SELECT MAX(id) FROM chat
                    WHERE gid IS NOT NULL
                    GROUP BY gid
                  )
            """)
            last_msgs = {}
            for r in cur.fetchall():
                last_msgs[r["gid"]] = (
                    r["content"] or "",
                    str(r.get("created_at", "")),
                )

        return [
            {
                "gid": r["gid"],
                "title": r["title"],
                "description": r.get("description") or "",
                "owner_id": r.get("owner_id", ""),
                "member_count": r.get("member_count", 0),
                "last_message": last_msgs.get(r["gid"], ("", ""))[0],
                "last_time": last_msgs.get(r["gid"], ("", ""))[1],
                "created_at": str(r.get("created_at", "")),
            }
            for r in rows
        ]
    except Exception as e:
        logger.warning(f"get_my_groups failed: {e}")
        return []
    finally:
        conn.close()


# ── Mutate ──────────────────────────────────────

def invite_members(gid: int, uids: list[int], requester_uid: int) -> dict:
    """Add members to a group. requester must be owner or admin."""
    conn = get_conn()
    if conn is None:
        return {"ok": False, "error": "DB unavailable"}
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    added = 0
    try:
        with conn.cursor() as cur:
            if not _is_owner_or_admin(gid, requester_uid, cur):
                return {"ok": False, "error": "Permission denied"}
            for uid in uids:
                try:
                    cur.execute(
                        "INSERT IGNORE INTO group_members "
                        "(gid, uid, participant_type, joined_at) "
                        "VALUES (%s, %s, 'member', %s)",
                        (gid, uid, now),
                    )
                    if cur.rowcount:
                        added += 1
                except Exception:
                    pass
            cur.execute(
                "UPDATE `groups` SET updated_at = %s WHERE gid = %s",
                (now, gid),
            )
            conn.commit()
        return {"ok": True, "gid": gid, "added": added}
    except Exception as e:
        logger.warning(f"invite_members failed: {e}")
        return {"ok": False, "error": str(e)}
    finally:
        conn.close()


def update_group(gid: int, requester_uid: int,
                 title: str = "", description: str = "",
                 announcement: str = "") -> dict:
    """Update group info. announcement=non-empty appends to list, ''=no-op."""
    conn = get_conn()
    if conn is None:
        return {"ok": False, "error": "DB unavailable"}
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with conn.cursor() as cur:
            if not _is_owner_or_admin(gid, requester_uid, cur):
                return {"ok": False, "error": "Permission denied"}
            sets: list[str] = []
            vals: list = []
            if title:
                sets.append("title = %s")
                vals.append(title)
            if description:
                sets.append("description = %s")
                vals.append(description)
            if announcement.strip():
                cur.execute(
                    "SELECT metadata FROM `groups` WHERE gid = %s", (gid,))
                row = cur.fetchone()
                meta: dict = {}
                try:
                    meta = _json.loads(row["metadata"] or "{}")
                except Exception:
                    pass
                anns: list = meta.get("announcements", [])
                # simple ID
                an_id = f"_an{len(anns)+1}_{int(datetime.now().timestamp())}"
                anns.append({
                    "id": an_id,
                    "text": announcement.strip(),
                    "created_by": requester_uid,
                    "created_at": now,
                })
                meta["announcements"] = anns
                # backward-compat top-level announcement field
                meta["announcement"] = announcement.strip()
                sets.append("metadata = %s")
                vals.append(_json.dumps(meta, ensure_ascii=False))
            if not sets:
                return {"ok": False, "error": "Nothing to update"}
            sets.append("updated_at = %s")
            vals.append(now)
            vals.append(gid)
            cur.execute(
                f"UPDATE `groups` SET {', '.join(sets)} WHERE gid = %s",
                vals,
            )
            conn.commit()
        return {"ok": True}
    except Exception as e:
        logger.warning(f"update_group failed: {e}")
        return {"ok": False, "error": str(e)}
    finally:
        conn.close()


def delete_announcement(gid: int, an_id: str,
                        requester_uid: int) -> dict:
    """Delete an announcement by id. Only owner or admin can do this."""
    conn = get_conn()
    if conn is None:
        return {"ok": False, "error": "DB unavailable"}
    try:
        with conn.cursor() as cur:
            if not _is_owner_or_admin(gid, requester_uid, cur):
                return {"ok": False, "error": "Permission denied"}
            cur.execute(
                "SELECT metadata FROM `groups` WHERE gid = %s", (gid,))
            row = cur.fetchone()
            meta: dict = {}
            try:
                meta = _json.loads(row["metadata"] or "{}")
            except Exception:
                pass
            old_anns: list = meta.get("announcements", [])
            anns = [a for a in old_anns if a.get("id") != an_id]
            if len(anns) == len(old_anns):
                return {"ok": False, "error": "Announcement not found"}
            meta["announcements"] = anns
            # keep top-level in sync
            meta["announcement"] = anns[-1]["text"] if anns else ""
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cur.execute(
                "UPDATE `groups` SET metadata = %s, updated_at = %s "
                "WHERE gid = %s",
                (_json.dumps(meta, ensure_ascii=False), now, gid),
            )
            conn.commit()
        return {"ok": True}
    except Exception as e:
        logger.warning(f"delete_announcement failed: {e}")
        return {"ok": False, "error": str(e)}
    finally:
        conn.close()


def transfer_ownership(gid: int, new_owner_uid: int,
                       requester_uid: int) -> dict:
    """Transfer group ownership. Only current owner can do this."""
    conn = get_conn()
    if conn is None:
        return {"ok": False, "error": "DB unavailable"}
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT owner_id FROM `groups` WHERE gid = %s", (gid,))
            g = cur.fetchone()
            if not g:
                return {"ok": False, "error": "Group not found"}
            if str(g["owner_id"]) != str(requester_uid):
                return {"ok": False, "error": "Only the owner can transfer ownership"}
            # New owner must be a member
            cur.execute(
                "SELECT 1 FROM group_members WHERE gid = %s AND uid = %s",
                (gid, new_owner_uid),
            )
            if not cur.fetchone():
                return {"ok": False, "error": "New owner must be a group member"}
            # Update groups.owner_id
            cur.execute(
                "UPDATE `groups` SET owner_id = %s, updated_at = %s WHERE gid = %s",
                (str(new_owner_uid), now, gid),
            )
            # Update admins: add old owner as admin
            admins_raw = g.get("admins") or "[]"
            try:
                admins = _json.loads(admins_raw)
            except Exception:
                admins = []
            old_uid = str(requester_uid)
            if old_uid not in [str(a) for a in admins]:
                admins.append(int(requester_uid))
                cur.execute(
                    "UPDATE `groups` SET admins = %s WHERE gid = %s",
                    (_json.dumps(admins), gid),
                )
            conn.commit()
        return {"ok": True}
    except Exception as e:
        logger.warning(f"transfer_ownership failed: {e}")
        return {"ok": False, "error": str(e)}
    finally:
        conn.close()


def leave_group(gid: int, uid: int) -> dict:
    """Leave a group. Anyone can leave freely (including owner — group stays)."""
    conn = get_conn()
    if conn is None:
        return {"ok": False, "error": "DB unavailable"}
    try:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM group_members WHERE gid = %s AND uid = %s",
                (gid, uid),
            )
            conn.commit()
        return {"ok": True}
    except Exception as e:
        logger.warning(f"leave_group failed: {e}")
        return {"ok": False, "error": str(e)}
    finally:
        conn.close()


def remove_member(gid: int, uid: int, requester_uid: int) -> dict:
    """Remove a member from a group. requester must be owner or admin."""
    conn = get_conn()
    if conn is None:
        return {"ok": False, "error": "DB unavailable"}
    try:
        with conn.cursor() as cur:
            if not _is_owner_or_admin(gid, requester_uid, cur):
                return {"ok": False, "error": "Permission denied"}
            cur.execute(
                "DELETE FROM group_members WHERE gid = %s AND uid = %s",
                (gid, uid),
            )
            conn.commit()
        return {"ok": True}
    except Exception as e:
        logger.warning(f"remove_member failed: {e}")
        return {"ok": False, "error": str(e)}
    finally:
        conn.close()
