"""
Hermes WinPeek 收件箱检查器

被 watch 触发后，inbox-reader.js 写入 agent-2022-messages.json。
本模块读取该文件，将新消息注入 Hermes chat 上下文。

用法:
    from hermes_cli.winpeek_inbox import check_inbox
    new_msgs = check_inbox()
    # new_msgs -> [{"from": "...", "content": "...", "ts": "..."}, ...]
"""

import json
import os
from pathlib import Path
from datetime import datetime

INBOX_FILE = Path.home() / ".winpeek-prod" / "agent-2022-messages.json"
LAST_READ_FILE = Path.home() / ".winpeek-prod" / "agent-2022-last-read.txt"


def check_inbox() -> list[dict]:
    """读取 WinPeek 收件箱，返回自上次读取后的新消息。"""
    if not INBOX_FILE.exists():
        return []

    try:
        data = json.loads(INBOX_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []

    last_ts = _get_last_read()
    new_messages = []

    # inbox 条目 (最近5条，格式: {ts, from_uid, from_name, body})
    for entry in data.get("inbox", []):
        entry_ts = entry.get("ts", "")
        if entry_ts > last_ts:
            new_messages.append({
                "from": entry.get("from_name") or f"uid:{entry.get('from_uid', '?')}",
                "content": entry.get("body", ""),
                "ts": entry_ts,
            })

    # pending messages (来自 chat 表的聚合，格式: {from_uid, messages, count, latest})
    for msg_group in data.get("messages", []):
        group_latest = msg_group.get("latest", "")
        if group_latest and group_latest > last_ts:
            # 把聚合的消息拆成独立条目
            parts = msg_group.get("messages", "").split(" | ")
            for part in parts:
                if part.strip():
                    new_messages.append({
                        "from": f"uid:{msg_group.get('from_uid', '?')}",
                        "content": part.strip(),
                        "ts": group_latest,
                    })

    # 更新最后读取时间
    if new_messages:
        _set_last_read(data.get("ts", datetime.now().isoformat()))

    return new_messages


def _get_last_read() -> str:
    try:
        return LAST_READ_FILE.read_text(encoding="utf-8").strip()
    except Exception:
        return "1970-01-01"


def _set_last_read(ts: str) -> None:
    try:
        LAST_READ_FILE.parent.mkdir(parents=True, exist_ok=True)
        LAST_READ_FILE.write_text(ts, encoding="utf-8")
    except Exception:
        pass


def format_inbox_summary(messages: list[dict]) -> str:
    """将新消息格式化为可展示的摘要文本。"""
    if not messages:
        return ""

    lines = ["\n📬 WinPeek 新消息:"]
    for msg in messages[-10:]:  # 最多显示10条
        ts = msg.get("ts", "")[:19].replace("T", " ")
        content = msg.get("content", "")[:100]
        lines.append(f"  [{ts}] {msg['from']}: {content}")
    return "\n".join(lines)


# ── 独立运行: python -m hermes_cli.winpeek_inbox ──
if __name__ == "__main__":
    msgs = check_inbox()
    if msgs:
        print(format_inbox_summary(msgs))
        print(f"\n共 {len(msgs)} 条新消息")
    else:
        print("📭 WinPeek 收件箱为空")
