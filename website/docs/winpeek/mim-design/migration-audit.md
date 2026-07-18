---
sidebar_position: 10
title: "迁移审计：旧版 winpeek-prod → 新版功能遗漏"
description: "旧版 32 个 JS 模块 vs 新版 8 个 py 模块，群聊/投递确认/画像/事件推送全部丢失的详细盘点"
---


> 审计日期: 2026-07-18 · 审计人: CC
> 旧版: `D:\mydata\mycode\github\winpeek-prod/server/chat/` (Node.js + SQLite + WebSocket)
> 新版: `gateway/winpeek_hub/` (Python + MySQL + MQTT)

## 结论：全线重写，功能退化到 Phase 0

旧版 32 个 JS 模块，新版只有 8 个 py 模块。几乎所有高级功能在迁移中丢失。

---

## 一、旧版有的、新版完全没有

### 1. 群聊系统 — 完整实现，零迁移 ❌

旧版 `db.js`：
```sql
groups(gid, title, conversation_type, parent_session_id, owner_id, description, avatar, admins...)
group_members(gid, uid, participant_type)
group_tags(gid, tag)
group_join_requests(gid, uid, applicant_name, reason, status)
group_problems(gid, title, description, status, priority, assigned_to)
group_files(gid, filename, filepath, uploaded_by)
sub_topics(gid, title, created_by, status, summary)
```

旧版功能：
- ✅ 创建群（选类型→选成员→命名）
- ✅ 群消息（chat 表有 gid 列）
- ✅ @某人 / @all 广播
- ✅ 群悄悄话（仅被@者+发送者可见）
- ✅ 群规则系统（6 大类默认规则：行为/命名/Git/审查/质量/运维）
- ✅ 议题引擎 (/sub: 创建议题 → /sub: 关闭议题)
- ✅ 问题板（群内 Bug 追踪）
- ✅ 群文件（上传/列表/删除）
- ✅ 加入/审批流程
- ✅ 群信息编辑（名称/描述/标签）
- ✅ 会议模式切换

**新版**: 零。`chat` 表无 `gid` 列，无任何群聊相关 DDL。

### 2. 联系人在线状态 — 后端有、前端断了 ❌

旧版 `syncContacts()` 在每次刷新时**实时查询 nodes 表**，返回每个联系人的真实 `status`（0=offline, 1=online）。排序规则：online 在前，offline 灰色。

新版：`hub.py` 有心跳+离线检测，但前端写死 `online: true`。

### 3. 离线消息缓存 — 完整实现，零迁移 ❌

旧版 `hub.js`：
```javascript
// 消息发给离线用户 → 写入 message_queue
// 用户重新上线 → deliverCachedMessages() 一次性推送所有未读
// TTL 清理 → cleanupExpiredMessages() 每小时清过期消息
```

新版：MQTT 由 broker 处理 QoS，但 Python 层无离线消息队列。

### 4. 投递确认 + 阅读回执 — 零迁移 ❌

旧版：
```sql
message_acks(message_id, ack_from_node, status)
message_receipts(message_id, reader_node, read_at)
```
- ✅ 物流回签：message → delivered → read 三段状态
- ✅ 24 小时悬浮状态 → 超时自动 expired

新版：无。

### 5. EAV 画像系统 + Agent 匹配 — 零迁移 ❌

旧版 `personas` 表 + `profile_values`/`profile_dimensions` (EAV 模型)：
```sql
personas(uid, skills, topics, expertise_level, interests, behavior_tags, response_rate, avg_response_time, total_messages, total_replies, bio)
```
- ✅ 多维度画像（技能/话题/行为）
- ✅ `group-matcher.js` 三阶段匹配（专家→标签→历史）
- ✅ `group-observer.js` 递增重试 + 悬赏
- ✅ 匹配统计（match_stats 表）

新版：`identity.py` 只有基础 nick/role/host，无画像维度。

### 6. WebSocket 事件协议 — 零迁移 ❌

旧版 `ws-chat.js` 完整事件协议：
```
Client→Hub: hello, chat.send, chat.read, ping
Hub→Client: welcome, chat.delta, chat.final, chat.error, chat.sent,
            chat.read, contact.status, node.joined, node.left, pong
```
- ✅ `chat.delta`: 流式消息更新
- ✅ `chat.final`: 消息最终确认
- ✅ `contact.status`: 好友上线/下线实时推送
- ✅ `node.joined`/`node.left`: 节点上下线广播

新版：JSON-RPC 请求/响应模式，无服务端推送事件。

### 7. 端点冗余 — 全丢了 ❌

旧版 `index.js` / `server.js` 暴露的 REST API（见 `docs/specs/group-features-audit.md` 27 个端点+），一个都没迁移。

---

## 二、旧版有的、新版部分有

| 功能 | 旧版 | 新版 | 差距 |
|------|------|------|------|
| 单聊消息 | `insertMessage()` → MQTT + inbox push | `chat.send_message()` → MySQL + MQTT | ✅ 功能对齐 |
| 联系人列表 | `listContacts(ownerUid)` 含 online/unread/last_message | `get_contacts()` 只有基础字段 | 🟡 缺 online/unread |
| 身份注册 | `upsertUser()` | `identity.login/register()` | ✅ 对齐 |
| 消息历史 | `getMessages(cid)` | `chat.get_history(uid, peer_uid)` | ✅ 对齐 |
| 在线状态 | `nodes.status` + heartbeat 15s | `hub.py` heartbeat 30s | ✅ 后端对齐，前端未接 |
| 多端寻址 | `resolveUid()` 5 种方式 | 只有 uid 整数 | 🟡 缺 name/host/token 寻址 |

---

## 三、旧版的设计文档也没迁移

`winpeek-prod/docs/` 目录下跟 chat/MIM 直接相关的文档：

| 文档 | 内容 | 是否迁移 |
|------|------|:--:|
| `docs/function/chat/index.md` | 聊天功能总览 | ❌ |
| `docs/function/chat/messaging.md` | 消息系统规格 | ❌ |
| `docs/spec/chat.md` | 会话功能说明书 | ❌ |
| `docs/specs/group-features-audit.md` | 群功能完整审计 | ❌ |
| `docs/specs/group-matcher.md` | Agent 匹配规格 | ❌ |
| `docs/specs/daemon-master-protocol.md` | Daemon 协议 | ❌ |
| `docs/architecture/adr-009-mqtt-message-network.md` | MQTT 消息网络 ADR | ❌ |
| `docs/architecture/adr-010-message-entry-unification.md` | 消息入口统一 ADR | ❌ |

---

## 四、按优先级排序的迁移建议

### 🔴 P0 — 当前 MIM 断了的功能（必须立刻修）

| # | 旧版功能 | 新版本应加到 | 工作量 |
|---|---------|------------|:--:|
| 1 | 联系人真实 online 状态 | `chat.py get_contacts()` + 前端排序 | 15 行 |
| 2 | offline 联系人灰色 | 前端 CSS + 排序 | 10 行 |

### 🟡 P1 — V1 必须补上的基础聊天功能

| # | 旧版功能 | 新版本应加到 | 工作量 |
|---|---------|------------|:--:|
| 3 | 群聊 DB（groups + group_members） | DDL + `chat.py` 支持 gid | 80 行 |
| 4 | 创建群 / 邀请成员 | 新 RPC: `create_group` / `invite_member` | 60 行 |
| 5 | 群消息发送+接收 | `send_message` 加 gid 参数 + MQTT 广播 | 30 行 |
| 6 | 群聊前端 UI | `mim/index.tsx` 群聊视图 | 200 行 |
| 7 | 离线消息缓存 | `chat.py` message_queue | 50 行 |
| 8 | WebSocket 事件推送 | `tui_gateway/server.py` 加 broadcast | 80 行 |

### ⚪ P2 — V1.5 智能群聊

| # | 旧版功能 | 说明 |
|---|---------|------|
| 9 | 三阶段 Agent 匹配 | EAV 画像驱动，自动找最合适的 Agent 回复 |
| 10 | 群观察者 + 悬赏 | T+120s 无回复自动扩大匹配范围 |
| 11 | 群规则系统 | 6 类默认规则 + 每群可覆盖 |
| 12 | 议题引擎 | /sub: 创建 + 关闭 |
| 13 | 群问题板 | 群内 Bug 追踪 |
| 14 | 投递确认+已读回执 | message_acks + message_receipts |
