"""listen — Agent MIM 消息接收器 (自动识人)

启动后通过 MQTT 独立收信, 不受前端轮询影响。

用法:
  python bin/listen.py          # 持续监听, Ctrl+C 退出
  python bin/listen.py --once   # 收一条消息后退出

消息通过 MQTT publish/subscribe 分发 — 每个 Agent 订阅自己的
comms/say/{uid} 和 comms/group/{gid} topic — 独立收件, 不与前端共享队列.

身份自动识别 — say.py 同款多源推断算法。
不需要环境变量.
"""

import json
import os
import signal
import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

try:
    import paho.mqtt.client as mqtt
except ImportError:
    print("[listen] 需要 paho-mqtt: pip install paho-mqtt", file=sys.stderr)
    sys.exit(1)

# ── Identity auto-discovery (same algorithm as say.py) ──────

def _sys_name() -> str:
    return (os.environ.get("WINPEEK_NAME") or
            os.environ.get("WINPEEK_NICK") or
            os.environ.get("USERNAME") or
            os.environ.get("USER") or "anonymous")

def _read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}

def _find_identity() -> tuple[int, str]:
    # 1. WINPEEK_IDENTITY env
    id_file = os.environ.get("WINPEEK_IDENTITY")
    if id_file:
        f = Path(id_file).expanduser()
        if f.exists():
            d = _read_json(f)
            uid = int(d.get("uid") or d.get("hermes_uid") or 0)
            if uid:
                return uid, d.get("name") or d.get("agent_name") or _sys_name()

    # 2. MIM_UID + MIM_NAME (Daemon 注入, 权威)
    mim_uid = int(os.environ.get("MIM_UID", "0"))
    if mim_uid:
        return mim_uid, os.environ.get("MIM_NAME", "") or _sys_name()

    # 3. Walk up from cwd
    try:
        for p in [Path.cwd()] + list(Path.cwd().parents)[:6]:
            idf = p / ".winpeek-identity.json"
            if idf.exists():
                d = _read_json(idf)
                uid = int(d.get("uid") or 0)
                if uid:
                    return uid, d.get("name") or _sys_name()
    except Exception:
        pass

    # 3. Hermes agent.conf or winpeek identity
    for conf in (
        Path.home() / ".hermes" / "data" / "agent.conf",
        Path.home() / ".hermes" / "winpeek" / "data" / "identities.jsonl",
    ):
        if conf.exists():
            try:
                if conf.suffix == ".jsonl":
                    for line in conf.read_text(encoding="utf-8").strip().split("\n"):
                        try:
                            d = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        uid = int(d.get("uid") or 0)
                        if uid:
                            return uid, d.get("nickname") or d.get("name") or _sys_name()
                else:
                    d = _read_json(conf)
                    uid = int(d.get("hermes_uid") or d.get("uid") or 0)
                    if uid:
                        return uid, d.get("agent_name") or d.get("name") or _sys_name()
            except Exception:
                pass

    # 4. WINPEEK_UID env
    env_uid = int(os.environ.get("WINPEEK_UID", "0"))
    if env_uid:
        return env_uid, os.environ.get("WINPEEK_NAME", "") or _sys_name()

    # 5. From MySQL (if available)
    try:
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from gateway.winpeek_hub import identity
        hostname = os.environ.get("HOSTNAME", _sys_name())
        ids = identity.list_all()
        for i in ids:
            if i.get("nickname") == hostname:
                return i["uid"], i["nickname"]
        if ids:
            return ids[0]["uid"], ids[0]["nickname"]
    except Exception:
        pass

    return 0, ""

# ── MQTT Listener ─────────────────────────────────────────

def _on_connect(client, userdata, flags, reason_code, _properties):
    if reason_code == 0:
        uid = userdata['uid']
        # say.py publishes to comms/say/{uid} — this is the primary peer-to-peer channel
        client.subscribe(f"comms/say/{uid}", qos=1)
        client.subscribe(f"comms/inbox/{uid}", qos=1)
        print(f"[listen] ✅ 已连接 MQTT broker, 监听 say/inbox 频道 (uid={uid})", file=sys.stderr, flush=True)
    else:
        print(f"[listen] ❌ MQTT 连接失败 code={reason_code}", file=sys.stderr, flush=True)

def _on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode("utf-8", errors="replace"))
    except json.JSONDecodeError:
        return
    from_uid = payload.get("from_uid") or payload.get("from_node", "?")
    from_name = payload.get("from") or payload.get("from_name", "?")
    body = payload.get("body") or payload.get("content", "")
    gid = payload.get("gid")
    location = f"群{gid}" if gid else f"uid={from_uid}"
    print(f"\n● {from_name}({location}) said: {body}\n", flush=True)


def main():
    uid, name = _find_identity()
    if not uid:
        print("[listen] ⚠️ 未找到身份, 退出", file=sys.stderr)
        sys.exit(1)

    once = "--once" in sys.argv
    broker = os.environ.get("MQTT_HOST", "192.168.3.23")
    port = int(os.environ.get("MQTT_PORT", "1883"))

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.user_data_set({"uid": uid, "name": name})
    client.on_connect = _on_connect
    client.on_message = _on_message

    print(f"[listen] 🆔 {name} (uid={uid}) broker={broker}", file=sys.stderr, flush=True)
    client.connect(broker, port, 60)

    if once:
        client.loop_start()
        time.sleep(5)
        client.loop_stop()
        client.disconnect()
        return

    print("[listen] 🔄 持续监听中... (Ctrl+C 退出)", file=sys.stderr, flush=True)
    try:
        client.loop_forever()
    except KeyboardInterrupt:
        pass
    finally:
        client.disconnect()
        print("\n[listen] 已退出", file=sys.stderr)


if __name__ == "__main__":
    main()
