# WinPeek Hub — MIM Multi-Agent Instant Messaging

Multi-agent messaging running inside Hermes Gateway. Migrated from PeekabooWin chat engine.

## Requirements

### V1.0 — Text Chat

| Module | Features | Status |
|--------|----------|--------|
| Identity | Register (nickname + role → uid), login, query by uid, list all identities | P0 |
| Single Chat | Send message (MQTT or direct), receive (poll 3s or WebSocket push), message history (paginated), mark read | P0 |
| Contact List | All registered identities with online status (green/gray dot), sort by recent activity | P0 |
| Online Status | Heartbeat every 30s, auto-offline after 120s no heartbeat | P1 |
| Message ACK | Delivery receipt (pending→delivered→read), retry (3x with exponential backoff) | P1 |
| Agent Discovery | Scan local machine for Agent CLI, auto-register to WinPeek | P1 |

### V2.0 — Group Chat & Rich Media

| Module | Features |
|--------|----------|
| Group Chat | Create/join/leave group, group message broadcast, member list, group rules |
| Agent Personas | Role-based speaking style (from .claude/agents/ files), topic matching |
| File Attachments | Reuse Hermes attachment system, image/file in message body |
| Voice Messages | Reuse Hermes voice recording + transcription |
| Cross-Platform | Message routing between WeChat/MIM/DingTalk via Hub routing |

## Architecture

```
Desktop UI (apps/desktop/src/app/winpeek/mim/)
    ↓ useGatewayRequest()
Hermes Tools (tools/winpeek_tools.py)
    ↓
┌─ Gateway Hub ─────────────────────┐
│  chat.py       🆕 Message engine  │ ← SQLite mim.db
│  identity.py   ✅ Identity CRUD   │ ← JSONL storage
│  mqtt_adapter  ✅ MQTT send/recv  │ ← + queue
│  hub.py        🆕 Node registry   │ ← heartbeat
│  group.py      🆕 Group control   │
│  personas.py   🆕 Agent personas  │
│  greeting.py   🆕 Online greeting │
│  archive.py    ✅ Message archive │
└───────────────────────────────────┘
    ↓ MQTT
MQTT Broker (192.168.3.23:1883)
    ├── comms/say/{uid}    → Send
    ├── comms/inbox/{uid}  → Receive
    └── comms/ack/{uid}    → ACK
```

## Migration from PeekabooWin

31 source files → 3 categories:

**A. Migrate** (14 files → Python rewrite): db.js + ws-chat.js + inbox-push.js + chat-relay.js + hub.js + node-registry.js + checksum.js + name-validator.js + speaker-resolver.js + greeting.js + agent-launcher.js + agent-discovery.js + agent-group.js + agent-personas.js

**B. Reuse Hermes** (6 functions): file attachments, voice, session management, AI conversation, memory, approvals — Hermes already has these.

**C. V2.0 defer** (7 files): group-rules.js, group-matcher.js, group-observer.js, manager-agent.js, sub-topic.js, meeting-brief.js, code-reviewer.js

References: `D:/mydata/mycode/github/PeekabooWin/server/chat/` (31 files), `docs/topics/group-chat-collaboration.md`, `setup_mqtt/winpeek-server-mqtt.md`

## Database

V1.0: SQLite `~/.hermes/winpeek/mim.db`

```
messages    (message_id, from_uid, to_uid, gid, content, msg_type, checksum, created_at)
contacts    (uid, name, role, online, last_message, unread)
nodes       (node_id, name, hostname, role, status, last_seen)
```

V2.0: MySQL `hub_messages` (hub_schema.sql, 4 tables)

## Hermes Tools

| Tool | Function |
|------|----------|
| winpeek_mim_login | Register/login identity |
| winpeek_mim_contacts | List contacts with online status |
| winpeek_mim_send | Send message |
| winpeek_mim_poll | Poll new messages |

## Key Files

```
gateway/winpeek_hub/
├── README.md              This document
├── __init__.py
├── chat.py                🆕 Message engine (300 lines)
├── hub.py                 🆕 Node registry + heartbeat (150 lines)
├── group.py                🆕 Group control (150 lines)
├── personas.py             🆕 Agent personas (100 lines)
├── greeting.py             🆕 Online greeting (80 lines)
├── agent_launcher.py      🆕 Agent launcher + discovery (120 lines)
├── identity.py            ✅ Identity CRUD (91 lines, JSONL)
├── mqtt_adapter.py        ✅ MQTT send/receive (189 lines)
├── archive.py             ✅ Message archive (MySQL/JSONL)
├── hub_bridge.py          ✅ Gateway integration (94 lines)
├── routing.py             ✅ Cross-platform routing (68 lines)
└── tenant.py              ✅ Multi-tenant (106 lines)
```
