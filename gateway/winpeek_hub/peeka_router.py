"""
peeka_router.py — Peeka message routing engine.

Three‑layer routing decision for incoming MIM messages:

  Layer 1: Greeting template matching (0 Token, daemon auto‑reply)
  Layer 2: Daemon local knowledge (0 Token, daemon answers from state)
  Layer 3: Forward to target Agent (LLM decides via its own MCP tools)
"""

import json
import logging
import socket
from typing import Optional

logger = logging.getLogger(__name__)

# ── 5‑class message classifier ─────────────────

AD_KEYWORDS = ["推广", "招商", "营销", "广告", "促销", "优惠", "限时", "免费领取"]
GREETING_KEYWORDS = ["早安", "晚安", "谢谢", "多谢", "在吗", "在不在", "你好", "hello",
                     "吃了没", "吃饭了吗", "好久不见"]
NOTIFICATION_KEYWORDS = ["版本", "更新", "告警", "通知", "公告", "上线", "离线", "提醒"]
REQUEST_MARKERS = ["什么", "怎么", "如何", "为什么", "帮我", "查一下", "看一下",
                   "检查", "能不能", "可以", "请", "?"]

def classify(body: str) -> str:
    """Classify a message body into one of 5 categories.

    Returns: 'greeting' | 'notification' | 'advertisement' | 'request' | 'other'
    """
    b = body.strip()
    if not b:
        return "other"

    # 1. Advertisement filter (highest priority — drop silently)
    for kw in AD_KEYWORDS:
        if kw in b:
            return "advertisement"

    # 2. Greeting
    for kw in GREETING_KEYWORDS:
        if kw in b:
            return "greeting"

    # 3. Notification
    for kw in NOTIFICATION_KEYWORDS:
        if kw in b:
            return "notification"

    # 4. Request (check for question markers)
    for marker in REQUEST_MARKERS:
        if marker in b:
            return "request"

    # 5. Default: short messages are likely greetings, long ones are requests
    if len(b) <= 5:
        return "greeting"
    return "request"


# ── Layer 1: greeting auto‑reply ───────────────

def _match_greeting(body: str) -> Optional[str]:
    """Try to match body against greeting templates (delegates to daemon)."""
    try:
        from apps.winpeek_injector.daemon import match_greeting as _daemon_match
        return _daemon_match(body)
    except ImportError:
        return None


# ── Layer 2: daemon local knowledge ────────────

DAEMON_KNOWLEDGE = {
    "agent_list": lambda state, **kw:
        f"本机发现 {len(state.get('runtimes', []))} 个 Agent"
        if state.get("runtimes")
        else "暂未发现本机 Agent",
    "machine_name": lambda **kw: socket.gethostname(),
    "machine": lambda **kw: socket.gethostname(),
    "谁在": lambda state, body, **kw:
        _answer_who(state, body),
    "有哪些": lambda state, body, **kw:
        f"本机 Agent: {', '.join(r['agent_type'] for r in state.get('runtimes', []))}"
        if state.get("runtimes")
        else "暂未发现",
}

def _answer_who(state: dict, body: str) -> str:
    """Answer questions like '谁在' / '你是谁' etc."""
    runtimes = state.get("runtimes", [])
    if not runtimes:
        return "我是 Peeka Daemon，暂未发现本机已注册的 Agent。"
    types = ", ".join(r["agent_type"] for r in runtimes)
    return f"我是 Peeka Daemon，本机已注册 Agent: {types}"

def daemon_known(state: dict, body: str) -> Optional[str]:
    """Check if daemon can answer from local knowledge. Returns answer or None."""
    for pattern, handler in DAEMON_KNOWLEDGE.items():
        if pattern in body:
            try:
                return handler(state=state, body=body)
            except Exception:
                continue
    return None


# ── Layer 3: context assembly ──────────────────

def _get_daemon_state() -> dict:
    """Get daemon state safely."""
    try:
        from apps.winpeek_injector.daemon import get_local_state
        return get_local_state()
    except ImportError:
        return {"machine": socket.gethostname(), "runtimes": []}


def _get_peeka_name(uid: int) -> str:
    """Lookup peeka_name for a uid."""
    try:
        from gateway.winpeek_hub import identity
        user = identity.get_by_uid(uid)
        if user:
            return user.get("peeka_name", "")
    except Exception:
        pass
    return ""


def _derive_relation(from_peeka: str, to_peeka: str) -> str:
    """Derive relationship from PeekaNames."""
    if not from_peeka or not to_peeka:
        return "unknown"
    f_host = from_peeka.split("-")[1] if "-" in from_peeka else ""
    t_host = to_peeka.split("-")[1] if "-" in to_peeka else ""
    if f_host and f_host == t_host:
        return "same_machine"
    f_domain = from_peeka.split("hotime.cn")[0] if "hotime.cn" in from_peeka else ""
    t_domain = to_peeka.split("hotime.cn")[0] if "hotime.cn" in to_peeka else ""
    if f_domain and f_domain == t_domain:
        return "same_org"
    return "external"


def assemble_context(from_uid: int, to_uid: int, body: str, tag: str) -> dict:
    """Assemble context payload for layer‑3 forwarding."""
    from_peeka = _get_peeka_name(from_uid)
    to_peeka = _get_peeka_name(to_uid)
    relation = _derive_relation(from_peeka, to_peeka)

    # Get some history (recent messages between this pair)
    history = []
    try:
        from gateway.winpeek_hub.chat import get_history
        msgs = get_history(to_uid, from_uid, limit=5)
        if msgs:
            history = [{"from": m["from_uid"], "content": m["content"]}
                       for m in msgs if isinstance(m, dict)]
    except Exception:
        pass

    return {
        "peer_uid": from_uid,
        "peeka_name": from_peeka,
        "relation": relation,
        "tag": tag,
        "history_count": len(history),
        "history": history,
    }


# ── Main routing entry point ───────────────────

def route_incoming(from_uid: int, to_uid: int, body: str) -> dict:
    """Route an incoming message through the 3‑layer system.

    Returns a dict with:
      - action: 'auto_reply' | 'daemon_answer' | 'forward' | 'drop'
      - reply: str (for auto_reply / daemon_answer)
      - context: dict (for forward)
      - tag: str (message classification)
    """
    tag = classify(body)

    # ── Drop advertisements ──
    if tag == "advertisement":
        logger.info(f"[Peeka] drop ad from={from_uid} body={body[:30]}")
        return {"action": "drop", "tag": tag, "reply": ""}

    # ── Layer 1: greeting auto‑reply ──
    if tag == "greeting":
        reply = _match_greeting(body)
        if reply:
            logger.info(f"[Peeka] layer1 from={from_uid} to={to_uid} reply={reply}")
            return {"action": "auto_reply", "tag": tag, "reply": reply}

    # ── Layer 2: daemon local knowledge ──
    state = _get_daemon_state()
    answer = daemon_known(state, body)
    if answer:
        logger.info(f"[Peeka] layer2 from={from_uid} to={to_uid} answer={answer}")
        return {"action": "daemon_answer", "tag": tag, "reply": answer}

    # ── Layer 3: forward to Agent ──
    ctx = assemble_context(from_uid, to_uid, body, tag)
    logger.info(f"[Peeka] layer3 from={from_uid} to={to_uid} tag={tag}")
    return {"action": "forward", "tag": tag, "reply": "", "context": ctx}
