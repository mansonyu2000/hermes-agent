"""
mqtt_adapter.py — MIM MQTT 平台适配器

让 Hermes 通过 MQTT Broker 收发消息，实现多实例互通。

Topic 协议 (对应 WinPeek 约定):
  comms/inbox/{uid}   → Agent 订阅, 接收发给自己的消息
  comms/say/{uid}     → Agent 发布, 发送消息给指定 uid
  comms/ack/{uid}     → 消息回执

配置 (.env 或环境变量):
  MIM_UID=2022              # 当前用户的唯一 ID
  MIM_NAME="yuyangmin"      # 显示名
  MIM_BROKER=192.168.3.23   # MQTT Broker 地址
  MIM_PORT=1883             # MQTT 端口
"""

import json
import logging
import os
import threading
import time
from typing import Optional

try:
    import paho.mqtt.client as mqtt
    HAS_PAHO = True
except ImportError:
    HAS_PAHO = False

logger = logging.getLogger(__name__)

# ── 配置 ──────────────────────────────────────────────────

UID = int(os.getenv("MIM_UID", "0"))
NAME = os.getenv("MIM_NAME", f"user_{UID}")
BROKER = os.getenv("MIM_BROKER", "192.168.3.23")
PORT = int(os.getenv("MIM_PORT", "1883"))

INBOX_TOPIC = f"comms/inbox/{UID}"
SAY_TOPIC_PREFIX = "comms/say"

_client: Optional[mqtt.Client] = None
_message_handler = None  # 回调: (from_uid, from_name, text) -> agent_response


def is_configured() -> bool:
    """检查是否已配置 MIM"""
    return UID > 0 and bool(NAME)


def is_available() -> bool:
    """检查 paho-mqtt 是否安装且已配置"""
    return HAS_PAHO and is_configured()


def set_message_handler(handler):
    """设置消息处理回调"""
    global _message_handler
    _message_handler = handler


# ── MQTT 回调 ────────────────────────────────────────────

def _on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        client.subscribe(f"{INBOX_TOPIC}", qos=1)
        logger.info(f"📡 MIM 已连接 {BROKER}:{PORT}, 订阅 {INBOX_TOPIC}")
    else:
        logger.warning(f"MIM 连接失败: code={reason_code}")


def _on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
    except json.JSONDecodeError:
        return

    from_uid = payload.get("from_uid", "")
    from_name = payload.get("from", "?")
    body = payload.get("body", "")

    # 跳过自己的回声
    if str(from_uid) == str(UID):
        return

    logger.info(f"📩 [{from_name} ({from_uid})]: {body[:80]}")

    if _message_handler:
        try:
            _message_handler(from_uid, from_name, body)
        except Exception as e:
            logger.warning(f"MIM 消息处理失败: {e}")


# ── 连接管理 ──────────────────────────────────────────────

def connect():
    """连接 MQTT Broker (非阻塞)"""
    global _client
    if not is_available():
        logger.warning("MIM 不可用: paho-mqtt 未安装或 MIM_UID 未设置")
        return None

    _client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    _client.on_connect = _on_connect
    _client.on_message = _on_message

    try:
        _client.connect(BROKER, PORT, 60)
        # 在后台线程运行
        t = threading.Thread(target=_client.loop_forever, daemon=True)
        t.start()
        logger.info(f"MIM started: uid={UID} name={NAME} broker={BROKER}:{PORT}")
        return _client
    except Exception as e:
        logger.warning(f"MIM 连接失败: {e}")
        return None


def disconnect():
    """断开 MQTT"""
    global _client
    if _client:
        _client.disconnect()
        _client = None


# ── 发送 ──────────────────────────────────────────────────

def send_message(target_uid: int, text: str, target_name: str = "") -> bool:
    """
    发送消息给指定 UID 的用户。
    对方通过 comms/inbox/{target_uid} 收到。
    """
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
        logger.info(f"📤 MIM → {target_name or target_uid}: {text[:60]}")
        return result.rc == mqtt.MQTT_ERR_SUCCESS
    except Exception as e:
        logger.warning(f"MIM 发送失败: {e}")
        return False


def broadcast_message(text: str, exclude_uids: list = None) -> int:
    """
    向所有在线用户广播消息。
    返回实际发送数。
    """
    # 简化版: 通过通配话题发布
    if not _client:
        return 0
    topic = "comms/inbox/broadcast"
    payload = json.dumps({
        "from_uid": str(UID),
        "from": NAME,
        "body": text,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }, ensure_ascii=False)
    try:
        _client.publish(topic, payload, qos=1)
        return 1
    except Exception:
        return 0


def status() -> dict:
    """返回 MIM 连接状态"""
    return {
        "enabled": is_configured(),
        "connected": _client is not None,
        "uid": UID,
        "name": NAME,
        "broker": f"{BROKER}:{PORT}",
        "topic": INBOX_TOPIC,
    }
