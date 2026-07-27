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
import os
import time

from typing import Any

from tools.registry import registry

logger = logging.getLogger(__name__)

_SENSITIVE_KEYS = frozenset({'password', 'old_password', 'new_password', 'token', 'secret', 'api_key', 'credential', 'passwd', 'auth_token'})

def _sanitize(args: dict) -> dict:
    """Return a copy of args with sensitive fields redacted for safe logging."""
    return {k: ('***' if k.lower() in _SENSITIVE_KEYS else v) for k, v in args.items()}


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
        logger.exception("handler failed: %s", str(e))
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
        logger.exception("handler failed: %s", str(e))
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
        logger.exception("handler failed: %s", str(e))
        return json.dumps({"error": f"MIM center unreachable ({type(e).__name__}): {e}"})


def _handle_mim_login(args: dict) -> str:
    forwarded = _mim_center_call("winpeek_mim_login", args)
    if forwarded is not None:
        return forwarded
    nickname = args.get("nickname", "").strip()
    password = args.get("password", "")
    if not nickname:
        return json.dumps({"error": "nickname required"})
    if not password:
        return json.dumps({"error": "password required"})
    try:
        from gateway.winpeek_hub import identity
        from gateway.winpeek_hub.chat import set_active_session
    except ImportError as e:
        return json.dumps({"error": f"MIM Hub not loaded: {e}"})
    result = identity.login(nickname, password)
    if not result:
        return json.dumps({"error": f"login failed — wrong nickname or password"})
    set_active_session(result["uid"], result["nickname"])
    return json.dumps({"ok": True, "identity": result})


def _handle_mim_send(args: dict) -> str:
    forwarded = _mim_center_call("winpeek_mim_send", args)
    if forwarded is not None:
        return forwarded
    body = args.get("body", "")
    to_uid = args.get("to_uid")
    if not to_uid or not body:
        return json.dumps({"error": "to_uid and body required"})
    try:
        from gateway.winpeek_hub.chat import send_message, active_uid, active_name
    except ImportError:
        return json.dumps({"error": "MIM Hub not loaded"})
    # Explicit uid (e.g. desktop frontend passes its logged-in identity) wins
    # over the process-global active session, which may belong to another user.
    uid = int(args.get("uid") or 0) or active_uid()
    if not uid:
        return json.dumps({"error": "not logged in — call winpeek_mim_login first"})
    from_name = args.get("from_name") or (active_name() if uid == active_uid() else "") or f"user_{uid}"
    return json.dumps(send_message(uid, from_name, int(to_uid), body))


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
    # Memory queue (real-time)
    queue_msgs = poll_messages(uid)
    # File inbox (persisted L3 messages)
    inbox_msgs = []
    try:
        from apps.winpeek_injector.daemon import read_inbox
        inbox_msgs = read_inbox(uid)
    except ImportError:
        pass
    return json.dumps({
        "messages": queue_msgs,
        "inbox": inbox_msgs,
        "inbox_count": len(inbox_msgs),
    })


def _handle_mim_contacts(args: dict) -> str:
    forwarded = _mim_center_call("winpeek_mim_contacts", args)
    if forwarded is not None:
        return forwarded
    try:
        from gateway.winpeek_hub.chat import get_contacts, active_uid
    except ImportError:
        return json.dumps({"error": "MIM Hub not loaded"})
    uid = int(args.get("uid") or 0) or active_uid()
    return json.dumps({"contacts": get_contacts(uid)})


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
        "description": "Send a message to another agent via MQTT. Sender identity from env MIM_UID/MIM_NAME. Recipient receives on their inbox topic.",
        "parameters": {
            "type": "object",
            "properties": {
                "to_uid": {"type": "integer", "description": "Recipient agent uid"},
                "body": {"type": "string", "description": "Message text"},
            },
            "required": ["to_uid", "body"],
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
    return json.dumps({"messages": get_history(uid, peer_uid, gid, limit)})

registry.register(
    name="winpeek_mim_history",
    toolset="winpeek_rpa",
    schema={
        "name": "winpeek_mim_history",
        "description": "Get conversation history with a peer. Returns messages in chronological order.",
        "parameters": {
            "type": "object",
            "properties": {
                "peer_uid": {"type": "integer", "description": "The peer agent's uid"},
                "limit": {"type": "integer", "description": "Max messages (default 50)"},
                "uid": {"type": "integer", "description": "Own uid (optional; defaults to active session)"},
            },
            "required": ["peer_uid"],
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


# ── MIM: Search Users ──

def _handle_mim_search_users(args: dict) -> str:
    forwarded = _mim_center_call("winpeek_mim_search_users", args)
    if forwarded is not None:
        return forwarded
    q = str(args.get("q", "") or "")
    filters_raw = args.get("filters", {}) or {}
    try:
        from gateway.winpeek_hub.chat import search_users
        results = search_users(q, filters_raw)
        return json.dumps({"users": results, "count": len(results)})
    except ImportError:
        return json.dumps({"error": "MIM Hub not loaded"})
    except Exception as e:
        logger.exception("search_users failed: %s", str(e))
        return json.dumps({"error": str(e)})


registry.register(
    name="winpeek_mim_search_users",
    toolset="winpeek_rpa",
    schema={
        "name": "winpeek_mim_search_users",
        "description": "Search MIM users by nickname, UID, role. Supports batch UID list via filters.uids='2022,2034'.",
        "parameters": {
            "type": "object",
            "properties": {
                "q": {"type": "string", "description": "Search query (nickname/UID/role)"},
                "filters": {
                    "type": "object",
                    "description": "Optional: {identity_type:'mim-agent', uids:'2022,2034'}",
                },
            },
        },
    },
    handler=lambda args, **kw: _handle_mim_search_users(args),
    check_fn=lambda: True,
    description="MIM user search",
)

logger.info("WinPeek MIM tools: +user_info +search_users")


# ── MIM: Friend Management (F1.3, F1.4) ──

def _handle_mim_add_contact(args: dict) -> str:
    forwarded = _mim_center_call("winpeek_mim_add_contact", args)
    if forwarded is not None:
        return forwarded
    from_uid = int(args.get("uid", 0))
    to_uid = int(args.get("to_uid", 0))
    if not from_uid or not to_uid:
        return json.dumps({"ok": False, "error": "uid and to_uid required"})
    try:
        from gateway.winpeek_hub.chat import add_contact
        result = add_contact(from_uid, to_uid, str(args.get("message", "")))
        return json.dumps(result)
    except ImportError:
        return json.dumps({"error": "MIM Hub not loaded"})


registry.register(
    name="winpeek_mim_add_contact",
    toolset="winpeek_rpa",
    schema={
        "name": "winpeek_mim_add_contact",
        "description": "Add a friend to contacts.",
        "parameters": {
            "type": "object",
            "properties": {
                "uid": {"type": "integer", "description": "Your uid"},
                "to_uid": {"type": "integer", "description": "Target uid to add as friend"},
                "message": {"type": "string", "description": "Optional greeting message"},
            },
            "required": ["uid", "to_uid"],
        },
    },
    handler=lambda args, **kw: _handle_mim_add_contact(args),
    description="MIM add friend",
)


def _handle_mim_remove_contact(args: dict) -> str:
    forwarded = _mim_center_call("winpeek_mim_remove_contact", args)
    if forwarded is not None:
        return forwarded
    uid = int(args.get("uid", 0))
    target_uid = int(args.get("target_uid", 0))
    if not uid or not target_uid:
        return json.dumps({"ok": False, "error": "uid and target_uid required"})
    try:
        from gateway.winpeek_hub.chat import remove_contact
        result = remove_contact(uid, target_uid)
        return json.dumps(result)
    except ImportError:
        return json.dumps({"error": "MIM Hub not loaded"})


registry.register(
    name="winpeek_mim_remove_contact",
    toolset="winpeek_rpa",
    schema={
        "name": "winpeek_mim_remove_contact",
        "description": "Remove a friend from contacts.",
        "parameters": {
            "type": "object",
            "properties": {
                "uid": {"type": "integer", "description": "Your uid"},
                "target_uid": {"type": "integer", "description": "Contact uid to remove"},
            },
            "required": ["uid", "target_uid"],
        },
    },
    handler=lambda args, **kw: _handle_mim_remove_contact(args),
    description="MIM remove friend",
)


def _handle_mim_search_history(args: dict) -> str:
    forwarded = _mim_center_call("winpeek_mim_search_history", args)
    if forwarded is not None:
        return forwarded
    uid = int(args.get("uid", 0))
    q = str(args.get("q", ""))
    peer_uid = int(args.get("peer_uid", 0))
    gid = int(args.get("gid", 0))
    if not uid or not q:
        return json.dumps({"error": "uid and q required"})
    try:
        from gateway.winpeek_hub.chat import search_history
        results = search_history(uid, q, peer_uid, gid)
        return json.dumps({"messages": results, "count": len(results)})
    except ImportError:
        return json.dumps({"error": "MIM Hub not loaded"})


registry.register(
    name="winpeek_mim_search_history",
    toolset="winpeek_rpa",
    schema={
        "name": "winpeek_mim_search_history",
        "description": "Search chat history by keyword.",
        "parameters": {
            "type": "object",
            "properties": {
                "uid": {"type": "integer", "description": "Your uid"},
                "q": {"type": "string", "description": "Search keyword"},
                "peer_uid": {"type": "integer", "description": "Optional: limit to this peer"},
                "gid": {"type": "integer", "description": "Optional: limit to this group"},
            },
            "required": ["uid", "q"],
        },
    },
    handler=lambda args, **kw: _handle_mim_search_history(args),
    description="MIM message search",
)


def _handle_mim_mark_read(args: dict) -> str:
    forwarded = _mim_center_call("winpeek_mim_mark_read", args)
    if forwarded is not None:
        return forwarded
    uid = int(args.get("uid", 0))
    peer_uid = int(args.get("peer_uid", 0))
    if not uid:
        return json.dumps({"error": "uid required"})
    try:
        from gateway.winpeek_hub.chat import mark_read
        n = mark_read(uid, peer_uid)
        return json.dumps({"ok": True, "marked": n})
    except ImportError:
        return json.dumps({"error": "MIM Hub not loaded"})


registry.register(
    name="winpeek_mim_mark_read",
    toolset="winpeek_rpa",
    schema={
        "name": "winpeek_mim_mark_read",
        "description": "Mark messages from peer as read.",
        "parameters": {
            "type": "object",
            "properties": {
                "uid": {"type": "integer", "description": "Your uid"},
                "peer_uid": {"type": "integer", "description": "Optional: mark read from this peer only"},
            },
            "required": ["uid"],
        },
    },
    handler=lambda args, **kw: _handle_mim_mark_read(args),
    description="MIM mark messages as read",
)

logger.info("WinPeek MIM tools: +add_contact +remove_contact +search_history +mark_read")

# ── MIM: User (真人) Registration ──


def _handle_mim_user_register(args: dict) -> str:
    forwarded = _mim_center_call("winpeek_mim_user_register", args)
    if forwarded is not None:
        return forwarded
    name = (args.get("name") or args.get("nickname") or "").strip()
    gender = (args.get("gender") or "").strip()
    password = args.get("password", "a@123321")
    if not name or gender not in ("male", "female"):
        return json.dumps({"error": "name and gender (male/female) required"})
    try:
        from gateway.winpeek_hub import identity
        # Check if name already exists → login
        result = identity.login(name, password)
        if not result:
            result = identity.register_user(name, gender, password)
        if not result:
            return json.dumps({"error": f"User {name} already registered — wrong password"})
        # Set active session so subsequent sends use this identity
        from gateway.winpeek_hub.chat import set_active_session
        set_active_session(result["uid"], result["nickname"])
        return json.dumps({"ok": True, "identity": result})
    except ImportError:
        return json.dumps({"error": "MIM Hub not loaded"})


# ── MIM: Device Check ──


def _handle_mim_device_check(args: dict) -> str:
    forwarded = _mim_center_call("winpeek_mim_device_check", args)
    if forwarded is not None:
        return forwarded
    hostname = (args.get("hostname") or "").strip()
    if not hostname:
        return json.dumps({"error": "hostname required"})
    try:
        from gateway.winpeek_hub import identity
        device = identity.check_device(hostname)
        return json.dumps({"device": device})
    except ImportError:
        return json.dumps({"error": "MIM Hub not loaded"})


# ── MIM: Device Register ──


def _handle_mim_device_register(args: dict) -> str:
    forwarded = _mim_center_call("winpeek_mim_device_register", args)
    if forwarded is not None:
        return forwarded
    hostname = (args.get("hostname") or "").strip()
    owner_uid = int(args.get("owner_uid", 0))
    if not hostname or not owner_uid:
        return json.dumps({"error": "hostname and owner_uid required"})
    try:
        from gateway.winpeek_hub import identity
        import platform
        # Gather basic device info
        os_name = platform.system()
        os_version = platform.version()
        cpu_model = platform.processor() or ""
        device = identity.check_device(hostname)
        if device:
            return json.dumps({"ok": True, "device": device, "already_registered": True})
        result = identity.register_device(
            hostname, owner_uid,
            os_name=os_name, os_version=os_version,
            cpu_model=cpu_model, device_type="pc",
        )
        if not result:
            return json.dumps({"error": f"Device {hostname} already registered"})
        return json.dumps({"ok": True, "device": result})
    except ImportError:
        return json.dumps({"error": "MIM Hub not loaded"})


# ── MIM: My Device (auto-detect hostname) ──


def _handle_mim_my_device(args: dict) -> str:
    forwarded = _mim_center_call("winpeek_mim_my_device", args)
    if forwarded is not None:
        return forwarded
    try:
        import socket
        hostname = socket.gethostname()
        from gateway.winpeek_hub import identity
        device = identity.check_device(hostname)
        # Also check for mim-user identities on this machine
        users = identity.list_all()
        human_users = [{"uid": u["uid"], "nickname": u["nickname"],
                         "gender": u.get("gender"), "role": u["role"]}
                        for u in users if u.get("identity_type") == "mim-user"]
        return json.dumps({
            "hostname": hostname,
            "device": device,
            "humanUsers": human_users,
        })
    except ImportError:
        return json.dumps({"error": "MIM Hub not loaded"})


# ── MIM: My Agents (all agents belonging to a User) ──


def _handle_mim_my_agents(args: dict) -> str:
    forwarded = _mim_center_call("winpeek_mim_my_agents", args)
    if forwarded is not None:
        return forwarded
    uid = int(args.get("uid", 0))
    if not uid:
        return json.dumps({"error": "uid required"})
    try:
        from gateway.winpeek_hub import identity
        # Find all agents whose manager_uid = uid (belong to this User)
        all_users = identity.list_all()
        agents = [
            {"uid": u["uid"], "nickname": u["nickname"], "role": u["role"],
             "agent_type": u.get("agent_type", ""), "host": u.get("host", ""),
             "peeka_name": u.get("peeka_name", ""), "identity_type": u.get("identity_type", ""),
             "manager_uid": u.get("manager_uid", 0)}
            for u in all_users
            if u.get("manager_uid") == uid and u.get("identity_type") == "mim-agent"
        ]
        return json.dumps({"uid": uid, "agents": agents, "count": len(agents)})
    except ImportError:
        return json.dumps({"error": "MIM Hub not loaded"})


# ── Register ──

registry.register(
    name="winpeek_mim_user_register",
    toolset="winpeek_rpa",
    schema={
        "name": "winpeek_mim_user_register",
        "description": "Register a human user (真人). Requires name + gender (male/female). Password defaults to a@123321.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Display name"},
                "gender": {"type": "string", "description": "male or female"},
                "password": {"type": "string", "description": "Login password (default a@123321)"},
            },
            "required": ["name", "gender"],
        },
    },
    handler=lambda args, **kw: _handle_mim_user_register(args),
    check_fn=lambda: True,
    requires_env=[],
    description="MIM human user registration",
)

registry.register(
    name="winpeek_mim_device_check",
    toolset="winpeek_rpa",
    schema={
        "name": "winpeek_mim_device_check",
        "description": "Check if a device (hostname) is already registered. Returns device info or null.",
        "parameters": {
            "type": "object",
            "properties": {"hostname": {"type": "string"}},
            "required": ["hostname"],
        },
    },
    handler=lambda args, **kw: _handle_mim_device_check(args),
    check_fn=lambda: True,
    requires_env=[],
    description="MIM device check by hostname",
)

registry.register(
    name="winpeek_mim_device_register",
    toolset="winpeek_rpa",
    schema={
        "name": "winpeek_mim_device_register",
        "description": "Register a device (电脑) to machines table. Requires hostname + owner_uid.",
        "parameters": {
            "type": "object",
            "properties": {
                "hostname": {"type": "string"},
                "owner_uid": {"type": "integer"},
            },
            "required": ["hostname", "owner_uid"],
        },
    },
    handler=lambda args, **kw: _handle_mim_device_register(args),
    check_fn=lambda: True,
    requires_env=[],
    description="MIM device registration",
)

registry.register(
    name="winpeek_mim_my_device",
    toolset="winpeek_rpa",
    schema={
        "name": "winpeek_mim_my_device",
        "description": "Auto-detect current device (hostname). Returns device info + human users on this machine.",
        "parameters": {"type": "object", "properties": {}},
    },
    handler=lambda args, **kw: _handle_mim_my_device(args),
    check_fn=lambda: True,
    requires_env=[],
    description="MIM auto-detect my device",
)

registry.register(
    name="winpeek_mim_my_agents",
    toolset="winpeek_rpa",
    schema={
        "name": "winpeek_mim_my_agents",
        "description": "List all MIM agents belonging to a Peeka User (by master_uid).",
        "parameters": {
            "type": "object",
            "properties": {"uid": {"type": "integer", "description": "Peeka User uid"}},
            "required": ["uid"],
        },
    },
    handler=lambda args, **kw: _handle_mim_my_agents(args),
    check_fn=lambda: True,
    requires_env=[],
    description="MIM list user's agents",
)

logger.info("WinPeek MIM tools: +user_register +device_check +device_register +my_device +my_agents")


# ── MIM: Register with Squad ──

def _handle_register_with_squad(args: dict) -> str:
    uid = int(args.get("uid", 0))
    logger.info("RPC call: winpeek_register_with_squad uid=%s is_new=%s name=%s", uid, args.get("is_new_squad"), args.get("squad_name", "?"))
    forwarded = _mim_center_call("winpeek_register_with_squad", args)
    if forwarded is not None:
        return forwarded
    uid = int(args.get("uid", 0))
    if not uid:
        return json.dumps({"ok": False, "error": "uid required"})
    try:
        from gateway.winpeek_hub import organization
        result = organization.register_with_squad(
            uid=uid,
            squad_id=int(args.get("squad_id", 0)),
            is_new_squad=bool(args.get("is_new_squad", False)),
            squad_name=str(args.get("squad_name", "")),
            squad_desc=str(args.get("squad_desc", "")),
            person_name=str(args.get("person_name", "")),
            email=str(args.get("email", "")),
            phone=str(args.get("phone", "")),
            hostname=str(args.get("hostname", "")),
            invite_code=str(args.get("invite_code", "")),
            industry=str(args.get("industry", "")),
            address=str(args.get("address", "")),
            website=str(args.get("website", "")),
            contact_email=str(args.get("contact_email", "")),
            contact_phone=str(args.get("contact_phone", "")),
            legal_person=str(args.get("legal_person", "")),
        )
        return json.dumps(result)
    except ImportError:
        logger.exception("MIM Hub import failed for register_with_squad")
        return json.dumps({"ok": False, "error": "MIM Hub not loaded"})
    except Exception as e:
        logger.exception("register_with_squad failed: uid=%s", uid)
        return json.dumps({"ok": False, "error": str(e)})


registry.register(
    name="winpeek_register_with_squad",
    toolset="winpeek_rpa",
    schema={
        "name": "winpeek_register_with_squad",
        "description": "Register a Peeka user with a squad (organization). Create new squad or join existing one.",
        "parameters": {
            "type": "object",
            "properties": {
                "uid": {"type": "integer", "description": "User uid"},
                "is_new_squad": {"type": "boolean", "description": "Create new squad if true"},
                "squad_name": {"type": "string", "description": "New squad name"},
                "squad_desc": {"type": "string", "description": "Squad description"},
                "squad_id": {"type": "integer", "description": "Existing squad id to join"},
                "invite_code": {"type": "string", "description": "Invite code to join"},
                "person_name": {"type": "string", "description": "Person display name"},
                "email": {"type": "string", "description": "Email"},
                "hostname": {"type": "string", "description": "Machine hostname"},
                "industry": {"type": "string", "description": "Industry"},
                "address": {"type": "string", "description": "Address"},
                "website": {"type": "string", "description": "Website URL"},
                "contact_email": {"type": "string", "description": "Contact email"},
                "contact_phone": {"type": "string", "description": "Contact phone"},
                "legal_person": {"type": "string", "description": "Legal person name"},
            },
            "required": ["uid"],
        },
    },
    handler=lambda args, **kw: _handle_register_with_squad(args),
    check_fn=lambda: True,
    requires_env=[],
    description="MIM register with squad (create or join)",
)

logger.info("WinPeek MIM tools: +register_with_squad")


# ── MIM: Change Password ──

def _handle_mim_change_password(args: dict) -> str:
    forwarded = _mim_center_call("winpeek_mim_change_password", args)
    if forwarded is not None:
        return forwarded
    uid = int(args.get("uid", 0))
    old_password = args.get("old_password", "")
    new_password = args.get("new_password", "")
    if not uid or not old_password or not new_password:
        return json.dumps({"error": "uid, old_password and new_password required"})
    try:
        from gateway.winpeek_hub import identity
        user = identity.get_by_uid(uid)
        if not user:
            return json.dumps({"error": "user not found"})
        check = identity.login(user["nickname"], old_password)
        if not check:
            return json.dumps({"error": "old password incorrect"})
        ok = identity.set_password(uid, new_password)
        return json.dumps({"ok": ok, "error": None if ok else "failed to update password"})
    except ImportError:
        return json.dumps({"error": "MIM Hub not loaded"})


registry.register(
    name="winpeek_mim_change_password",
    toolset="winpeek_rpa",
    schema={
        "name": "winpeek_mim_change_password",
        "description": "Change password for a MIM user. Requires old password verification.",
        "parameters": {
            "type": "object",
            "properties": {
                "uid": {"type": "integer", "description": "User uid"},
                "old_password": {"type": "string", "description": "Current password"},
                "new_password": {"type": "string", "description": "New password to set"},
            },
            "required": ["uid", "old_password", "new_password"],
        },
    },
    handler=lambda args, **kw: _handle_mim_change_password(args),
    check_fn=lambda: True,
    requires_env=[],
    description="MIM change password",
)


# ── MIM: Update Profile ──

def _handle_mim_update_profile(args: dict) -> str:
    forwarded = _mim_center_call("winpeek_mim_update_profile", args)
    if forwarded is not None:
        return forwarded
    uid = int(args.get("uid", 0))
    if not uid:
        return json.dumps({"error": "uid required"})
    # IDOR fix: require password verification before allowing profile edits
    password = args.get("password", "")
    if not password:
        return json.dumps({"error": "password required to update profile"})
    from gateway.winpeek_hub import identity
    user = identity.get_by_uid(uid)
    if not user or not identity.login(user.get("nickname", ""), password):
        return json.dumps({"error": "authentication failed"})
    allowed = {"nickname", "title", "bio", "skills", "role", "gender"}
    updates = {}
    for k in allowed:
        if k in args and args[k] is not None:
            updates[k] = args[k]
    if not updates:
        return json.dumps({"error": "no fields to update"})
    try:
        from gateway.winpeek_hub.db import get_conn
        conn = get_conn()
        if conn is None:
            return json.dumps({"error": "DB unavailable"})
        try:
            with conn.cursor() as cur:
                if "nickname" in updates:
                    cur.execute("SELECT uid FROM users WHERE nickname = %s AND uid != %s",
                                (updates["nickname"], uid))
                    if cur.fetchone():
                        return json.dumps({"error": "nickname already taken"})
                sets = ", ".join("`%s` = %%s" % k for k in updates)
                cur.execute("UPDATE users SET %s WHERE uid = %%s" % sets,
                            list(updates.values()) + [uid])
                conn.commit()
            return json.dumps({"ok": True})
        finally:
            conn.close()
    except ImportError:
        return json.dumps({"error": "MIM Hub not loaded"})
    except Exception as e:
        logger.exception("handler failed: %s", str(e))
        return json.dumps({"error": str(e)})


registry.register(
    name="winpeek_mim_update_profile",
    toolset="winpeek_rpa",
    schema={
        "name": "winpeek_mim_update_profile",
        "description": "Update MIM user profile fields (nickname, title, bio, skills, role, gender). Requires password authentication.",
        "parameters": {
            "type": "object",
            "properties": {
                "uid": {"type": "integer", "description": "User uid"},
                "password": {"type": "string", "description": "Current password for authentication"},
                "nickname": {"type": "string", "description": "New display name"},
                "title": {"type": "string", "description": "Job title"},
                "bio": {"type": "string", "description": "Self-introduction"},
                "skills": {"type": "string", "description": "Comma-separated skills"},
                "role": {"type": "string", "description": "Role"},
                "gender": {"type": "string", "description": "Gender: male/female"},
            },
            "required": ["uid", "password"],
        },
    },
    handler=lambda args, **kw: _handle_mim_update_profile(args),
    check_fn=lambda: True,
    requires_env=[],
    description="MIM update user profile",
)

logger.info("WinPeek MIM tools: +change_password +update_profile")


# ── Org CRUD complete handlers ────────────────────────────────────────

def _make_org_handler(rpc_name: str, org_fn_name: str, param_map: dict = None):
    """Factory for organization.py → json wrapper handlers.

    org_fn_name: actual function name in organization.py (e.g. 'list_squads')
    param_map: {frontend_key: backend_param_name} for mismatched names.
               e.g. {"uid": "requester_uid"} when frontend sends 'uid' but
               the org.py function expects 'requester_uid'.
    """
    pmap = param_map or {}
    def handler(args: dict) -> str:
        logger.info("RPC call: %s uid=%s", rpc_name, args.get('uid', args.get('requester_uid', '?')))
        forwarded = _mim_center_call(rpc_name, args)
        if forwarded is not None:
            return forwarded
        try:
            from gateway.winpeek_hub import organization
            fn = getattr(organization, org_fn_name)
            import inspect
            sig = inspect.signature(fn)
            call_kwargs = {}
            remaining = dict(args)
            has_var_kw = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values())

            for p_name, p in sig.parameters.items():
                if p.kind == inspect.Parameter.VAR_KEYWORD:
                    # Pass all remaining unmapped args into **kwargs
                    for k in list(remaining.keys()):
                        if k not in call_kwargs:
                            call_kwargs[k] = remaining.pop(k)
                    continue
                if p.kind == inspect.Parameter.VAR_POSITIONAL:
                    continue
                # Apply param_map: frontend_key → backend_param_name
                frontend_key = pmap.get(p_name, p_name)
                if frontend_key in args:
                    val = args[frontend_key]
                    if val is not None:
                        call_kwargs[p_name] = val
                    remaining.pop(frontend_key, None)

            # Any leftover unmapped args → **kwargs if fn accepts them
            if has_var_kw:
                call_kwargs.update(remaining)

            result = fn(**call_kwargs)
            return json.dumps(result)
        except ImportError:
            logger.exception("MIM Hub import failed for %s", rpc_name)
            return json.dumps({"error": "MIM Hub not loaded"})
        except Exception as e:
            logger.exception("Handler %s failed: args=%s", rpc_name, json.dumps(_sanitize(args), default=str)[:500])
            return json.dumps({"ok": False, "error": str(e)})
    return handler


# Batch-register all squad/person/machine/agent CRUD handlers
# Format: (rpc_name, org_function_name, description, param_map)
# param_map: {frontend_key: backend_param_name} for mismatched names
CRUD_HANDLERS = [
    ('winpeek_squad_list',       'list_squads',       'List all squads',                          None),
    ('winpeek_squad_upsert',     'upsert_squad',      'Create or update a squad',                 None),
    ('winpeek_squad_delete',     'delete_squad',      'Delete a squad',                           {"requester_uid": "uid"}),
    ('winpeek_squad_search',     'search_squads',     'Search squads by name',                    None),
    ('winpeek_person_list',      'list_persons',      'List persons in a squad',                  None),
    ('winpeek_person_upsert',    'upsert_person',     'Create or update a person',                None),
    ('winpeek_person_delete',    'delete_person',     'Delete a person',                          None),
    ('winpeek_person_approve',   'approve_person',    'Approve or reject a person',               None),
    ('winpeek_machine_list',     'list_machines',     'List machines/devices',                    None),
    ('winpeek_machine_delete',   'delete_machine',    'Delete a machine',                         None),
    ('winpeek_machine_approve',  'approve_machine',   'Approve or reject a machine',              None),
    ('winpeek_machine_detail',   'get_machine_detail','Get machine detail',                       None),
    ('winpeek_agent_list',       'list_agents',       'List agents',                              None),
    ('winpeek_agent_upsert',     'upsert_agent',      'Create or update an agent',                {"id": "agent_id"}),
    ('winpeek_agent_delete',     'delete_agent',      'Delete an agent',                          None),
    ('winpeek_org_tree',         'get_org_tree',      'Get full org hierarchy',                   None),
    ('winpeek_org_status',       'get_org_status',    'Get org status for a user',                {"winpeek_uid": "uid"}),
    ('winpeek_pending_list',     'get_pending',       'Get pending approvals',                    {"requester_uid": "uid"}),
    ('winpeek_join_squad',       'join_squad',        'Join an existing squad',                   None),
]

MISSING_HANDLERS = [
    ('winpeek_scan_register',    'scan_and_register_machine', 'Scan and register machine',         None),
    ('winpeek_mim_set_master',   'link_account',              'Set master account',                None),
]

for rpc_name, org_fn, desc, pmap in CRUD_HANDLERS + MISSING_HANDLERS:
    handler = _make_org_handler(rpc_name, org_fn, pmap)
    handler_name = f'_handle_{rpc_name.replace("winpeek_", "")}'
    globals()[handler_name] = handler
    registry.register(
        name=rpc_name,
        toolset="winpeek_rpa",
        schema={
            "name": rpc_name,
            "description": desc,
            "parameters": {"type": "object", "properties": {}, "additionalProperties": True},
        },
        handler=lambda args, h=handler, **kw: h(args),
        check_fn=lambda: True,
        requires_env=[],
        description=desc,
    )

# Explicit handler for invite codes (not in organization.py)
def _handle_get_invite_code(args: dict) -> str:
    try:
        from gateway.winpeek_hub import identity
        users = identity.list_all()
        # Extract invite codes from org membership
        from gateway.winpeek_hub import organization
        status = organization.get_org_status(int(args.get("uid", 0)))
        codes = []
        if status.get("linked") and status.get("squad", {}).get("invite_code"):
            codes.append({"code": status["squad"]["invite_code"], "squad": status["squad"]["name"]})
        return json.dumps({"invite_codes": codes})
    except Exception as e:
        logger.exception("handler failed: %s", str(e))
        return json.dumps({"ok": False, "error": str(e)})

registry.register(
    name="winpeek_my_invite_codes",
    toolset="winpeek_rpa",
    schema={"name":"winpeek_my_invite_codes","description":"Get my invite codes","parameters":{"type":"object","properties":{"uid":{"type":"integer"}}}},
    handler=lambda args, **kw: _handle_get_invite_code(args),
    check_fn=lambda: True, requires_env=[],
    description="Get invite codes",
)

logger.info(f"WinPeek MIM tools: +org CRUD ({len(CRUD_HANDLERS)} handlers +machine_detail +scan_register +mim_set_master +invite_codes)")
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
        logger.exception("handler failed: %s", str(e))
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
        logger.exception("handler failed: %s", str(e))
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
        logger.exception("handler failed: %s", str(e))
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
        logger.exception("handler failed: %s", str(e))
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
        logger.exception("handler failed: %s", str(e))
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
        logger.exception("handler failed: %s", str(e))
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

# ── MIM: Local agents (daemon state) ──

def _handle_mim_local_agents(args: dict) -> str:
    """Return daemon‑discovered agents on this machine. Never forwarded."""
    try:
        from apps.winpeek_injector.daemon import get_local_state
        state = get_local_state()
    except ImportError:
        state = {}
    # Determine current mode: same logic as _mim_center_call
    mode = "center"
    try:
        from hermes_cli.config import load_config
        mim = (load_config().get("winpeek", {}) or {}).get("mim", {}) or {}
        if str(mim.get("center_url") or "").strip():
            mode = "client"
    except Exception:
        pass
    return json.dumps({
        "mode": mode,
        "machine": state.get("machine", ""),
        "agents": [
            {
                "agent_type": r["agent_type"],
                "name": AGENT_TYPE_NAMES.get(r["agent_type"], r["agent_type"]),
                "detected_via": "daemon",
                "uid": r.get("uid") or 0,
                "registered": r.get("registered", False),
            }
            for r in state.get("runtimes", [])
        ],
    })

AGENT_TYPE_NAMES = {
    "claude-code": "Claude Code",
    "hermes": "Hermes Agent",
    "qoder": "Qoder",
    "traecli": "Trae CLI",
}

registry.register(
    name="winpeek_mim_local_agents",
    toolset="winpeek_rpa",
    schema={
        "name": "winpeek_mim_local_agents",
        "description": "List agent runtimes discovered by the local daemon. Shows machine mode, agent type, and registration status.",
        "parameters": {"type": "object", "properties": {}},
    },
    handler=lambda args, **kw: _handle_mim_local_agents(args),
    check_fn=lambda: True,
    requires_env=[],
    description="MIM local agent discovery",
)


# ── F3: Agent auto-reply — inbox + status handlers ──

def _handle_mim_check_inbox(args: dict) -> str:
    """Agent reads its unread inbox. Called by agent or frontend."""
    try:
        from gateway.winpeek_hub.chat import active_uid
    except ImportError:
        active_uid = lambda: 0
    uid = int(args.get("uid") or 0) or active_uid()
    if not uid:
        return json.dumps({"error": "uid required — login first"})
    try:
        from apps.winpeek_injector.daemon import read_inbox, get_local_state
        messages = read_inbox(uid)
        state = get_local_state()
        return json.dumps({
            "uid": uid,
            "unread_count": len(messages),
            "messages": messages,
            "reliability_pending": state.get("reliability_pending", 0),
        })
    except ImportError:
        return json.dumps({"error": "MIM Hub not loaded"})
    except Exception as e:
        logger.exception("check_inbox failed: %s", str(e))
        return json.dumps({"error": str(e)})


registry.register(
    name="winpeek_mim_check_inbox",
    toolset="winpeek_rpa",
    schema={
        "name": "winpeek_mim_check_inbox",
        "description": "Check agent's unread inbox messages. Returns message list with sender info and body.",
        "parameters": {
            "type": "object",
            "properties": {
                "uid": {"type": "integer", "description": "Agent uid to check inbox for"},
            },
            "required": ["uid"],
        },
    },
    handler=lambda args, **kw: _handle_mim_check_inbox(args),
    check_fn=lambda: True,
    description="MIM agent inbox check",
)


def _handle_mim_agent_status(args: dict) -> str:
    """Return agent online/reply status for frontend display."""
    try:
        from apps.winpeek_injector.daemon import get_local_state, get_pending_reliability
        state = get_local_state()
        runtimes = state.get("runtimes", [])
        inbox_summary = state.get("inbox_summary", {})
        pending = get_pending_reliability()

        agents = []
        for r in runtimes:
            agent_uid = str(r.get("uid", ""))
            summary = inbox_summary.get(agent_uid, {})
            agents.append({
                "uid": r.get("uid"),
                "agent_type": r["agent_type"],
                "registered": r.get("registered", False),
                "unread": summary.get("unread_count", 0),
                "delivered": summary.get("delivered_count", 0),
                "online": True,  # daemon reports = agent is online
            })

        return json.dumps({
            "machine": state.get("machine", ""),
            "agents": agents,
            "pending_chase": len(pending),
        })
    except ImportError:
        return json.dumps({"error": "MIM Hub not loaded"})
    except Exception as e:
        logger.exception("agent_status failed: %s", str(e))
        return json.dumps({"error": str(e)})


registry.register(
    name="winpeek_mim_agent_status",
    toolset="winpeek_rpa",
    schema={
        "name": "winpeek_mim_agent_status",
        "description": "Get agent online status, inbox counts, and pending chase reminders. For frontend status indicators.",
        "parameters": {"type": "object", "properties": {}},
    },
    handler=lambda args, **kw: _handle_mim_agent_status(args),
    check_fn=lambda: True,
    description="MIM agent online/reply status",
)


logger.info("WinPeek MIM tools: +local_agents +check_inbox +agent_status +read_digest +mark_replied")


# ── Digest + reply tracking ──

def _handle_mim_read_digest(args: dict) -> str:
    """Agent reads accumulated L1/L2 auto-reply digest on startup."""
    try:
        from gateway.winpeek_hub.chat import active_uid
    except ImportError:
        active_uid = lambda: 0
    uid = int(args.get("uid") or 0) or active_uid()
    try:
        from apps.winpeek_injector.daemon import pop_digest_entries, build_digest_message, read_inbox
        entries = pop_digest_entries()
        inbox_count = 0
        if uid:
            inbox_count = len(read_inbox(uid))
        return json.dumps({
            "digest": build_digest_message(entries) if entries else "",
            "auto_reply_count": len(entries),
            "pending_inbox": inbox_count,
        })
    except ImportError:
        return json.dumps({"error": "MIM Hub not loaded"})
    except Exception as e:
        logger.exception("read_digest failed: %s", str(e))
        return json.dumps({"error": str(e)})


registry.register(
    name="winpeek_mim_read_digest",
    toolset="winpeek_rpa",
    schema={
        "name": "winpeek_mim_read_digest",
        "description": "Read accumulated L1/L2 auto-reply digest (greetings handled while agent was offline). Returns digest message + pending inbox count.",
        "parameters": {
            "type": "object",
            "properties": {
                "uid": {"type": "integer", "description": "Agent uid"},
            },
        },
    },
    handler=lambda args, **kw: _handle_mim_read_digest(args),
    check_fn=lambda: True,
    description="MIM L1/L2 auto-reply digest reader",
)


def _handle_mim_mark_replied(args: dict) -> str:
    """Agent marks an inbox message as replied."""
    try:
        from gateway.winpeek_hub.chat import active_uid
    except ImportError:
        active_uid = lambda: 0
    uid = int(args.get("uid") or 0) or active_uid()
    mid = str(args.get("mid", ""))
    if not uid or not mid:
        return json.dumps({"error": "uid and mid required"})
    try:
        from apps.winpeek_injector.daemon import mark_replied, update_reliability
        mark_replied(uid, mid)
        update_reliability(mid, "replied")
        return json.dumps({"ok": True, "mid": mid})
    except ImportError:
        return json.dumps({"error": "MIM Hub not loaded"})
    except Exception as e:
        logger.exception("mark_replied failed: %s", str(e))
        return json.dumps({"error": str(e)})


registry.register(
    name="winpeek_mim_mark_replied",
    toolset="winpeek_rpa",
    schema={
        "name": "winpeek_mim_mark_replied",
        "description": "Mark an inbox message as replied. Called after agent sends its reply.",
        "parameters": {
            "type": "object",
            "properties": {
                "uid": {"type": "integer", "description": "Agent uid"},
                "mid": {"type": "string", "description": "Message mid to mark as replied"},
            },
            "required": ["uid", "mid"],
        },
    },
    handler=lambda args, **kw: _handle_mim_mark_replied(args),
    check_fn=lambda: True,
    description="MIM mark inbox message as replied",
)
