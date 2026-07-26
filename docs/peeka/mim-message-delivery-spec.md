---
title: "MIM 消息投递完整规格 — 需求·架构·计划"
type: "requirements+design"
phase: "build"
module: "mim"
version: "v1"
status: "in_progress"
last_updated: "2026-07-27"
author_subagent: "Claude Code"
zentao_product: 11
zentao_project: 29
zentao_execution: 30
related:
  - "./mim-chat-v1-spec.md"
  - "./mim-architecture-dev-doc.md"
  - "./settings-v1-dev-doc.md"
---

# MIM 消息投递完整规格

## 1. 需求定义

### 1.1 核心需求

消息从发送者到达接收者 Agent 对话框，经历 3 个过程，**全部被动投递，零轮询**。

### 1.2 消息分级处理（减少 Agent 干扰）

| 层级 | 消息类型 | 处理方 | Token 消耗 | 说明 |
|:--:|------|------|:--:|------|
| **L1** | 问候/礼貌用语 | Daemon 模板匹配 | 0 | 早安/晚安/你好/谢谢/在吗 等 |
| **L2** | 简单查询 | Daemon 本地知识库 | 0 | 机器名/Agent列表/谁在/有哪些 等 |
| **—** | 广告/推广 | Daemon 存档+特征提取 | 0 | 去重(重复丢弃)，提取关键词→归档到发送方画像 |
| **L3** | 请求/通知/其他 | **LLM Agent** | 按需 | 只有这类消息才进入 Agent 对话框 |

**设计原则**: Daemon 是本地管家——过滤噪音，只把真正需要 LLM 处理的消息交给 Agent。
但**广告不是纯粹的噪音**——它是发送方的输出/自我介绍，提取其关键信息可了解对方"是做什么的"。
重复广告丢弃，新广告存档并抽取特征词，写入发送方的人物画像（供后续交互参考）。

### 1.3 消息分类规则（5 类）

```
classify(body):
  body 含 "推广/招商/营销/广告/促销/优惠/限时/免费领取" → advertisement (去重→存档→画像)
  body 含 "早安/晚安/谢谢/多谢/在吗/在不在/你好/hello/吃了没/好久不见" → greeting (L1)
  body 含 "版本/更新/告警/通知/公告/上线/离线/提醒" → notification (L3)
  body 含 "什么/怎么/如何/为什么/帮我/查一下/看一下/检查/能不能/可以/请/?" → request (L3)
  len(body) ≤ 5 → greeting (L1)
  其他 → request (L3)
```

**广告处理** (新增):
```
advertisement → 指纹去重 (发送方+关键词)
  ├─ 重复 → 丢弃
  └─ 新广告 → 提取关键词 → 存入发送方画像 (skills/keywords/business_scope)
              → 记入 digest 摘要 (Agent 可回溯哪些人发了广告)
```

### 1.4 Agent 类型适配

| Agent | 收信方式 | 原因 |
|------|---------|------|
| **Hermes** (开源) | MQTT 直接推送进 chatbox | 可改 `cli.py`，消息直达 `_pending_input` |
| **Claude Code** (闭源) | RPA/ConPTY 空投注入 | 无法改 chatbox，模拟键盘鼠标输入 |

## 2. 架构设计

### 2.1 三个过程全景

```
过程 1: 发信 → MIM 服务器 (MySQL + Gateway + MQTT)
过程 2: MQTT → 本机统一信箱 (Peeka Daemon 管理)
过程 3: 信箱 → Agent 对话框 (被动弹出，零轮询)
```

```
say.py → MQTT comms/say/{uid}
  │
  ▼
过程 1 — Gateway (mqtt_adapter.py):
  1. 订阅 comms/say/# 收到消息
  2. say→inbox relay → 发布 comms/inbox/{uid}
  3. route_incoming() L1/L2/L3 分流
  │
  ├─ L1/L2 → Daemon 自动回复 + 记入 digest
  └─ L3 → write_to_inbox(agent_uid)
  │
  ▼
过程 2 — Peeka Daemon:
  统一信箱: ~/.peeka/data/messages/{uid}/
    ├── inbox/    ← L3 消息到达 (JSON文件)
    └── outbox/   ← Agent 回复出口 (Daemon 负责投递)
  │
  ▼
过程 3 — Agent 被动弹出:
  Hermes:     winpeek_mqtt.py → _pending_input → 立即响应
  Claude Code: engine.py RPA → 窗口注入 → Enter触发
```

### 2.2 L1/L2/L3 路由决策 (peeka_router.py)

```python
def route_incoming(from_uid, to_uid, body) -> dict:
    tag = classify(body)

    if tag == "advertisement":
        # 不丢弃 — 提取特征, 去重, 写入发送方画像
        fp = f"{from_uid}|{_extract_keywords(body)}"
        if _ad_fingerprint_seen(fp):
            return {"action": "duplicate_drop"}           # 重复→丢弃
        _ad_fingerprint_remember(fp)
        _update_sender_profile(from_uid, body)            # 提取关键词→画像
        return {"action": "ad_archive", "tag": tag}       # 存档, 不进Agent

    if tag == "greeting":
        reply = _match_greeting(body)                   # L1: 模板匹配
        if reply:
            return {"action": "auto_reply", "reply": reply}

    state = _get_daemon_state()
    answer = daemon_known(state, body)                  # L2: 本地知识库
    if answer:
        return {"action": "daemon_answer", "reply": answer}

    ctx = assemble_context(from_uid, to_uid, body, tag) # L3: 转发Agent
    return {"action": "forward", "context": ctx}
```

### 2.3 chat.py 中的路由执行

```python
# send_message() → route_incoming() 之后:

if decision["action"] in ("auto_reply", "daemon_answer"):
    # Daemon 替 Agent 回复（发信者无感知）
    _enqueue_auto_reply(to_uid, from_uid, reply, from_name)
    add_digest_entry(from_uid, from_name, body, reply, layer)
    # ↑ 记入 digest，Agent 上线时会看到摘要

elif decision["action"] == "ad_archive":
    # 新广告 → 去重通过 → 提取关键词归档到发送方画像
    # Agent 不会被这条消息打扰, 但画像已更新
    _archive_ad(from_uid, body)

elif decision["action"] == "duplicate_drop":
    # 重复广告 → 丢弃

elif decision["action"] == "forward":
    # L3: 写 inbox + 被动投递
    write_to_inbox(to_uid, msg_dict)
    # + 窗口注入 (RPA/ConPTY for CC / MQTT for Hermes)
```

### 2.4 Daemon 问候模板 (daemon.py L1)

```python
GREETING_TEMPLATES = {
    "吃了没": "吃了，别担心。",   "吃饭了吗": "吃了，别担心。",
    "早安": "早安，新的一天开始。", "晚安": "晚安，早点休息。",
    "谢谢": "不客气。",           "多谢": "不客气。",
    "在吗": "在的，请说。",       "在不在": "在的，请说。",
    "你好": "你好，请问有什么可以帮忙？",
    "hello": "Hi there, how can I help?",
}
```

### 2.5 Daemon 本地知识库 (daemon.py L2)

```python
DAEMON_KNOWLEDGE = {
    "agent_list": → "本机发现 N 个 Agent",
    "machine_name": → hostname,
    "谁在": → Agent 列表,
    "有哪些": → Agent类型列表,
}
```

### 2.6 Digest 摘要（Agent 上线时通知）

```python
# L1/L2 自动回复累积在 digest
add_digest_entry(from_uid, from_name, body, reply, layer)

# Agent 上线时读取
entries = pop_digest_entries()
msg = build_digest_message(entries)
# → "[MIM管家] 我不在的时候，帮你处理了以下消息:
#     1. 张三(uid=100) 说: "你好"
#        → 我回 (L1自动回复): "你好，请问有什么可以帮忙？"
#     以上共 N 条，无需你回复。"
```

## 3. 统一信箱规格

### 3.1 目录结构

```
~/.peeka/data/messages/
├── {uid}/
│   ├── inbox/           ← L3 消息到达 (JSON文件, 每个消息一个文件)
│   │   └── {mid}.json
│   ├── outbox/          ← Agent 回复出口 (Daemon 监控, 有新文件立即投递)
│   │   └── {mid}.json
│   └── .manifest.json   ← 信箱状态 (unread_count, delivered_count, 更新时间)
├── {uid}/
│   └── ...
└── .inject              ← 兼容旧 .inject 文件的全局通知管道
```

### 3.2 inbox 消息格式

```json
{
  "mid": "mim-1785081297222-2e30df42",
  "from_uid": 2033,
  "from_name": "Claude Code",
  "from_role": "Developer",
  "from_peeka_name": "Claude CodeXX-claude-code-hotime.cn",
  "relation": "same_machine",
  "body": "请帮我检查系统状态",
  "context": { "peer_uid": 2033, "tag": "request", "history": [...] },
  "received_at": "2026-07-27T00:41:37",
  "is_retry": false,
  "retry_count": 0
}
```

### 3.3 outbox 消息格式

```json
{
  "mid": "reply-xxx",
  "to_uid": 2033,
  "body": "系统状态正常，3个Agent在线",
  "reply_to_mid": "mim-1785081297222-2e30df42",
  "written_at": "2026-07-27T00:42:00"
}
```

## 4. 开发计划

### Phase 1: 统一信箱路径 ⏳

| # | 任务 | 文件 | 状态 |
|---|------|------|:--:|
| 1.1 | 定义信箱目录结构 `~/.peeka/data/messages/{uid}/inbox/outbox/` | 新增规范 | ⏳ |
| 1.2 | Daemon 启动时创建所有 Agent 的信箱目录 | `daemon.py:_init_inbox()` | ⏳ |
| 1.3 | 更新 `write_to_inbox()` 写入到新路径 | `daemon.py:write_to_inbox()` | ⏳ |
| 1.4 | 兼容旧路径 `~/.hermes/winpeek/inbox/` | softlink 或迁移 | ⏳ |

### Phase 2: 过程3 被动投递 — Hermes

| # | 任务 | 文件 | 状态 |
|---|------|------|:--:|
| 2.1 | Gateway inbox 到达后写 `.inject` 文件 | `mqtt_adapter.py:_on_message()` | ⏳ |
| 2.2 | 复用 `winpeek_mqtt.py` MQTT 推送 (主路径, 已有) | `cli.py:15194-15207` | ✅ |
| 2.3 | Daemon 监控 outbox 有新文件 → 自动调用 `say` 发送 | `daemon.py` | ⏳ |
| 2.4 | L1/L2 digest 在 Agent 上线时送达 | `winpeek_mim_read_digest` RPC | ✅ F3 已实现 |

### Phase 4: Daemon 增强

> Claude Code 投递方案：见 `docs/peeka/cc-delivery-spec.md`（独立文档）

| # | 任务 | 文件 | 状态 |
|---|------|------|:--:|
| 4.1 | 统一 inbox→outbox 监控线程 | `daemon.py` | ⏳ |
| 4.2 | 可靠性追踪: 未读超时 → 催问 | `daemon.py:get_pending_reliability()` | ✅ 已有 |
| 4.3 | 广告分类增强: 指纹去重 + 关键词提取 + 写入发送方画像 | `peeka_router.py:classify()` + 新增 `ad_profiler` | ⏳ |
| 4.4 | 多 Agent 同机共存 (各 uid 独立信箱) | `daemon.py` | ✅ 已有 |

## 5. 验收标准

| 场景 | 预期 |
|------|------|
| 用户 A 发 "你好" → Agent B | Daemon L1 自动回复 "你好，请问有什么可以帮忙？" |
| 用户 A 发 "谁在" → Agent B | Daemon L2 回答本机 Agent 列表 |
| 用户 A 发 "帮我查错误日志" → Agent B | L3 进 inbox → Agent 弹出 → Agent 自主回复 |
| 用户 A 发 "最新AI工具推广，免费试用" → Agent B | 分类为广告 → 去重检查 → 首次: 提取关键词("AI工具", "推广") → 写入A的画像, Agent不被打扰; 重复: 丢弃 |
| 同一个 A 再次发相同广告 → Agent B | 指纹命中 → 丢弃（重复不存档） |
| Agent B 查看 A 的画像 | 可见 A 的业务关键词 "AI工具/推广"（从历史广告中提取） |
| Agent 离线期间有 3 条 L1/L2 消息 | Agent 上线时收到 digest 摘要，不被逐条打扰 |

## 6. 与之前 F3 实现的衔接

F3 Sprint 已实现（2026-07-27）:
- `route_incoming()` L1/L2/L3 分流 ✅
- `write_to_inbox()` + `read_inbox()` + `mark_replied()` ✅
- `winpeek_mim_check_inbox` + `winpeek_mim_read_digest` + `winpeek_mim_mark_replied` RPC ✅
- MQTT say→inbox relay ✅
- 可靠性追踪 + chase 催问 ✅

F3 基础上本次补充:
- 统一信箱路径 (`~/.peeka/data/messages/`)
- Daemon outbox 监控 + 自动发送
- `.inject` 写入 (过程3 Hermes 被动弹出)
