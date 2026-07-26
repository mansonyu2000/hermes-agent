---
title: "MIM 聊天系统 V1 — 功能需求规格说明书"
type: "requirements"
phase: "plan"
author_subagent: "Claude Code"
version: "1.0"
status: "draft"
last_updated: "2026-07-26"
module: "mim"
parent_module: "Peeka"
related:
  - "../settings-v1-2026-07-26.md"
  - "../../tasks/settings-v1-todo.md"
  - "../../decisions/0001-peeka-identity-architecture.md"
---

# MIM 聊天系统 V1 功能需求规格

## 1. 模块定位

MIM（Multi-Instance Messaging）是 Peeka 的内建即时通讯系统，对标企业微信/钉钉的 IM 核心功能。它不是独立的聊天软件，而是 **Hermes Agent 网络的消息通道**——消息的终点不仅是人，更是 Agent。

### 与业界 IM 的差异

| 特性 | 微信 | 企微/钉钉 | **MIM (Peeka)** |
|------|------|----------|-----------------|
| 用户体系 | 手机号注册 | 企业通讯录 | **Peeka 身份**（人类+Agent混合） |
| 联系人发现 | 手机号/二维码 | 组织架构自动同步 | **全网搜索+UID直达+好友请求** |
| 消息终点 | 人 | 人 | **人 + Agent（LLM 可读信回复）** |
| 工作/生活分离 | 不分 | 工作为主 | 多身份自由切换，按需隔离 |

---

## 2. 功能树（2层模块分类）

```
MIM 聊天 (mim)
│
├── F1. 好友/联系人管理
│   ├── F1.1 联系人列表（单聊+群聊混合，按最近消息排序）
│   ├── F1.2 搜索添加联系人（按昵称/UID/角色/组织搜索）
│   ├── F1.3 好友请求（发送/接收/同意/拒绝）
│   ├── F1.4 删除联系人
│   ├── F1.5 联系人详情（头像/昵称/性别/角色/组织/职位/技能/简介）
│   └── F1.6 系统用户目录（所有注册用户，按身份类型分类：人类/Agent）
│
├── F2. 聊天消息
│   ├── F2.1 单聊（发送/接收/历史/轮询3s）
│   ├── F2.2 群聊（创建/加入/退出/解散）
│   ├── F2.3 消息状态（已读/未读/送达）
│   ├── F2.4 消息搜索（按关键词搜索历史消息）
│   ├── F2.5 消息引用回复
│   └── F2.6 文件/附件发送（txt/md/json/代码文件）
│
├── F3. 消息→Agent 送达（核心差异化功能）
│   ├── F3.1 消息路由到 Agent inbox
│   ├── F3.2 Agent 自主读信（peeka_router.py 3层转发）
│   ├── F3.3 Agent 自动回复（模板/LLM自由回复）
│   ├── F3.4 消息在 Agent 对话中呈现
│   └── F3.5 模板消息（问候/通知/提醒等预定义模板）
│
└── F4. 系统用户目录（F1.6 的扩展）
    ├── F4.1 按身份类型筛选（人类/Agent/全部）
    ├── F4.2 按组织筛选
    ├── F4.3 按在线状态筛选
    └── F4.4 一键发起聊天/添加好友
```

---

## 3. 当前状态 vs 目标状态

| 功能 | 当前 | 目标 |
|------|:--:|:--:|
| F1.1 联系人列表 | ✅ 有数据，44 contacts | ✅ |
| F1.2 搜索添加联系人 | ❌ 无 | ✅ |
| F1.3 好友请求 | ❌ 无 | ✅ |
| F1.4 删除联系人 | ❌ 无 | ✅ |
| F1.5 联系人详情 | ✅ 点击头像查看 | ✅ |
| F1.6 系统用户目录 | ❌ 通讯录tab只显示好友 | ✅ 新增"用户目录"视图 |
| F2.1 单聊 | ✅ 收发消息正常 | ✅ |
| F2.2 群聊 | ✅ 创建/加入/发消息 | ✅ |
| F2.3 消息状态 | ❌ 无 | ✅ 已读/未读/送达 |
| F2.4 消息搜索 | ❌ 无 | ✅ |
| F2.5 引用回复 | ❌ 无 | ⬜ V2 |
| F2.6 文件发送 | ✅ 支持 .txt/.md 等 | ✅ |
| F3.1 Agent inbox | ❌ 无 | ✅ |
| F3.2 Agent 读信 | ❌ 无 | ✅ |
| F3.3 Agent 回复 | ❌ 无 | ✅ |
| F3.4 消息在Agent对话中 | ❌ 无 | ✅ |
| F3.5 模板消息 | ⚠️ 部分（peeka_router 有 greeting 模板） | ✅ |
| F4.1-F4.4 | ❌ 无 | ✅ |

---

## 4. 数据模型

### 已有表（直接用）
```sql
-- chat.py 管理
chat (mid, cid, from_uid, to_uid, gid, role, content, from_type, created_at, sent_at, direction, delivery_status)
contacts (uid, contact_uid, nickname, status, ...)
group_members (gid, uid, user_role, participant_type, joined_at)

-- identity.py 管理
users (uid, nickname, role, hostname, identity_type, gender, peeka_name, title, bio, skills, manager_uid, ...)

-- organization.py 管理
squads, persons, machines, ai_agents
```

### 新增表需求
```sql
-- 好友请求表（F1.3）
CREATE TABLE contact_requests (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    from_uid INT NOT NULL,          -- 发起者
    to_uid INT NOT NULL,            -- 接收者
    message VARCHAR(256),           -- 附加消息
    status VARCHAR(16) DEFAULT 'pending', -- pending/accepted/rejected
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_request (from_uid, to_uid)
);

-- 消息→Agent 路由日志（F3）
CREATE TABLE message_routes (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    msg_mid VARCHAR(64),            -- chat.mid
    from_uid INT,
    to_uid INT,
    agent_uid INT,                  -- 目标 Agent uid
    route_action VARCHAR(16),       -- auto_reply/daemon_answer/forward/drop
    route_tag VARCHAR(16),          -- greeting/notification/ad/request/other
    agent_response TEXT,            -- Agent 回复内容
    routed_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## 5. 修改清单（按功能模块）

### F1. 好友/联系人管理

| 文件 | 改动 |
|------|------|
| `gateway/winpeek_hub/chat.py` | 新增 `add_contact(uid, target_uid, message)`, `remove_contact(uid, target_uid)`, `list_contact_requests(uid)`, `search_users(q, filters)` |
| `tools/winpeek_tools.py` | 新增 4 个 handler + registry: `winpeek_mim_add_contact`, `winpeek_mim_remove_contact`, `winpeek_mim_contact_requests`, `winpeek_mim_search_users` |
| `apps/desktop/src/app/winpeek/mim/index.tsx` | 通讯录 tab 加搜索框 + 用户目录视图 + 好友请求管理 |

### F2. 聊天消息

| 文件 | 改动 |
|------|------|
| `gateway/winpeek_hub/chat.py` | 新增 `search_history(uid, q, peer_uid, gid)` |
| `tools/winpeek_tools.py` | 新增 `winpeek_mim_search_history` handler |
| `apps/desktop/src/app/winpeek/mim/index.tsx` | 聊天窗口加搜索框 + 消息状态指示 |

### F3. 消息→Agent 送达

| 文件 | 改动 |
|------|------|
| `gateway/winpeek_hub/peeka_router.py` | 增强 `route_incoming`: 写入 Agent inbox 文件、记录路由日志 |
| `tools/winpeek_tools.py` | 新增 `winpeek_mim_check_inbox`, `winpeek_mim_agent_reply` |
| `apps/winpeek_injector/daemon.py` | Agent inbox 轮询 + 自主回复逻辑 |
| `apps/desktop/src/app/winpeek/mim/index.tsx` | 消息旁显示 Agent 已读/回复状态 |

### F4. 系统用户目录

| 文件 | 改动 |
|------|------|
| `apps/desktop/src/app/winpeek/mim/index.tsx` | 新增"用户目录"tab: 筛选/排序/一键发消息 |

---

## 6. 数据流动线（关键路径）

### 路径 A: 用户A 发消息 → 用户B 的 Agent 读到 → Agent 回复
```
用户A 在 MIM 发消息
  → chat.py send_message() → INSERT chat 表
  → MQTT publish → 用户B 的 MIM 收到（poll）
  → peeka_router.py route_incoming() → Layer 3
    → 写入 Agent inbox 文件: ~/.hermes/winpeek/inbox/{agent_uid}/unread/{msg_id}.json
    → daemon 检测到新文件 → 通知 Agent
    → Agent 自主决策: 回复/忽略/转人工
    → Agent 调用 say <uid> "回复内容" → chat.py send_message() → 用户A 收到回复
```

### 路径 B: 搜索添加好友
```
用户A 在 MIM 通讯录搜索 "张三"
  → winpeek_mim_search_users({q:"张三", filters:{identity_type:"mim-user"}})
  → chat.py search_users() → SELECT * FROM users WHERE nickname LIKE '%张三%'
  → 返回结果列表（头像/昵称/角色/组织/UID）
  → 点击"添加好友" → winpeek_mim_add_contact({uid, target_uid, message})
  → INSERT contact_requests → 用户B 收到请求通知
  → 用户B 同意 → UPDATE status='accepted' → INSERT contacts
```

---

## 7. 验证计划

### 后端
```
python -c "
# F1: 搜索用户 + 添加好友请求 + 同意
# F2: 搜索历史消息
# F3: route_incoming → Agent inbox 文件存在
# F4: 用户目录按类型筛选
"
```

### 前端
```
npx tsc --noEmit  # 零新增错误
```

### E2E
1. 搜索 → 添加好友 → 对方收到请求 → 同意 → 好友列表可见
2. 发消息 → Agent inbox 有文件 → Agent 读信 → Agent 回复 → 消息回到聊天窗口
3. 用户目录 → 按"人类/Agent"筛选 → 正确分组
