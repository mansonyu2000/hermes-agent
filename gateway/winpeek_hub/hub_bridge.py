"""
hub_bridge.py — WinPeek Hub 零侵入集成桥

在 gateway/run.py 启动时自动加载（通过环境变量 WINPEEK_HUB_ENABLED=1）。
不修改任何 Hermes 核心文件。

使用方式:
  1. 设置环境变量: WINPEEK_HUB_ENABLED=1
  2. Hermes Gateway 启动时自动加载 Hub
  3. Hub 在 gateway hooks 中注册消息监听
"""

import os
import logging

logger = logging.getLogger(__name__)

_HUB_LOADED = False


def is_enabled() -> bool:
    """检查 Hub 是否应启用"""
    return os.getenv("WINPEEK_HUB_ENABLED", "0") == "1"


def try_load_hub():
    """尝试加载 Hub（幂等，只加载一次）"""
    global _HUB_LOADED
    if _HUB_LOADED:
        return True
    if not is_enabled():
        logger.debug("WinPeek Hub disabled (WINPEEK_HUB_ENABLED != 1)")
        return False

    try:
        from gateway.winpeek_hub import tenant, routing, archive, identity
        _HUB_LOADED = True
        logger.info("WinPeek Hub loaded: tenant + routing + archive + identity")
        _register_routes()
        return True
    except ImportError as e:
        logger.warning(f"WinPeek Hub import failed: {e}")
        return False
    except Exception as e:
        logger.warning(f"WinPeek Hub init failed: {e}")
        return False


def _register_routes():
    """Register WinPeek identity routes with the Gateway."""
    try:
        from fastapi import APIRouter
        from fastapi.responses import JSONResponse
        from gateway.winpeek_hub import identity

        router = APIRouter(prefix="/api", tags=["winpeek"])

        @router.post("/identities/register")
        async def api_register(request: dict):
            nickname = (request.get("nickname") or "").strip()
            role = request.get("role", "Developer")
            if not nickname:
                return JSONResponse({"error": "nickname required"}, 400)
            result = identity.register(nickname, role)
            if result is None:
                return JSONResponse({"error": "nickname taken"}, 409)
            return JSONResponse(result)

        @router.post("/identities/login")
        async def api_login(request: dict):
            nickname = (request.get("nickname") or "").strip()
            if not nickname:
                return JSONResponse({"error": "nickname required"}, 400)
            result = identity.login(nickname)
            if result is None:
                return JSONResponse({"error": "not found"}, 404)
            return JSONResponse(result)

        @router.get("/identities")
        async def api_list_identities():
            return JSONResponse(identity.list_all())

        # Mount router on the gateway app
        from hermes_cli.web_server import app as _app
        _app.include_router(router)
        logger.info("WinPeek identity routes registered: /api/identities/*")
    except Exception as e:
        logger.warning(f"Failed to register identity routes: {e}")


def on_message_received(platform: str, from_uid: str, from_name: str,
                        content: str, msg_type: str = "text"):
    """
    Gateway hook: 当收到一条 IM 消息时调用。
    
    做两件事:
      1. 归档消息
      2. 如果需要跨平台投递，返回目标信息
    
    Returns:
        None 或 {"platform": "...", "platform_uid": "...", "display_name": "..."}
    """
    if not _HUB_LOADED:
        return None

    from gateway.winpeek_hub import tenant, routing, archive

    # 1. 查找租户
    t = tenant.get_tenant_for_user(platform, from_uid)
    tenant_id = t["tenant_id"] if t else "unknown"

    # 2. 归档
    archive.archive_message(
        tenant_id=tenant_id,
        from_platform=platform,
        from_uid=from_uid,
        to_platform="agent",
        to_uid="hermes",
        content=content,
        msg_type=msg_type,
    )

    # 3. 跨平台路由（如果消息包含 "@某人" 模式）
    #    格式: "@李四 你好" → 尝试投递到李四绑定的平台
    import re
    at_match = re.match(r'@(\S+)\s+(.*)', content)
    if at_match:
        target_name = at_match.group(1)
        actual_msg = at_match.group(2)
        target = routing.resolve_cross_platform_target(platform, from_uid, target_name)
        if target:
            return {
                **target,
                "content": actual_msg,
            }

    return None
