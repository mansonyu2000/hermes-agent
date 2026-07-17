# MIM — Multi-Agent Instant Messaging

Multi-agent messaging inside Hermes Gateway. Agents register an identity, discover peers, send and receive messages over MQTT. Migrated from PeekabooWin chat engine.

## Requirements

### V1.0

| Feature | Description | Status |
|---------|-------------|--------|
| Identity | Register (nickname + role → uid), login, query by uid, list all | ✅ |
| 1-to-1 chat | Send via MQTT, receive via poll, message history (paginated) | 🆕 chat.py needed |
| Contact list | All registered identities with online status (green/gray) | ✅ identity.list_all() |
| Online heartbeat | 30s ping, auto-offline after 120s | 🆕 hub.py needed |
| Message ACK | Delivery receipt (pending→delivered→read), retry 3x | 🆕 |

## Database

### MIM Chat Storage (当前: SQLite)

MIM 的实时聊天数据目前使用 **per-user SQLite**，每个用户独立文件：

```
~/.hermes/winpeek/data/uid{uid}/mim.db
```

每个用户一个 `mim.db`，包含 `messages` 表（from_uid, to_uid, content, msg_ts）。

### Hub Archive (MySQL / JSONL)

消息归档支持 MySQL，用于审计/合规/多端同步：

```
Host:     192.168.3.23 (htubs24)
Port:     3306
User:     winpeek
Password: Server33
Database: winpeek-db2
Table:    hub_messages
```

配置方式（环境变量）：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `WINPEEK_DB_HOST` | `192.168.3.23` | MySQL 主机 |
| `WINPEEK_DB_PORT` | `3306` | MySQL 端口 |
| `WINPEEK_DB_USER` | `winpeek` | MySQL 用户 |
| `WINPEEK_DB_PASS` | `Server33` | MySQL 密码 |
| `WINPEEK_DB_NAME` | `winpeek-db2` | MySQL 数据库名 |
| `HUB_ARCHIVE_ENGINE` | `mysql` | 归档引擎: `mysql` / `jsonl` / `off` |

> 生产环境建议设置 `WINPEEK_DB_USER=winpeek`、`WINPEEK_DB_PASS=Server33` 连接 htubs24 的 `winpeek-db2` 数据库。

### V2.0

| Feature | Description |
|---------|-------------|
| Group chat | Create/join/leave, group broadcast, member list |
| Agent personas | Role-based speaking style from `.claude/agents/` files |
| File attachments | Reuse Hermes attachment system |
| Voice messages | Reuse Hermes voice recording |
| Cross-platform | Route messages between WeChat/MIM/DingTalk |

## Where Everything Lives

```
MIM
├── gateway/winpeek_hub/        ← Backend engine (7 files, 668 lines)
│   ├── README.md               ← This document: requirements + design
│   ├── identity.py   ✅        Register/login/list (JSONL)
│   ├── mqtt_adapter.py ✅      MQTT connect/publish/subscribe (paho-mqtt)
│   ├── chat.py       🆕        Message CRUD + memory queue (SQLite)
│   ├── hub.py        🆕        Node registry + heartbeat + dead detection
│   ├── archive.py    ✅        Message archive (MySQL/JSONL)
│   ├── hub_bridge.py ✅        Gateway lifecycle hooks
│   ├── routing.py    ✅        Cross-platform routing
│   └── tenant.py     ✅        Multi-tenant management
│
├── tools/winpeek_tools.py      ← Hermes tools (0 MIM tools registered)
│   ├── winpeek_mim_login       🆕 Register/login identity
│   ├── winpeek_mim_send        🆕 Send message via MQTT
│   ├── winpeek_mim_poll        🆕 Poll incoming messages
│   └── winpeek_mim_contacts    🆕 List contacts
│
├── apps/desktop/.../mim/        ← Frontend (371 lines)
│   └── index.tsx                Chat UI: login panel, contact list, chat bubbles
│
├── website/docs/user-guide/features/
│   └── mim-chat.md              ← User guide
│
└── PeekabooWin (migration source)
    └── D:/mydata/mycode/github/PeekabooWin/server/chat/ (31 files)
        ├── ws-chat.js           WebSocket protocol
        ├── db.js                SQLite CRUD reference
        ├── inbox-push.js        MQTT bridge reference
        └── docs/migration/winpeek-chat-to-hermes-migration.md
```

## Message Flow

```
Agent A (uid=2022)                    Agent B (uid=2027)
     │                                      │
     │ 1. Frontend calls winpeek_mim_send   │
     ↓                                      │
  chat.send_message()                       │
     │   writes to SQLite for history       │
     │                                      │
     │ 2. MQTT publish comms/say/2027       │
     ↓                                      │
  MQTT Broker (192.168.3.23:1883) ─────────→ 3. comms/inbox/2027
                                                │
                                            4. mqtt_adapter._on_message()
                                                │  appends to _pending queue
                                                │
                                            5. Frontend polls every 3s
                                                winpeek_mim_poll → clears queue
                                                │
                                            6. Appears in chat window
```

## Data Flow

```
User types "hello" in MIM frontend
  → frontend calls winpeek_mim_send(to_uid=2027, body="hello")
    → chat.send_message() writes SQLite mim.db
    → mqtt_adapter.send_message() publishes to MQTT
      → Broker delivers to Agent B's inbox topic
        → Agent B's mqtt_adapter._on_message() enqueues
          → Agent B's frontend polls winpeek_mim_poll every 3s
            → chat.poll_messages() returns + clears queue
              → Message displayed in chat window
```

## Message Format

```json
{
  "from_uid": "2022",
  "from": "CC-yu2",
  "to_uid": "2027",
  "body": "task done",
  "ts": "2026-07-12T15:30:00"
}
```

## MQTT Topics

| Topic | Direction | QoS | Purpose |
|-------|-----------|-----|---------|
| `comms/say/{uid}` | Agent → Broker | 1 | Send message |
| `comms/inbox/{uid}` | Broker → Agent | 1 | Receive message |
| `comms/ack/{uid}` | Agent → Broker | 1 | Delivery receipt |

Broker: `192.168.3.23:1883` (mosquitto). Subscriptions via `mqtt_adapter.connect()`.

## Key Files (Code Reference)

### identity.py (91 lines, ✅)

```python
from gateway.winpeek_hub import identity

identity.register("name", "Developer")   # → {uid, nickname, role}
identity.login("name")                    # → identity dict or None
identity.list_all()                       # → list of all identities
```

Stores to `~/.hermes/winpeek/identities.jsonl`.

### mqtt_adapter.py (189 lines, ✅)

Connects to MQTT broker, subscribes to `comms/inbox/{UID}`. Exposes `send_message(target_uid, text)` and `connect()`. Incoming messages route to `_message_handler` callback.

Requires env vars: `MIM_UID`, `MIM_NAME`, `MIM_BROKER`, `MIM_PORT`.

### chat.py (🆕, ~150 lines)

Message engine. Creates SQLite `~/.hermes/winpeek/mim.db` with `messages` table. Provides:

- `send_message(from_uid, from_name, to_uid, body)` — persist + MQTT publish
- `poll_messages(to_uid)` — return + clear memory queue
- `enqueue(msg)` — called by mqtt_adapter._on_message

### hub.py (🆕, ~80 lines)

Node registry: register agent on startup, heartbeat every 30s, mark nodes offline after 120s without heartbeat.

## How to Start Development

1. **Read this README** — understand what exists and what's needed
2. **Read the migration doc**: `docs/superpowers/specs/2026-07-12-mim-migration-design.md`
3. **Read the user guide**: `website/docs/user-guide/features/mim-chat.md`
4. **Create chat.py**: message engine with SQLite persistence + MQTT bridge
5. **Create hub.py**: online status tracking
6. **Register 4 tools** in `tools/winpeek_tools.py`
7. **Replace mock data** in `apps/desktop/.../mim/index.tsx` (4 sections)
8. **Run quality checks**: `python scripts/winpeek-quality-check.py`

## Technical Design Docs

- [Identity API design](../../docs/design/mim-identity-api.md) — Hub Server 独立端口方案 (Qoder-yu2)
- [Migration design](../../docs/superpowers/specs/2026-07-12-mim-migration-design.md) — PeekabooWin → Hermes 迁移方案
- [User guide](../../website/docs/user-guide/features/mim-chat.md) — 面向用户的功能文档

## Reference

- PeekabooWin source: `D:/mydata/mycode/github/PeekabooWin/server/chat/`
- PeekabooWin migration: `D:/mydata/mycode/github/PeekabooWin/docs/migration/winpeek-chat-to-hermes-migration.md`
- MQTT broker: `192.168.3.23:1883`
