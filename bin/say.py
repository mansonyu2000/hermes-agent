"""say — Agent MQTT 消息 (自动识人)

用法:
  say <to_uid> "消息内容"
  say 2022 "done, SHA a62eb1b"
  say 2022 "报到" --gid 1048

身份自动识别 — 不需要 --uid，不用设环境变量。
say 自动从配置文件推断"谁在说话"。
"""
import sys, json, time, os, argparse
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

import paho.mqtt.client as mqtt


# ── 身份自动发现 ──────────────────────────────────────────────

def _sys_name() -> str:
    return (os.environ.get("WINPEEK_NAME") or
            os.environ.get("WINPEEK_NICK") or
            os.environ.get("USERNAME") or
            os.environ.get("USER") or "anonymous")


def _read_json(path: Path) -> dict:
    try: return json.loads(path.read_text(encoding="utf-8"))
    except Exception: return {}


def _find_identity() -> tuple[int, str]:
    """自动推断发送者 (uid, name)。

    查找顺序:
      1. WINPEEK_IDENTITY 环境变量 → JSON 文件
      2. cwd 往上找 .winpeek-identity.json (项目级)
      3. ~/.hermes/data/agent.conf (Hermes — 默认身份)
      4. ~/.claude/winpeek-identity.json (CC 兜底)
      5. WINPEEK_UID 环境变量
    """

    # 1. 显式指向
    id_file = os.environ.get("WINPEEK_IDENTITY")
    if id_file:
        for f in (Path(id_file).expanduser(),):
            if f.exists():
                d = _read_json(f)
                uid = int(d.get("uid") or d.get("hermes_uid") or 0)
                if uid:
                    return uid, d.get("name") or d.get("agent_name") or _sys_name()

    # 2. 从 cwd 往上找
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

    # 3. Hermes agent.conf (默认身份 — 机器的主人)
    for conf in (
        Path.home() / ".hermes" / "data" / "agent.conf",
        Path.home() / ".winpeek" / "agent.conf",
    ):
        if conf.exists():
            d = _read_json(conf)
            uid = int(d.get("hermes_uid") or 0)
            if uid:
                return uid, (d.get("agent_name") or d.get("name") or
                             os.environ.get("WINPEEK_NAME") or _sys_name())

    # 4. CC 身份兜底
    cc = Path.home() / ".claude" / "winpeek-identity.json"
    if cc.exists():
        d = _read_json(cc)
        uid = int(d.get("uid") or 0)
        if uid:
            return uid, d.get("name") or _sys_name()

    # 5. 环境变量
    env_uid = os.environ.get("WINPEEK_UID")
    if env_uid:
        return int(env_uid), _sys_name()

    return 0, _sys_name()


# ── 发送 ──────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="say — Agent MQTT 消息")
    parser.add_argument("to_uid", help="目标 uid")
    parser.add_argument("text", help="消息内容")
    parser.add_argument("--gid", "-g", help="群 gid", default="")
    parser.add_argument("--uid", "-u", type=int, default=None)
    parser.add_argument("--name", "-n", default=None)
    args = parser.parse_args()

    auto_uid, auto_name = _find_identity()
    from_uid = args.uid if args.uid else auto_uid
    from_name = args.name if args.name else auto_name

    if not from_uid:
        print("[say] 找不到发送者 uid", file=sys.stderr)
        print("  创建 ~/.hermes/data/agent.conf: {\"hermes_uid\": YOUR_UID}", file=sys.stderr)
        sys.exit(1)

    payload = {
        "from": from_name, "from_uid": from_uid,
        "to_uid": args.to_uid, "body": args.text,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    if args.gid:
        payload["gid"] = args.gid

    host = os.environ.get("MQTT_HOST", "192.168.3.23")

    # 方案A: MQTT
    try:
        c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        c.connect(host, 1883, 5)
        c.publish(f"comms/say/{args.to_uid}", json.dumps(payload), qos=1)
        c.disconnect()
        target = f"gid={args.gid}" if args.gid else f"uid={args.to_uid}"
        print(f"[say] {from_name}[{from_uid}] → {target}")
    except Exception as e:
        # 方案B: REST API 兜底
        hub = os.environ.get("WINPEEK_HUB", "http://192.168.3.44:2000")
        try:
            __import__("urllib.request").request.urlopen(
                __import__("urllib.request").request.Request(
                    f"{hub}/api/chat/post",
                    data=json.dumps({
                        "from_node": str(from_uid),
                        "from_name": from_name,
                        "to_node": str(args.to_uid),
                        "content": args.text,
                    }).encode(),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                ),
                timeout=10,
            )
            print(f"[say-API] {from_name}[{from_uid}] → uid={args.to_uid}")
        except Exception as e2:
            print(f"[say] 失败: MQTT={e} API={e2}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
