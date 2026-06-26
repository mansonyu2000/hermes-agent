"""sendmsg — Hermes 内部消息客户端 → 发给本地 daemon

Hermes 内的 Agent 代码调用这个，不需要管 MQTT/身份/通道。

用法:
  python -m hermes_cli.sendmsg <to_uid> "消息"
  python -m hermes_cli.sendmsg 2022 "done, SHA a62eb1b"

=== Hermes message adapter ===
sendmsg 自动附带上下文:
  - from_uid / from_name → 从 agent.conf 读
  - 当前 git branch + HEAD SHA (如果在 repo 内)
  - 调用 cwd

Agent 只需要说"我完成了"，adapter 自动拼完整上下文。
"""
import json, os, socket, subprocess, sys, time
from pathlib import Path

DAEMON = ("127.0.0.1", 11884)


def _read_identity() -> tuple[int, str]:
    """从 agent.conf 读 Hermes 身份。"""
    for conf in (
        Path.home() / ".hermes" / "data" / "agent.conf",
        Path.home() / ".winpeek" / "agent.conf",
    ):
        if conf.exists():
            try:
                d = json.loads(conf.read_text(encoding="utf-8"))
                uid = int(d.get("hermes_uid") or 0)
                if uid:
                    return uid, d.get("agent_name") or d.get("name") or "Hermes"
            except Exception:
                pass
    env_uid = os.environ.get("WINPEEK_UID")
    if env_uid:
        return int(env_uid), os.environ.get("WINPEEK_NAME") or "Hermes"
    return 0, "Hermes"


def _git_context() -> str:
    """自动获取当前 git 上下文。"""
    try:
        branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            stderr=subprocess.DEVNULL, timeout=3,
        ).decode().strip()
        sha = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL, timeout=3,
        ).decode().strip()
        return f"[{branch} {sha}]"
    except Exception:
        return ""


def send(to_uid: int | str, body: str, gid: str = "") -> bool:
    """发给 daemon。1 行代码，自动带身份+上下文。"""
    from_uid, from_name = _read_identity()
    if not from_uid:
        print("[sendmsg] 无身份: 创建 ~/.hermes/data/agent.conf", file=sys.stderr)
        return False

    git_ctx = _git_context()
    if git_ctx and git_ctx not in body:
        body = f"{body} {git_ctx}"

    msg = {
        "from_uid": from_uid,
        "from_name": from_name,
        "to_uid": int(to_uid),
        "body": body,
        "gid": gid,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    try:
        s = socket.create_connection(DAEMON, timeout=2)
        s.sendall((json.dumps(msg) + "\n").encode())
        s.close()
        target = f"gid={gid}" if gid else f"uid={to_uid}"
        print(f"[sendmsg] {from_name}[{from_uid}] → {target}")
        return True
    except Exception as e:
        # Fallback: 直接走 say.py
        print(f"[sendmsg] daemon 不通, 回退 say: {e}", file=sys.stderr)
        try:
            import __import__ as _imp
            subprocess.run(
                [sys.executable, str(Path(__file__).parent.parent.parent / "PeekabooWin" / "bin" / "say.py"),
                 str(to_uid), body],
                timeout=10,
            )
            return True
        except Exception:
            return False


# CLI 入口
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python -m hermes_cli.sendmsg <to_uid> <消息>", file=sys.stderr)
        sys.exit(1)
    send(sys.argv[1], " ".join(sys.argv[2:]))
