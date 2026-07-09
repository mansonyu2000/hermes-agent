#!/usr/bin/env python3
"""
Hermes Agent → AgentMemory Shell Hook Bridge

Reads the Hermes shell-hook JSON payload from stdin and forwards selected
events to the AgentMemory REST API (POST /agentmemory/remember).

Supported events:
  - post_tool_call  → records tool name, status, duration
  - on_session_start → records session metadata
  - on_session_end   → records session-end summary

Configuration (via env vars or defaults):
  AGENTMEMORY_URL     – http://192.168.3.9:3111
  AGENTMEMORY_SECRET  – agentmemory-wuhai-2026
  AGENTMEMORY_SLOTS   – hermes-agent
  AGENTMEMORY_TIMEOUT – 5 (seconds)

Exit: 0 always (hooks must never crash the agent).
"""

from __future__ import annotations

import json
import os
import sys
import traceback
import urllib.request
from datetime import datetime, timezone

# ── Config ────────────────────────────────────────────────────────────

AGENTMEMORY_URL = os.environ.get(
    "AGENTMEMORY_URL", "http://192.168.3.9:3111"
)
AGENTMEMORY_SECRET = os.environ.get(
    "AGENTMEMORY_SECRET", "agentmemory-wuhai-2026"
)
AGENTMEMORY_SLOTS = os.environ.get(
    "AGENTMEMORY_SLOTS", "hermes-agent"
)
AGENTMEMORY_TIMEOUT = int(os.environ.get("AGENTMEMORY_TIMEOUT", "5"))

REMEMBER_URL = f"{AGENTMEMORY_URL.rstrip('/')}/agentmemory/remember"

# ── Event filters ─────────────────────────────────────────────────────

# Tool names whose calls we always record (file I/O, shell, etc.)
RECORD_TOOLS = {
    "read_file", "write_file", "edit_file", "delete_file",
    "terminal", "bash", "shell",
    "browser_navigate", "browser_click",
    "web_search", "web_fetch",
    "remember", "recall", "recap", "handoff",  # agentmemory self-calls
}

# Maximum content length for tool_input/result in the memory text
MAX_CONTENT_LEN = 200


# ── Helpers ───────────────────────────────────────────────────────────

def _send_memory(content: str, tags: list[str] | None = None) -> bool:
    """POST a remember entry to AgentMemory. Returns True on success."""
    payload = json.dumps({
        "content": content,
        "tags": tags or [],
    }).encode("utf-8")

    req = urllib.request.Request(
        REMEMBER_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {AGENTMEMORY_SECRET}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=AGENTMEMORY_TIMEOUT) as resp:
            return 200 <= resp.status < 300
    except Exception:
        # Hook failures must be silent — never crash the agent.
        return False


def _truncate(s: str, n: int = MAX_CONTENT_LEN) -> str:
    """Truncate a string for memory content."""
    if len(s) <= n:
        return s
    return s[:n - 3] + "..."


def _tool_input_summary(tool_input: dict | None) -> str:
    """Create a short summary of the tool input for memory recording."""
    if not tool_input:
        return ""
    if isinstance(tool_input, dict):
        # Prioritize common fields
        for key in ("command", "path", "file_path", "url", "query"):
            if key in tool_input:
                val = str(tool_input[key])
                return _truncate(val)
        # Fallback: first key-value
        first_key = next(iter(tool_input), None)
        if first_key:
            return _truncate(f"{first_key}: {tool_input[first_key]}")
    return _truncate(str(tool_input))


# ── Event handlers ────────────────────────────────────────────────────

def handle_post_tool_call(payload: dict) -> None:
    """Record a tool call result to AgentMemory."""
    tool_name = payload.get("tool_name", "unknown")
    tool_input = payload.get("tool_input") or payload.get("extra", {}).get("args", {})
    extra = payload.get("extra", {})
    status = extra.get("status", "ok")
    duration_ms = extra.get("duration_ms", 0)
    error_msg = extra.get("error_message", "")

    if tool_name not in RECORD_TOOLS:
        return

    summary = _tool_input_summary(tool_input)
    msg_parts = [f"[{tool_name}]"]
    if summary:
        msg_parts.append(summary)
    msg_parts.append(f"→ {status}")
    if duration_ms:
        msg_parts.append(f"({duration_ms}ms)")
    if error_msg:
        msg_parts.append(f"err: {_truncate(error_msg)}")

    content = " ".join(msg_parts)
    _send_memory(content, tags=[tool_name, "hook", status])


def handle_on_session_start(payload: dict) -> None:
    """Record session start to AgentMemory."""
    extra = payload.get("extra", {})
    model = extra.get("model", "unknown")
    platform = extra.get("platform", "unknown")
    session_id = payload.get("session_id", "")

    content = (
        f"🟢 Session started | model={model} | platform={platform}"
    )
    if session_id:
        content += f" | session={_truncate(session_id, 20)}"

    _send_memory(content, tags=["session", "start", platform])


def handle_on_session_end(payload: dict) -> None:
    """Record session end to AgentMemory."""
    extra = payload.get("extra", {})
    completed = extra.get("completed", False)
    interrupted = extra.get("interrupted", False)
    model = extra.get("model", "unknown")

    if interrupted:
        state = "⏸️ interrupted"
    elif completed:
        state = "✅ completed"
    else:
        state = "🔴 ended"

    content = f"{state} | model={model}"
    _send_memory(content, tags=["session", "end"])


# ── Dispatch ──────────────────────────────────────────────────────────

EVENT_HANDLERS = {
    "post_tool_call": handle_post_tool_call,
    "on_session_start": handle_on_session_start,
    "on_session_end": handle_on_session_end,
}


def main() -> None:
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return
        payload = json.loads(raw)
    except (json.JSONDecodeError, Exception):
        return

    event = payload.get("hook_event_name", "")
    handler = EVENT_HANDLERS.get(event)

    if handler is None:
        return

    try:
        handler(payload)
    except Exception:
        # Never crash the agent — hooks are best-effort.
        traceback.print_exc(file=sys.stderr)


if __name__ == "__main__":
    main()
