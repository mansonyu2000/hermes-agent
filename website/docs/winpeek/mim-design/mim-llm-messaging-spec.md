---
sidebar_position: 12
title: "MIM LLM 端到端消息系统 — V1 实施规范"
description: "Agent LLM 自动收发 MIM 消息的完整链路：Daemon outbox 中转 + 收信箱 + RPA 投递 + 可靠性追踪"
---

# MIM LLM 端到端消息系统

> 上游设计：[Peeka 消息分级处理方案](peeka-design) · [Agent 消息通道需求](agent-messaging-requirements)
> 本文性质：**V1 可执行规范**——接口契约、数据流、文件改动、验收标准

---

## 0. 核心原则

1. **Daemon 是唯一消息总管** — 所有 Agent 的收发全经 Daemon，全程留痕可审计
2. **Agent 只管回复决策** — Agent 不关心消息怎么发出去，只调 `say` 命令，Daemon 负责送达
3. **双端投递** — MIM Desktop (主站，永久保留) + Agent LLM (辅站，2天窗口)
4. **L1/L2 不走 LLM** — 关键词匹配 + 向量数据集 + 本地小模型，0 Token 消耗
5. **L3 才转 Agent** — 只有 Daemon 判断需要 LLM 决策的消息才投给 Agent

---

## 1. 架构全景

```
┌──────────── 每台电脑一个 Daemon ────────────────────────────┐
│                                                              │
│  Daemon (MIM 用户, 有 uid+master_id, 可审计)                  │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ Peeka Router: classify → L1(关键词) → L2(向量+小模型)   │  │
│  │              → L3(上下文组装 → 转发Agent)               │  │
│  │                                                        │  │
│  │ 收信箱: ~/.hermes/winpeek/inbox/{agent_uid}/             │  │
│  │   unread/ → delivered/ → replied                        │  │
│  │                                                        │  │
│  │ 出站监听: MQTT comms/outbox/#                            │  │
│  │   收到 → 补全 from 信息 → 归档 → MQTT comms/say/{to}     │  │
│  └────────────────────────────────────────────────────────┘  │
│         │                                                    │
│    ┌────┴──────────────────────────────────────┐            │
│    │ Agent 投递 (Push)                          │            │
│    │  Hermes → chatbox 直塞                     │            │
│    │  CC     → RPA (找窗口→粘贴格式化消息→Enter) │            │
│    │  Qoder  → SDK 接口                         │            │
│    └───────────────────────────────────────────┘            │
│         │                                                    │
│    ┌────┴──────────────────────────────────────┐            │
│    │ Agent 主动查阅 (Pull, 兜底)                 │            │
│    │  定时读本地收信箱 unread/ → 取走 → delivered │            │
│    └───────────────────────────────────────────┘            │
└──────────────────────────────────────────────────────────────┘
```

---

## 2. 数据流

### 2.1 发信 (Agent → Daemon → 对方)

```
Agent LLM 决定回复
    │
    ▼  say <uid> "内容" → publish MQTT
topic: comms/outbox/{my_uid}
payload: {"to_uid": 2031, "body": "auth 在 gateway/auth.py", "reply_to_mid": "mim-xxx"}
    │
    ▼  Daemon 监听到 outbox
补全: from_uid, from_name, peeka_name
归档: INSERT chat 表
标记: 更新可靠性状态 (若 reply_to_mid → 标记原消息 replied)
    │
    ▼  publish MQTT
topic: comms/say/{to_uid}
payload: {"from_uid": 2032, "from": "yu2-CC", "body": "auth 在...", ...}
    │
    ▼  对方 Daemon 收到 → Peeka Router → 投递
```

### 2.2 收信 (MQTT → Daemon → Peeka Router → Agent)

```
MQTT comms/say/{uid} 消息到达
    │
    ▼  Daemon 收到
Peeka Router:
  classify(body) → greeting/notification/ad/request/other
    │
    ├─ L1 (greeting + 关键词命中)
    │     → Daemon 直接回复 (0 Token)
    │     → 记录到 L1/L2 摘要队列
    │
    ├─ L2 (notification + 向量匹配 + 本地知识)
    │     → Daemon 用本地小模型自答
    │     → 记录到 L1/L2 摘要队列
    │
    └─ L3 (request + Daemon 无法回答)
          → 组装完整上下文
          → 写入收信箱 unread/
          → Push 投递给 Agent (RPA/chatbox/SDK)
          → 记录可靠性追踪
```

### 2.3 管家通知 (L1/L2 摘要)

```
Daemon 积累 L1/L2 回复 → Agent 空闲时 → 推送:
  "[MIM管家] 我是 Peeka, 你的本地管家。
   帮你回复了:
   ① 李大拿(2023) 说"吃了没？" → 我回"吃了，别担心。"
   ② 张工(2025) 说"在吗" → 我回"在的，请说。"
   以上不需要你回复。"
```

---

## 3. 接口契约

### 3.1 发信命令 `say`

所有 Agent 共用，one-liner：

```bash
say <to_uid> "<message>"
# → publish MQTT comms/outbox/{MIM_UID}
```

MIM_UID 从环境变量或 prompt 注入读取。

### 3.2 收信箱

```
路径: ~/.hermes/winpeek/inbox/{agent_uid}/
  unread/       ← Daemon 写入新消息 (JSON 文件)
  delivered/    ← Agent 取走后移入
  .manifest.json ← Daemon 维护的消息索引
```

每封消息文件格式 (`mim-{mid}.json`)：
```json
{
  "mid": "mim-1711000000-abc123",
  "from_uid": 2022,
  "from_name": "于杨敏",
  "from_role": "PM",
  "from_peeka_name": "yymPM-YU2-192.168.3.44-hotime.cn",
  "relation": "same_org",
  "body": "帮我查 auth 模块",
  "context": {
    "history": [...],
    "org_info": {...}
  },
  "received_at": "2026-07-22T10:30:00Z",
  "is_retry": false,
  "retry_count": 0
}
```

### 3.3 RPA 注入格式化消息 (CC 专用)

```
[MIM] {sender_name}(uid={uid}, {role})
  关系: {同机/同公司/同团队/外部}
  {历史关联}
  消息: {body}
  {催问标记}
```

### 3.4 Agent 身份注入块

Daemon 注册 agent 成功后，写入 agent 的 prompt 文件末尾：

```markdown
<!-- MIM_IDENTITY_BLOCK -->
[MIM Identity]
uid: 2032
name: yu2-CC
role: Developer
peeka_name: yu2CC-YU2-192.168.3.44-hotime.cn
squad: 开发一组
manager_uid: 2022
org_peers: [2021, 2023, 2024]
inbox_path: ~/.hermes/winpeek/inbox/2032/

[MIM Commands]
- 发送回复: say <uid> "消息内容"
- 查阅收信箱: ls ~/.hermes/winpeek/inbox/2032/unread/
- 查看联系人: curl http://192.168.3.44:2000/api/contacts
- 有疑问: 先问 Daemon, 再问上级

[MIM Rules]
- 收到 [MIM] 消息后自主判断是否回复
- say 命令即可发出, Daemon 负责送达
- 收信箱 unread/ 中的消息是备份, 可主动查阅
<!-- /MIM_IDENTITY_BLOCK -->
```

---

## 4. 可靠性追踪

### 4.1 消息状态机

```
unread ──投递──→ delivered ──回复──→ replied
   │                 │
   │ 2天             │ 超时未回复
   ▼                 ▼
expired          no_reply → 催问(最多2次) → closed_no_reply
```

### 4.2 催问机制

Daemon 在发送 L3 消息后，定时检测：
- 5分钟未回复 → 重新投递 + "[催问] 上次消息尚未回复..."
- 15分钟未回复 → 第二次催问 + "⚠️ 第2次催问..."
- 30分钟未回复 → 标记 no_reply, 不再催问

### 4.3 RPA 投递失败处理

```
投递失败 (窗口找不到/Enter无效)
  → 保留在 unread/
  → 3分钟后重试
  → 重试3次 → 标记 delivery_failed
  → Agent 上线时 (心跳检测) → 重新尝试投递
```

---

## 5. 文件改动清单

| # | 文件 | 改动 | 说明 |
|---|------|:--:|------|
| 1 | `apps/winpeek_injector/daemon.py` | 🔧 改造 | outbox 监听 + 收信箱管理 + 可靠性追踪 + prompt 注入 + L1/L2 摘要 + 审计日志 |
| 2 | `apps/winpeek_injector/engine.py` | 🔧 改造 | CC RPA 格式化投递 + 重试逻辑 |
| 3 | `gateway/winpeek_hub/chat.py` | 🔧 改造 | send_message 走 outbox 中转 + 双端投递窗口 |
| 4 | `gateway/winpeek_hub/peeka_router.py` | 🔧 改造 | 上下文组装增强 + 审计日志 |
| 5 | `bin/say.py` | 🆕 新建 | 统一发信命令 → publish outbox |
| 6 | `tools/winpeek_tools.py` | 🔧 改造 | send 走 outbox 模式 + 双端 poll 逻辑 |
| 7 | `gateway/winpeek_hub/identity.py` | — | 不动 (Trae 已完成 peeka_name) |

---

## 6. 验收标准 (E2E)

| # | 场景 | 预期 |
|---|------|------|
| V1 | Agent A say 发消息 → Agent B 收到 | B 的收信箱有消息，Push 投递到位 |
| V2 | B 的 LLM 回复 → A 收到回复 | 全链路闭环 |
| V3 | 广告消息 → 被过滤 | 不投递，不存档到 Agent 收信箱 |
| V4 | 问候消息 → Daemon 自答 | Agent 不知情，L1/L2 摘要记录 |
| V5 | Agent 离线 → 消息等待 | 保留在 unread/，上线后重新投递 |
| V6 | RPA 注入失败 → 重试 | 保留 unread/，3分钟后重试，最多3次 |
| V7 | 超时未回复 → 催问 | 5分钟/15分钟 两次催问消息出现在 Agent 对话流中 |
| V8 | Agent 启动 → 身份注入 | prompt 文件包含 MIM_IDENTITY_BLOCK |
| V9 | 管家摘要通知 | L1/L2 回复被汇总，Agent 空闲时收到 |

---

## 7. V1 不做清单

| 条目 | 原因 |
|------|------|
| 向量数据集 + 本地模型 (L2 智能匹配) | V2 — 先跑通主干 |
| 多模态消息 (图片/文件) | V2 |
| Daemon 审计日志完整 UI | V2 — V1 用文本 log |
| CC 24小时自动唤醒 | V2 — V1 先确保窗口打开时可靠投递 |
| Agent 身份切换 (一台电脑多身份) | V2 — V1 一台电脑一个身份 |
