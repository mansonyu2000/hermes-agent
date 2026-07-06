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
