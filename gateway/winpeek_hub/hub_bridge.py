"""
hub_bridge.py — WinPeek Hub 零侵入集成桥

在 gateway/run.py 启动时自动加载。不需要额外参数或环境变量。
不修改任何 Hermes 核心文件。

两种运行模式 (由 config.yaml 的 winpeek.mim.center_url 决定):

  服务端模式 (未配置 center_url):
    全量加载: identity + MySQL + MQTT + Daemon + Hub
    仅 1-2 台消息中心服务器需要数据库与 Broker 凭据

  客户端模式 (配置了 center_url):
    MQTT only (say.py CLI 用共享 Broker)
    跳过 MySQL + Daemon + Peeka Router
    所有 RPC 通过 _mim_center_call() 转发到中心 serve

配置方式 (config.yaml):
  # 服务端 (中心)
  winpeek:
    mim:
      enabled: true
      broker: 192.168.3.23

  # 客户端
  winpeek:
    mim:
      enabled: true
      center_url: "http://192.168.3.44:2000"
"""

import os
import logging

logger = logging.getLogger(__name__)

_HUB_LOADED = False


def is_enabled() -> bool:
    """检查 Hub 是否应启用。优先级: config.yaml > 环境变量"""
    try:
        from hermes_cli.config import load_config
        cfg = load_config()
        mim = cfg.get("winpeek", {}).get("mim", {})
        if isinstance(mim, dict) and "enabled" in mim:
            return bool(mim["enabled"])
    except Exception:
        pass
    return os.getenv("WINPEEK_HUB_ENABLED", "0") == "1"


def is_center_mode() -> bool:
    """True = 本机是服务中心 (有 MySQL + MQTT + Daemon).
    False = 客户端模式 (转发到 center, 本地只跑 WebSocket 网关)."""
    try:
        from hermes_cli.config import load_config
        mim = (load_config().get("winpeek", {}) or {}).get("mim", {}) or {}
        return not bool(str(mim.get("center_url") or "").strip())
    except Exception:
        return True  # config 读不到 → 保守假设是中心


def try_load_hub():
    """尝试加载 Hub（幂等，只加载一次）。

    服务端模式 (无 center_url):
      加载全部: identity + MySQL + MQTT + Daemon + Hub

    客户端模式 (配了 center_url):
      只启动 MQTT (say.py CLI 用共享 Broker)
      跳过 MySQL + Daemon + Peeka Router (全部 RPC 已走中心转发)
    """
    global _HUB_LOADED
    if _HUB_LOADED:
        return True
    if not is_enabled():
        logger.debug("WinPeek Hub disabled (WINPEEK_HUB_ENABLED != 1)")
        return False

    _center = is_center_mode()

    # ── MQTT 连接 (两种模式都启动: say.py CLI 发给共享 Broker) ──
    try:
        from gateway.winpeek_hub import mqtt_adapter
        mqtt_adapter._resolve_identity()
        if mqtt_adapter.is_configured() and mqtt_adapter.is_available():
            mqtt_adapter.connect()
            logger.info(
                "WinPeek MQTT connected: uid=%s name=%s broker=%s:%s",
                mqtt_adapter.UID, mqtt_adapter.NAME,
                mqtt_adapter.BROKER, mqtt_adapter.PORT,
            )
        else:
            logger.info(
                "WinPeek MQTT skipped: uid=%s name=%s",
                mqtt_adapter.UID, mqtt_adapter.NAME,
            )
    except Exception as e:
        logger.warning("WinPeek MQTT connect failed: %s", e)

    # ── 客户端模式: MCP 注入 + 身份块 ──
    if not _center:
        _client_inject()
        logger.info(
            "WinPeek Hub: client mode (center_url configured) — "
            "MQTT only, RPCs forwarded to center"
        )
        _HUB_LOADED = True
        return True

    # ═══════════════════════════════════════════════
    # 以下为服务端专属
    # ═══════════════════════════════════════════════

    try:
        from gateway.winpeek_hub import identity, tenant, routing
        logger.info("WinPeek Hub loaded: identity + tenant + routing")
    except ImportError as e:
        logger.warning("WinPeek Hub import failed: %s", e)
        return False

    # ── chat 引擎 (MySQL) ──
    try:
        from gateway.winpeek_hub.db import get_conn
        conn = get_conn()
        if conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
            conn.close()
            logger.info("WinPeek chat engine ready (MySQL)")
        else:
            logger.warning("WinPeek MySQL unavailable")
    except Exception as e:
        logger.warning("WinPeek chat engine init failed: %s", e)

    # ── hub (在线状态) ──
    try:
        from gateway.winpeek_hub import hub
        if mqtt_adapter.is_configured() and os.getenv("MIM_UID", "0") != "0":
            hub.register_node(
                mqtt_adapter.UID,
                mqtt_adapter.NAME,
                role="Agent",
                host=os.getenv("HOSTNAME", "local"),
            )
            logger.info(
                "WinPeek node registered: %s (%s)",
                mqtt_adapter.UID, mqtt_adapter.NAME,
            )
    except Exception as e:
        logger.warning("WinPeek node registration failed: %s", e)

    # ── Agent Injector daemon ──
    try:
        from apps.winpeek_injector.daemon import start_daemon
        start_daemon()
        logger.info("WinPeek injector daemon started")
    except Exception as e:
        logger.warning("WinPeek injector start failed: %s", e)

    _HUB_LOADED = True
    return True


def _client_inject():
    """客户端模式: 注入 MCP 配置 + MIM 身份块 (不需要 MySQL)。

    从本地 ~/.hermes/data/agent.conf 读取身份,
    写入 ~/.claude/settings.json (MCP) + ~/.claude/CLAUDE.md (身份块)。
    服务端模式下由 daemon 的 register_and_inject() 处理, 不经过此函数。
    """
    import json as _json
    from pathlib import Path as _Path

    HOME = _Path.home()

    # 1. 读本地身份
    uid = 0
    name = ""
    pw = ""
    role = "Agent"
    agent_conf = HOME / ".hermes" / "data" / "agent.conf"
    if agent_conf.exists():
        try:
            d = _json.loads(agent_conf.read_text(encoding="utf-8"))
            uid = int(d.get("hermes_uid", 0))
            name = d.get("agent_name", "") or d.get("name", "")
            pw = d.get("password", "")
            role = d.get("role", "Agent")
        except Exception:
            pass
    if not uid:
        uid = int(os.getenv("MIM_UID", "0"))
    if not name:
        name = os.getenv("MIM_NAME", "") or socket.gethostname()

    if not uid:
        logger.warning("Client inject: no identity found (agent.conf or env)")
        return

    # 2. 注入 MCP 配置文件
    import socket
    try:
        from apps.winpeek_injector.daemon import inject_mcp_config
    except ImportError:
        inject_mcp_config = None

    if inject_mcp_config:
        for p in [
            HOME / ".claude" / "settings.json",
            HOME / ".hermes" / "mcp.json",
            HOME / ".qoder" / "settings.json",
        ]:
            if p.exists():
                try:
                    inject_mcp_config(p)
                except Exception:
                    pass

    # 3. 注入 MIM_IDENTITY_BLOCK
    fake_scanner = {"agent_type": "hermes", "name": name}
    fake_identity = {
        "nickname": name,
        "role": role,
        "peeka_name": f"{name}XX-{socket.gethostname()}-hotime.cn",
        "squad_name": "",
        "manager_uid": 0,
    }
    try:
        from apps.winpeek_injector.daemon import _inject_agent_prompt
        _inject_agent_prompt(uid, fake_identity, fake_scanner, pw)
    except Exception as e:
        logger.debug("Client prompt inject failed: %s", e)

    logger.info("Client inject: uid=%s name=%s MCP+prompt injected", uid, name)


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
