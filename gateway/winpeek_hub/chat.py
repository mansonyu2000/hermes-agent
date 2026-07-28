"""MIM message engine — send, receive, contacts, history.

Uses winpeek-db2 MySQL (chat, contacts tables).
Memory queue bridges MQTT incoming → frontend polling.
"""

import json
import logging
import time
import uuid
from datetime import datetime
from typing import Optional

from .db import get_conn

logger = logging.getLogger(__name__)


# ── Active session ────────────────────────────────

import json as _json
from pathlib import Path as _Path

_SESSION_FILE = _Path.home() / ".hermes" / "winpeek" / ".session"

_active_uid: int = 0
_active_name: str = ""


def _restore_session():
    """Restore session from disk after serve restart."""
    global _active_uid, _active_name
    try:
        if _SESSION_FILE.exists():
            data = _json.loads(_SESSION_FILE.read_text())
            _active_uid = int(data.get("uid", 0))
            _active_name = str(data.get("name", ""))
    except Exception:
        pass


def set_active_session(uid: int, name: str = ""):
    global _active_uid, _active_name
    _active_uid = uid
    _active_name = name
    try:
        _SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
        _SESSION_FILE.write_text(_json.dumps({"uid": uid, "name": name}))
    except Exception:
        pass


# restore on module load
_restore_session()


def active_uid() -> int:
    return _active_uid


def active_name() -> str:
    return _active_name


# ── Memory queue (MQTT → frontend polling bridge) ─

_pending: list[dict] = []
_group_gids_cache: dict[int, tuple[set, float]] = {}  # {uid: (gids, ts)}


def enqueue(msg: dict):
    _pending.append(msg)


def _get_user_gids(uid: int) -> set:
    """Cached group-membership lookup (5s TTL)."""
    now = time.time()
    cached = _group_gids_cache.get(uid)
    if cached and now - cached[1] < 5:
        return cached[0]
    gids: set = set()
    try:
        conn = get_conn()
        if conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT gid FROM group_members WHERE uid = %s", (uid,))
                gids = {r["gid"] for r in cur.fetchall()}
            conn.close()
    except Exception:
        pass
    _group_gids_cache[uid] = (gids, now)
    return gids


def poll_messages(to_uid: int) -> list[dict]:
    gids = _get_user_gids(to_uid)
    mine = [m for m in _pending
            if m.get("to_uid") == to_uid or m.get("gid", 0) in gids]
    _pending[:] = [m for m in _pending
                   if not (m.get("to_uid") == to_uid or m.get("gid", 0) in gids)]
    return mine


# ── Send ────────────────────────────────────────

def _next_mid() -> str:
    """Generate a message ID: mim-{timestamp}-{random}"""
    return f"mim-{int(time.time()*1000)}-{uuid.uuid4().hex[:8]}"


def send_message(from_uid: int, from_name: str, to_uid: int, body: str) -> dict:
    """Send a single-chat message."""
    conn = get_conn()
    if conn is None:
        return {"ok": False, "error": "DB unavailable"}
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
                cur.execute("SELECT nickname FROM users WHERE uid = %s", (to_uid,))
                peer = cur.fetchone()
                peer_name = peer.get("nickname") if peer else f"user_{to_uid}"
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

    # Local delivery (memory queue — instant for same‑machine receivers)
    enqueue({
        "mid": mid,
        "to_uid": to_uid,
        "from_uid": from_uid,
        "from_name": from_name,
        "content": body,
        "time": now,
    })

    # Register mid with dedup tracker BEFORE MQTT publish.
    # When the MQTT relay loops back (same machine), _on_message
    # will see this mid in _seen_mids and skip the duplicate enqueue.
    # Cross‑machine: receiver's instance won't have this mid yet → delivers.
    try:
        from gateway.winpeek_hub.mqtt_adapter import mark_mid_seen
        mark_mid_seen(mid)
    except Exception:
        pass

    # MQTT publish via say topic (relay handles say→inbox forwarding)
    try:
        from gateway.winpeek_hub.mqtt_adapter import send_message as mqtt_send
        mqtt_send(to_uid, body, from_name,
                  origin_uid=from_uid, origin_name=from_name, mid=mid)
    except Exception as e:
        logger.warning(f"MIM MQTT publish failed for mid={mid}: {e}")

    # ── Peeka routing: 3‑layer decision ──
    try:
        from gateway.winpeek_hub.peeka_router import route_incoming
        decision = route_incoming(from_uid, to_uid, body)

        if decision["action"] in ("auto_reply", "daemon_answer"):
            # Daemon auto‑reply as the recipient (B → A)
            reply = decision["reply"]
            layer = 1 if decision["action"] == "auto_reply" else 2

            # Record to L1/L2 digest
            try:
                from apps.winpeek_injector.daemon import add_digest_entry
                add_digest_entry(from_uid, from_name, body, reply, layer)
            except Exception:
                pass

            _enqueue_auto_reply(to_uid, from_uid, reply, _resolve_name(to_uid))

        elif decision["action"] == "drop":
            # Remove from pending queue (advertisement dropped)
            _pending[:] = [m for m in _pending
                           if m.get("mid") != mid]

        elif decision["action"] == "forward":
            ctx = decision.get("context", {})
            # Write to recipient agent's inbox
            msg_dict = {
                "mid": mid,
                "from_uid": from_uid,
                "from_name": from_name,
                "from_role": ctx.get("peer_role", ""),
                "from_peeka_name": ctx.get("peeka_name", ""),
                "relation": ctx.get("relation", "unknown"),
                "body": body,
                "context": ctx,
                "received_at": now,
                "is_retry": False,
                "retry_count": 0,
            }
            try:
                from apps.winpeek_injector.daemon import write_to_inbox, track_l3_message
                write_to_inbox(to_uid, msg_dict)
                track_l3_message(mid, to_uid, from_uid)
            except Exception as e:
                logger.warning(f"[Peeka] inbox write failed: {e}")

            # Phase 2: Passive delivery to ALL mim-agent types
            # (Hermes, Claude Code, Qoder — any agent with a window)
            try:
                from gateway.winpeek_hub import identity
                agent_info = identity.get_by_uid(to_uid)
                is_agent = (
                    agent_info
                    and agent_info.get("identity_type") in ("mim-agent", "ai")
                )
                if is_agent:
                    from apps.winpeek_injector.engine import deliver_mim_message
                    if deliver_mim_message(to_uid, msg_dict):
                        from apps.winpeek_injector.daemon import mark_delivered, update_reliability
                        mark_delivered(to_uid, mid)
                        update_reliability(mid, "delivered")
                        logger.info(
                            "[Peeka] passive delivery: mid=%s to agent uid=%s type=%s",
                            mid[:16], to_uid, agent_info.get("agent_type", "?")
                        )
            except Exception:
                pass

    except Exception as e:
        logger.warning(f"[Peeka] routing error: {e}")

    return {"ok": True, "mid": mid}


def _enqueue_auto_reply(from_uid: int, to_uid: int, reply: str, original_from_name: str):
    """Enqueue an auto‑reply message without DB INSERT."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    enqueue({
        "to_uid": to_uid,
        "from_uid": from_uid,
        "from_name": "🤖 " + original_from_name,  # denote auto-reply
        "content": reply,
        "time": now,
        "is_auto_reply": True,
    })


# ── Group Send ──────────────────────────────────

def send_group_message(from_uid: int, from_name: str, gid: int, body: str) -> dict:
    """Send a group chat message. Delivers to all group members."""
    conn = get_conn()
    if conn is None:
        return {"ok": False, "error": "DB unavailable"}
    try:
        with conn.cursor() as cur:
            # Verify sender is a group member
            cur.execute(
                "SELECT 1 FROM group_members WHERE gid = %s AND uid = %s",
                (gid, from_uid))
            if not cur.fetchone():
                return {"ok": False, "error": "not a group member"}

            mid = _next_mid()
            cid = str(uuid.uuid4().hex[:16])
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Insert with gid
            cur.execute(
                """INSERT INTO chat
                   (mid, cid, from_uid, to_uid, gid, role, content, from_type,
                    created_at, sent_at, direction, delivery_status)
                   VALUES (%s, %s, %s, 0, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (mid, cid, from_uid, gid, "user", body, "mim",
                 now, now, "outgoing", "sent"),
            )
            conn.commit()

            # Get all group member uids
            cur.execute(
                "SELECT uid FROM group_members WHERE gid = %s", (gid,))
            member_uids = [r["uid"] for r in cur.fetchall()]
    except Exception as e:
        logger.warning(f"MIM group send DB failed: {e}")
        return {"ok": False, "error": str(e)}
    finally:
        conn.close()

    # Enqueue for each member (skip sender)
    for muid in member_uids:
        if muid == from_uid:
            continue
        enqueue({
            "mid": mid,
            "to_uid": muid,
            "from_uid": from_uid,
            "from_name": from_name,
            "content": body,
            "time": now,
            "gid": gid,
        })

    # Register mid with dedup tracker before MQTT publish
    try:
        from gateway.winpeek_hub.mqtt_adapter import mark_mid_seen
        mark_mid_seen(mid)
    except Exception:
        pass

    # MQTT broadcast via say topic for each member
    try:
        from gateway.winpeek_hub.mqtt_adapter import send_message as mqtt_send
        for muid in member_uids:
            if muid == from_uid:
                continue
            mqtt_send(muid, body, from_name,
                      origin_uid=from_uid, origin_name=from_name, mid=mid)
    except Exception as e:
        logger.warning(f"MIM group MQTT publish failed for mid={mid}: {e}")

    return {"ok": True, "mid": mid, "gid": gid, "members": len(member_uids)}


# ── Helpers ─────────────────────────────────────

def _resolve_name(uid: int) -> str:
    try:
        from gateway.winpeek_hub import identity
        u = identity.get_by_uid(uid)
        return u.get("nickname", f"uid_{uid}") if u else f"uid_{uid}"
    except Exception:
        return f"uid_{uid}"

# ── History ─────────────────────────────────────

def get_history(uid: int, peer_uid: int = 0, gid: int = 0,
                limit: int = 50) -> list[dict]:
    """Get conversation history. gid>0 = group chat, else peer-to-peer."""
    conn = get_conn()
    if conn is None:
        return []
    try:
        with conn.cursor() as cur:
            if gid:
                # Security: only group members can read group history
                cur.execute(
                    "SELECT 1 FROM group_members WHERE gid = %s AND uid = %s",
                    (gid, uid),
                )
                if not cur.fetchone():
                    return []
                cur.execute(
                    """SELECT from_uid, to_uid, role, content, created_at
                       FROM chat
                       WHERE gid = %s
                       ORDER BY id DESC LIMIT %s""",
                    (gid, limit),
                )
            else:
                cur.execute(
                    """SELECT from_uid, to_uid, role, content, created_at
                       FROM chat
                       WHERE gid IS NULL
                         AND ((from_uid = %s AND to_uid = %s)
                           OR (from_uid = %s AND to_uid = %s))
                       ORDER BY id DESC LIMIT %s""",
                    (uid, peer_uid, peer_uid, uid, limit),
                )
            rows = list(reversed(cur.fetchall()))
            # Resolve names for all uids in this conversation
            uid_names: dict[int, str] = {}
            for r in rows:
                for field in ("from_uid", "to_uid"):
                    u = r.get(field)
                    if u is not None and u not in uid_names:
                        uid_names[u] = _resolve_name(int(u))
            return [
                {
                    "from_uid": r["from_uid"],
                    "to_uid": r["to_uid"],
                    "from_name": uid_names.get(int(r.get("from_uid", 0)), ""),
                    "content": r["content"],
                    "msg_ts": str(r.get("created_at", "")),
                }
                for r in rows
            ]
    finally:
        conn.close()


# ── Contacts ────────────────────────────────────

def get_contacts(requester_uid: int = 0) -> dict:
    """Get all users as contacts with real online status + last message info.

    requester_uid: only returns last_message previews from conversations
    involving this uid. 0 = skip previews entirely (anonymous/no auth).

    Returns {"contacts": [...], "groups": [...]}."""
    contacts: list[dict] = []
    groups: list[dict] = []
    try:
        from gateway.winpeek_hub import identity, hub
        users = identity.list_all()
        previews: dict[int, tuple[str, str]] = {}
        if requester_uid > 0:
            conn = get_conn()
            if conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT t.from_uid, t.to_uid, t.content, t.created_at
                        FROM chat t
                        INNER JOIN (
                            SELECT MAX(id) AS max_id
                            FROM chat
                            WHERE gid IS NULL
                              AND (from_uid = %s OR to_uid = %s)
                            GROUP BY CASE WHEN from_uid < to_uid
                                THEN CONCAT(from_uid,'-',to_uid)
                                ELSE CONCAT(to_uid,'-',from_uid) END
                        ) m ON t.id = m.max_id
                    """, (requester_uid, requester_uid))
                    for row in cur.fetchall():
                        fu = row["from_uid"]
                        tu = row["to_uid"]
                        previews[fu] = previews.get(fu) or (row["content"], row["created_at"])
                        previews[tu] = previews.get(tu) or (row["content"], row["created_at"])
                conn.close()
        for u in users:
            uid = u["uid"]
            u["online"] = hub.is_online(uid)
            p = previews.get(uid)
            u["last_message"] = p[0] if p else ""
            u["last_msg_ts"] = p[1] if p else ""
        contacts = users

        # ── Groups ──
        if requester_uid > 0:
            try:
                from gateway.winpeek_hub.group import get_my_groups
                groups = get_my_groups(requester_uid)
            except Exception:
                pass

        return {"contacts": contacts, "groups": groups}
    except Exception:
        return {"contacts": [], "groups": []}


def get_user_contacts(uid: int) -> list[dict]:
    """Get contacts for a specific user from contacts table."""
    conn = get_conn()
    if conn is None:
        return []
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


# ── Search ───────────────────────────────────────

def search_users(q: str = "", filters: dict | None = None) -> list[dict]:
    """Search users by nickname/UID/role. q supports comma-separated UIDs.

    Returns list of user dicts with 'online' field. Empty search (no q + no
    filters) returns all users. Comma-separated digits in q are parsed as UIDs.
    """
    from gateway.winpeek_hub import identity, hub
    users = identity.list_all()
    results = []
    q = (q or "").strip().lower()
    # Parse UIDs from q (comma-separated) or filters.uids
    uids = []
    if filters and filters.get("uids"):
        uids = [int(u) for u in str(filters["uids"]).split(",") if u.strip().isdigit()]
    elif q and all(p.strip().isdigit() for p in q.split(",")):
        uids = [int(p.strip()) for p in q.split(",") if p.strip()]
        q = ""
    type_filter = (filters or {}).get("identity_type", "")
    # Require at least one filter criterion — don't enumerate all users
    has_criteria = bool(uids) or bool(q) or bool(type_filter)
    if not has_criteria:
        return []
    for u in users:
        uid = u.get("uid", 0)
        nick = (u.get("nickname") or "").lower()
        role = (u.get("role") or "").lower()
        id_type = u.get("identity_type", "")
        if (uids and uid in uids) or (q and (q in nick or q in role or q == str(uid))) or (type_filter and id_type == type_filter):
            results.append({**u, "online": hub.is_online(uid)})
    return results[:50]


# ── Friend Requests (F1.3) ───────────────────────

def add_contact(from_uid: int, to_uid: int, message: str = "") -> dict:
    """Add a friend. For now auto-accepts (same as old PeekabooWin behavior)."""
    conn = get_conn()
    if conn is None:
        return {"ok": False, "error": "DB unavailable"}
    try:
        with conn.cursor() as cur:
            # Check if already exists in contacts
            cur.execute(
                "SELECT 1 FROM contacts WHERE uid=%s AND c_uid=%s",
                (from_uid, to_uid))
            if cur.fetchone():
                return {"ok": False, "error": "already friends"}
            # Insert bidirectional
            cur.execute(
                "INSERT INTO contacts (uid, c_uid, display_name, status, last_contact_at) "
                "VALUES (%s,%s,%s,'active',NOW())",
                (from_uid, to_uid, _resolve_name(to_uid)))
            cur.execute(
                "INSERT INTO contacts (uid, c_uid, display_name, status, last_contact_at) "
                "VALUES (%s,%s,%s,'active',NOW())",
                (to_uid, from_uid, _resolve_name(from_uid)))
            # Also insert into contact_requests for audit
            cur.execute(
                "INSERT INTO contact_requests (from_uid, to_uid, message, status) "
                "VALUES (%s,%s,%s,'accepted') "
                "ON DUPLICATE KEY UPDATE status='accepted'",
                (from_uid, to_uid, message[:256]))
            conn.commit()
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}
    finally:
        conn.close()


def remove_contact(uid: int, target_uid: int) -> dict:
    """Remove a contact bidirectionally."""
    conn = get_conn()
    if conn is None:
        return {"ok": False, "error": "DB unavailable"}
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM contacts WHERE uid=%s AND c_uid=%s", (uid, target_uid))
            cur.execute("DELETE FROM contacts WHERE uid=%s AND c_uid=%s", (target_uid, uid))
            conn.commit()
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}
    finally:
        conn.close()


def list_contact_requests(uid: int) -> list[dict]:
    """List pending/recent friend requests for a user."""
    conn = get_conn()
    if conn is None:
        return []
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT cr.*, u.nickname AS from_nick, u.role AS from_role "
                "FROM contact_requests cr "
                "LEFT JOIN users u ON cr.from_uid = u.uid "
                "WHERE cr.to_uid = %s OR cr.from_uid = %s "
                "ORDER BY cr.created_at DESC LIMIT 50",
                (uid, uid))
            return [{k: str(v) if isinstance(v, bytes) else v
                     for k, v in r.items()} for r in cur.fetchall()]
    finally:
        conn.close()


# ── Message Search (F2.4) ─────────────────────────

def search_history(uid: int, q: str, peer_uid: int = 0, gid: int = 0) -> list[dict]:
    """Search chat history by keyword."""
    conn = get_conn()
    if conn is None:
        return []
    try:
        with conn.cursor() as cur:
            like = f"%{q}%"
            if gid:
                # Auth: verify group membership
                cur.execute(
                    "SELECT 1 FROM group_members WHERE gid=%s AND uid=%s",
                    (gid, uid))
                if not cur.fetchone():
                    return []
                cur.execute(
                    "SELECT from_uid, to_uid, content, created_at FROM chat "
                    "WHERE gid=%s AND content LIKE %s ORDER BY id DESC LIMIT 30",
                    (gid, like))
            elif peer_uid:
                cur.execute(
                    "SELECT from_uid, to_uid, content, created_at FROM chat "
                    "WHERE gid IS NULL AND content LIKE %s "
                    "AND ((from_uid=%s AND to_uid=%s) OR (from_uid=%s AND to_uid=%s)) "
                    "ORDER BY id DESC LIMIT 30",
                    (like, uid, peer_uid, peer_uid, uid))
            else:
                cur.execute(
                    "SELECT from_uid, to_uid, content, created_at FROM chat "
                    "WHERE content LIKE %s AND (from_uid=%s OR to_uid=%s) "
                    "ORDER BY id DESC LIMIT 30",
                    (like, uid, uid))
            return [
                {"from_uid": r["from_uid"],
                 "from_name": _resolve_name(int(r.get("from_uid", 0))),
                 "content": r["content"],
                 "msg_ts": str(r.get("created_at", ""))}
                for r in cur.fetchall()
            ]
    finally:
        conn.close()


# ── Message Status (F2.3) ─────────────────────────

def mark_read(uid: int, peer_uid: int = 0) -> int:
    """Mark messages from peer_uid to uid as read."""
    conn = get_conn()
    if conn is None:
        return 0
    try:
        with conn.cursor() as cur:
            if peer_uid:
                cur.execute(
                    "UPDATE chat SET delivery_status='read' "
                    "WHERE to_uid=%s AND from_uid=%s AND delivery_status='sent'",
                    (uid, peer_uid))
            else:
                cur.execute(
                    "UPDATE chat SET delivery_status='read' "
                    "WHERE to_uid=%s AND delivery_status='sent'",
                    (uid,))
            affected = cur.rowcount
            conn.commit()
        return affected
    finally:
        conn.close()
