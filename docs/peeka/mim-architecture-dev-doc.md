---
title: "MIM 消息服务器架构 — 技术文档"
type: "dev-doc"
phase: "build"
module: "mim"
version: "v1"
status: "approved"
last_updated: "2026-07-27"
author_subagent: "Claude Code"
related:
  - "./mim-chat-v1-spec.md"
  - "./settings-v1-dev-doc.md"
  - "../../tasks/mim-chat-v1-todo.md"
  - "../../.zentao/mapping.json"
---

# MIM 消息服务器架构 — 技术文档

> 基于已运行两个月的生产环境代码分析。所有结论均有代码引用，不做猜测。

## 1. 组件全景图

MIM 消息系统由 **4 个独立组件** 通过 MQTT Broker 连接：

```
┌─────────────────────────────────────────────────────────────────────┐
│                        MQTT Broker                                  │
│                    192.168.3.23:1883 (mosquitto)                    │
│                                                                     │
│  Topic 协议 (3-channel):                                            │
│    comms/say/{uid}     — 发信 (Agent → Broker)                      │
│    comms/inbox/{uid}   — 收信 (Broker → Agent)                      │
│    comms/ack/{uid}     — 回执 (Agent → Broker)                      │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
   ┌────▼─────┐    ┌───────▼───────┐   ┌──────▼──────┐
   │  say.py  │    │ winpeek-prod  │   │  hermes-    │
   │  (发信)  │    │  (消息中心)   │   │  mqtt-      │
   │          │    │  Port: 2000   │   │  bridge.py  │
   │ say →    │    │  say→inbox    │   │  (被动投递) │
   │ comms/   │    │  转发 + DB    │   │             │
   │ say/     │    │  归档 + MQTT  │   │ inbox/ →   │
   │          │    │               │   │  .inject →  │
   └──────────┘    └───────────────┘   │  Hermes     │
                                       └─────────────┘
```

| # | 组件 | 代码位置 | 角色 |
|---|------|---------|------|
| 1 | **say.py** | `winpeek-prod/bin/say.py` (生产) / `PeekabooWin/bin/say.py` (上游) | Agent 发信命令 |
| 2 | **winpeek-prod** | `D:\mydata\mycode\github\winpeek-prod\` | MIM 消息中心服务 |
| 3 | **hermes-mqtt-bridge.py** | `PeekabooWin/bin/hermes-mqtt-bridge.py` | 被动投递桥 |
| 4 | **Gateway (mqtt_adapter.py)** | `hermes-agent-cc/gateway/winpeek_hub/` | Gateway 内置 MIM |

## 2. winpeek-prod — MIM 消息中心 (Port 2000)

**启动**: `D:\mydata\mycode\github\winpeek-prod\start.bat`
```bat
set WINPEEK_PORT=2000
node bin/desktop-start.js --no-browser
```

**核心文件**:
- `bin/peekaboo-win-server.js` — HTTP + WebSocket 服务端入口
- `server/chat/inbox-push.js` — **MQTT 消息中转核心** (206 行)
- `server/chat/db.js` — SQLite 聊天数据库 (WAL 模式)
- `desktop/src/mcp/api-server.js` — REST API (9527 端口)

### 2.1 inbox-push.js — MQTT 消息中转核心

`server/chat/inbox-push.js` 是消息中心的中枢，代码分析如下：

**MQTT 连接** (line 26):
```javascript
_mqttClient = mqtt.connect("mqtt://192.168.3.23:1883", {
    clientId: "winpeek-prod",
    clean: false,
    reconnectPeriod: 5000
});
```

**订阅 3 个 topic** (lines 32-40):
```javascript
_mqttClient.subscribe("comms/ack/#", { qos: 1 });
_mqttClient.subscribe("comms/say/#", { qos: 1 });     // ← 接收 say 发来的信
_mqttClient.subscribe("comms/inbox/#", { qos: 1 });    // ← 接收 inbox 发来的信
```

**消息处理逻辑** (line 46-75):
```javascript
_mqttClient.on("message", (topic, payload) => {
    const msg = JSON.parse(payload.toString());
    if (topic.startsWith("comms/say/") || topic.startsWith("comms/inbox/")) {
        // 去重 (指纹: from_uid|to_uid|body前100字符)
        // → insertMessage(DB归档)
        // → 通知前端 (_onSayMessage 回调)
    }
});
```

**发信函数** `pushMqtt()` (line 99-126):
```javascript
function pushMqtt(uid, agentName, mid, fromName, fromUid, body, gid) {
    const topic = `comms/inbox/${uid}`;
    const payload = JSON.stringify({
        mid, from: fromName, from_uid: fromUid,
        body: body.slice(0, 500), gid, ts: new Date().toISOString()
    });
    getMqtt().publish(topic, payload, { qos: 1 });
}
```

**收件箱文件** (lines 148-177):
```javascript
export function pushToInbox(toUid, msg) {
    // 1. appendFileSync → {uid}.jsonl (持久化)
    // 2. pushMqtt() → comms/inbox/{uid} (实时推送)
}
```

### 2.2 chat DB — 聊天数据存储

`server/chat/db.js`:
- 引擎: SQLite (WAL 模式)
- 位置: `%USERPROFILE%\.winpeek\data\winpeek.db`
- 核心表: `chat`, `contacts`, `groups`, `group_members`, `nodes`

### 2.3 完整消息流 (生产环境)

```
Agent A: say 2022 "任务完成"
  │
  ▼
say.py → MQTT comms/say/2022
  │
  ▼
winpeek-prod inbox-push.js:
  1. 收到 comms/say/2022 消息
  2. insertMessage(DB) — 归档到 SQLite
  3. pushToInbox(to_uid=2022):
     a. appendFile → 2022.jsonl (文件收件箱)
     b. pushMqtt → comms/inbox/2022 (MQTT实时推送)
  │
  ▼
hermes-mqtt-bridge.py:
  1. 订阅 comms/inbox/2022
  2. 收到消息 → 格式化 "名字[uid] said: 内容"
  3. 写入 ~/.winpeek/inbox/.inject
  │
  ▼
Hermes (build/lib/cli.py:14052):
  1. 主循环轮询 ~/.winpeek/inbox/.inject (每次迭代检查)
  2. 读取内容 → _pending_input.put(_inj)
  3. 像用户输入一样处理 → Agent 立即响应
```

## 3. say.py — Agent 发信命令

**实际执行路径**: `C:\Users\Administrator\winpeek\setup_mqtt\agent\say.py`  
**系统路径**: `/c/Users/Administrator/bin/say` → `python ~/winpeek/setup_mqtt/agent/say.py`

**代码** (53 行):
```python
from_uid = int(os.environ.get("WINPEEK_UID", 2025))
from_name = os.environ.get("WINPEEK_NAME") or os.environ.get("USER")
payload = {"from": from_name, "from_uid": from_uid, "to_uid": args.to_uid,
           "body": args.text, "ts": time.strftime(...)}
c.publish(f"comms/say/{args.to_uid}", json.dumps(payload), qos=1)
```

**发布 topic**: `comms/say/{to_uid}` (不是 `comms/inbox/{to_uid}`)

## 4. hermes-mqtt-bridge.py — 被动投递桥

**文件**: `D:\mydata\mycode\github\PeekabooWin\bin\hermes-mqtt-bridge.py` (65 行)

**启动**:
```bash
python hermes-mqtt-bridge.py 2022   # 为 Hermes(uid=2022) 启动桥
```

**工作流程**:
```python
# 订阅
TOPIC = f"comms/inbox/{HERMES_UID}"   # line 11

# 收到消息
def on_message(client, userdata, msg):
    payload = json.loads(msg.payload.decode())
    # 格式化
    formatted = f"{name}[{uid}] said: {body}"
    # 写入 .inject 文件
    with open(INJECT, "w") as f: f.write(formatted)
    # INJECT = ~/.winpeek/inbox/.inject (line 12)
```

## 5. Gateway mqtt_adapter.py — 内置 MIM 适配器

**文件** (两个版本):
- 生产: `hermes-agent/gateway/winpeek_hub/mqtt_adapter.py` (上游, pip installed)
- 开发: `hermes-agent-cc/gateway/winpeek_hub/mqtt_adapter.py` (我们的仓库)

**2026-07-27 新增**: `comms/say/#` → `comms/inbox/{uid}` relay (line 115-122):
```python
# ── Say relay: comms/say/{uid} → comms/inbox/{uid} (MIM message center) ──
if msg.topic.startswith("comms/say/"):
    to_uid = int(msg.topic.rsplit("/", 1)[-1])
    if to_uid:
        payload_str = json.dumps(payload, ensure_ascii=False)
        client.publish(f"comms/inbox/{to_uid}", payload_str, qos=1)
        logger.info(f"MIM say→inbox relay: uid={to_uid}")
    return
```

**订阅** (line 95-98):
```python
client.subscribe("comms/inbox/#", qos=1)
client.subscribe("comms/outbox/#", qos=1)
client.subscribe("comms/group/#", qos=1)
client.subscribe("comms/say/#", qos=1)      # ← 2026-07-27 新增
```

## 6. Hermes 收信 — .inject 轮询机制

**文件**: `D:\mydata\mycode\github\hermes-agent\build\lib\cli.py` (line 14052)

Hermes 主循环每次迭代检查 `.inject` 文件:
```python
# ── External inject hook: ~/.winpeek/.inject → _pending_input
inject_path = os.path.expanduser("~/.winpeek/inbox/.inject")
if os.path.exists(inject_path):
    with open(inject_path, encoding='utf-8') as _f:
        _inj = _f.read().strip()
    os.unlink(inject_path)
    if _inj:
        self._pending_input.put(_inj)
```

> 注意: 此轮询机制在 `build/lib/cli.py` 中 (打包版本), 不在源码 `cli.py` 中。
> Hermes TUI (`hermes --tui`) 通过 `tui_gateway/entry.py` 启动，此路径**没有** `.inject` 轮询。

## 7. 当前运行状态 (2026-07-27)

| 组件 | 状态 | 说明 |
|------|:--:|------|
| MQTT Broker (192.168.3.23:1883) | ✅ 运行 | mosquitto 服务 |
| say.py | ✅ 可用 | 全局命令, 发到 comms/say/ |
| winpeek-prod (Port 2000) | ❌ 未运行 | MIM 消息中心编译的 |
| hermes-mqtt-bridge.py | ❌ 未运行 | 被动投递桥 |
| Hermes serve (Port 8642) | ✅ 运行 | 由 hermes serve 启动 |
| Hermes TUI (hermes --tui) | ❌ 未运行 | TUI 依赖安装异常 |
| Gateway mqtt_adapter relay | ⏳ 已提交 | 需重启 Gateway 生效 |

## 8. 消息流对比: 生产环境 vs 当前开发环境

### 生产环境 (有 winpeek-prod)

```
say 2022 "消息"
  → MQTT comms/say/2022
  → winpeek-prod inbox-push.js 收信
  → pushToInbox(2022):
      ├─ 2022.jsonl (文件持久化)
      └─ pushMqtt → MQTT comms/inbox/2022
  → hermes-mqtt-bridge.py 收到
  → .inject 文件
  → Hermes 主循环轮询 → 被动弹出 ✅
```

### 当前开发环境 (无 winpeek-prod, 用 Gateway relay)

```
say 2022 "消息"
  → MQTT comms/say/2022
  → Gateway mqtt_adapter.py relay
  → MQTT comms/inbox/2022
  → ??? (需要 hermes-mqtt-bridge.py 或 Gateway 内置 .inject 轮询)
```

## 9. 待完成的集成工作

| # | 任务 | 状态 |
|---|------|:--:|
| 1 | 重启 Gateway 加载 say→inbox relay | ⏳ |
| 2 | 启动 hermes-mqtt-bridge.py (或 Gateway 内置 .inject 轮询) | ⏳ |
| 3 | 验证 end-to-end: say → relay → bridge → Hermes 弹出 | ⏳ |

## 10. 关键配置文件

| 文件 | 用途 |
|------|------|
| `~/.hermes/data/agent.conf` | Hermes uid 身份 (当前: `{"hermes_uid":2034}`) |
| `~/.winpeek/agent.conf` | WinPeek 全局配置 (MQTT host 等) |
| `~/.hermes/winpeek/inbox/{uid}/` | 文件收件箱目录 |
| `~/.winpeek/inbox/.inject` | bridge 写入, Hermes 主循环轮询读取 |

## 11. 代码引用索引

| 文件 | 行数 | 关键内容 |
|------|:--:|------|
| `winpeek-prod/server/chat/inbox-push.js` | 206 | say→inbox 转发 + 文件收件箱 + MQTT 发布 |
| `winpeek-prod/server/chat/db.js` | 1000+ | SQLite 聊天数据库 (chat/contacts/nodes) |
| `winpeek-prod/bin/desktop-start.js` | 30+ | 启动入口 (server + agent-launcher) |
| `winpeek-prod/start.bat` | 31 | 生产环境启动脚本，端口 2000 |
| `PeekabooWin/bin/hermes-mqtt-bridge.py` | 65 | MQTT→.inject 被动投递桥 |
| `PeekabooWin/bin/say.py` | 160 | 全局 say 命令 (自动识人) |
| `~/winpeek/setup_mqtt/agent/say.py` | 53 | 实际执行的 say 脚本 |
| `hermes-agent-cc/gateway/winpeek_hub/mqtt_adapter.py` | 300 | Gateway MQTT 适配器 (含 say→inbox relay) |
| `hermes-agent/build/lib/cli.py:14052` | 10 | .inject 文件轮询 (Hermes 被动读信核心) |
