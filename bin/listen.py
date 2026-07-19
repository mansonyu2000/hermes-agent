"""listen — Agent MIM 消息接收器 (自动识人)

启动后持续轮询 MIM 消息，有新消息直接打印到终端。

用法:
  python bin/listen.py          # 一次轮询, 打印未读后退出
  python bin/listen.py --watch  # 持续监听, 每3s轮询, Ctrl+C 退出

身份自动识别 — say.py 同款多源推断算法。
不需要环境变量。
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

    # 2. Walk up from cwd
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
                        d = _read_json(Path("/dev/null"))
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

# ── Poll ──────────────────────────────────────────────────

def poll(uid: int, seen: set[str]) -> list[dict]:
    """Poll for new messages. Returns only unseen ones."""
    try:
        from gateway.winpeek_hub.chat import poll_messages
        msgs = poll_messages(uid)
        new = []
        for m in msgs:
            mid = f"{m.get('from_uid')}-{m.get('content','')}-{m.get('time','')}"
            if mid not in seen:
                seen.add(mid)
                new.append(m)
        return new
    except Exception as e:
        print(f"[listen] poll error: {e}", file=sys.stderr)
        return []


def main():
    watch = "--watch" in sys.argv
    uid, name = _find_identity()
    if not uid:
        print("[listen] ⚠️ 未找到身份, 请设置 WINPEEK_UID 或创建 .winpeek-identity.json", file=sys.stderr)
        sys.exit(1)

    print(f"[listen] ✅ 身份: {name} (uid={uid})", file=sys.stderr)

    seen: set[str] = set()
    running = True

    def _stop(*_):
        nonlocal running
        running = False
    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)

    try:
        msgs = poll(uid, seen)
        for m in msgs:
            from_name = m.get("from_name", "?")
            content = m.get("content", "")
            print(f"\n● {from_name}({m.get('from_uid','?')}) said: {content}\n", flush=True)

        if not watch:
            if not msgs:
                print("[listen] 没有新消息", file=sys.stderr)
            return

        print(f"[listen] 🔄 持续监听中... (每3秒, Ctrl+C 退出)", file=sys.stderr)
        while running:
            time.sleep(3)
            msgs = poll(uid, seen)
            for m in msgs:
                from_name = m.get("from_name", "?")
                content = m.get("content", "")
                print(f"\n● {from_name}({m.get('from_uid','?')}) said: {content}\n", flush=True)

    except KeyboardInterrupt:
        pass
    print("\n[listen] 已退出", file=sys.stderr)


if __name__ == "__main__":
    main()
