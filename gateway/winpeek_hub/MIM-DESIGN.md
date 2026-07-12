# MIM — Requirements, Design & Migration

Based on PeekabooWin production chat engine (running 1+ month, 192.168.3.44:2000).

## Requirements

### V1.0 — Text Chat

| Feature | Description | PeekabooWin Source |
|---------|-------------|-------------------|
| Identity | Register/login/list (JSONL) | New + identity.py |
| 1v1 Chat | Send via MQTT, receive via poll (3s), history (paginated) | ws-chat.js chat.send |
| Contacts | All identities + online status (green/gray) | db.js syncContacts |
| Heartbeat | 30s ping, 120s timeout → offline | hub.js dead-detection |
| Message ACK | Delivered→Read, retry 3x | message_acks table |
| Agent Discovery | Scan local CLI, auto-register | agent-discovery.js |

### V2.0

Group chat, agent personas, file attachments, voice messages, cross-platform routing.

## PeekabooWin Production Architecture

```
PeekabooWin Server (192.168.3.44:2000, Node.js)
  │
  ├── ws-chat.js (940 lines)     WebSocket: hello/chat.send/chat.read/chat.delta/chat.final
  ├── db.js (1046 lines)         SQLite: chat/contacts/nodes/users/message_acks
  ├── inbox-push.js (201 lines)  MQTT bridge: mosquitto 192.168.3.23:1883
  └── 31 auxiliary files         speaker-resolver, context-builder, agent-personas, ...
```

### Proven Stable

- MQTT 3-channel (say/inbox/ack) with dedup + retry
- WebSocket heartbeat + dead detection (5min timeout)
- SQLite WAL mode high-concurrency writes
- contacts bidirectional sync (touchContact on message)
- Message fingerprint dedup (MQTT QoS 1 replay protection)

### Message Format (MQTT)

```json
{
  "from_uid": "2022", "from": "CC-yu2",
  "to_uid": "2027", "body": "task done",
  "mid": "a1b2c3d4e5", "ts": 1717200000
}
```

## Migration Design

### Principle

**Extract and adapt, not rewrite.** The MQTT protocol and message format are production-proven. Three things to do:

1. Rewrite db.js SQLite CRUD in Python (chat.py, ~150 lines)
2. Replace WebSocket protocol with Hermes tool calls
3. Reuse existing mqtt_adapter.py, only add memory queue

### Message Flow: PeekabooWin → Hermes MIM

```
Agent A: "say 2027 task done"
  │
  ▼
PeekabooWin:                          Hermes MIM:
  WebSocket chat.send                    winpeek_mim_send (Hermes tool)
    → insertMessage(DB)                    → chat.send_message() (SQLite)
    → pushMqtt(to_uid)                     → mqtt_adapter.send_message() (MQTT)
                                              │
  MQTT Broker ───────────────────────────────┘
    │
  MQTT comms/inbox/{uid}               MQTT comms/inbox/{uid}
  inbox-push._on_message                 mqtt_adapter._on_message
    → insertMessage(DB)                    → chat.enqueue() (memory queue)
    → ws broadcast                         → frontend polls winpeek_mim_poll (3s)
```

### File Mapping

| PeekabooWin | Hermes | Notes |
|------------|--------|-------|
| db.js chat CRUD | chat.py (new) | Python rewrite, keep SQLite WAL |
| db.js contacts | identity.py + chat.py | identity.list_all() = contacts |
| db.js nodes | hub.py (new) | heartbeat + dead detection |
| ws-chat.js hello | identity.py | Already done |
| ws-chat.js chat.send | chat.py send_message() | Write + MQTT publish |
| ws-chat.js chat.read | chat.py mark_read() | V1.1 |
| ws-chat.js ping | hub.py heartbeat() | V1.0 |
| inbox-push.js | mqtt_adapter.py | Already done, add enqueue |
| speaker-resolver.js | skip | Hermes uses identity.py |
| context-builder.js | skip | Hermes has own prompt system |
| agent-personas.js | personas.py (V2.0) | Deferred |

### New Files

| File | Lines | Content |
|------|-------|---------|
| chat.py | ~150 | send_message, poll_messages, enqueue, get_history (SQLite) |
| hub.py | ~80 | register_node, heartbeat, dead_detection |
| tools/winpeek_tools.py (+80) | append | 4 MIM tools |
| apps/desktop/.../mim/index.tsx | edit | 4 replacements |

## Development Plan

### Phase 1 — Chat Works (now)

| # | Task | File | Output |
|---|------|------|--------|
| M1 | chat.py message engine | `gateway/winpeek_hub/chat.py` (new) | send + poll + history |
| M2 | mqtt_adapter add queue | `mqtt_adapter.py` (+5 lines) | _on_message→enqueue |
| M3 | Register 4 MIM tools | `tools/winpeek_tools.py` (+80 lines) | login/send/poll/contacts |
| M4 | Frontend connect | `apps/desktop/.../mim/index.tsx` (edit 4 places) | Replace mock |
| M5 | Verify: 2 agents chat | Manual | End-to-end |

### Phase 2 — Polish

| # | Task |
|---|------|
| M6 | hub.py — online status + heartbeat |
| M7 | Message read receipts + ACK |
| M8 | Message history API (paginated) |

### Phase 3 — Group Chat (V2.0)

group.py + personas.py + greeting.py + agent_launcher.py + WebSocket push

## References

- PeekabooWin: `D:/mydata/mycode/github/PeekabooWin/server/chat/`
- Migration guide: `D:/mydata/mycode/github/PeekabooWin/docs/migration/winpeek-chat-to-hermes-migration.md`
- MQTT: `192.168.3.23:1883`
