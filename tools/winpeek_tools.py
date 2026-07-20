"""
winpeek_tools.py — WinPeek RPA 工具注册

注册到 Hermes 的工具系统（tools/registry.py），
和 computer_use 同级别，前端通过 useGatewayRequest 直接调用。

注册后 Hermes Agent 可以调用:
  - winpeek_wechat_send(contact_name, message)
  - winpeek_wechat_collect_msgs(contact_name, max_pages)
  - winpeek_wechat_collect_contacts()
  - winpeek_list_templates()
"""

from __future__ import annotations

import json
import logging
from typing import Any

from tools.registry import registry

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════
# 工具实现
# ═══════════════════════════════════════════════════════

def _handle_send_message(args: dict) -> str:
    """给微信好友发送消息"""
    contact = args.get("contact_name", "")
    message = args.get("message", "")
    if not contact or not message:
        return json.dumps({"error": "缺少参数 contact_name 或 message"})

    try:
        # 方式1: 直接用 wechat_uia.py (毫秒级)
        from plugins.winpeek_rpa.platforms.wechat.uia import WeChatUIA
        wx = WeChatUIA()
        wx.search_and_open(contact)
        wx.send_message(message)
        return json.dumps({"ok": True, "contact": contact, "sent": message})

    except Exception as e:
        # 方式2: 降级到 cua-driver 模板 (秒级)
        logger.warning(f"WeChatUIA failed: {e}, falling back to template")
        return json.dumps({
            "ok": False,
            "error": str(e),
            "fallback": "use computer_use or the wechat_send_message template",
        })


def _handle_collect_msgs(args: dict) -> str:
    """采集微信好友的聊天记录"""
    contact = args.get("contact_name", "")
    max_pages = int(args.get("max_pages", 80))
    if not contact:
        return json.dumps({"error": "缺少参数 contact_name"})

    try:
        from plugins.winpeek_rpa.platforms.wechat.uia import WeChatUIA
        from plugins.winpeek_rpa.platforms.wechat.db import WeChatDB
        from plugins.winpeek_rpa.platforms.wechat.api import WeChatEyes, WeChatHands, WeChatEngine

        wx = WeChatUIA()
        db = WeChatDB()
        w = wx._window
        eyes = WeChatEyes(w)
        hands = WeChatHands(None, wx, w)
        engine = WeChatEngine(db, eyes, hands, w)

        wx.search_and_open(contact)
        ins, dup = engine.collect_msgs(contact, max_pages=max_pages)
        return json.dumps({"ok": True, "inserted": ins, "duplicates": dup})

    except Exception as e:
        return json.dumps({"ok": False, "error": str(e)})


def _handle_collect_contacts(args: dict) -> str:
    """采集微信通讯录"""
    try:
        from plugins.winpeek_rpa.platforms.wechat.uia import WeChatUIA
        from plugins.winpeek_rpa.platforms.wechat.db import WeChatDB

        wx = WeChatUIA()
        db = WeChatDB()
        wx.click_nav("通讯录")
        # 调用原有的 collect_contacts 逻辑
        from plugins.winpeek_rpa.platforms.wechat.contacts import collect_all_contacts
        count = collect_all_contacts(wx, db)
        return json.dumps({"ok": True, "contacts_collected": count})

    except Exception as e:
        return json.dumps({"ok": False, "error": str(e)})


def _handle_list_templates(args: dict) -> str:
    """列出已学习的 MCP 模板"""
    import os
    from pathlib import Path
    templates_dir = Path(os.path.expanduser("~/.hermes/winpeek/templates"))
    if not templates_dir.exists():
        return json.dumps({"templates": []})

    templates = []
    for f in sorted(templates_dir.glob("*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            meta = data.get("meta", {})
            templates.append({
                "name": meta.get("name", f.stem),
                "version": meta.get("version", "?"),
                "description": meta.get("description", ""),
                "tested": meta.get("tested", False),
            })
        except Exception:
            pass
    return json.dumps({"count": len(templates), "templates": templates})


# ═══════════════════════════════════════════════════════
# 注册到 Hermes 工具系统
# ═══════════════════════════════════════════════════════

def _check_winpeek_requirements() -> bool:
    """检查 WinPeek 工具是否可用（微信必须已安装）"""
    import shutil
    import os
    # 检查微信是否存在
    wechat_paths = [
        r"D:\Program Files\Weixin\Weixin.exe",
        r"C:\Program Files\Weixin\Weixin.exe",
        r"C:\Program Files (x86)\Weixin\Weixin.exe",
        os.path.expandvars(r"%ProgramFiles%\Weixin\Weixin.exe"),
    ]
    for p in wechat_paths:
        if os.path.exists(p):
            return True
    return bool(shutil.which("Weixin.exe")) or bool(shutil.which("WeChat.exe"))


# ── 注册 ──

registry.register(
    name="winpeek_wechat_send",
    toolset="winpeek_rpa",
    schema={
        "name": "winpeek_wechat_send",
        "description": "给微信好友发送消息（直接调用 wechat_uia.py，毫秒级）",
        "parameters": {
            "type": "object",
            "properties": {
                "contact_name": {
                    "type": "string",
                    "description": "微信好友名或备注名",
                },
                "message": {
                    "type": "string",
                    "description": "要发送的消息内容",
                },
            },
            "required": ["contact_name", "message"],
        },
    },
    handler=lambda args, **kw: _handle_send_message(args),
    check_fn=_check_winpeek_requirements,
    requires_env=[],
    description="给微信好友发送消息 — WinPeek UIA 引擎驱动",
)

registry.register(
    name="winpeek_wechat_collect_msgs",
    toolset="winpeek_rpa",
    schema={
        "name": "winpeek_wechat_collect_msgs",
        "description": "采集微信好友的聊天记录",
        "parameters": {
            "type": "object",
            "properties": {
                "contact_name": {
                    "type": "string",
                    "description": "微信好友名",
                },
                "max_pages": {
                    "type": "integer",
                    "description": "最大翻页数，默认 80",
                    "default": 80,
                },
            },
            "required": ["contact_name"],
        },
    },
    handler=lambda args, **kw: _handle_collect_msgs(args),
    check_fn=_check_winpeek_requirements,
    requires_env=[],
    description="采集微信聊天记录 — WinPeek 引擎驱动",
)

registry.register(
    name="winpeek_wechat_collect_contacts",
    toolset="winpeek_rpa",
    schema={
        "name": "winpeek_wechat_collect_contacts",
        "description": "采集微信通讯录联系人",
        "parameters": {
            "type": "object",
            "properties": {},
        },
    },
    handler=lambda args, **kw: _handle_collect_contacts(args),
    check_fn=_check_winpeek_requirements,
    requires_env=[],
    description="采集微信通讯录 — WinPeek 引擎驱动",
)

registry.register(
    name="winpeek_list_templates",
    toolset="winpeek_rpa",
    schema={
        "name": "winpeek_list_templates",
        "description": "列出 WinPeek 已学习的 MCP 模板",
        "parameters": {"type": "object", "properties": {}},
    },
    handler=lambda args, **kw: _handle_list_templates(args),
    check_fn=lambda: True,
    requires_env=[],
    description="列出已学习的 WinPeek RPA 模板",
)

logger.info("WinPeek RPA tools registered: send + collect_msgs + collect_contacts + list_templates")

# ═══════════════════════════════════════════════════════
# MIM 工具
# ═══════════════════════════════════════════════════════
#
# 两种运行模式（由 config.yaml 的 winpeek.mim.center_url 决定）：
#
#   客户端模式（配置了 center_url）：
#     本机不连 MySQL/MQTT。所有 MIM RPC 原样转发到中心 hermes serve
#     （就近原则：主中心 192.168.3.10 / 备中心 192.168.3.44）。
#     Desktop → 本地 serve → 中心 serve，客户端只有一条对外连接。
#
#   中心模式（未配置 center_url）：
#     走本地 hub（gateway/winpeek_hub → MySQL + MQTT）。
#     仅 1-2 台消息中心服务器需要数据库与 Broker 凭据。
#
# 转发请求带 _mim_forwarded 标记：中心收到已转发的请求直接走本地 hub，
# 即使中心自己也配了 center_url 也不会二次转发（防递归）。

_MIM_CENTER_UNSET = object()
_mim_center_cached: object = _MIM_CENTER_UNSET


def _mim_center() -> "tuple[str, str] | None":
    """Return (ws_url, token) of the central MIM server, or None → local-hub mode.

    Read once per process (serve restart picks up config changes).
    URL comes from config.yaml (non-secret); token from HERMES_MIM_CENTER_TOKEN
    in ~/.hermes/.env (secret), matching the center's dashboard session token.
    """
    global _mim_center_cached
    if _mim_center_cached is not _MIM_CENTER_UNSET:
        return _mim_center_cached  # type: ignore[return-value]
    url = ""
    try:
        from hermes_cli.config import load_config
        mim = (load_config().get("winpeek", {}) or {}).get("mim", {}) or {}
        url = str(mim.get("center_url") or "").strip()
    except Exception:
        url = ""
    if not url:
        _mim_center_cached = None
        return None
    ws_url = url.replace("https://", "wss://").replace("http://", "ws://").rstrip("/") + "/api/ws"
    token = os.getenv("HERMES_MIM_CENTER_TOKEN", "").strip()
    _mim_center_cached = (ws_url, token)
    return _mim_center_cached  # type: ignore[return-value]


def _mim_center_call(method_name: str, args: dict) -> "str | None":
    """Forward one MIM RPC to the central server over a short-lived WS.

    Returns the handler-style JSON string, or None when no center is
    configured (caller falls through to the local hub) or when this request
    was already forwarded once (_mim_forwarded — the center serves it locally).
    """
    if args.get("_mim_forwarded"):
        args.pop("_mim_forwarded", None)
        return None
    center = _mim_center()
    if center is None:
        return None
    ws_url, token = center
    full_url = f"{ws_url}?token={token}" if token else ws_url
    try:
        import websocket  # websocket-client (sync)
        conn = websocket.create_connection(full_url, timeout=10)
        try:
            conn.send(json.dumps({
                "jsonrpc": "2.0",
                "id": 1,
                "method": method_name,
                "params": {**args, "_mim_forwarded": True},
            }))
            deadline = time.time() + 15
            while time.time() < deadline:
                frame = json.loads(conn.recv())
                if frame.get("id") != 1:
                    continue  # skip gateway.ready & other event frames
                err = frame.get("error")
                if err:
                    msg = err.get("message", "center error") if isinstance(err, dict) else str(err)
                    return json.dumps({"error": f"MIM center: {msg}"})
                result = frame.get("result")
                return result if isinstance(result, str) else json.dumps(result)
            return json.dumps({"error": "MIM center timeout"})
        finally:
            conn.close()
    except Exception as e:
        return json.dumps({"error": f"MIM center unreachable ({type(e).__name__}): {e}"})


def _handle_mim_login(args: dict) -> str:
    forwarded = _mim_center_call("winpeek_mim_login", args)
    if forwarded is not None:
        return forwarded
    nickname = args.get("nickname", "").strip()
    role = args.get("role", "Developer")
    password = args.get("password", "123321")  # default password
    if not nickname:
        return json.dumps({"error": "nickname required"})
    try:
        from gateway.winpeek_hub import identity, hub
        from gateway.winpeek_hub.chat import set_active_session
    except ImportError as e:
        return json.dumps({"error": f"MIM Hub not loaded: {e}"})
    result = identity.login(nickname, password) or identity.register(nickname, role, password=password)
    if not result:
        return json.dumps({"error": f"login failed — wrong nickname or password"})
    set_active_session(result["uid"], result["nickname"])
    # Register + heartbeat so this user appears online in contacts
    hub.register_node(result["uid"], result["nickname"], result.get("role", role))
    hub.heartbeat(result["uid"])
    # Auto-register machine in org tree (lightweight — hostname only, no full scan)
    try:
        from gateway.winpeek_hub.organization import upsert_machine
        import socket
        hostname = socket.gethostname()
        upsert_machine(hostname, device_type="pc", winpeek_uid=result["uid"])
    except Exception:
        pass
    return json.dumps({"ok": True, "identity": result})


def _handle_mim_send(args: dict) -> str:
    forwarded = _mim_center_call("winpeek_mim_send", args)
    if forwarded is not None:
        return forwarded
    body = args.get("body", "")
    to_uid = int(args.get("to_uid") or 0)
    gid = int(args.get("gid") or 0)
    if not body:
        return json.dumps({"error": "body required"})
    if not to_uid and not gid:
        return json.dumps({"error": "to_uid or gid required"})
    try:
        from gateway.winpeek_hub.chat import send_message, active_uid, active_name
    except ImportError:
        return json.dumps({"error": "MIM Hub not loaded"})
    uid = int(args.get("uid") or 0) or active_uid()
    if not uid:
        return json.dumps({"error": "not logged in — call winpeek_mim_login first"})
    from_name = args.get("from_name") or (active_name() if uid == active_uid() else "") or f"user_{uid}"
    return json.dumps(send_message(uid, from_name, body, to_uid=to_uid, gid=gid))


def _handle_mim_poll(args: dict) -> str:
    forwarded = _mim_center_call("winpeek_mim_poll", args)
    if forwarded is not None:
        return forwarded
    try:
        from gateway.winpeek_hub.chat import poll_messages, active_uid
    except ImportError:
        return json.dumps({"error": "MIM Hub not loaded"})
    uid = int(args.get("uid") or 0) or active_uid()
    if not uid:
        return json.dumps({"messages": []})
    return json.dumps({"messages": poll_messages(uid)})


def _handle_mim_contacts(args: dict) -> str:
    forwarded = _mim_center_call("winpeek_mim_contacts", args)
    if forwarded is not None:
        return forwarded
    try:
        from gateway.winpeek_hub.chat import get_contacts, active_uid
    except ImportError:
        return json.dumps({"error": "MIM Hub not loaded"})
    uid = int(args.get("uid") or 0) or active_uid()
    return json.dumps(get_contacts(uid))


registry.register(
    name="winpeek_mim_login",
    toolset="winpeek_rpa",
    schema={
        "name": "winpeek_mim_login",
        "description": "Register or login to MIM messaging. Password defaults to 123321.",
        "parameters": {
            "type": "object",
            "properties": {
                "nickname": {"type": "string", "description": "Your display name"},
                "password": {"type": "string", "description": "Login password (default 123321)"},
                "role": {"type": "string", "description": "Developer/Architect/Ops/QA/PM"},
            },
            "required": ["nickname"],
        },
    },
    handler=lambda args, **kw: _handle_mim_login(args),
    check_fn=lambda: True,
    requires_env=[],
    description="MIM identity register/login",
)

registry.register(
    name="winpeek_mim_send",
    toolset="winpeek_rpa",
    schema={
        "name": "winpeek_mim_send",
        "description": "Send a message to another agent or group via MQTT.",
        "parameters": {
            "type": "object",
            "properties": {
                "to_uid": {"type": "integer", "description": "Recipient uid (single chat)"},
                "gid": {"type": "integer", "description": "Group id (group chat)"},
                "body": {"type": "string", "description": "Message text"},
            },
            "required": ["body"],
        },
    },
    handler=lambda args, **kw: _handle_mim_send(args),
    check_fn=lambda: True,
    requires_env=[],
    description="MIM send message via MQTT",
)

registry.register(
    name="winpeek_mim_poll",
    toolset="winpeek_rpa",
    schema={
        "name": "winpeek_mim_poll",
        "description": "Check for new incoming MIM messages. Returns messages sent to the calling agent (uid from env MIM_UID). Call every 3 seconds.",
        "parameters": {"type": "object", "properties": {}},
    },
    handler=lambda args, **kw: _handle_mim_poll(args),
    check_fn=lambda: True,
    requires_env=[],
    description="MIM poll incoming messages",
)

registry.register(
    name="winpeek_mim_contacts",
    toolset="winpeek_rpa",
    schema={
        "name": "winpeek_mim_contacts",
        "description": "List all registered agent identities.",
        "parameters": {"type": "object", "properties": {}},
    },
    handler=lambda args, **kw: _handle_mim_contacts(args),
    check_fn=lambda: True,
    requires_env=[],
    description="MIM contact list",
)

logger.info("WinPeek MIM tools registered: login + send + poll + contacts")

# ── MIM: Online status ──

def _handle_mim_online(args: dict) -> str:
    forwarded = _mim_center_call("winpeek_mim_online", args)
    if forwarded is not None:
        return forwarded
    try:
        from gateway.winpeek_hub import hub
        from gateway.winpeek_hub.mqtt_adapter import UID, NAME
    except ImportError:
        return json.dumps({"error": "MIM Hub not loaded"})
    hub.register_node(UID, NAME)
    hub.heartbeat(UID)
    hub.sweep_dead_nodes()
    return json.dumps({"nodes": hub.list_nodes()})

registry.register(
    name="winpeek_mim_online",
    toolset="winpeek_rpa",
    schema={
        "name": "winpeek_mim_online",
        "description": "Register heartbeat and get online status of all nodes. Call every 30 seconds.",
        "parameters": {"type": "object", "properties": {}},
    },
    handler=lambda args, **kw: _handle_mim_online(args),
    check_fn=lambda: True,
    requires_env=[],
    description="MIM heartbeat + online status list",
)

logger.info("WinPeek MIM online tool registered")

# ── MIM: Message History ──

def _handle_mim_history(args: dict) -> str:
    forwarded = _mim_center_call("winpeek_mim_history", args)
    if forwarded is not None:
        return forwarded
    peer_uid = int(args.get("peer_uid", 0))
    gid = int(args.get("gid", 0))
    limit = int(args.get("limit", 50))
    if not peer_uid and not gid:
        return json.dumps({"error": "peer_uid or gid required"})
    try:
        from gateway.winpeek_hub.chat import get_history, active_uid
    except ImportError:
        return json.dumps({"error": "MIM Hub not loaded"})
    uid = int(args.get("uid") or 0) or active_uid()
    if not uid:
        return json.dumps({"error": "not logged in — call winpeek_mim_login first"})
    return json.dumps({"messages": get_history(uid, peer_uid, gid=gid, limit=limit)})

registry.register(
    name="winpeek_mim_history",
    toolset="winpeek_rpa",
    schema={
        "name": "winpeek_mim_history",
        "description": "Get conversation history with a peer or group.",
        "parameters": {
            "type": "object",
            "properties": {
                "peer_uid": {"type": "integer", "description": "The peer agent's uid (single chat)"},
                "gid": {"type": "integer", "description": "Group id (group chat)"},
                "limit": {"type": "integer", "description": "Max messages (default 50)"},
                "uid": {"type": "integer", "description": "Own uid (optional; defaults to active session)"},
            },
            "required": [],
        },
    },
    handler=lambda args, **kw: _handle_mim_history(args),
    check_fn=lambda: True,
    requires_env=[],
    description="MIM conversation history",
)

logger.info("WinPeek MIM tools: +online +history")

# ── MIM: User Info ──


def _handle_mim_user_info(args: dict) -> str:
    forwarded = _mim_center_call("winpeek_mim_user_info", args)
    if forwarded is not None:
        return forwarded
    uid = int(args.get("uid", 0))
    if not uid:
        return json.dumps({"error": "uid required"})
    try:
        from gateway.winpeek_hub import identity
    except ImportError:
        return json.dumps({"error": "MIM Hub not loaded"})
    user = identity.get_by_uid(uid)
    if not user:
        return json.dumps({"error": "user not found"})
    return json.dumps({"user": user})


registry.register(
    name="winpeek_mim_user_info",
    toolset="winpeek_rpa",
    schema={
        "name": "winpeek_mim_user_info",
        "description": "Get detailed profile info for a user by uid.",
        "parameters": {
            "type": "object",
            "properties": {
                "uid": {"type": "integer", "description": "User uid to query"},
            },
            "required": ["uid"],
        },
    },
    handler=lambda args, **kw: _handle_mim_user_info(args),
    check_fn=lambda: True,
    requires_env=[],
    description="MIM user profile info",
)

logger.info("WinPeek MIM tools: +user_info")

# ── Portrait: 画像分析工具 ──────────────────────────

def _portrait_calc_metrics(chats, friend):
    """从聊天记录计算5维评分"""
    total = len(chats)
    if total == 0:
        return {"familiarity": 10, "trust": 30, "curiosity": 10, "initiative": 20, "risk": 5}

    from_me = sum(1 for m in chats if m.get("is_from_me"))
    from_other = total - from_me
    long_msgs = sum(1 for m in chats if m.get("content") and len(str(m.get("content", ""))) > 50)
    long_ratio = long_msgs / max(total, 1)

    msg_dates = set()
    for m in chats:
        ts = m.get("msg_ts")
        if ts:
            msg_dates.add(str(ts)[:10] if isinstance(ts, str) else ts.strftime("%Y-%m-%d"))
    active_days = max(len(msg_dates), 1)

    from datetime import datetime
    first_met = friend.get("first_met")
    days_known = 365
    if first_met:
        try:
            days_known = max((datetime.now() - datetime.strptime(str(first_met)[:10], "%Y-%m-%d")).days, 30)
        except Exception:
            pass

    familiarity = min(100, int(min(active_days / max(days_known, 30), 1) * 50 + min(total / 50, 1) * 30 + (20 if active_days > 3 else 0)))
    trust = min(100, int((from_other / max(total, 1)) * 60 + long_ratio * 40))
    curiosity = min(100, int(long_ratio * 70 + 20))
    initiative = min(100, int((from_me / max(total, 1)) * 80 + 10))

    st = friend.get("source_type") or ""
    risk_map = {"card_share": 25, "phone_search": 20, "group_chat": 30, "wxid_search": 35, "qr_scan": 40}
    risk = risk_map.get(st, 15)

    return {"familiarity": familiarity, "trust": trust, "curiosity": curiosity, "initiative": initiative, "risk": risk}


def _portrait_calc_stage(friend):
    from datetime import datetime
    first_met = friend.get("first_met")
    if not first_met:
        return "初识", 0
    try:
        days = (datetime.now() - datetime.strptime(str(first_met)[:10], "%Y-%m-%d")).days
    except Exception:
        return "初识", 0
    if days <= 7:       return "初识", 0
    elif days <= 30:    return "熟悉", 1
    elif days <= 90:    return "稳定", 2
    else:               return "长期", 3


def _handle_wechat_accounts(args: dict) -> str:
    """列出数据库中可用的微信账户（采集过的wxid）"""
    import pymysql, os
    try:
        conn = pymysql.connect(
            host=os.environ.get("DB_HOST", "192.168.3.23"),
            user=os.environ.get("DB_USER", "winpeek"),
            password=os.environ.get("DB_PASS", "Server33"),
            database=os.environ.get("DB_NAME", "winpeek-db2"),
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor)
    except Exception as e:
        return json.dumps({"error": f"MySQL: {e}"})

    try:
        cur = conn.cursor()
        # 找 self 账号：from_uid 频率最高且跨越多个 to_uid
        cur.execute("""
        SELECT from_uid as wxid, COUNT(DISTINCT to_uid) as contacts, COUNT(*) as msgs
        FROM wechat_chat WHERE gid IS NULL AND is_date_sep=0 AND from_uid IS NOT NULL AND to_uid IS NOT NULL
        GROUP BY from_uid HAVING contacts >= 2 ORDER BY msgs DESC LIMIT 10
        """)
        accounts = []
        for row in cur.fetchall():
            wxid = row["wxid"]
            # 尝试在 wechat_friend 中找
            cur2 = conn.cursor()
            cur2.execute("SELECT nickname, avatar_url FROM wechat_friend WHERE nickname=%s OR alias=%s LIMIT 1", (wxid, wxid))
            f = cur2.fetchone()
            accounts.append({
                "wxid": wxid,
                "nickname": f["nickname"] if f else wxid,
                "avatar": f.get("avatar_url", "") if f else "",
                "contacts": row["contacts"],
                "messages": row["msgs"],
            })
        return json.dumps({"ok": True, "accounts": accounts})
    except Exception as e:
        return json.dumps({"error": str(e)})
    finally:
        conn.close()


def _handle_portrait_list(args: dict) -> str:
    """返回画像列表（排序：谁该联系）"""
    import pymysql
    import os
    limit = int(args.get("limit", 50))
    mode = args.get("mode", "contact")  # contact | cooling | all
    wxid = args.get("wxid", "").strip()  # 指定微信账户

    try:
        conn = pymysql.connect(
            host=os.environ.get("DB_HOST", "192.168.3.23"),
            user=os.environ.get("DB_USER", "winpeek"),
            password=os.environ.get("DB_PASS", "Server33"),
            database=os.environ.get("DB_NAME", "winpeek-db2"),
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor)
    except Exception as e:
        return json.dumps({"error": f"MySQL连接失败: {e}"})

    try:
        cur = conn.cursor()
        # 获取有聊天记录的好友（可选 wxid 过滤）
        wxid_filter = ""
        wxid_params = []
        if wxid:
            wxid_filter = """
              AND (f.nickname IN (SELECT DISTINCT to_uid FROM wechat_chat WHERE gid IS NULL AND is_date_sep=0 AND from_uid=%s)
                OR f.nickname IN (SELECT DISTINCT from_uid FROM wechat_chat WHERE gid IS NULL AND is_date_sep=0 AND to_uid=%s)
                OR f.alias IN (SELECT DISTINCT to_uid FROM wechat_chat WHERE gid IS NULL AND is_date_sep=0 AND from_uid=%s)
                OR f.alias IN (SELECT DISTINCT from_uid FROM wechat_chat WHERE gid IS NULL AND is_date_sep=0 AND to_uid=%s))
            """
            wxid_params = [wxid, wxid, wxid, wxid]

        cur.execute(f"""
        SELECT f.id, f.wxid, f.nickname, f.alias, f.region, f.source, f.source_type,
               f.tags, f.avatar_url, f.first_met, f.signature
        FROM wechat_friend f
        WHERE f.is_friend = 1 AND f.nickname IS NOT NULL
          AND (f.nickname IN (SELECT DISTINCT from_uid FROM wechat_chat WHERE gid IS NULL AND is_date_sep=0 AND from_uid IS NOT NULL)
            OR f.nickname IN (SELECT DISTINCT to_uid FROM wechat_chat WHERE gid IS NULL AND is_date_sep=0 AND to_uid IS NOT NULL)
            OR f.alias IN (SELECT DISTINCT from_uid FROM wechat_chat WHERE gid IS NULL AND is_date_sep=0 AND from_uid IS NOT NULL)
            OR f.alias IN (SELECT DISTINCT to_uid FROM wechat_chat WHERE gid IS NULL AND is_date_sep=0 AND to_uid IS NOT NULL))
          {wxid_filter}
        ORDER BY f.id
        """, wxid_params)
        friends = cur.fetchall()

        results = []
        for f in friends:
            # 获取聊天记录
            nickname = f["nickname"] or ""
            alias = f["alias"] or ""
            params = []
            conds = []
            for name in (nickname, alias):
                if name:
                    conds.append("(from_uid = %s OR to_uid = %s)")
                    params.extend([name, name])
            if conds:
                cur.execute(
                    f"SELECT id, content, is_from_me, msg_type, msg_ts FROM wechat_chat "
                    f"WHERE ({' OR '.join(conds)}) AND gid IS NULL AND is_date_sep = 0 ORDER BY msg_ts ASC",
                    params)
                chats = cur.fetchall()
            else:
                chats = []

            if not chats:
                continue

            metrics = _portrait_calc_metrics(chats, f)
            stage, stage_idx = _portrait_calc_stage(f)

            # 标签
            source_tag_map = {"card_share": "名片分享", "phone_search": "手机号", "wxid_search": "微信号",
                              "group_chat": "群聊", "qr_scan": "扫一扫"}
            tags = []
            if f.get("tags"):
                tags.extend([t.strip() for t in str(f["tags"]).split(",") if t.strip()][:2])
            st = f.get("source_type") or ""
            tag = source_tag_map.get(st)
            if tag and tag not in tags:
                tags.insert(0, tag)

            # 最后消息时间
            last_ts = chats[-1].get("msg_ts") if chats else None
            last_time = ""
            days_since = 999
            if last_ts:
                from datetime import datetime
                last_str = str(last_ts)[:19] if last_ts else ""
                try:
                    last_dt = datetime.strptime(last_str, "%Y-%m-%d %H:%M:%S")
                    days_since = (datetime.now() - last_dt).days
                    last_time = last_dt.strftime("%m-%d %H:%M")
                except Exception:
                    pass

            # 优先度 = 亲密度 + 是否为商业用户
            priority = metrics["familiarity"] * 0.5 + metrics["trust"] * 0.2 - max(0, days_since - 30) * 0.3

            category = "normal"
            if days_since > 30 and metrics["familiarity"] > 40:
                category = "need_contact"
            if metrics.get("risk", 0) > 30 and days_since > 14:
                category = "biz_follow"

            results.append({
                "id": str(f["id"]),
                "wxid": f["wxid"],
                "name": f["nickname"],
                "alias": f.get("alias") or "",
                "title": f.get("signature") or f.get("alias") or "",
                "region": f.get("region") or "",
                "stage": stage,
                "stage_idx": stage_idx,
                "tags": tags,
                "avatar": f.get("avatar_url") or "",
                "metrics": metrics,
                "events_count": len(chats),
                "last_time": last_time,
                "days_since": days_since,
                "priority": round(priority, 1),
                "category": category,
                "source_type": st,
            })

        # 排序
        if mode == "cooling":
            results.sort(key=lambda r: (-r["days_since"], -r["metrics"]["familiarity"]))
        else:
            results.sort(key=lambda r: (-r["priority"]))

        return json.dumps({"ok": True, "count": len(results), "items": results[:limit]})
    except Exception as e:
        return json.dumps({"error": str(e)})
    finally:
        conn.close()


def _handle_portrait_detail(args: dict) -> str:
    """返回单个好友的画像详情"""
    import pymysql
    import os
    friend_id = args.get("friend_id") or args.get("wxid")
    if not friend_id:
        return json.dumps({"error": "friend_id or wxid required"})

    try:
        conn = pymysql.connect(
            host=os.environ.get("DB_HOST", "192.168.3.23"),
            user=os.environ.get("DB_USER", "winpeek"),
            password=os.environ.get("DB_PASS", "Server33"),
            database=os.environ.get("DB_NAME", "winpeek-db2"),
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor)
    except Exception as e:
        return json.dumps({"error": f"MySQL连接失败: {e}"})

    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM wechat_friend WHERE id = %s OR wxid = %s LIMIT 1",
            (friend_id, str(friend_id)))
        f = cur.fetchone()
        if not f:
            return json.dumps({"error": "friend not found"})

        nickname = f["nickname"] or ""
        alias = f["alias"] or ""
        params = []
        conds = []
        for name in (nickname, alias):
            if name:
                conds.append("(from_uid = %s OR to_uid = %s)")
                params.extend([name, name])
        if conds:
            cur.execute(
                f"SELECT id, content, is_from_me, msg_type, msg_ts FROM wechat_chat "
                f"WHERE ({' OR '.join(conds)}) AND gid IS NULL AND is_date_sep = 0 ORDER BY msg_ts ASC",
                params)
            chats = cur.fetchall()
        else:
            chats = []

        metrics = _portrait_calc_metrics(chats, f)
        stage, stage_idx = _portrait_calc_stage(f)

        # 事件聚合
        events = []
        batch_size = max(1, len(chats) // min(8, max(1, len(chats))))
        batch_size = min(batch_size, 100)
        for i in range(0, len(chats), batch_size):
            batch = chats[i:i+batch_size]
            if not batch:
                continue
            ts = batch[0].get("msg_ts")
            date_str = str(ts)[:10] if ts else "时间待补"
            samples = [m for m in batch if m.get("content") and len(str(m.get("content", ""))) > 5][:3]
            sample_text = "；".join(str(m.get("content", ""))[:40] for m in samples)
            detail_lines = [f"[{'我' if m.get('is_from_me') else 'TA'}] {str(m.get('content', ''))[:120]}" for m in batch[:12]]
            events.append({
                "date": date_str,
                "title": f"对话记录 #{i//batch_size + 1}",
                "summary": sample_text[:80] or f"共{len(batch)}条消息",
                "detail": "\n".join(detail_lines),
                "stage": min(stage_idx, 3),
            })

        return json.dumps({
            "ok": True,
            "profile": {
                "id": str(f["id"]),
                "wxid": f["wxid"],
                "name": f["nickname"],
                "alias": f.get("alias") or "",
                "region": f.get("region") or "",
                "source": f.get("source") or "",
                "source_type": f.get("source_type") or "",
                "signature": f.get("signature") or "",
                "avatar": f.get("avatar_url") or "",
                "first_met": str(f.get("first_met", ""))[:10] if f.get("first_met") else "",
                "stage": stage,
                "stage_idx": stage_idx,
                "metrics": metrics,
                "events": events[:15],
                "events_count": len(chats),
            }
        })
    except Exception as e:
        return json.dumps({"error": str(e)})
    finally:
        conn.close()


# ── 注册 ──

registry.register(
    name="winpeek_wechat_accounts",
    toolset="winpeek_rpa",
    schema={
        "name": "winpeek_wechat_accounts",
        "description": "列出数据库中已采集的微信账户",
        "parameters": {"type": "object", "properties": {}},
    },
    handler=lambda args, **kw: _handle_wechat_accounts(args),
    check_fn=lambda: True,
    requires_env=[],
    description="列出可用微信账户",
)

registry.register(
    name="winpeek_portrait_list",
    toolset="winpeek_rpa",
    schema={
        "name": "winpeek_portrait_list",
        "description": "获取微信好友画像列表（按沟通优先级排序）。mode: contact(谁该联系) / cooling(降温预警) / all(全部)",
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "返回数量，默认50"},
                "mode": {"type": "string", "description": "排序模式: contact/cooling/all"},
            },
        },
    },
    handler=lambda args, **kw: _handle_portrait_list(args),
    check_fn=lambda: True,
    requires_env=[],
    description="微信好友画像列表",
)

registry.register(
    name="winpeek_portrait_detail",
    toolset="winpeek_rpa",
    schema={
        "name": "winpeek_portrait_detail",
        "description": "获取单个微信好友的完整画像（含5维评分+事件时间线）",
        "parameters": {
            "type": "object",
            "properties": {
                "friend_id": {"type": "string", "description": "好友id或wxid"},
            },
            "required": ["friend_id"],
        },
    },
    handler=lambda args, **kw: _handle_portrait_detail(args),
    check_fn=lambda: True,
    requires_env=[],
    description="微信好友完整画像",
)

logger.info("WinPeek Portrait tools registered: list + detail")
# ── MIM: Group Chat ──


def _handle_mim_group_create(args: dict) -> str:
    forwarded = _mim_center_call("winpeek_mim_group_create", args)
    if forwarded is not None:
        return forwarded
    title = (args.get("title") or "").strip()
    member_uids = args.get("member_uids") or []
    description = args.get("description", "")
    if not title or not member_uids:
        return json.dumps({"error": "title and member_uids required"})
    try:
        from gateway.winpeek_hub.chat import active_uid
        from gateway.winpeek_hub.group import create_group
    except ImportError:
        return json.dumps({"error": "MIM Hub not loaded"})
    uid = int(args.get("uid") or 0) or active_uid()
    if not uid:
        return json.dumps({"error": "not logged in"})
    member_uids = [int(m) for m in member_uids]
    return json.dumps(create_group(uid, title, member_uids, description))


def _handle_mim_group_list(args: dict) -> str:
    forwarded = _mim_center_call("winpeek_mim_group_list", args)
    if forwarded is not None:
        return forwarded
    try:
        from gateway.winpeek_hub.chat import active_uid
        from gateway.winpeek_hub.group import get_my_groups
    except ImportError:
        return json.dumps({"error": "MIM Hub not loaded"})
    uid = int(args.get("uid") or 0) or active_uid()
    if not uid:
        return json.dumps({"groups": []})
    return json.dumps({"groups": get_my_groups(uid)})


def _handle_mim_group_info(args: dict) -> str:
    forwarded = _mim_center_call("winpeek_mim_group_info", args)
    if forwarded is not None:
        return forwarded
    gid = int(args.get("gid", 0))
    if not gid:
        return json.dumps({"error": "gid required"})
    try:
        from gateway.winpeek_hub.chat import active_uid
        from gateway.winpeek_hub.group import get_group_info
    except ImportError:
        return json.dumps({"error": "MIM Hub not loaded"})
    uid = int(args.get("uid") or 0) or active_uid()
    info = get_group_info(gid, requester_uid=uid)
    if not info:
        return json.dumps({"error": "group not found"})
    return json.dumps({"group": info})


def _handle_mim_group_invite(args: dict) -> str:
    forwarded = _mim_center_call("winpeek_mim_group_invite", args)
    if forwarded is not None:
        return forwarded
    gid = int(args.get("gid", 0))
    uids = args.get("uids") or []
    if not gid or not uids:
        return json.dumps({"error": "gid and uids required"})
    try:
        from gateway.winpeek_hub.chat import active_uid
        from gateway.winpeek_hub.group import invite_members
    except ImportError:
        return json.dumps({"error": "MIM Hub not loaded"})
    uid = int(args.get("uid") or 0) or active_uid()
    uids = [int(u) for u in uids]
    return json.dumps(invite_members(gid, uids, requester_uid=uid))


# ── Register group RPCs ──

registry.register(
    name="winpeek_mim_group_create",
    toolset="winpeek_rpa",
    schema={
        "name": "winpeek_mim_group_create",
        "description": "Create a new group chat with initial members.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Group name"},
                "member_uids": {"type": "array", "items": {"type": "integer"},
                                "description": "Initial member uids"},
                "description": {"type": "string", "description": "Group description"},
            },
            "required": ["title", "member_uids"],
        },
    },
    handler=lambda args, **kw: _handle_mim_group_create(args),
    check_fn=lambda: True,
    requires_env=[],
    description="MIM create group",
)

registry.register(
    name="winpeek_mim_group_list",
    toolset="winpeek_rpa",
    schema={
        "name": "winpeek_mim_group_list",
        "description": "List groups the current user belongs to.",
        "parameters": {"type": "object", "properties": {}},
    },
    handler=lambda args, **kw: _handle_mim_group_list(args),
    check_fn=lambda: True,
    requires_env=[],
    description="MIM my group list",
)

registry.register(
    name="winpeek_mim_group_info",
    toolset="winpeek_rpa",
    schema={
        "name": "winpeek_mim_group_info",
        "description": "Get group detail including member list.",
        "parameters": {
            "type": "object",
            "properties": {
                "gid": {"type": "integer", "description": "Group id"},
            },
            "required": ["gid"],
        },
    },
    handler=lambda args, **kw: _handle_mim_group_info(args),
    check_fn=lambda: True,
    requires_env=[],
    description="MIM group info",
)

registry.register(
    name="winpeek_mim_group_invite",
    toolset="winpeek_rpa",
    schema={
        "name": "winpeek_mim_group_invite",
        "description": "Invite members to a group.",
        "parameters": {
            "type": "object",
            "properties": {
                "gid": {"type": "integer", "description": "Group id"},
                "uids": {"type": "array", "items": {"type": "integer"},
                         "description": "Member uids to add"},
            },
            "required": ["gid", "uids"],
        },
    },
    handler=lambda args, **kw: _handle_mim_group_invite(args),
    check_fn=lambda: True,
    requires_env=[],
    description="MIM group invite",
)

logger.info("WinPeek MIM tools: +group (create/list/info/invite)")

# ── MIM: Group Settings ──


def _handle_mim_group_update(args: dict) -> str:
    forwarded = _mim_center_call("winpeek_mim_group_update", args)
    if forwarded is not None:
        return forwarded
    gid = int(args.get("gid", 0))
    if not gid:
        return json.dumps({"error": "gid required"})
    try:
        from gateway.winpeek_hub.chat import active_uid
        from gateway.winpeek_hub.group import update_group
    except ImportError:
        return json.dumps({"error": "MIM Hub not loaded"})
    uid = int(args.get("uid") or 0) or active_uid()
    if not uid:
        return json.dumps({"error": "not logged in"})
    return json.dumps(update_group(
        gid, uid,
        title=args.get("title", ""),
        description=args.get("description", ""),
        announcement=args.get("announcement", ""),
    ))


def _handle_mim_group_transfer(args: dict) -> str:
    forwarded = _mim_center_call("winpeek_mim_group_transfer", args)
    if forwarded is not None:
        return forwarded
    gid = int(args.get("gid", 0))
    new_owner_uid = int(args.get("new_owner_uid", 0))
    if not gid or not new_owner_uid:
        return json.dumps({"error": "gid and new_owner_uid required"})
    try:
        from gateway.winpeek_hub.chat import active_uid
        from gateway.winpeek_hub.group import transfer_ownership
    except ImportError:
        return json.dumps({"error": "MIM Hub not loaded"})
    uid = int(args.get("uid") or 0) or active_uid()
    if not uid:
        return json.dumps({"error": "not logged in"})
    return json.dumps(transfer_ownership(gid, new_owner_uid, uid))


registry.register(
    name="winpeek_mim_group_update",
    toolset="winpeek_rpa",
    schema={
        "name": "winpeek_mim_group_update",
        "description": "Update group name, description, or announcement.",
        "parameters": {
            "type": "object",
            "properties": {
                "gid": {"type": "integer", "description": "Group id"},
                "title": {"type": "string", "description": "New group name"},
                "description": {"type": "string", "description": "New description"},
                "announcement": {"type": "string", "description": "Group announcement (@all notification)"},
            },
            "required": ["gid"],
        },
    },
    handler=lambda args, **kw: _handle_mim_group_update(args),
    check_fn=lambda: True,
    requires_env=[],
    description="MIM group update",
)

registry.register(
    name="winpeek_mim_group_transfer",
    toolset="winpeek_rpa",
    schema={
        "name": "winpeek_mim_group_transfer",
        "description": "Transfer group ownership to another member.",
        "parameters": {
            "type": "object",
            "properties": {
                "gid": {"type": "integer", "description": "Group id"},
                "new_owner_uid": {"type": "integer", "description": "New owner uid (must be a member)"},
            },
            "required": ["gid", "new_owner_uid"],
        },
    },
    handler=lambda args, **kw: _handle_mim_group_transfer(args),
    check_fn=lambda: True,
    requires_env=[],
    description="MIM group ownership transfer",
)

logger.info("WinPeek MIM tools: +group_settings (update/transfer)")

# ── MIM: Group Announcement Delete ──


def _handle_mim_announcement_delete(args: dict) -> str:
    forwarded = _mim_center_call("winpeek_mim_announcement_delete", args)
    if forwarded is not None:
        return forwarded
    gid = int(args.get("gid", 0))
    an_id = (args.get("an_id") or "").strip()
    if not gid or not an_id:
        return json.dumps({"error": "gid and an_id required"})
    try:
        from gateway.winpeek_hub.chat import active_uid
        from gateway.winpeek_hub.group import delete_announcement
    except ImportError:
        return json.dumps({"error": "MIM Hub not loaded"})
    uid = int(args.get("uid") or 0) or active_uid()
    if not uid:
        return json.dumps({"error": "not logged in"})
    return json.dumps(delete_announcement(gid, an_id, uid))


registry.register(
    name="winpeek_mim_announcement_delete",
    toolset="winpeek_rpa",
    schema={
        "name": "winpeek_mim_announcement_delete",
        "description": "Delete a group announcement by id.",
        "parameters": {
            "type": "object",
            "properties": {
                "gid": {"type": "integer", "description": "Group id"},
                "an_id": {"type": "string", "description": "Announcement id"},
            },
            "required": ["gid", "an_id"],
        },
    },
    handler=lambda args, **kw: _handle_mim_announcement_delete(args),
    check_fn=lambda: True,
    requires_env=[],
    description="MIM group announcement delete",
)

logger.info("WinPeek MIM tools: +announcement_delete")

# ── MIM: Leave Group ──


def _handle_mim_group_leave(args: dict) -> str:
    forwarded = _mim_center_call("winpeek_mim_group_leave", args)
    if forwarded is not None:
        return forwarded
    gid = int(args.get("gid", 0))
    if not gid:
        return json.dumps({"error": "gid required"})
    try:
        from gateway.winpeek_hub.chat import active_uid
        from gateway.winpeek_hub.group import leave_group
    except ImportError:
        return json.dumps({"error": "MIM Hub not loaded"})
    uid = int(args.get("uid") or 0) or active_uid()
    if not uid:
        return json.dumps({"error": "not logged in"})
    return json.dumps(leave_group(gid, uid))


registry.register(
    name="winpeek_mim_group_leave",
    toolset="winpeek_rpa",
    schema={
        "name": "winpeek_mim_group_leave",
        "description": "Leave a group. Anyone can leave freely.",
        "parameters": {
            "type": "object",
            "properties": {"gid": {"type": "integer", "description": "Group id"}},
            "required": ["gid"],
        },
    },
    handler=lambda args, **kw: _handle_mim_group_leave(args),
    check_fn=lambda: True,
    requires_env=[],
    description="MIM group leave",
)

logger.info("WinPeek MIM tools: +group_leave")

# ═══════════════════════════════════════════════════════
#  SOFTWARE & ACCOUNT MANAGEMENT
# ═══════════════════════════════════════════════════════


def _handle_software_list(args: dict) -> str:
    try:
        from gateway.winpeek_hub.software import list_softwares
        from gateway.winpeek_hub.icon_extractor import get_icon_url, ensure_cache_dir
        import base64 as _b64, os as _os
        softs = list_softwares()
        cache = ensure_cache_dir()
        for s in softs:
            png_path = None
            if s.get("icon_path"):
                png_path = cache / _os.path.basename(s["icon_path"])
            elif s.get("exe_path"):
                url = get_icon_url(s["name"])
                if url:
                    png_path = cache / url.split("/")[-1]
            if png_path and png_path.exists():
                try:
                    data = png_path.read_bytes()
                    s["icon_data"] = "data:image/png;base64," + _b64.b64encode(data).decode()
                except Exception:
                    pass
        return json.dumps({"softwares": softs})
    except ImportError:
        return json.dumps({"error": "MIM Hub not loaded"})


def _handle_software_upsert(args: dict) -> str:
    name = (args.get("name") or "").strip()
    if not name:
        return json.dumps({"error": "name required"})
    try:
        from gateway.winpeek_hub.software import upsert_software
        allow = ["install_path", "exe_path", "launch_args", "description",
                 "company", "version", "latest_version", "registry_info", "icon_path",
                 "category", "platform", "last_launched_at", "exit_normal"]
        fields = {k: args[k] for k in allow if k in args}
        return json.dumps(upsert_software(name, **fields))
    except ImportError:
        return json.dumps({"error": "MIM Hub not loaded"})


def _handle_account_list(args: dict) -> str:
    try:
        from gateway.winpeek_hub.software import list_accounts
        uid = int(args.get("uid", 0))
        software_id = int(args.get("software_id", 0))
        return json.dumps({"accounts": list_accounts(uid=uid, software_id=software_id)})
    except ImportError:
        return json.dumps({"error": "MIM Hub not loaded"})


def _handle_account_upsert(args: dict) -> str:
    try:
        from gateway.winpeek_hub.software import upsert_account
        allow = ["id", "software_id", "uid", "wxid", "nickname",
                 "auth_type", "auth_value", "priority", "meta", "is_active"]
        fields = {k: args[k] for k in allow if k in args}
        return json.dumps(upsert_account(**fields))
    except ImportError:
        return json.dumps({"error": "MIM Hub not loaded"})


def _handle_account_set_active(args: dict) -> str:
    account_id = int(args.get("account_id", 0))
    uid = int(args.get("uid", 0))
    if not account_id or not uid:
        return json.dumps({"error": "account_id and uid required"})
    try:
        from gateway.winpeek_hub.software import set_active_account
        return json.dumps(set_active_account(account_id, uid))
    except ImportError:
        return json.dumps({"error": "MIM Hub not loaded"})


def _handle_account_delete(args: dict) -> str:
    account_id = int(args.get("account_id", 0))
    if not account_id:
        return json.dumps({"error": "account_id required"})
    try:
        from gateway.winpeek_hub.software import delete_account
        return json.dumps(delete_account(account_id))
    except ImportError:
        return json.dumps({"error": "MIM Hub not loaded"})


# ── Register ──

registry.register(
    name="winpeek_software_list",
    toolset="winpeek_rpa",
    schema={
        "name": "winpeek_software_list",
        "description": "列出本机已注册的所有软件",
        "parameters": {"type": "object", "properties": {}},
    },
    handler=lambda args, **kw: _handle_software_list(args),
    check_fn=lambda: True,
    requires_env=[],
    description="WinPeek 软件清单",
)

registry.register(
    name="winpeek_software_upsert",
    toolset="winpeek_rpa",
    schema={
        "name": "winpeek_software_upsert",
        "description": "注册或更新一个软件信息（name 为唯一键）",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "软件名称"},
                "install_path": {"type": "string", "description": "安装路径"},
                "exe_path": {"type": "string", "description": "启动路径"},
                "launch_args": {"type": "string", "description": "启动参数"},
                "description": {"type": "string"},
                "company": {"type": "string"},
                "version": {"type": "string"},
                "latest_version": {"type": "string"},
                "registry_info": {"type": "string", "description": "JSON 注册表信息"},
                "category": {"type": "string"},
                "platform": {"type": "string", "description": "wechat/douyin/dingtalk/feishu/..."},
                "last_launched_at": {"type": "string"},
                "exit_normal": {"type": "integer"},
            },
            "required": ["name"],
        },
    },
    handler=lambda args, **kw: _handle_software_upsert(args),
    check_fn=lambda: True,
    requires_env=[],
    description="WinPeek 软件注册",
)

registry.register(
    name="winpeek_account_list",
    toolset="winpeek_rpa",
    schema={
        "name": "winpeek_account_list",
        "description": "列出软件账号，可按 uid 或 software_id 过滤",
        "parameters": {
            "type": "object",
            "properties": {
                "uid": {"type": "integer", "description": "Hermes 用户 uid"},
                "software_id": {"type": "integer", "description": "软件 id"},
            },
        },
    },
    handler=lambda args, **kw: _handle_account_list(args),
    check_fn=lambda: True,
    requires_env=[],
    description="WinPeek 软件账号列表",
)

registry.register(
    name="winpeek_account_upsert",
    toolset="winpeek_rpa",
    schema={
        "name": "winpeek_account_upsert",
        "description": "注册或更新一个软件账号（传 id=更新）",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {"type": "integer", "description": "账号 id（更新时传入）"},
                "software_id": {"type": "integer"},
                "uid": {"type": "integer", "description": "归属用户 uid"},
                "wxid": {"type": "string", "description": "平台账号 ID"},
                "nickname": {"type": "string", "description": "账号昵称/标签"},
                "auth_type": {"type": "string", "description": "token/cookie/apikey/qrcode"},
                "auth_value": {"type": "string", "description": "授权凭证"},
                "priority": {"type": "integer", "description": "同软件多账号优先级"},
                "meta": {"type": "object", "description": "扩展字段"},
                "is_active": {"type": "integer", "description": "当前激活=1"},
            },
            "required": [],
        },
    },
    handler=lambda args, **kw: _handle_account_upsert(args),
    check_fn=lambda: True,
    requires_env=[],
    description="WinPeek 软件账号注册",
)

registry.register(
    name="winpeek_account_set_active",
    toolset="winpeek_rpa",
    schema={
        "name": "winpeek_account_set_active",
        "description": "切换激活的软件账号（同软件其他账号自动失效）",
        "parameters": {
            "type": "object",
            "properties": {
                "account_id": {"type": "integer"},
                "uid": {"type": "integer"},
            },
            "required": ["account_id", "uid"],
        },
    },
    handler=lambda args, **kw: _handle_account_set_active(args),
    check_fn=lambda: True,
    requires_env=[],
    description="WinPeek 软件账号切换",
)

registry.register(
    name="winpeek_account_delete",
    toolset="winpeek_rpa",
    schema={
        "name": "winpeek_account_delete",
        "description": "删除一个软件账号",
        "parameters": {
            "type": "object",
            "properties": {"account_id": {"type": "integer"}},
            "required": ["account_id"],
        },
    },
    handler=lambda args, **kw: _handle_account_delete(args),
    check_fn=lambda: True,
    requires_env=[],
    description="WinPeek 删除软件账号",
)

logger.info("WinPeek software tools registered: 软件清单 + 账号管理")

# ═══════════════════════════════════════════════════════
#  SCANNER: 本地软件/硬件扫描
# ═══════════════════════════════════════════════════════


def _handle_hwinfo(args: dict) -> str:
    """返回硬件信息（CPU/内存/磁盘/GPU/OS）"""
    try:
        from gateway.winpeek_hub.scanner import get_hardware_info
        return json.dumps({"ok": True, "hardware": get_hardware_info()})
    except ImportError:
        return json.dumps({"error": "Scanner not loaded"})


def _handle_scan_sync(args: dict) -> str:
    """扫描本地软件 → 入库，返回同步报告"""
    try:
        from gateway.winpeek_hub.scanner import scan_and_sync
        return json.dumps(scan_and_sync())
    except ImportError:
        return json.dumps({"error": "Scanner not loaded"})


def _handle_software_by_category(args: dict) -> str:
    """按分类返回软件列表"""
    try:
        from gateway.winpeek_hub.software import list_softwares
        softs = list_softwares()
        by_cat: dict[str, list] = {}
        for s in softs:
            cat = s.get("category") or "其它"
            by_cat.setdefault(cat, []).append(s)
        # sort categories: 社交/商城/金融/政务 first, then alphabetically
        priority = ["社交", "商城", "金融", "政务", "编程", "办公", "图形", "磁盘", "影音", "安全"]
        ordered = {}
        for cat in priority:
            if cat in by_cat:
                ordered[cat] = by_cat.pop(cat)
        for cat in sorted(by_cat):
            ordered[cat] = by_cat[cat]
        return json.dumps({"ok": True, "categories": ordered})
    except ImportError:
        return json.dumps({"error": "MIM Hub not loaded"})


registry.register(
    name="winpeek_hwinfo",
    toolset="winpeek_rpa",
    schema={
        "name": "winpeek_hwinfo",
        "description": "获取本机硬件信息：CPU/内存/磁盘/GPU/OS",
        "parameters": {"type": "object", "properties": {}},
    },
    handler=lambda args, **kw: _handle_hwinfo(args),
    check_fn=lambda: True,
    requires_env=[],
    description="WinPeek 本机硬件信息",
)

registry.register(
    name="winpeek_scan_sync",
    toolset="winpeek_rpa",
    schema={
        "name": "winpeek_scan_sync",
        "description": "扫描本机已安装软件并同步到数据库，返回同步报告",
        "parameters": {"type": "object", "properties": {}},
    },
    handler=lambda args, **kw: _handle_scan_sync(args),
    check_fn=lambda: True,
    requires_env=[],
    description="WinPeek 软件扫描同步",
)

registry.register(
    name="winpeek_software_by_category",
    toolset="winpeek_rpa",
    schema={
        "name": "winpeek_software_by_category",
        "description": "按分类获取软件清单",
        "parameters": {"type": "object", "properties": {}},
    },
    handler=lambda args, **kw: _handle_software_by_category(args),
    check_fn=lambda: True,
    requires_env=[],
    description="WinPeek 软件分类清单",
)

logger.info("WinPeek scanner tools registered: hwinfo + scan_sync + by_category")

# ═══════════════════════════════════════════════════════
#  ORGANIZATION: squad → person → machine
# ═══════════════════════════════════════════════════════


def _handle_squad_list(args: dict) -> str:
    try:
        from gateway.winpeek_hub.organization import list_squads
        return json.dumps({"squads": list_squads()})
    except ImportError:
        return json.dumps({"error": "Not loaded"})


def _handle_squad_upsert(args: dict) -> str:
    name = (args.get("name") or "").strip()
    if not name:
        return json.dumps({"error": "name required"})
    try:
        from gateway.winpeek_hub.chat import active_uid
        from gateway.winpeek_hub.organization import upsert_squad
        uid = active_uid()
        allow = ["description", "meta", "address", "industry", "founded_at",
                 "legal_person", "contact_phone", "website", "contact_email", "managed_by_uid"]
        return json.dumps(upsert_squad(name, requester_uid=uid, **{k: args[k] for k in allow if k in args}))
    except ImportError:
        return json.dumps({"error": "Not loaded"})


def _handle_person_list(args: dict) -> str:
    try:
        from gateway.winpeek_hub.organization import list_persons
        squad_id = int(args.get("squad_id", 0))
        return json.dumps({"persons": list_persons(squad_id)})
    except ImportError:
        return json.dumps({"error": "Not loaded"})


def _handle_person_upsert(args: dict) -> str:
    name = (args.get("name") or "").strip()
    if not name:
        return json.dumps({"error": "name required"})
    try:
        from gateway.winpeek_hub.chat import active_uid
        from gateway.winpeek_hub.organization import upsert_person
        uid = active_uid()
        if not uid:
            return json.dumps({"error": "not logged in"})
        allow = ["id", "squad_id", "email", "phone", "notes", "meta"]
        return json.dumps(upsert_person(name, requester_uid=uid,
                          **{k: args[k] for k in allow if k in args}))
    except ImportError:
        return json.dumps({"error": "Not loaded"})


def _handle_machine_list(args: dict) -> str:
    try:
        from gateway.winpeek_hub.organization import list_machines
        person_id = int(args.get("person_id", 0))
        return json.dumps({"machines": list_machines(person_id)})
    except ImportError:
        return json.dumps({"error": "Not loaded"})


def _handle_machine_detail(args: dict) -> str:
    machine_id = int(args.get("machine_id", 0))
    if not machine_id:
        return json.dumps({"error": "machine_id required"})
    try:
        from gateway.winpeek_hub.chat import active_uid
        from gateway.winpeek_hub.organization import get_machine_detail
        uid = active_uid()
        if not uid:
            return json.dumps({"error": "not logged in"})
        d = get_machine_detail(machine_id, requester_uid=uid)
        return json.dumps({"machine": d} if d else {"error": "not found"})
    except ImportError:
        return json.dumps({"error": "Not loaded"})


def _handle_scan_register(args: dict) -> str:
    """全自动：注册本机 + 扫描硬件 + 同步软件，一次调用"""
    try:
        from gateway.winpeek_hub.organization import scan_and_register_machine
        from gateway.winpeek_hub.chat import active_uid
        # Use only server-side active_uid, never caller-supplied uid
        uid = active_uid()
        if not uid:
            return json.dumps({"error": "not logged in"})
        hostname = (args.get("hostname") or "").strip()
        return json.dumps(scan_and_register_machine(uid, hostname))
    except ImportError:
        return json.dumps({"error": "Not loaded"})


def _handle_org_tree(args: dict) -> str:
    """完整组织树：squads → persons → machines → software 数"""
    try:
        from gateway.winpeek_hub.organization import get_org_tree
        return json.dumps(get_org_tree())
    except ImportError:
        return json.dumps({"error": "Not loaded"})


# ── Register ──

for rpc_name, desc, params, handler in [
    ("winpeek_squad_list", "列出所有 squad", {}, _handle_squad_list),
    ("winpeek_squad_upsert", "创建/更新 squad", {"name": {"type": "string"}, "description": {"type": "string"}}, _handle_squad_upsert),
    ("winpeek_person_list", "列出人员（可按 squad_id 过滤）", {"squad_id": {"type": "integer", "default": 0}}, _handle_person_list),
    ("winpeek_person_upsert", "创建/更新人员", {"id": {"type": "integer"}, "name": {"type": "string"}, "squad_id": {"type": "integer"}, "email": {"type": "string"}, "phone": {"type": "string"}}, _handle_person_upsert),
    ("winpeek_machine_list", "列出电脑（可按 person_id 过滤）", {"person_id": {"type": "integer", "default": 0}}, _handle_machine_list),
    ("winpeek_machine_detail", "电脑详情 + 软件清单", {"machine_id": {"type": "integer"}}, _handle_machine_detail),
    ("winpeek_scan_register", "一键扫描注册：硬件 + 软件全入库", {"uid": {"type": "integer"}, "hostname": {"type": "string"}}, _handle_scan_register),
    ("winpeek_org_tree", "完整组织树", {}, _handle_org_tree),
]:
    registry.register(
        name=rpc_name,
        toolset="winpeek_rpa",
        schema={"name": rpc_name, "description": desc,
                "parameters": {"type": "object", "properties": params,
                               "required": [k for k, v in params.items()
                                            if v.get("default") is None and k not in ("id",)][:5] or []}},
        handler=lambda args, h=handler, **kw: h(args),
        check_fn=lambda: True,
        requires_env=[],
        description=desc,
    )

logger.info("WinPeek org tools registered: squad + person + machine + org_tree")

# ── ORG: join squad ──


def _handle_org_status(args: dict) -> str:
    try:
        from gateway.winpeek_hub.chat import active_uid
        from gateway.winpeek_hub.organization import get_org_status
        uid = active_uid()
        if not uid: return json.dumps({"error": "not logged in"})
        return json.dumps(get_org_status(uid))
    except ImportError: return json.dumps({"error": "Not loaded"})


def _handle_join_squad(args: dict) -> str:
    squad_id = int(args.get("squad_id", 0))
    if not squad_id: return json.dumps({"error": "squad_id required"})
    try:
        from gateway.winpeek_hub.chat import active_uid
        from gateway.winpeek_hub.organization import join_squad, get_org_status
        uid = active_uid()
        if not uid: return json.dumps({"error": "not logged in"})
        status = get_org_status(uid)
        if not status.get("machine_id"):
            return json.dumps({"error": "no machine registered — restart app"})
        return json.dumps(join_squad(status["machine_id"], squad_id, uid))
    except ImportError: return json.dumps({"error": "Not loaded"})


registry.register(
    name="winpeek_org_status", toolset="winpeek_rpa",
    schema={"name": "winpeek_org_status", "description": "查询当前用户的组织归属状态，返回可选 squad 列表",
            "parameters": {"type": "object", "properties": {}}},
    handler=lambda args, **kw: _handle_org_status(args), check_fn=lambda: True, requires_env=[],
    description="WinPeek 组织归属状态",
)
registry.register(
    name="winpeek_join_squad", toolset="winpeek_rpa",
    schema={"name": "winpeek_join_squad", "description": "选择加入一个 squad（自动创建 person 关联）",
            "parameters": {"type": "object", "properties": {"squad_id": {"type": "integer"}}, "required": ["squad_id"]}},
    handler=lambda args, **kw: _handle_join_squad(args), check_fn=lambda: True, requires_env=[],
    description="WinPeek 加入组织",
)

logger.info("WinPeek org tools: +org_status +join_squad")

# ── AGENT & ACCOUNT RPCs ──


def _handle_agent_list(args: dict) -> str:
    try:
        from gateway.winpeek_hub.chat import active_uid
        from gateway.winpeek_hub.organization import list_agents
        uid = active_uid()
        return json.dumps({"agents": list_agents(
            squad_id=int(args.get("squad_id", 0)),
            machine_id=int(args.get("machine_id", 0)),
            requester_uid=uid,
        )})
    except ImportError: return json.dumps({"error": "Not loaded"})


def _handle_agent_upsert(args: dict) -> str:
    name = (args.get("name") or "").strip()
    if not name: return json.dumps({"error": "name required"})
    try:
        from gateway.winpeek_hub.chat import active_uid
        from gateway.winpeek_hub.organization import upsert_agent
        uid = active_uid()
        if not uid: return json.dumps({"error": "not logged in"})
        allow = ["id", "agent_type", "uid", "person_id", "squad_id", "machine_id", "role", "status", "config_json"]
        return json.dumps(upsert_agent(name, requester_uid=uid, **{k: args[k] for k in allow if k in args}))
    except ImportError: return json.dumps({"error": "Not loaded"})


for rpc_name, desc, params, handler in [
    ("winpeek_agent_list", "列出AI Agent", {"squad_id": {"type": "integer"}, "machine_id": {"type": "integer"}}, _handle_agent_list),
    ("winpeek_agent_upsert", "注册/更新 AI Agent", {"name": {"type": "string"}, "agent_type": {"type": "string"}, "machine_id": {"type": "integer"}}, _handle_agent_upsert),
]:
    registry.register(
        name=rpc_name, toolset="winpeek_rpa",
        schema={"name": rpc_name, "description": desc,
                "parameters": {"type": "object", "properties": params,
                               "required": [k for k, v in params.items() if v.get("default") is None and k not in ("id", "squad_id", "machine_id")]}},
        handler=lambda args, h=handler, **kw: h(args), check_fn=lambda: True, requires_env=[], description=desc,
    )

logger.info("WinPeek agent tools registered: list + upsert")

# ── APPROVAL RPCs ──


def _handle_person_approve(args: dict) -> str:
    pid = int(args.get("person_id", 0))
    action = (args.get("action") or "").strip()
    if not pid or action not in ("approved", "rejected"):
        return json.dumps({"error": "person_id and action (approved/rejected) required"})
    try:
        from gateway.winpeek_hub.chat import active_uid
        from gateway.winpeek_hub.organization import approve_person
        uid = active_uid()
        if not uid: return json.dumps({"error": "not logged in"})
        return json.dumps(approve_person(pid, action, uid))
    except ImportError: return json.dumps({"error": "Not loaded"})


def _handle_machine_approve(args: dict) -> str:
    mid = int(args.get("machine_id", 0))
    action = (args.get("action") or "").strip()
    if not mid or action not in ("approved", "rejected"):
        return json.dumps({"error": "machine_id and action (approved/rejected) required"})
    try:
        from gateway.winpeek_hub.chat import active_uid
        from gateway.winpeek_hub.organization import approve_machine
        uid = active_uid()
        if not uid: return json.dumps({"error": "not logged in"})
        return json.dumps(approve_machine(mid, action, uid))
    except ImportError: return json.dumps({"error": "Not loaded"})


def _handle_pending_list(args: dict) -> str:
    try:
        from gateway.winpeek_hub.chat import active_uid
        from gateway.winpeek_hub.organization import get_pending
        squad_id = int(args.get("squad_id", 0))
        return json.dumps(get_pending(squad_id, requester_uid=active_uid()))
    except ImportError: return json.dumps({"error": "Not loaded"})


for rpc_name, desc, params, handler in [
    ("winpeek_person_approve", "审批人员注册", {"person_id": {"type": "integer"}, "action": {"type": "string"}}, _handle_person_approve),
    ("winpeek_machine_approve", "审批设备注册", {"machine_id": {"type": "integer"}, "action": {"type": "string"}}, _handle_machine_approve),
    ("winpeek_pending_list", "待审批列表", {"squad_id": {"type": "integer"}}, _handle_pending_list),
]:
    registry.register(
        name=rpc_name, toolset="winpeek_rpa",
        schema={"name": rpc_name, "description": desc,
                "parameters": {"type": "object", "properties": params,
                               "required": [k for k in params if k not in ("squad_id",)]}},
        handler=lambda args, h=handler, **kw: h(args), check_fn=lambda: True, requires_env=[], description=desc,
    )

logger.info("WinPeek approval tools registered: person_approve + machine_approve + pending_list")

# ── REGISTRATION WIZARD ──


def _handle_squad_search(args: dict) -> str:
    q = (args.get("q") or "").strip()
    if not q: return json.dumps({"squads": []})
    try:
        from gateway.winpeek_hub.organization import search_squads
        return json.dumps({"squads": search_squads(q)})
    except ImportError: return json.dumps({"error": "Not loaded"})


def _handle_register_with_squad(args: dict) -> str:
    try:
        from gateway.winpeek_hub.chat import active_uid
        from gateway.winpeek_hub.organization import register_with_squad
        uid = active_uid()
        if not uid: return json.dumps({"error": "not logged in"})
        return json.dumps(register_with_squad(
            uid=uid,
            is_new_squad=bool(args.get("is_new_squad")),
            squad_id=int(args.get("squad_id", 0)),
            squad_name=(args.get("squad_name") or "").strip(),
            squad_desc=(args.get("squad_desc") or "").strip(),
            person_name=(args.get("person_name") or "").strip(),
            email=(args.get("email") or "").strip(),
            phone=(args.get("phone") or "").strip(),
            hostname=(args.get("hostname") or "").strip(),
            invite_code=(args.get("invite_code") or "").strip(),
            industry=(args.get("industry") or "").strip(),
            address=(args.get("address") or "").strip(),
            website=(args.get("website") or "").strip(),
            contact_email=(args.get("contact_email") or "").strip(),
            contact_phone=(args.get("contact_phone") or "").strip(),
            legal_person=(args.get("legal_person") or "").strip(),
        ))
    except ImportError: return json.dumps({"error": "Not loaded"})


registry.register(
    name="winpeek_squad_search", toolset="winpeek_rpa",
    schema={"name": "winpeek_squad_search", "description": "按名称搜索组织",
            "parameters": {"type": "object", "properties": {"q": {"type": "string"}}, "required": ["q"]}},
    handler=lambda args, **kw: _handle_squad_search(args), check_fn=lambda: True, requires_env=[],
    description="搜索组织",
)
registry.register(
    name="winpeek_register_with_squad", toolset="winpeek_rpa",
    schema={"name": "winpeek_register_with_squad",
            "description": "一键注册：创建/加入 squad → person → machine → winpeek_account",
            "parameters": {"type": "object", "properties": {
                "is_new_squad": {"type": "boolean"}, "squad_id": {"type": "integer"},
                "squad_name": {"type": "string"}, "squad_desc": {"type": "string"},
                "person_name": {"type": "string"}, "email": {"type": "string"},
                "phone": {"type": "string"}, "hostname": {"type": "string"},
                "invite_code": {"type": "string"},
            }, "required": ["is_new_squad"]}},
    handler=lambda args, **kw: _handle_register_with_squad(args), check_fn=lambda: True, requires_env=[],
    description="一键组织注册",
)

logger.info("WinPeek registration tools: search + register_with_squad")

# ── INVITE CODE ──


def _handle_get_invite_code(args: dict) -> str:
    try:
        from gateway.winpeek_hub.chat import active_uid
        from gateway.winpeek_hub.db import get_conn
        uid = active_uid()
        if not uid: return json.dumps({"error": "not logged in"})
        conn = get_conn()
        if not conn: return json.dumps({"error": "DB unavailable"})
        with conn.cursor() as cur:
            cur.execute("""
                SELECT s.invite_code, s.name, s.id
                FROM squads s
                INNER JOIN winpeek_accounts wa ON s.owner_person_id = wa.person_id
                WHERE wa.uid = %s
                ORDER BY s.id DESC LIMIT 5
            """, (uid,))
            codes = [{"squad_id": r["id"], "name": r["name"], "invite_code": r["invite_code"]}
                     for r in cur.fetchall()]
        conn.close()
        return json.dumps({"invite_codes": codes})
    except ImportError: return json.dumps({"error": "Not loaded"})


registry.register(
    name="winpeek_my_invite_codes", toolset="winpeek_rpa",
    schema={"name": "winpeek_my_invite_codes", "description": "获取我拥有的组织的邀请码",
            "parameters": {"type": "object", "properties": {}}},
    handler=lambda args, **kw: _handle_get_invite_code(args), check_fn=lambda: True, requires_env=[],
    description="我的组织邀请码",
)

logger.info("WinPeek invite_code tool registered")
