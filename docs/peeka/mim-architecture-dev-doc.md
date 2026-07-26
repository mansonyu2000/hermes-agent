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
---

# MIM 消息服务器架构 — 技术文档

> hermes-agent-cc 自包含架构。不依赖 winpeek-prod（老代码已弃用）。

## 1. 组件全景图

```
MQTT Broker (192.168.3.23:1883, mosquitto)
  comms/say/{uid}     — 发信
  comms/inbox/{uid}   — 收信
           │
   ┌───────┼───────┐
   │       │       │
say.py  Gateway  Hermes
(发信)  (消息中心) (收信)

say → comms/say/  →  Gateway relay  →  comms/inbox/  →  Hermes 被动弹出
```

| 组件 | 代码 | 角色 |
|------|------|------|
| say.py | `~/winpeek/setup_mqtt/agent/say.py` | 发信，发布到 `comms/say/{uid}` |
| Gateway | `gateway/winpeek_hub/mqtt_adapter.py` | 消息中心：订阅 say/#，转发到 inbox/# |
| Hermes | `build/lib/cli.py:14052` | .inject 轮询收信 |

## 2. Gateway — MIM 消息中心

**文件**: `gateway/winpeek_hub/mqtt_adapter.py`

### 订阅 (line 93-98)
```python
client.subscribe("comms/inbox/#", qos=1)
client.subscribe("comms/outbox/#", qos=1)
client.subscribe("comms/group/#", qos=1)
client.subscribe("comms/say/#", qos=1)  # ← 2026-07-27 新增
```

### say→inbox relay (line 115-122, 2026-07-27 新增)
```python
if msg.topic.startswith("comms/say/"):
    to_uid = int(msg.topic.rsplit("/", 1)[-1])
    payload_str = json.dumps(payload, ensure_ascii=False)
    client.publish(f"comms/inbox/{to_uid}", payload_str, qos=1)
    logger.info(f"MIM say→inbox relay: uid={to_uid}")
    return
```

### inbox 到达 → 内存队列 (line 134-146)
```python
enqueue({
    "from_uid": ..., "from_name": ..., "to_uid": UID,
    "content": body, "time": ...
})
```

## 3. say.py — Agent 发信

**文件**: `~/winpeek/setup_mqtt/agent/say.py` (53 行)

```python
from_uid = int(os.environ.get("WINPEEK_UID", 2025))
from_name = os.environ.get("WINPEEK_NAME") or os.environ.get("USER")
payload = {"from": from_name, "from_uid": from_uid,
           "to_uid": args.to_uid, "body": args.text}
c.publish(f"comms/say/{args.to_uid}", json.dumps(payload), qos=1)
```

## 4. Hermes 收信 — .inject 轮询

**文件**: `build/lib/cli.py:14052` (上游 hermes-agent 打包版本)

```python
inject_path = os.path.expanduser("~/.winpeek/inbox/.inject")
if os.path.exists(inject_path):
    with open(inject_path, encoding='utf-8') as _f:
        _inj = _f.read().strip()
    os.unlink(inject_path)
    if _inj:
        self._pending_input.put(_inj)
```

Hermes 主循环每次迭代检查 `.inject` 文件，有内容就注入 `_pending_input`，像用户输入一样处理。

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
  2. say→inbox relay → 发布 comms/inbox/2022
  3. 收到 comms/inbox/2022 → chat.enqueue() (内存队列)
  │
  ▼
（当前缺口）
  4. ⏳ 写 ~/.winpeek/inbox/.inject 文件
  │
  ▼
Hermes 主循环:
  5. 轮询 ~/.winpeek/inbox/.inject ✅
  6. 读取 → _pending_input.put() → Agent 立即响应 ✅
```

## 6. 当前状态与缺口

| # | 功能 | 状态 |
|---|------|:--:|
| 1 | say→inbox relay | ✅ 已实现 |
| 2 | 订阅 comms/say/# | ✅ 已实现 |
| 3 | 重启 Gateway 加载新代码 | ⏳ |
| 4 | inbox 到达后写 .inject 文件 | ⏳ 待实现 |

## 7. 代码引用

| 文件 | 仓库 | 作用 |
|------|------|------|
| `gateway/winpeek_hub/mqtt_adapter.py` | hermes-agent-cc | 消息中心(say→inbox relay) |
| `gateway/winpeek_hub/chat.py` | hermes-agent-cc | 消息引擎(send/poll/enqueue) |
| `gateway/winpeek_hub/hub_bridge.py` | hermes-agent-cc | Gateway 生命周期集成 |
| `~/winpeek/setup_mqtt/agent/say.py` | 本地安装 | 全局 say 命令 |
| `build/lib/cli.py:14052` | hermes-agent (上游) | .inject 轮询 |
