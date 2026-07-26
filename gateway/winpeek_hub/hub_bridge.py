"""
hub_bridge.py — WinPeek Hub 零侵入集成桥

在 gateway/run.py 启动时自动加载。不需要额外参数或环境变量。
不修改任何 Hermes 核心文件。

加载顺序: identity → mqtt_adapter(connect) → chat → archive → routing → tenant

配置方式 (config.yaml):
  winpeek:
    mim:
      enabled: true         # 启用 MIM 服务
      broker: 192.168.3.23  # MQTT Broker 地址 (可选)
      port: 1883            # MQTT 端口 (可选)

  dashboard:
    basic_auth:             # 绑定 0.0.0.0 时必须配 basic auth
      username: admin
      password_hash: "..."

启动:
  hermes serve --host 0.0.0.0   # 对外提供 MIM 服务
  hermes serve                    # 仅本地 (默认 127.0.0.1)
"""

import os
import logging
import threading

logger = logging.getLogger(__name__)

_HUB_LOADED = False
_load_lock = threading.Lock()


def is_enabled() -> bool:
    """检查 Hub 是否应启用。优先级: config.yaml > 环境变量"""
    # 优先读 config.yaml
    try:
        from hermes_cli.config import load_config
        cfg = load_config()
        mim = cfg.get("winpeek", {}).get("mim", {})
        if isinstance(mim, dict) and "enabled" in mim:
            return bool(mim["enabled"])
    except Exception:
        pass
    # Fallback 环境变量 (向后兼容)
    return os.getenv("WINPEEK_HUB_ENABLED", "0") == "1"


def try_load_hub():
    """尝试加载 Hub（幂等，线程安全）。

    加载所有 Hub 模块，启动 MQTT 连接。
    跟随 hermes serve / hermes gateway 自动执行，
    不需要手动操作。"""
    global _HUB_LOADED
    if _HUB_LOADED:
        return True
    with _load_lock:
        if _HUB_LOADED:
            return True
        if not is_enabled():
            logger.debug("WinPeek Hub disabled (WINPEEK_HUB_ENABLED != 1)")
            return False
        _HUB_LOADED = True  # prevent concurrent threads from re-entering

    try:
        from gateway.winpeek_hub import identity, tenant, routing, archive
        logger.info("WinPeek Hub loaded: identity + tenant + routing + archive")
    except ImportError as e:
        logger.warning(f"WinPeek Hub import failed: {e}")
        return False

    # ── 启动 MQTT 连接 ──
    try:
        from gateway.winpeek_hub import mqtt_adapter
        mqtt_adapter._resolve_identity()  # 先解析身份(从DB读取)
        if mqtt_adapter.is_configured() and mqtt_adapter.is_available():
            mqtt_adapter.connect()
            logger.info(
                f"WinPeek MQTT connected: uid={mqtt_adapter.UID} "
                f"name={mqtt_adapter.NAME} "
                f"broker={mqtt_adapter.BROKER}:{mqtt_adapter.PORT}"
            )
        else:
            logger.info(
                f"WinPeek MQTT skipped: uid={mqtt_adapter.UID} "
                f"name={mqtt_adapter.NAME} "
                f"(identity DB empty or paho-mqtt missing)"
            )
    except Exception as e:
        logger.warning(f"WinPeek MQTT connect failed: {e}")

    # ── 初始化 chat 引擎 (MySQL) ──
    try:
        from gateway.winpeek_hub.db import get_conn
        # Verify MySQL connection by testing a simple query
        conn = get_conn()
        if conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
            conn.close()
            logger.info("WinPeek chat engine ready (MySQL)")
        else:
            logger.warning("WinPeek MySQL unavailable")
    except Exception as e:
        logger.warning(f"WinPeek chat engine init failed: {e}")

    # ── 初始化 hub (在线状态) ──
    try:
        from gateway.winpeek_hub import hub
        if mqtt_adapter.is_configured() and os.getenv("MIM_UID", "0") != "0":
            hub.register_node(
                mqtt_adapter.UID,
                mqtt_adapter.NAME,
                role="Agent",
                host=os.getenv("HOSTNAME", "local"),
            )
            logger.info(f"WinPeek node registered: {mqtt_adapter.UID} ({mqtt_adapter.NAME})")
    except Exception as e:
        logger.warning(f"WinPeek node registration failed: {e}")

    # ── 启动 Agent Injector daemon ──
    try:
        from apps.winpeek_injector.daemon import start_daemon
        start_daemon()
        logger.info("WinPeek injector daemon started")
    except Exception as e:
        logger.warning(f"WinPeek injector start failed: {e}")

    return True


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
