---
sidebar_label: "Build MIM Messaging"
title: "Build the MIM Messaging Feature"
description: "Step-by-step guide to building the Multi-Agent Instant Messaging feature — architecture, message flow, tool registration, and deployment"
---

# Build MIM — Multi-Agent Instant Messaging

This is a **worked example** of adding a feature to WinPeek, following the [WinPeek development guide](./winpeek-development.md). Use it as a reference when building other features.

## What You're Building

Multi-agent instant messaging over MQTT. Two Hermes agents can send text messages to each other in real time.

```
Agent A (uid=2022)                    Agent B (uid=2027)
     │                                      │
     │ say 2027 "task done"                 │
     ↓                                      │
  MQTT publish comms/say/2027               │
     ↓                                      │
  MQTT Broker (192.168.3.23:1883)           │
     │                                      │
     └────→ comms/inbox/2027 ──────────────→│
                                            ↓
                                     winpeek_mim_poll picks it up
                                     "Agent A: task done"
```

## Architecture

```
Desktop UI (apps/desktop/.../winpeek/mim/index.tsx)
    ↑ useGatewayRequest() — Hermes IPC bridge
    │
tools/winpeek_tools.py     ← 4 MIM tools registered here
    │
    ├─→ winpeek_mim_login    → identity.register() / login()
    ├─→ winpeek_mim_send     → chat.send_message() + MQTT publish
    ├─→ winpeek_mim_poll     → read memory queue (MQTT received msgs)
    └─→ winpeek_mim_contacts → identity.list_all() + online status
    │
gateway/winpeek_hub/         ← MIM backend engine
    │
    ├─ identity.py    ✅  Register / login / list (JSONL)
    ├─ mqtt_adapter.py ✅  MQTT connect / publish / on_message
    ├─ chat.py        🆕  Message CRUD (SQLite), memory queue
    ├─ hub.py         🆕  Node registry, heartbeat, dead detection
    ├─ archive.py     ✅  Message archive (MySQL/JSONL)
    ├─ hub_bridge.py  ✅  Gateway lifecycle hooks
    ├─ routing.py     ✅  Cross-platform routing
    └─ tenant.py      ✅  Multi-tenant management
    │
MQTT Broker (192.168.3.23:1883)
    ├─ comms/say/{uid}      — agent publishes to send
    ├─ comms/inbox/{uid}    — broker publishes to deliver
    └─ comms/ack/{uid}      — agent publishes to confirm receipt
```

## Files Involved

| File | Status | What it does |
|------|--------|-------------|
| `gateway/winpeek_hub/identity.py` (91 lines) | ✅ | Register, login, list all identities. Stores to `~/.hermes/winpeek/identities.jsonl`. |
| `gateway/winpeek_hub/mqtt_adapter.py` (189 lines) | ✅ | Connect to MQTT broker, send/receive messages. Subscribes to `comms/inbox/{uid}`. Needs `+queue` patch for polling. |
| `gateway/winpeek_hub/chat.py` | 🆕 | Message engine. `send_message()` writes to SQLite + publishes to MQTT. `poll_messages()` returns queued messages. `get_contacts()` returns list with online status. |
| `tools/winpeek_tools.py` | 📝 | Register 4 MIM tools alongside existing WeChat tools. |
| `apps/desktop/.../winpeek/mim/index.tsx` (371 lines) | 📝 | Chat UI. Currently uses mock data. Replace 4 sections with real API calls. |

## Step 1: Understand the Message Flow

### Sending a message

```
1. User types "hello" in frontend, clicks Send
2. Frontend calls winpeek_mim_send(to_uid=2027, body="hello")
3. winpeek_mim_send handler:
   a. chat.send_message(from_uid=self, to_uid=2027, body="hello")
      → writes to SQLite (for history)
   b. mqtt_adapter.send_message(target_uid=2027, text="hello")
      → MQTT publish to comms/say/2027
4. MQTT Broker receives it
5. Broker publishes to comms/inbox/2027 (Agent B subscribed)
6. Agent B's mqtt_adapter._on_message() fires
   → appends message to `_pending_messages` queue
7. Agent B's frontend polls winpeek_mim_poll every 3 seconds
   → reads and clears `_pending_messages`
   → displays new message
```

### Receiving a message

```
MQTT Broker → comms/inbox/{my_uid}
  → mqtt_adapter._on_message(client, userdata, msg)
    → parse JSON { from_uid, from, body, ts }
    → skip if from_uid == my_uid (echo rejection)
    → append to _pending_messages list

Frontend (every 3 seconds):
  → call winpeek_mim_poll()
    → chat.poll_messages()
      → return list(_pending_messages); _pending_messages.clear()
    → if messages, append to React state
```

## Step 2: Write the Message Engine (`chat.py`)

Create `gateway/winpeek_hub/chat.py`:

```python
"""MIM message engine — send, receive, contacts, history."""

import json, sqlite3, time
from datetime import datetime
from pathlib import Path

DB_PATH = Path.home() / ".hermes" / "winpeek" / "mim.db"

# ── DB ──────────────────────────────────────────

def _db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_uid INTEGER NOT NULL,
            to_uid INTEGER NOT NULL,
            from_name TEXT,
            content TEXT NOT NULL,
            msg_ts TEXT NOT NULL DEFAULT (datetime('now','localtime'))
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_msg_to ON messages(to_uid)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_msg_from ON messages(from_uid)")
    conn.commit()
    return conn

# ── Memory queue (messages received via MQTT) ──

_pending: list[dict] = []

def enqueue(msg: dict):
    """MQTT _on_message calls this. Message goes into polling queue."""
    _pending.append(msg)

def poll_messages(to_uid: int) -> list[dict]:
    """Called by winpeek_mim_poll every 3s. Returns + clears queue."""
    msgs = [m for m in _pending if m.get("to_uid") == to_uid]
    _pending[:] = [m for m in _pending if m.get("to_uid") != to_uid]
    return msgs

# ── Send ────────────────────────────────────────

def send_message(from_uid: int, from_name: str, to_uid: int, body: str) -> dict:
    """Persist to DB, then publish via MQTT."""
    conn = _db()
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        "INSERT INTO messages (from_uid, to_uid, from_name, content, msg_ts) VALUES (?,?,?,?,?)",
        (from_uid, to_uid, from_name, body, ts))
    conn.commit()
    conn.close()

    # Publish to MQTT
    from gateway.winpeek_hub.mqtt_adapter import send_message as mqtt_send
    mqtt_send(to_uid, body, "")

    return {"ok": True, "msg_ts": ts}
```

## Step 3: Patch MQTT Adapter

In `gateway/winpeek_hub/mqtt_adapter.py`, the `_on_message` callback already receives incoming messages. Add one line to route them into the chat queue:

```python
def _on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
    except json.JSONDecodeError:
        return

    from_uid = payload.get("from_uid", "")
    from_name = payload.get("from", "?")
    body = payload.get("body", "")

    if str(from_uid) == str(UID):
        return  # skip echo

    # 🆕 Route into chat queue so frontend can poll it
    try:
        from gateway.winpeek_hub.chat import enqueue
        enqueue({
            "from_uid": from_uid,
            "from_name": from_name,
            "to_uid": UID,
            "content": body,
            "time": payload.get("ts", time.strftime("%Y-%m-%dT%H:%M:%S")),
        })
    except Exception:
        pass

    # existing handler logic below...
```

## Step 4: Register Hermes Tools

In `tools/winpeek_tools.py`, add 4 tool registrations:

```python
# ── MIM: Login ──

def _handle_mim_login(args: dict) -> str:
    nickname = args.get("nickname", "").strip()
    if not nickname:
        return json.dumps({"error": "nickname required"})
    from gateway.winpeek_hub import identity
    result = identity.login(nickname) or identity.register(nickname, "Developer")
    if not result:
        return json.dumps({"error": f"name '{nickname}' taken"})
    return json.dumps({"ok": True, "identity": result})

registry.register(
    name="winpeek_mim_login",
    toolset="winpeek_rpa",
    schema={
        "name": "winpeek_mim_login",
        "description": "Register or login to MIM messaging. Returns identity with uid.",
        "parameters": {
            "type": "object",
            "properties": {
                "nickname": {"type": "string", "description": "Your display name"},
            },
            "required": ["nickname"],
        },
    },
    handler=lambda args, **kw: _handle_mim_login(args),
    check_fn=lambda: True,
    requires_env=[],
    description="MIM identity register/login",
)

# ── MIM: Send ──

def _handle_mim_send(args: dict) -> str:
    from gateway.winpeek_hub.mqtt_adapter import UID, NAME
    from_uid = args.get("from_uid", UID)
    from_name = args.get("from_name", NAME)
    to_uid = args.get("to_uid")
    body = args.get("body", "")
    if not to_uid or not body:
        return json.dumps({"error": "to_uid and body required"})
    from gateway.winpeek_hub.chat import send_message
    return json.dumps(send_message(from_uid, from_name, int(to_uid), body))

registry.register(
    name="winpeek_mim_send",
    toolset="winpeek_rpa",
    schema={
        "name": "winpeek_mim_send",
        "description": "Send a message to another agent via MQTT",
        "parameters": {
            "type": "object",
            "properties": {
                "to_uid": {"type": "integer", "description": "Recipient agent uid"},
                "body": {"type": "string", "description": "Message text"},
            },
            "required": ["to_uid", "body"],
        },
    },
    handler=lambda args, **kw: _handle_mim_send(args),
    check_fn=lambda: True,
    requires_env=[],
    description="MIM send message",
)

# ── MIM: Poll ──

def _handle_mim_poll(args: dict) -> str:
    uid = args.get("uid", 0)
    from gateway.winpeek_hub.chat import poll_messages
    return json.dumps({"messages": poll_messages(int(uid))})

registry.register(
    name="winpeek_mim_poll",
    toolset="winpeek_rpa",
    schema={
        "name": "winpeek_mim_poll",
        "description": "Check for new incoming messages",
        "parameters": {
            "type": "object",
            "properties": {
                "uid": {"type": "integer", "description": "Your agent uid"},
            },
        },
    },
    handler=lambda args, **kw: _handle_mim_poll(args),
    check_fn=lambda: True,
    requires_env=[],
    description="MIM poll new messages",
)

# ── MIM: Contacts ──

def _handle_mim_contacts(args: dict) -> str:
    from gateway.winpeek_hub import identity
    return json.dumps({"contacts": identity.list_all()})

registry.register(
    name="winpeek_mim_contacts",
    toolset="winpeek_rpa",
    schema={
        "name": "winpeek_mim_contacts",
        "description": "List all registered agent identities with online status",
        "parameters": {"type": "object", "properties": {}},
    },
    handler=lambda args, **kw: _handle_mim_contacts(args),
    check_fn=lambda: True,
    requires_env=[],
    description="MIM contact list",
)
```

## Step 5: Connect the Frontend

`apps/desktop/src/app/winpeek/mim/index.tsx` currently uses 8 hardcoded mock contacts and localStorage login. Replace 4 sections:

**Login** — call `winpeek_mim_login` instead of `localStorage`:

```tsx
const handleLogin = useCallback(async (name: string) => {
  const result = await gatewayRequest('winpeek_mim_login', { nickname: name })
  const data = JSON.parse(result)
  if (data.ok) {
    setIdentity(data.identity)
    localStorage.setItem('mim-identity', JSON.stringify(data.identity))
  }
}, [gatewayRequest])
```

**Contacts** — call `winpeek_mim_contacts` instead of `DEFAULT_CONTACTS`:

```tsx
useEffect(() => {
  if (!identity) return
  gatewayRequest('winpeek_mim_contacts', {}).then(r => {
    const data = JSON.parse(r)
    setContacts(data.contacts.map((c: any) => ({
      id: String(c.uid), name: c.nickname, uid: c.uid,
      role: c.role, online: true, lastMessage: '', unread: 0
    })))
  })
}, [identity])
```

**Send** — call `winpeek_mim_send` instead of local `setMessages`:

```tsx
const handleSend = useCallback(async () => {
  if (!inputText.trim() || !activeContact || !identity) return
  await gatewayRequest('winpeek_mim_send', {
    from_uid: identity.uid, from_name: identity.name,
    to_uid: activeContact.uid, body: inputText.trim()
  })
  setInputText('')
}, [inputText, activeContact, identity])
```

**Receive** — poll `winpeek_mim_poll` every 3 seconds:

```tsx
useEffect(() => {
  if (!identity) return
  const interval = setInterval(() => {
    gatewayRequest('winpeek_mim_poll', { uid: identity.uid }).then(r => {
      const data = JSON.parse(r)
      if (data.messages?.length > 0) {
        setMessages(prev => [...prev, ...data.messages.map((m: any) => ({
          id: `m-${Date.now()}-${Math.random()}`,
          fromUid: m.from_uid, fromName: m.from_name,
          content: m.content, time: m.time,
          isSelf: m.from_uid === identity.uid,
        }))])
      }
    })
  }, 3000)
  return () => clearInterval(interval)
}, [identity])
```

## Step 6: Deploy

```bash
# 1. Ensure MQTT broker is running
# Already at 192.168.3.23:1883 (mosquitto)

# 2. Set environment variables
export WINPEEK_HUB_ENABLED=1
export MIM_UID=2027
export MIM_NAME="your-agent-name"

# 3. Start Hermes gateway
hermes serve

# 4. Open Hermes Desktop → click MIM in sidebar → login
```

## Step 7: Verify

```bash
# Python: register an identity
python3 -c "
from gateway.winpeek_hub import identity
identity.register('test-agent', 'Developer')
print(identity.list_all())
"

# Check MQTT connection
python3 -c "
from gateway.winpeek_hub import mqtt_adapter
print(mqtt_adapter.status())
"

# Run quality checks
python scripts/winpeek-quality-check.py
```

## How This Fits the Big Picture

This tutorial followed the [general development guide](./winpeek-development.md) Step 1-7. MIM is one module of three. The other two (Automation platforms, Assets features) follow the same pattern — different backend directories, same tool registration, same frontend connect → quality check → deploy flow.

## Related

- [WinPeek Architecture](../developer-guide/winpeek.md) — how the three modules relate
- [MIM Migration Design](../../docs/superpowers/specs/2026-07-12-mim-migration-design.md) — from PeekabooWin
- [MQTT Adapter source](../../../gateway/winpeek_hub/mqtt_adapter.py)
- [Identity source](../../../gateway/winpeek_hub/identity.py)
