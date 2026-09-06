"""
mqtt_adapter.py — MIM MQTT 平台适配器

让 Hermes 通过 MQTT Broker 收发消息，实现多实例互通。

身份自动从 MySQL winpeek-db2.users 表读取，不需要手动设环境变量。
首次启动时自动注册默认身份。

Topic 协议:
  comms/inbox/{uid}   → Agent 订阅, 接收发给自己的消息
  comms/say/{uid}     → Agent 发布, 发送消息给指定 uid
  comms/ack/{uid}     → 消息回执

配置 (.env 或 config.yaml, 可选):
  MIM_BROKER=192.168.3.23   # MQTT Broker 地址 (默认)
  MIM_PORT=1883             # MQTT 端口 (默认)
  MIM_SIGNING_SECRET        # HMAC 签名密钥 (服务端共享), 未配置则跳过签名验证
"""

import hashlib
import hmac
import json
import logging
import os
import socket
import threading
import time
from typing import Optional

try:
    import paho.mqtt.client as mqtt
    HAS_PAHO = True
except ImportError:
    HAS_PAHO = False

logger = logging.getLogger(__name__)

# ── 身份 (从 identity DB 自动读取, 不依赖环境变量) ─────

UID: int = 0
NAME: str = ""
ROLE: str = "Agent"

def _resolve_identity():
    """从环境变量或 identity JSONL 读取身份。无身份时用本机主机名自动注册。

    2026-08-09 修复: 之前直接取 identity DB 第一个身份(=uid=1 yuyangmin 用户),
    导致 serve 的 MQTT adapter 身份=uid=1, 用户发的消息被
    "Guard: skip own messages (from_uid==UID)" 当成"自己发的"丢弃
    → 用户 → Hermes 的消息永不落库/投递。
    现在优先用 MIM_UID/MIM_NAME env(serve 启动时注入 serve 自身 agent 身份,
    如 MIM_UID=2033 MIM_NAME='Claude Code'), env 未设置才回退 identity DB。
    """
    global UID, NAME, ROLE
    try:
        _env_uid = os.getenv("MIM_UID", "").strip()
        if _env_uid.isdigit() and int(_env_uid) > 0:
            UID = int(_env_uid)
            NAME = os.getenv("MIM_NAME", "").strip() or f"serve-{UID}"
            ROLE = os.getenv("MIM_ROLE", "Agent")
            logger.info(f"MIM identity from env: uid={UID} name={NAME} role={ROLE}")
            return
        from gateway.winpeek_hub import identity
        ids = identity.list_all()
        if ids:
            first = ids[0]
            UID = first.get("uid", 0)
            NAME = first.get("nickname", "")
            ROLE = first.get("role", "Agent")
            logger.info(f"MIM identity resolved: uid={UID} name={NAME} ({len(ids)} total)")
        if not UID or not NAME:
            # 自动注册: 主机名 = 昵称
            hostname = socket.gethostname().split(".")[0]
            result = identity.register(hostname, "Agent", hostname)
            if result:
                UID = result["uid"]
                NAME = result["nickname"]
                ROLE = result.get("role", "Agent")
                logger.info(f"MIM identity auto-created: uid={UID} name={NAME}")
    except Exception as e:
        logger.warning(f"MIM identity resolve failed: {e}")

# ── 配置 (仅 Broker 地址可从环境变量覆盖) ──────────────

BROKER = os.getenv("MIM_BROKER", "192.168.3.23")
PORT = int(os.getenv("MIM_PORT", "1883"))

SIGNING_SECRET = os.getenv("MIM_SIGNING_SECRET", "").strip()
SIGNING_ENABLED = bool(SIGNING_SECRET)

# 2026-08-09 多实例隔离: PROD 用 MIM_TOPIC_PREFIX=comms-prod, dev 用 comms/
# 避免远程 dev 实例(3.10)订阅 comms/outbox/# 抢 PROD 的 outbox 消息 → 重复消息。
_TOPIC_PREFIX = os.getenv("MIM_TOPIC_PREFIX", "comms").strip().rstrip("/")
SAY_TOPIC_PREFIX = f"{_TOPIC_PREFIX}/say"
OUTBOX_TOPIC = f"{_TOPIC_PREFIX}/outbox"
GROUP_TOPIC_PREFIX = f"{_TOPIC_PREFIX}/group"
INBOX_TOPIC_PREFIX = f"{_TOPIC_PREFIX}/inbox"
ACK_TOPIC_PREFIX = f"{_TOPIC_PREFIX}/ack"


# ── HMAC 消息签名 ──────────────────────────────────

def _sign_payload(payload: dict, secret: str | None = None) -> dict:
    """Sign a payload with HMAC-SHA256 over canonical fields.

    Canonical string: mid|from_uid|to_uid|body|ts
    Skips gracefully if no secret configured.
    """
    secret = secret or SIGNING_SECRET
    if not secret:
        return payload

    canonical = "|".join([
        str(payload.get("mid", "")),
        str(payload.get("from_uid", "")),
        str(payload.get("to_uid", "")),
        str(payload.get("body", "")),
        str(payload.get("ts", "")),
    ])
    sig = hmac.new(
        secret.encode("utf-8"),
        canonical.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    payload["sig"] = sig
    payload["sig_alg"] = "hmac-sha256"
    return payload


def _verify_payload(payload: dict, secret: str | None = None) -> bool:
    """Verify HMAC signature on a received payload.

    Returns True if signature matches or signing is disabled.
    Returns False if signature is present but invalid.
    """
    secret = secret or SIGNING_SECRET
    if not secret:
        return True  # signing disabled → trust all

    sig = payload.get("sig", "")
    if not sig:
        logger.warning("[MIM SIG] message missing signature, rejected")
        return False

    expected_alg = "hmac-sha256"
    if payload.get("sig_alg") != expected_alg:
        logger.warning("[MIM SIG] unknown sig_alg=%s, rejected", payload.get("sig_alg"))
        return False

    # Re-compute over canonical fields (strip sig/sig_alg before hashing)
    canonical = "|".join([
        str(payload.get("mid", "")),
        str(payload.get("from_uid", "")),
        str(payload.get("to_uid", "")),
        str(payload.get("body", "")),
        str(payload.get("ts", "")),
    ])
    expected = hmac.new(
        secret.encode("utf-8"),
        canonical.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected, sig):
        logger.warning("[MIM SIG] signature mismatch for mid=%s, rejected", payload.get("mid", ""))
        return False

    return True

_client: Optional["mqtt.Client"] = None  # forward ref — paho 可能未安装, 不可在模块级求值 mqtt
_message_handler = None

# Dedup: prevent double‑delivery when local enqueue + MQTT relay both fire
# (same‑machine messages go through both paths after from_uid fix)
_seen_mids: set[str] = set()
_MAX_SEEN_MIDS = 2000


def is_configured() -> bool:
    return UID > 0 and bool(NAME)


def is_available() -> bool:
    return HAS_PAHO and is_configured()


def set_message_handler(handler):
    global _message_handler
    _message_handler = handler


# ── MQTT 回调 ────────────────────────────────────

def _on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        client.subscribe(f"{INBOX_TOPIC_PREFIX}/#", qos=1)
        client.subscribe(f"{OUTBOX_TOPIC}/#", qos=1)
        client.subscribe(f"{GROUP_TOPIC_PREFIX}/#", qos=1)
        client.subscribe(f"{SAY_TOPIC_PREFIX}/#", qos=1)
        logger.info(f"MIM connected {BROKER}:{PORT}, uid={UID} name={NAME} prefix={_TOPIC_PREFIX}")
    else:
        logger.warning(f"MIM connect failed: code={reason_code}")


def _on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
    except json.JSONDecodeError:
        return

    # ── Outbox: Agent → Daemon relay ──
    if msg.topic.startswith(f"{OUTBOX_TOPIC}/"):
        _handle_outbox(msg.topic, payload)
        return

    # ── Say relay: comms/say/{uid} → comms/inbox/{uid} ──
    if msg.topic.startswith(f"{SAY_TOPIC_PREFIX}/"):
        to_uid = int(msg.topic.rsplit("/", 1)[-1])
        if to_uid:
            # 2026-08-09 去重修复: say relay 分支也要检查 mid, 否则
            # 同一条消息(如 QoS 重发/双通配订阅)会 relay 多次 →
            # 用户端看到"自动产生"的重复消息。
            mid = payload.get("mid", "")
            if mid:
                if mid in _seen_mids:
                    logger.debug(f"MIM say relay skip (dup mid={mid})")
                    return
                _seen_mids.add(mid)
                if len(_seen_mids) > _MAX_SEEN_MIDS:
                    _seen_mids.clear()
            payload_str = json.dumps(payload, ensure_ascii=False)
            client.publish(f"{INBOX_TOPIC_PREFIX}/{to_uid}", payload_str, qos=1)
            logger.info(f"MIM say→inbox relay: uid={to_uid}")
            # 2026-08-09 修复: MQTT 直发路径(send_message daemon_alive=False 时)
            # 只 relay 不 enqueue → serve 的 _pending 队列为空 → Hermes 用
            # winpeek_mim_poll 拉不到消息(UI 历史/收信全空)。
            # 当 to_uid 是本 serve 的身份时, 同时 enqueue 到 _pending, 供 WS poll 消费。
            if to_uid == UID:
                try:
                    from gateway.winpeek_hub.chat import enqueue
                    enqueue({
                        "mid": mid or f"mim-{int(time.time()*1000)}",
                        "to_uid": to_uid,
                        "from_uid": payload.get("origin_uid") or payload.get("from_uid", "?"),
                        "from_name": payload.get("origin_name") or payload.get("from", "?"),
                        "content": payload.get("body", payload.get("content", "")),
                        "time": payload.get("ts", payload.get("time", "")),
                    })
                    logger.info(f"MIM say relay enqueue: uid={to_uid} (self)")
                except Exception as e:
                    logger.warning(f"MIM say relay enqueue failed: {e}")
        return

    # ── Signature verification (inbox messages only) ──
    if not _verify_payload(payload):
        logger.warning("[MIM SIG] rejected unsigned/tampered message on topic=%s", msg.topic)
        return

    from_uid = payload.get("from_uid", "")
    from_name = payload.get("from", "?")
    body = payload.get("body", "")
    gid = payload.get("gid")
    mid = payload.get("mid", "")

    # Business‑layer sender: origin_* takes precedence (validated by chat.send_message).
    # from_uid/from are the MQTT publisher identity (adapter) — NOT the sender.
    sender_uid = str(payload.get("origin_uid") or from_uid)
    sender_name = payload.get("origin_name") or from_name

    # Guard: only process messages addressed to our own UID.
    # Without this, any adapter subscribed to comms/inbox/# would receive
    # messages meant for other UIDs — a side effect of wildcard subscription.
    topic_to_uid = ""
    try:
        # topic format: comms/inbox/{uid} or comms/say/{uid} or comms/group/{gid}
        topic_to_uid = msg.topic.rsplit("/", 1)[-1]
    except Exception:
        pass
    if topic_to_uid and topic_to_uid.isdigit() and int(topic_to_uid) != UID:
        return  # not addressed to us — skip

    # Guard: skip own messages (adapter self-relay)
    if str(from_uid) == str(UID):
        return

    # Dedup: skip if we already enqueued this mid locally
    if mid and mid in _seen_mids:
        return
    if mid:
        _seen_mids.add(mid)
        if len(_seen_mids) > _MAX_SEEN_MIDS:
            _seen_mids.clear()  # coarse eviction — safe: >2000 backlog is extreme

    logger.info(f"[{sender_name} ({sender_uid})]: {body[:60]} topic={msg.topic} mid={mid}")

    # Route into chat queue
    try:
        from gateway.winpeek_hub.chat import enqueue
        enqueue({
            "from_uid": int(sender_uid) if str(sender_uid).isdigit() else 0,
            "from_name": sender_name,
            "to_uid": UID,
            "gid": gid,
            "content": body,
            "time": payload.get("ts", time.strftime("%Y-%m-%dT%H:%M:%S")),
        })
    except Exception as e:
        logger.debug(f"_handle_say: enqueue failed: {e}")

    if _message_handler:
        try:
            _message_handler(sender_uid, sender_name, body)
        except Exception as e:
            logger.warning(f"MIM handler error: {e}")


def _handle_outbox(topic: str, payload: dict):
    """Agent 发到 outbox 的消息 → Daemon 补全上下文 → 转发给收件人。

    Topic: comms/outbox/{from_uid}
    Payload: {"to_uid": int, "body": str, "reply_to_mid": str?, "ts": str?}

    全权委托 chat.send_message() 处理：
      DB 归档 → MQTT 发布 → 本地 enqueue → Peeka Router(L1/L2/L3)
    """
    to_uid = int(payload.get("to_uid", 0))
    body = payload.get("body", "")

    if not to_uid or not body:
        logger.warning(f"[outbox] 无效消息: to_uid={to_uid} body={body[:30]}")
        return

    # 从 topic 提取 from_uid
    parts = topic.split("/")
    from_uid_str = parts[-1] if len(parts) > 2 else ""
    try:
        from_uid = int(from_uid_str)
    except (ValueError, TypeError):
        logger.warning(f"[outbox] 无法从 topic 提取 uid: {topic}")
        return

    # 查 identity 补全名称
    from_name = f"user_{from_uid}"
    try:
        from gateway.winpeek_hub import identity
        user = identity.get_by_uid(from_uid)
        if user:
            from_name = user.get("nickname", from_name)
    except Exception as e:
        logger.debug(f"_handle_outbox: identity lookup failed: {e}")

    logger.info(f"[outbox] {from_name}[{from_uid}] → uid={to_uid}: {body[:60]}")

    # 全权委托 chat.send_message() — 它负责 DB+MQQT+enqueue+Peeka Router
    try:
        from gateway.winpeek_hub.chat import send_message as chat_send
        result = chat_send(from_uid, from_name, to_uid, body)
        logger.info(f"[outbox] chat_send result: {result.get('ok')} mid={result.get('mid','')[:20]}")
    except Exception as e:
        logger.warning(f"[outbox] chat_send 失败: {e}")


# ── 连接管理 ──────────────────────────────────────

def connect():
    """连接 MQTT Broker (后台线程, 非阻塞)"""
    global _client
    _resolve_identity()
    if not is_available():
        logger.info(f"MIM skipped: paho={HAS_PAHO} uid={UID} name={NAME}")
        return None

    _client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    _client.on_connect = _on_connect
    _client.on_message = _on_message

    try:
        _client.connect(BROKER, PORT, 60)
        t = threading.Thread(target=_client.loop_forever, daemon=True)
        t.start()
        logger.info(f"MIM started: uid={UID} name={NAME} broker={BROKER}:{PORT}")
        return _client
    except Exception as e:
        logger.warning(f"MIM connect failed: {e}")
        return None


def disconnect():
    global _client
    if _client:
        _client.disconnect()
        _client = None


# ── 发送 ──────────────────────────────────────────

def send_message(target_uid: int, text: str, target_name: str = "",
                 origin_uid: int = 0, origin_name: str = "",
                 mid: str = "") -> bool:
    """Publish to comms/say/{target_uid} (relay handles say→inbox forwarding).

    The adapter always publishes as its own identity (UID/NAME).
    origin_uid/origin_name: the *actual* business‑layer sender — only set by
    chat.send_message() which has already verified the authenticated session.
    Never accept direct caller‑supplied from_uid overrides — that's spoofing.

    mid: message ID for cross‑machine deduplication.
    """
    if not _client or target_uid <= 0:
        return False
    topic = f"{SAY_TOPIC_PREFIX}/{target_uid}"
    # Use origin_name as display sender — never expose adapter identity to receiver
    display_name = origin_name or NAME
    payload = {
        "from_uid": str(UID),
        "from": display_name,
        "to_uid": str(target_uid),
        "body": text,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    if origin_uid:
        payload["origin_uid"] = str(origin_uid)
        payload["origin_name"] = display_name
    if mid:
        payload["mid"] = mid
    # Sign payload for authenticity verification on receiver side
    _sign_payload(payload)
    try:
        payload_str = json.dumps(payload, ensure_ascii=False)
        result = _client.publish(topic, payload_str, qos=1)
        logger.info(f"MIM → {target_name or target_uid}: {text[:60]}")
        return result.rc == mqtt.MQTT_ERR_SUCCESS
    except Exception as e:
        logger.warning(f"MIM send failed: {e}")
        return False


def send_group_message(gid: int, text: str, from_name: str, from_uid: int = 0,
                      mid: str = "") -> bool:
    """Publish group message. Adapter identity is publisher; origin_* is sender."""
    if not _client or gid <= 0:
        return False
    topic = f"{GROUP_TOPIC_PREFIX}/{gid}"
    # Use from_name as display sender — never expose adapter identity to receiver
    display_name = from_name or NAME
    payload = {
        "from_uid": str(UID),
        "from": display_name,
        "gid": gid,
        "body": text,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    if from_uid:
        payload["origin_uid"] = str(from_uid)
        payload["origin_name"] = display_name
    if mid:
        payload["mid"] = mid
    # Sign payload for authenticity verification on receiver side
    _sign_payload(payload)
    try:
        payload_str = json.dumps(payload, ensure_ascii=False)
        result = _client.publish(topic, payload_str, qos=1)
        logger.info(f"MIM → group {gid}: {text[:60]}")
        return result.rc == mqtt.MQTT_ERR_SUCCESS
    except Exception as e:
        logger.warning(f"MIM group send failed: {e}")
        return False


def status() -> dict:
    return {
        "enabled": is_configured(),
        "connected": _client is not None,
        "uid": UID,
        "name": NAME,
        "broker": f"{BROKER}:{PORT}",
    }


def mark_mid_seen(mid: str):
    """Register a mid as already delivered locally.

    Call after local enqueue() so the MQTT relay (same-machine loopback)
    skips this mid — prevents double delivery.
    """
    if mid:
        _seen_mids.add(mid)
        if len(_seen_mids) > _MAX_SEEN_MIDS:
            _seen_mids.clear()
