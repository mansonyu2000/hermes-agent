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

> hermes-agent-cc 新架构。winpeek-prod 代码分析见附录 B 供参考。

## 1. 组件全景图

```
MQTT Broker (192.168.3.23:1883, mosquitto)
  comms/say/{uid}     — 发信 (Agent → Broker)
  comms/inbox/{uid}   — 收信 (Broker → Agent)
  comms/ack/{uid}     — 回执
           │
   ┌───────┼───────┐
   │       │       │
say.py  Gateway  Hermes
(发信)  (消息中心) (收信)

say → comms/say/  →  Gateway relay  →  comms/inbox/  →  .inject  →  Hermes 弹出
```

| # | 组件 | 代码位置 | 角色 |
|---|------|---------|------|
| 1 | **say.py** | `~/winpeek/setup_mqtt/agent/say.py` (53行) | 发信，发布到 `comms/say/{uid}` |
| 2 | **Gateway** | `hermes-agent-cc/gateway/winpeek_hub/mqtt_adapter.py` | MIM 消息中心 |
| 3 | **Hermes** | `hermes-agent/build/lib/cli.py:14052` | .inject 轮询收信 |

## 2. Gateway — MIM 消息中心

**文件**: `gateway/winpeek_hub/mqtt_adapter.py`

### 2.1 MQTT 连接

```python
BROKER = os.getenv("MIM_BROKER", "192.168.3.23")    # line 67
PORT = int(os.getenv("MIM_PORT", "1883"))              # line 68
```

从 MySQL `winpeek-db2.users` 表自动读取身份（`_resolve_identity()`），不需要手动设 `MIM_UID`/`MIM_NAME`。

### 2.2 订阅 (line 93-98)

```python
def _on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        client.subscribe("comms/inbox/#", qos=1)
        client.subscribe("comms/outbox/#", qos=1)
        client.subscribe("comms/group/#", qos=1)
        client.subscribe("comms/say/#", qos=1)        # ← 2026-07-27 新增
```

### 2.3 say→inbox relay (line 115-122, 2026-07-27 新增)

```python
# ── Say relay: comms/say/{uid} → comms/inbox/{uid} (MIM message center) ──
if msg.topic.startswith("comms/say/"):
    to_uid = int(msg.topic.rsplit("/", 1)[-1])
    if to_uid:
        payload_str = json.dumps(payload, ensure_ascii=False)
        client.publish(f"comms/inbox/{to_uid}", payload_str, qos=1)
        logger.info(f"MIM say→inbox relay: uid={to_uid} from={payload.get('from','?')}")
    return
```

### 2.4 inbox 到达 → 内存队列 (line 134-146)

```python
enqueue({
    "from_uid": int(from_uid) if str(from_uid).isdigit() else 0,
    "from_name": from_name,
    "to_uid": UID,
    "gid": gid,
    "content": body,
    "time": payload.get("ts", time.strftime("%Y-%m-%dT%H:%M:%S")),
})
```

### 2.5 outbox 处理 (line 155-198)

Agent 发到 `comms/outbox/{from_uid}` 的消息 → 补全上下文 → 委托 `chat.send_message()` 完成 DB 归档 + MQTT 发布 + Peeka Router。

## 3. say.py — Agent 发信

**文件**: `~/winpeek/setup_mqtt/agent/say.py` (53 行)

```python
from_uid = int(os.environ.get("WINPEEK_UID", 2025))
from_name = os.environ.get("WINPEEK_NAME") or os.environ.get("USER")

payload = {
    "from": from_name, "from_uid": from_uid,
    "to_uid": args.to_uid, "body": args.text,
    "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
}
c.publish(f"comms/say/{args.to_uid}", json.dumps(payload), qos=1)
```

**身份自动发现** (PeekabooWin/bin/say.py 完整版，160行):
1. `WINPEEK_IDENTITY` 环境变量 → JSON 文件
2. cwd 递归向上找 `.winpeek-identity.json` (项目级)
3. `~/.hermes/data/agent.conf` (Hermes 默认身份)
4. `~/.claude/winpeek-identity.json` (CC 兜底)
5. `WINPEEK_UID` 环境变量

**MQTT 格式** (生产验证 2 个月):
```json
{
  "from_uid": "2022", "from": "CC-yu2",
  "to_uid": "2027", "body": "task done",
  "mid": "a1b2c3d4e5", "ts": "2026-07-12T15:30:00"
}
```

## 4. Hermes 收信 — .inject 轮询

**关键节点** — 这是被动投递的核心，之前的文档未详细记录。

**文件**: `hermes-agent/build/lib/cli.py` line 14052 (打包版本，不在源码 `cli.py` 中)

```python
# ── External inject hook: ~/.winpeek/.inject → _pending_input
inject_path = os.path.expanduser("~/.winpeek/inbox/.inject")
if os.path.exists(inject_path):
    try:
        with open(inject_path, encoding='utf-8') as _f:
            _inj = _f.read().strip()
        os.unlink(inject_path)
        if _inj:
            self._pending_input.put(_inj)
    except Exception:
        pass
```

机制：
- Hermes 主循环**每次迭代**检查 `~/.winpeek/inbox/.inject`
- 有内容 → 注入 `_pending_input` → 像用户输入一样处理 → Agent 立即响应
- 读取后立即删除文件（`os.unlink`），不会重复处理
- 不在源码 `cli.py` 中，在打包版本 `build/lib/cli.py` 中

## 5. 完整消息流

```
Agent A: say 2022 "任务完成"
  │
  ▼
say.py → MQTT comms/say/2022
  │
  ▼
Gateway mqtt_adapter.py:
  1. 收到 comms/say/# 消息
  2. say→inbox relay → 发布 comms/inbox/2022     ← 2026-07-27 实现
  3. 收到 comms/inbox/2022 → chat.enqueue()       ← 已有
  │
  ▼ 缺口
  4. ⏳ 写 ~/.winpeek/inbox/.inject 文件
  │
  ▼
Hermes 主循环:
  5. 轮询 ~/.winpeek/inbox/.inject                ← 已有
  6. 读取 → _pending_input.put() → 立即响应        ← 已有
```

## 6. 新的MIM 客户端测试工作流

另外，我们的桌面应用本身也可以连接我们的服务端，如果客户端也需要测试，采用下面的流程，这些也需要新增，这是我们之前没有想到的。

4.1. 桌面应用 Websocket 连接（实时收消息）
`
ws://127.0.0.1:2000/ws
{
  type: "hello",
  params: {
    nodeId: "'$WINPEEK_UID'",
    name: "'$WINPEEK_NAME'",
    hostname: "'$HOSTNAME'",
    role: "'$ROLE'",
    clientType: "agent"
  }
}

4.2 REST接口

4.2.1 执行"你好"命令
`
curl -X POST http://127.0.0.1:2000/api/chat/send -H "Content-Type: application/json" -d '{"from_uid": '$WINPEEK_UID', "from_name": "'$WINPEEK_NAME'", "to_uid": '$WINPEEK_UID', "body": "你好"}'
`

4.2.2 设置活跃窗口
`
curl -X POST http://127.0.0.1:2000/api/set-active-window -H "Content-Type: application/json" -d '{"windowTitle": "Claude Code"}'
`

## 7. 当前状态 (2026-07-27)

| # | 功能 | 状态 |
|---|------|:--:|
| 1 | say→inbox relay | ✅ 已实现 |
| 2 | 订阅 comms/say/# | ✅ 已实现 |
| 3 | 重启 Gateway 加载新代码 | ⏳ |
| 4 | inbox 到达后写 .inject 文件 | ⏳ 待实现 |

## 8. 代码引用

| 文件 | 仓库 | 作用 |
|------|------|------|
| `gateway/winpeek_hub/mqtt_adapter.py` | hermes-agent-cc | 消息中心(say→inbox relay, 300行) |
| `gateway/winpeek_hub/chat.py` | hermes-agent-cc | 消息引擎(send/poll/enqueue) |
| `gateway/winpeek_hub/hub_bridge.py` | hermes-agent-cc | Gateway 生命周期集成 |
| `gateway/winpeek_hub/peeka_router.py` | hermes-agent-cc | 3层消息路由(L1/L2/L3) |
| `tools/winpeek_tools.py` | hermes-agent-cc | MIM RPC tools (login/send/poll/contacts) |
| `apps/winpeek_injector/daemon.py` | hermes-agent-cc | Agent 发现 + inbox 文件管理 + 可靠性追踪 |
| `~/winpeek/setup_mqtt/agent/say.py` | 本地安装 | 全局 say 命令 (53行) |
| `PeekabooWin/bin/say.py` | PeekabooWin | say 完整版 (160行, 自动识人) |
| `build/lib/cli.py:14052` | hermes-agent (上游) | .inject 轮询 (被动投递核心) |

## 附录 A: 关键节点说明

### A.1 MQTT Topic 拓扑

```
comms/say/{uid}     — Agent 发布消息 (say.py → Broker)
comms/inbox/{uid}   — Broker 推送给 Agent (Broker → bridge/Agent)
comms/ack/{uid}     — 消息回执 (Agent → Broker, 确认送达)
comms/outbox/{uid}  — Agent 回复发件箱 (Agent → Daemon 转发)
comms/group/{gid}   — 群聊消息
```

### A.2 被动投递链路 (3 个关键节点)

```
Node 1: say.py          →  MQTT comms/say/{uid}        (发信)
Node 2: Gateway relay   →  MQTT comms/inbox/{uid}       (转发)
Node 3: .inject 文件    →  Hermes _pending_input        (弹出)
```

**Node 2** 由 `mqtt_adapter.py` 的 say→inbox relay 实现（2026-07-27）。
**Node 3** 需要 Gateway 在收到 inbox 消息后写 `.inject` 文件（待实现）。

### A.3 .inject 文件格式

```
Claude Code[2033] said: 任务完成了
Hermes[2022] said: @群号1048 全体注意
```

格式: `{from_name}[{from_uid}] said: {body}`

## 附录 B: winpeek-prod 旧代码参考（已弃用，供参考）

> 以下代码来自 `D:\mydata\mycode\github\winpeek-prod\`，已运行 2 个月。
> 新架构由 hermes-agent-cc Gateway 承担消息中心。

### B.1 inbox-push.js — MQTT 消息中转 (206行)

**文件**: `winpeek-prod/server/chat/inbox-push.js`

核心功能:
```javascript
// MQTT 连接
_mqttClient = mqtt.connect("mqtt://192.168.3.23:1883", {
    clientId: "winpeek-prod", clean: false, reconnectPeriod: 5000
});

// 订阅
_mqttClient.subscribe("comms/ack/#", { qos: 1 });
_mqttClient.subscribe("comms/say/#", { qos: 1 });
_mqttClient.subscribe("comms/inbox/#", { qos: 1 });

// say/ 或 inbox/ 消息 → DB 归档 + 通知前端
_mqttClient.on("message", (topic, payload) => {
    // 去重 (指纹: from_uid|to_uid|body)
    // → insertMessage(DB)
    // → _onSayMessage 回调通知前端
});

// 发信: MQTT push 到目标 Agent 的 inbox topic
function pushMqtt(uid, agentName, mid, fromName, fromUid, body, gid) {
    const topic = `comms/inbox/${uid}`;
    const payload = JSON.stringify({
        mid, from: fromName, from_uid: fromUid,
        body: body.slice(0, 500), gid,
        ts: new Date().toISOString(),
    });
    getMqtt().publish(topic, payload, { qos: 1 });
}

// 收件箱文件持久化
function pushToInbox(toUid, msg) {
    appendFileSync(`${toUid}.jsonl`, JSON.stringify(line) + "\n");
    pushMqtt(toUid, ...);  // 同时 MQTT 实时推送
}
```

### B.2 db.js — SQLite 聊天数据库

**文件**: `winpeek-prod/server/chat/db.js`
- 引擎: SQLite WAL 模式
- 位置: `%USERPROFILE%\.winpeek\data\winpeek.db`
- 核心表: `chat`, `contacts`, `groups`, `group_members`, `nodes`

### B.3 启动方式

```bat
set WINPEEK_PORT=2000
set WINPEEK_DATA_DIR=%USERPROFILE%\.winpeek-prod
node bin/desktop-start.js --no-browser
```

### B.4 hermes-mqtt-bridge.py — 被动投递桥 (65行)

**文件**: `PeekabooWin/bin/hermes-mqtt-bridge.py`

```python
TOPIC = f"comms/inbox/{HERMES_UID}"
INJECT = os.path.expanduser("~/.winpeek/inbox/.inject")

def on_message(client, userdata, msg):
    payload = json.loads(msg.payload.decode())
    formatted = f"{name}[{uid}] said: {body}"
    with open(INJECT, "w", encoding="utf-8") as f:
        f.write(formatted)
```

这个独立进程现已不需要——Gateway 可以内置 `.inject` 写入。
