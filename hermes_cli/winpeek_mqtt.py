"""
Hermes WinPeek MQTT 收件监听器

架构: push > pull。MQTT broker 主动推送 → 后台线程接收 → 入队 →
      Hermes 主循环周期性 drain → 打印到终端。

无需独立 bridge 进程，无需文件轮询，无需 .inject 文件。

═══════════════════════════════════════════════════════════════
⚠️  发送消息必须用 say 命令，禁止用 send_message()：
═══════════════════════════════════════════════════════════════

  ✅ say 2022 "消息"      → comms/say/{uid} → Hub 归档+转发
  ❌ send_message(...)     → comms/inbox/{uid} 直推 → 绕过Hub无归档

  send_message() 仅用于 cron 报告等程序内部通知。
  Agent 间通信必须用 shell 命令 say。

  say 命令安装: PeekabooWin\\bin 加到系统 PATH。
  详细: PeekabooWin/docs/operations/new-machine-setup.md

═══════════════════════════════════════════════════════════════

配置来源: agent.conf (JSON)，机器独立，不进 git。
  查找顺序:
    1. ~/.winpeek/agent.conf
    2. ./agent.conf
    3. ./bin/agent.conf
  找不到则用默认值。

默认值:
  hermes_uid: 2022
  mqtt_host: 192.168.3.23
  mqtt_port: 1883

用法 (cli.py):
  from hermes_cli.winpeek_mqtt import start_mqtt_listener, drain_inbox, format_inbox_summary
  start_mqtt_listener()          # 启动时调用一次，后台线程持续运行
  ...
  msgs = drain_inbox()           # 主循环周期性调用
  if msgs:
      print(format_inbox_summary(msgs))
"""

import json
import threading
from datetime import datetime
from pathlib import Path

try:
    import paho.mqtt.client as mqtt
    HAS_PAHO = True
except ImportError:
    HAS_PAHO = False

# ── 线程安全队列 ──────────────────────────────────────────
_inbox_queue: list[dict] = []
_queue_lock = threading.Lock()
_listener_started = False
_mqtt_client = None  # paho client 引用, 收发复用同一条连接

# ── 默认值 (agent.conf 可覆盖) ─────────────────────────────
_DEFAULT_HOST = "192.168.3.23"
_DEFAULT_PORT = 1883
_DEFAULT_UID = 2022


def _find_agent_conf() -> Path | None:
    """查找 agent.conf 文件。"""
    candidates = [
        # 用户数据目录 (个性化配置，不进 git)
        Path.home() / ".winpeek" / "agent.conf",
        Path.home() / ".hermes" / "data" / "agent.conf",
        Path.home() / ".claude" / "data" / "agent.conf",
        # 项目仓库 (首次从 example 复制)
        Path("agent.conf"),
        Path("bin") / "agent.conf",
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


def _read_config() -> dict:
    """从 agent.conf 读取 hermes_uid, mqtt_host, mqtt_port。"""
    conf_path = _find_agent_conf()
    if conf_path is None:
        return {"uid": _DEFAULT_UID, "host": _DEFAULT_HOST, "port": _DEFAULT_PORT}
    try:
        data = json.loads(conf_path.read_text(encoding="utf-8"))
        return {
            "uid": int(data.get("hermes_uid", _DEFAULT_UID)),
            "host": data.get("mqtt_host", _DEFAULT_HOST),
            "port": int(data.get("mqtt_port", _DEFAULT_PORT)),
        }
    except Exception:
        return {"uid": _DEFAULT_UID, "host": _DEFAULT_HOST, "port": _DEFAULT_PORT}


def start_mqtt_listener(
    uid: int | None = None,
    mqtt_host: str | None = None,
    mqtt_port: int | None = None,
) -> None:
    """
    后台线程启动 MQTT 订阅，消息到达自动入队 _inbox_queue。

    幂等：多次调用只启动一次。
    调用点：cli.py 启动时调用一次即可。
    """
    global _listener_started
    if _listener_started:
        return
    if not HAS_PAHO:
        return

    cfg = _read_config()
    _uid = uid if uid is not None else cfg["uid"]
    _host = mqtt_host if mqtt_host is not None else cfg["host"]
    _port = mqtt_port if mqtt_port is not None else cfg["port"]

    if not _uid:
        return

    topic = f"comms/inbox/{_uid}"

    def on_connect(client, userdata, flags, reason_code, properties):
        client.subscribe(topic)

    def on_message(client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
        except Exception:
            return

        from_uid = str(payload.get("from_uid", ""))
        # 跳过自己发的消息
        if from_uid == str(_uid):
            return

        body = payload.get("body", "")
        # 跳过心跳/系统消息
        if body.startswith("收到来自"):
            return

        from_name = payload.get("from", payload.get("from_name", "?"))
        with _queue_lock:
            _inbox_queue.append({
                "from": from_name,
                "from_uid": from_uid,
                "content": body[:500],
                "ts": datetime.now().isoformat(),
                "gid": payload.get("gid", ""),
            })

    def _loop():
        global _mqtt_client
        while True:
            try:
                _mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
                _mqtt_client.on_connect = on_connect
                _mqtt_client.on_message = on_message
                _mqtt_client.connect(_host, _port, 60)
                _mqtt_client.loop_forever()
            except Exception:
                import time
                time.sleep(5)

    t = threading.Thread(target=_loop, daemon=True)
    t.start()
    _listener_started = True


def send_message(to_uid: int, body: str, from_name: str = "Hermes") -> bool:
    """
    ⚠️  内部通道 — 绕过 Hub，消息不进 DB，无聊天记录。

    仅用于 cron 报告、系统通知等程序内部消息。
    Agent 间通信必须用 shell 命令: say <uid> "消息"

    to_uid: 目标 WinPeek uid
    body: 消息正文
    from_name: 发送者显示名
    """
    global _mqtt_client
    if _mqtt_client is None:
        return False
    try:
        import json as _json
        _mqtt_client.publish(
            f"comms/inbox/{to_uid}",
            _json.dumps({
                "from_uid": _read_config()["uid"],
                "from": from_name,
                "body": body,
            }),
            qos=1,
        )
        return True
    except Exception:
        return False


def drain_inbox() -> list[dict]:
    """取出并清空收件队列。调用方负责格式化+展示。"""
    with _queue_lock:
        msgs = _inbox_queue[:]
        _inbox_queue.clear()
    return msgs


def format_inbox_summary(messages: list[dict]) -> str:
    """将新消息格式化为终端可展示的摘要文本。"""
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
