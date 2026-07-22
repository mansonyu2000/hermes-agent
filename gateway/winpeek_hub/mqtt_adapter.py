"""
mqtt_adapter.py — MIM MQTT 平台适配器

让 Hermes 通过 MQTT Broker 收发消息，实现多实例互通。

身份自动从 MySQL winpeek-db2.users 表读取，不需要手动设环境变量。
首次启动时自动注册默认身份。

Topic 协议:
  comms/inbox/{uid}   → Agent 订阅, 接收发给自己的消息
  comms/say/{uid}     → Agent 发布, 发送消息给指定 uid
  comms/ack/{uid}     → 消息回执

配置 (.env 或 config.yaml, 可选):
  MIM_BROKER=192.168.3.23   # MQTT Broker 地址 (默认)
  MIM_PORT=1883             # MQTT 端口 (默认)
"""

import json
import logging
import os
import socket
import threading
import time
from typing import Optional

try:
    import paho.mqtt.client as mqtt
    HAS_PAHO = True
except ImportError:
    HAS_PAHO = False

logger = logging.getLogger(__name__)

# ── 身份 (从 identity DB 自动读取, 不依赖环境变量) ─────

UID: int = 0
NAME: str = ""
ROLE: str = "Agent"

def _resolve_identity():
    """从 identity JSONL 读取身份。无身份时用本机主机名自动注册。"""
    global UID, NAME, ROLE
    try:
        from gateway.winpeek_hub import identity
        ids = identity.list_all()
        if ids:
            first = ids[0]
            UID = first.get("uid", 0)
            NAME = first.get("nickname", "")
            ROLE = first.get("role", "Agent")
            logger.info(f"MIM identity resolved: uid={UID} name={NAME} ({len(ids)} total)")
        if not UID or not NAME:
            # 自动注册: 主机名 = 昵称
            hostname = socket.gethostname().split(".")[0]
            result = identity.register(hostname, "Agent", hostname)
            if result:
                UID = result["uid"]
                NAME = result["nickname"]
                ROLE = result.get("role", "Agent")
                logger.info(f"MIM identity auto-created: uid={UID} name={NAME}")
    except Exception as e:
        logger.warning(f"MIM identity resolve failed: {e}")

# ── 配置 (仅 Broker 地址可从环境变量覆盖) ──────────────

BROKER = os.getenv("MIM_BROKER", "192.168.3.23")
PORT = int(os.getenv("MIM_PORT", "1883"))

SAY_TOPIC_PREFIX = "comms/say"
OUTBOX_TOPIC = "comms/outbox"
GROUP_TOPIC_PREFIX = "comms/group"

_client: Optional[mqtt.Client] = None
_message_handler = None


def is_configured() -> bool:
    return UID > 0 and bool(NAME)


def is_available() -> bool:
    return HAS_PAHO and is_configured()


def set_message_handler(handler):
    global _message_handler
    _message_handler = handler


# ── MQTT 回调 ────────────────────────────────────

def _on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        client.subscribe("comms/inbox/#", qos=1)
        client.subscribe("comms/outbox/#", qos=1)
        client.subscribe("comms/group/#", qos=1)
        logger.info(f"MIM connected {BROKER}:{PORT}, uid={UID} name={NAME}, inbox+outbox+group=all")
    else:
        logger.warning(f"MIM connect failed: code={reason_code}")


def _on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
    except json.JSONDecodeError:
        return

    # ── Outbox: Agent → Daemon relay ──
    if msg.topic.startswith("comms/outbox/"):
        _handle_outbox(msg.topic, payload)
        return

    from_uid = payload.get("from_uid", "")
    from_name = payload.get("from", "?")
    body = payload.get("body", "")
    gid = payload.get("gid")

    if str(from_uid) == str(UID):
        return

    logger.info(f"[{from_name} ({from_uid})]: {body[:80]}")

    # Route into chat queue
    try:
        from gateway.winpeek_hub.chat import enqueue
        enqueue({
            "from_uid": int(from_uid) if str(from_uid).isdigit() else 0,
            "from_name": from_name,
            "to_uid": UID,
            "gid": gid,
            "content": body,
            "time": payload.get("ts", time.strftime("%Y-%m-%dT%H:%M:%S")),
        })
    except Exception:
        pass

    if _message_handler:
        try:
            _message_handler(from_uid, from_name, body)
        except Exception as e:
            logger.warning(f"MIM handler error: {e}")


def _handle_outbox(topic: str, payload: dict):
    """Agent 发到 outbox 的消息 → Daemon 补全上下文 → 转发给收件人。

    Topic: comms/outbox/{from_uid}
    Payload: {"to_uid": int, "body": str, "reply_to_mid": str?, "ts": str?}

    全权委托 chat.send_message() 处理：
      DB 归档 → MQTT 发布 → 本地 enqueue → Peeka Router(L1/L2/L3)
    """
    to_uid = int(payload.get("to_uid", 0))
    body = payload.get("body", "")

    if not to_uid or not body:
        logger.warning(f"[outbox] 无效消息: to_uid={to_uid} body={body[:30]}")
        return

    # 从 topic 提取 from_uid
    parts = topic.split("/")
    from_uid_str = parts[-1] if len(parts) > 2 else ""
    try:
        from_uid = int(from_uid_str)
    except (ValueError, TypeError):
        logger.warning(f"[outbox] 无法从 topic 提取 uid: {topic}")
        return

    # 查 identity 补全名称
    from_name = f"user_{from_uid}"
    try:
        from gateway.winpeek_hub import identity
        user = identity.get_by_uid(from_uid)
        if user:
            from_name = user.get("nickname", from_name)
    except Exception:
        pass

    logger.info(f"[outbox] {from_name}[{from_uid}] → uid={to_uid}: {body[:60]}")

    # 全权委托 chat.send_message() — 它负责 DB+MQQT+enqueue+Peeka Router
    try:
        from gateway.winpeek_hub.chat import send_message as chat_send
        result = chat_send(from_uid, from_name, to_uid, body)
        logger.info(f"[outbox] chat_send result: {result.get('ok')} mid={result.get('mid','')[:20]}")
    except Exception as e:
        logger.warning(f"[outbox] chat_send 失败: {e}")


# ── 连接管理 ──────────────────────────────────────

def connect():
    """连接 MQTT Broker (后台线程, 非阻塞)"""
    global _client
    _resolve_identity()
    if not is_available():
        logger.info(f"MIM skipped: paho={HAS_PAHO} uid={UID} name={NAME}")
        return None

    _client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    _client.on_connect = _on_connect
    _client.on_message = _on_message

    try:
        _client.connect(BROKER, PORT, 60)
        t = threading.Thread(target=_client.loop_forever, daemon=True)
        t.start()
        logger.info(f"MIM started: uid={UID} name={NAME} broker={BROKER}:{PORT}")
        return _client
    except Exception as e:
        logger.warning(f"MIM connect failed: {e}")
        return None


def disconnect():
    global _client
    if _client:
        _client.disconnect()
        _client = None


# ── 发送 ──────────────────────────────────────────

def send_message(target_uid: int, text: str, target_name: str = "") -> bool:
    if not _client or target_uid <= 0:
        return False

    topic = f"{SAY_TOPIC_PREFIX}/{target_uid}"
    payload = json.dumps({
        "from_uid": str(UID),
        "from": NAME,
        "to_uid": str(target_uid),
        "body": text,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }, ensure_ascii=False)

    try:
        result = _client.publish(topic, payload, qos=1)
        logger.info(f"MIM → {target_name or target_uid}: {text[:60]}")
        return result.rc == mqtt.MQTT_ERR_SUCCESS
    except Exception as e:
        logger.warning(f"MIM send failed: {e}")
        return False


def send_group_message(gid: int, text: str, from_name: str, from_uid: int = 0) -> bool:
    if not _client or gid <= 0:
        return False
    topic = f"{GROUP_TOPIC_PREFIX}/{gid}"
    payload = json.dumps({
        "from_uid": str(from_uid or UID),
        "from": from_name or NAME,
        "gid": gid,
        "body": text,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }, ensure_ascii=False)
    try:
        result = _client.publish(topic, payload, qos=1)
        logger.info(f"MIM → group {gid}: {text[:60]}")
        return result.rc == mqtt.MQTT_ERR_SUCCESS
    except Exception as e:
        logger.warning(f"MIM group send failed: {e}")
        return False


def status() -> dict:
    return {
        "enabled": is_configured(),
        "connected": _client is not None,
        "uid": UID,
        "name": NAME,
        "broker": f"{BROKER}:{PORT}",
    }
