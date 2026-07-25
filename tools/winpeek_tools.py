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
        from gateway.winpeek_hub import identity
        from gateway.winpeek_hub.chat import set_active_session
    except ImportError as e:
        return json.dumps({"error": f"MIM Hub not loaded: {e}"})
    result = identity.login(nickname, password) or identity.register(nickname, role, password=password)
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
    limit = int(args.get("limit", 50))
    if not peer_uid:
        return json.dumps({"error": "peer_uid required"})
    try:
        from gateway.winpeek_hub.chat import get_history, active_uid
    except ImportError:
        return json.dumps({"error": "MIM Hub not loaded"})
    uid = int(args.get("uid") or 0) or active_uid()
    if not uid:
        return json.dumps({"error": "not logged in — call winpeek_mim_login first"})
    return json.dumps({"messages": get_history(uid, peer_uid, limit)})

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

logger.info("WinPeek MIM tools: +user_info")

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

logger.info("WinPeek MIM tools: +user_register +device_check +device_register +my_device")

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

logger.info("WinPeek MIM tools: +user_info +local_agents")
