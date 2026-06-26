"""sendmsg — Hermes 消息适配器

⚠️  STATUS: 未完成，禁止使用。依赖 daemon (也未完成)。
   当前收发请用 say 命令。

设计目标（待以后完善）:
  模板引擎 → 自动识人 → daemon:1880 → MQTT。
  Agent 只需 send(2022, "修好了", event="done")。

用法:
  from hermes_cli.sendmsg import send
  send(2022, "db.js 改了 2 行", event="done", task="Task 1.2")

=== Hermes message adapter ===

三层处理:
  1. 模板引擎 → 根据 event 选模板, 填变量 (快, 确定)
  2. 自动上下文 → git branch/SHA, cwd (自动附加)
  3. [可选] 本地 LLM 润色 → Ollama 通时把短句扩写为完整描述

Agent 只需说"我完成了" + event 标签, adapter 打包一切。
"""
import json, os, socket, subprocess, sys, time
from pathlib import Path

DAEMON = ("127.0.0.1", 1880)

# ── 内置模板 ────────────────────────────────────────────────
# 用户可在 ~/.hermes/data/msg-templates.json 覆盖/新增
_BUILTIN_TEMPLATES: dict[str, dict] = {
    "done": {
        "emoji": "✅",
        "template": "{task} 完成: {summary} [{branch} {sha}]",
    },
    "started": {
        "emoji": "🔧",
        "template": "{task} 开工 [{branch}]",
    },
    "blocked": {
        "emoji": "🚫",
        "template": "{task} 阻塞: {summary} — 需要帮助 [{branch}]",
    },
    "found": {
        "emoji": "🔍",
        "template": "{summary} — 已定位根因 [{branch} {sha}]",
    },
    "revert": {
        "emoji": "⏪",
        "template": "{task} 已回退: {summary} [{branch} {sha}]",
    },
}


def _load_templates() -> dict:
    """内置 + 用户覆盖。"""
    tmpl = dict(_BUILTIN_TEMPLATES)
    user_file = Path.home() / ".hermes" / "data" / "msg-templates.json"
    if user_file.exists():
        try:
            user = json.loads(user_file.read_text(encoding="utf-8"))
            tmpl.update(user)
        except Exception:
            pass
    return tmpl


# ── 身份 ──────────────────────────────────────────────────────

def _read_identity() -> tuple[int, str]:
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


# ── Git 上下文 ────────────────────────────────────────────────

def _git_info() -> dict[str, str]:
    """一次 git 调用拿 branch + SHA。"""
    try:
        branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            stderr=subprocess.DEVNULL, timeout=3,
        ).decode().strip()
        sha = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL, timeout=3,
        ).decode().strip()
        return {"branch": branch, "sha": sha}
    except Exception:
        return {"branch": "?", "sha": "?"}


# ── 本地 LLM 润色 (可选) ──────────────────────────────────────

def _llm_polish(raw: str, event: str) -> str:
    """用 Ollama 小模型把短句扩写为一条完整的上下文消息。

    仅在 Ollama 可达 + 消息很短(<30字)时使用。
    失败静默，返回原文。
    """
    try:
        import urllib.request
        prompt = (
            f"将以下 Agent 工作日志扩写为一条简短汇报 (≤40字, 中文):\n"
            f"事件: {event}\n"
            f"原文: {raw}\n"
            f"要求: 保留关键信息, 不编造, 可补充动作主体(如'修了/加了/改了')。"
        )
        req = urllib.request.Request(
            "http://127.0.0.1:11434/api/generate",
            data=json.dumps({
                "model": "qwen2.5:0.5b",
                "prompt": prompt,
                "stream": False,
            }).encode(),
            headers={"Content-Type": "application/json"},
        )
        resp = urllib.request.urlopen(req, timeout=8)
        result = json.loads(resp.read().decode())
        polished = result.get("response", "").strip()
        if polished and len(polished) < 80:
            return polished
    except Exception:
        pass
    return raw


# ── 格式化 ────────────────────────────────────────────────────

def _format(body: str, event: str | None = None, **kwargs) -> str:
    """模板引擎 + git 上下文。

    如果指定 event，用模板拼装。否则只附 git 信息。
    """
    git = _git_info()
    kwargs.setdefault("summary", body)
    kwargs.setdefault("branch", git["branch"])
    kwargs.setdefault("sha", git["sha"])

    if event:
        tmpl = _load_templates().get(event, {})
        fmt = tmpl.get("template", "{summary} [{branch} {sha}]")
        emoji = tmpl.get("emoji", "")
        try:
            msg = fmt.format(**kwargs)
        except KeyError:
            msg = f"{body} [{git['branch']} {git['sha']}]"
        return f"{emoji} {msg}".strip()
    else:
        # 无 event: 只附 git 上下文 (兼容旧调用)
        if "SHA" not in body and git["sha"] not in body:
            return f"{body} [{git['branch']} {git['sha']}]"
        return body


# ── 发送 ──────────────────────────────────────────────────────

def send(to_uid: int | str, body: str, *,
         event: str | None = None,
         gid: str = "",
         polish: bool = False,
         **kwargs) -> bool:
    """发给 daemon。

    Args:
        to_uid:  目标 uid
        body:    消息原文 (Agent 的自然语言)
        event:   事件标签 → 选模板 (done/started/blocked/found/revert)
        gid:     群 gid
        polish:  是否用本地 LLM 润色 (需要 Ollama)
        **kwargs: 模板变量 (task, summary, branch, sha 等)

    Returns:
        True if sent.

    >>> send(2022, "修好了", event="done", task="Task 1.2")
    → "✅ Task 1.2 完成: 修好了 [dev 97b7d3e]"
    """
    from_uid, from_name = _read_identity()
    if not from_uid:
        print("[sendmsg] 无身份: 创建 ~/.hermes/data/agent.conf", file=sys.stderr)
        return False

    # 模板格式化
    formatted = _format(body, event=event, **kwargs)

    # 可选 LLM 润色 (模板不匹配 或 显式请求)
    if polish and len(body) < 30:
        polished = _llm_polish(body, event or "done")
        if polished and polished != body:
            formatted = _format(polished, event=event, **kwargs)

    msg_payload = {
        "from_uid": from_uid,
        "from_name": from_name,
        "to_uid": int(to_uid),
        "body": formatted,
        "gid": gid,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    try:
        s = socket.create_connection(DAEMON, timeout=2)
        s.sendall((json.dumps(msg_payload) + "\n").encode())
        s.close()
        target = f"gid={gid}" if gid else f"uid={to_uid}"
        print(f"[sendmsg] {from_name}[{from_uid}] → {target}")
        return True
    except Exception as e:
        # 兜底: say.py
        print(f"[sendmsg] daemon 不通, 回退 say: {e}", file=sys.stderr)
        try:
            subprocess.run(
                [sys.executable,
                 str(Path(__file__).parent.parent.parent / "PeekabooWin" / "bin" / "say.py"),
                 str(to_uid), formatted],
                timeout=10,
            )
            return True
        except Exception:
            return False


# ── CLI 入口 ──────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="sendmsg — Hermes 消息适配器")
    p.add_argument("to_uid", help="目标 uid")
    p.add_argument("text", help="消息内容")
    p.add_argument("--event", "-e", help="事件标签 (done/started/blocked/found/revert)")
    p.add_argument("--gid", "-g", default="")
    p.add_argument("--polish", action="store_true", help="本地 LLM 润色")
    p.add_argument("--task", help="任务 ID")
    args = p.parse_args()

    kwargs = {}
    if args.task:
        kwargs["task"] = args.task

    send(args.to_uid, args.text, event=args.event, gid=args.gid,
         polish=args.polish, **kwargs)
