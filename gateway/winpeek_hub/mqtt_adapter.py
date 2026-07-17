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

INBOX_TOPIC = property(lambda self: f"comms/inbox/{UID}")
SAY_TOPIC_PREFIX = "comms/say"

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
        logger.info(f"MIM connected {BROKER}:{PORT}, uid={UID} name={NAME}, inbox=all")
    else:
        logger.warning(f"MIM connect failed: code={reason_code}")


def _on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
    except json.JSONDecodeError:
        return

    from_uid = payload.get("from_uid", "")
    from_name = payload.get("from", "?")
    body = payload.get("body", "")

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


def status() -> dict:
    return {
        "enabled": is_configured(),
        "connected": _client is not None,
        "uid": UID,
        "name": NAME,
        "broker": f"{BROKER}:{PORT}",
    }
