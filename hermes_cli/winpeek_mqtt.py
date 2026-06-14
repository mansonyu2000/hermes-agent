"""
Hermes WinPeek MQTT 收件监听器

替换 winpeek_inbox.py 的文件轮询方案。
直接订阅 MQTT comms/inbox/{uid}，消息到达立即注入 Hermes 上下文。

用法 (cli.py 启动时):
    from hermes_cli.winpeek_mqtt import start_mqtt_listener
    start_mqtt_listener(uid=2022, mqtt_host="192.168.3.3")
"""

import json
import threading
from datetime import datetime

try:
    import paho.mqtt.client as mqtt
    HAS_PAHO = True
except ImportError:
    HAS_PAHO = False


_inbox_queue = []  # 接收的消息队列
_queue_lock = threading.Lock()
_listener_started = False


def start_mqtt_listener(uid: int = 2022, mqtt_host: str = "192.168.3.3", mqtt_port: int = 1883):
    """后台线程启动 MQTT 订阅, 消息入队 _inbox_queue。"""
    global _listener_started
    if _listener_started or not HAS_PAHO:
        return

    topic = f"comms/inbox/{uid}"

    def on_connect(client, userdata, flags, reason_code, properties):
        client.subscribe(topic)

    def on_message(client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            body = payload.get("body", "")
            from_name = payload.get("from", payload.get("from_name", "?"))
            if body.startswith("收到来自"):
                return
            with _queue_lock:
                _inbox_queue.append({
                    "from": from_name,
                    "content": body[:500],
                    "ts": datetime.now().isoformat(),
                    "gid": payload.get("gid", ""),
                })
        except Exception:
            pass

    def _loop():
        while True:
            try:
                client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
                client.on_connect = on_connect
                client.on_message = on_message
                client.connect(mqtt_host, mqtt_port, 60)
                client.loop_forever()
            except Exception:
                import time
                time.sleep(5)

    t = threading.Thread(target=_loop, daemon=True)
    t.start()
    _listener_started = True


def drain_inbox() -> list[dict]:
    """取出并清空收件队列。每次 Hermes 轮询时调用。"""
    with _queue_lock:
        msgs = _inbox_queue[:]
        _inbox_queue.clear()
    return msgs


def format_inbox_summary(messages: list[dict]) -> str:
    """将新消息格式化为可展示的摘要文本。"""
    if not messages:
        return ""
    lines = ["\n📬 WinPeek:"]
    for msg in messages[-10:]:
        ts = msg.get("ts", "")[:19].replace("T", " ")
        content = msg.get("content", "")[:100]
        gid = msg.get("gid", "")
        tag = f" [群{gid}]" if gid else ""
        lines.append(f"  [{ts}] {msg['from']}{tag}: {content}")
    return "\n".join(lines)
