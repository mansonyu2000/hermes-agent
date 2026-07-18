---
sidebar_position: 11
title: "群聊功能规格"
description: "MIM 群聊的数据模型、RPC 接口、前端 UI 规格 — 从旧版 winpeek-prod 提取核心设计"
---


> 版本: v1.0 · 日期: 2026-07-18 · 目标版本: V1.5
> 参考: 旧版 `winpeek-prod/server/chat/` 完整群聊实现 (32 模块, Node.js + SQLite)

## 1. 现状

**当前（hermes-agent-cc）：零群聊。** 前端 `index.tsx` 有 `uid === 0 ? '群'` 占位符但后端从不返回 uid=0 的联系人。

**旧版（winpeek-prod）：完整群聊系统。** 本规格从旧版提取核心设计，适配新架构（Python + MySQL + MQTT）。

## 2. 数据模型

### 2.1 DDL

```sql
-- 群表
CREATE TABLE IF NOT EXISTS m_groups (
    gid         INTEGER PRIMARY KEY AUTO_INCREMENT,
    title       VARCHAR(128) NOT NULL,
    description TEXT,
    avatar      VARCHAR(512),
    owner_id    INTEGER NOT NULL,           -- 群主 uid
    admins      JSON DEFAULT '[]',          -- [uid, ...]
    group_type  VARCHAR(32) DEFAULT 'normal', -- normal / meeting / whisper
    status      TINYINT DEFAULT 1,          -- 1=active, 0=archived
    metadata    JSON DEFAULT '{}',
    created_at  DATETIME DEFAULT NOW(),
    updated_at  DATETIME DEFAULT NOW() ON UPDATE NOW(),
    INDEX idx_groups_owner (owner_id),
    INDEX idx_groups_status (status)
);

-- 群成员表
CREATE TABLE IF NOT EXISTS m_group_members (
    gid         INTEGER NOT NULL,
    uid         INTEGER NOT NULL,
    role        VARCHAR(32) DEFAULT 'member',  -- owner / admin / member
    joined_at   DATETIME DEFAULT NOW(),
    PRIMARY KEY (gid, uid),
    FOREIGN KEY (gid) REFERENCES m_groups(gid) ON DELETE CASCADE
);

-- 群标签表
CREATE TABLE IF NOT EXISTS m_group_tags (
    gid         INTEGER NOT NULL,
    tag         VARCHAR(64) NOT NULL,
    created_by  INTEGER,
    created_at  DATETIME DEFAULT NOW(),
    PRIMARY KEY (gid, tag),
    FOREIGN KEY (gid) REFERENCES m_groups(gid) ON DELETE CASCADE
);

-- chat 表加群聊列（已有表加列，兼容单聊）
ALTER TABLE chat ADD COLUMN gid INTEGER NULL;
ALTER TABLE chat ADD COLUMN mention_uids JSON NULL;  -- @了哪些人

-- 群消息索引
CREATE INDEX idx_chat_gid ON chat(gid);
```

### 2.2 表前缀

全部用 `m_` 前缀，与旧版 `group_*` 区分，避免与 Hermes 核心表名冲突。

---

## 3. 后端 RPC

### 3.1 群 CRUD

| RPC | 参数 | 返回 | 说明 |
|-----|------|------|------|
| `winpeek_mim_group_create` | `{title, description?, member_uids:[], tags?:[]}` | `{ok, gid}` | 创建群，创建者自动成为 owner |
| `winpeek_mim_group_update` | `{gid, title?, description?, avatar?}` | `{ok}` | 更新群信息（仅 owner/admin） |
| `winpeek_mim_group_delete` | `{gid}` | `{ok}` | 解散群（仅 owner） |
| `winpeek_mim_group_detail` | `{gid}` | `{group, members[], tags[]}` | 群详情 |
| `winpeek_mim_group_list` | `{uid}` | `{groups[]}` | 列出我加入的群 |

### 3.2 成员管理

| RPC | 参数 | 返回 | 说明 |
|-----|------|------|------|
| `winpeek_mim_group_invite` | `{gid, uids:[]}` | `{ok}` | 邀请成员（仅成员可邀请） |
| `winpeek_mim_group_join` | `{gid}` | `{ok}` | 申请加入（需审批） |
| `winpeek_mim_group_leave` | `{gid}` | `{ok}` | 退群 |
| `winpeek_mim_group_remove` | `{gid, uid}` | `{ok}` | 踢人（仅 owner/admin） |

### 3.3 群消息

| RPC | 参数 | 返回 | 说明 |
|-----|------|------|------|
| `winpeek_mim_group_send` | `{gid, body, mention_uids?:[]}` | `{ok, mid}` | 发群消息 |
| `winpeek_mim_group_history` | `{gid, limit?}` | `{messages[]}` | 群消息历史 |
| `winpeek_mim_group_poll` | `{gid}` | `{messages[]}` | 群消息轮询 |

### 3.4 群消息路由

```
消息发送者 ──→ MySQL chat 表 (gid={gid})
            ──→ MQTT comms/group/{gid}  ← 所有群成员订阅此 topic
            ──→ enqueue 本地投递 (群成员在同一台机器时)
```

MQTT 新增 topic：`comms/group/{gid}` — 群内全员订阅，单发即全员收。

---

## 4. 前端 UI

### 4.1 群列表

群聊联系人卡片与单聊同结构，区别：
- 头像：**2×2 马赛克**（前 4 个成员首字母），黄色底色 `bg-amber-500/20`
- 名字：群名（如"WinPeek 开发组"）
- 副标题：`{N} 人` 替代 "在线/离线"
- 排序：按群最新消息时间降序，排在所有单聊联系人之后

### 4.2 群聊天视图

与单聊视图完全一致，区别：
- 顶部显示群名 + 成员数
- 每条消息显示发送者名字（`fromName`，因为不是"我/对方"二选一）
- 自己的消息右对齐，他人的左对齐
- 消息内容中的 `@某人` 高亮为蓝色

### 4.3 新建群

```
┌─ 新建群聊 ─────────────────┐
│  群名称: ┌──────────────┐  │
│          │ WinPeek 开发组│  │
│          └──────────────┘  │
│  群描述: ┌──────────────┐  │
│          │ (可选)       │  │
│          └──────────────┘  │
│                            │
│  选择成员:                  │
│  ☑ yuyangmin (PM)         │
│  ☑ yudahai (Architect)    │
│  ☑ BackendCoder (Dev)     │
│  ☐ TestEngineer (QA)      │
│  ☐ Qoder (QA)             │
│                            │
│     [取消]      [创建]     │
└────────────────────────────┘
```

### 4.4 群信息面板（右侧）

```
┌─ 群信息 ───────────────────┐
│  [2×2 马赛克头像]           │
│  WinPeek 开发组             │
│  5 人 · 创建于 2026-07-18   │
│                            │
│  群描述: ...               │
│                            │
│  标签: #开发 #WinPeek       │
│                            │
│  ┌─ 成员 (5) ──────────┐  │
│  │  👤 yuyangmin  群主 │  │
│  │  👤 yudahai    管理 │  │
│  │  👤 BackendCoder    │  │
│  │  👤 Qoder           │  │
│  │  👤 TestEngineer    │  │
│  └────────────────────┘  │
│                            │
│  [+ 邀请成员]              │
│  [退出群聊]               │
└────────────────────────────┘
```

---

## 5. 与单聊的复用关系

| 组件 | 单聊 | 群聊 |
|------|:--:|:--:|
| 消息气泡渲染 | 同一组件 | ✅ 复用 |
| 消息历史 DB 写入 | `chat` 表 `to_uid` 列 | `chat` 表 `gid` 列 |
| MQTT 投递 | `comms/say/{uid}` 点对点 | `comms/group/{gid}` 广播 |
| 本地投递 | `enqueue({to_uid})` | `enqueue({gid})` |
| 消息轮询 | `poll_messages(uid)` | `poll_messages(gid)` |
| 联系人卡片 | 单人头像 | 马赛克多头像 |
| 输入框 | 完全复用 | 完全复用 |

---

## 6. V1.5 扩展（旧版有，选做）

| 功能 | 旧版实现 | 新版建议 |
|------|---------|---------|
| @某人 高亮 | `mention_uids` 字段 | 复用旧版设计 |
| @all 广播 | ws-chat.js L642 | MQTT 广播即可 |
| 群悄悄话 | whisper_session_id 隔离 | 视需求定 |
| 问题板 | group_problems 表 | 独立模块更合适 |
| 群文件 | group_files 表 | 独立模块更合适 |
| Agent 自动匹配 | group-matcher 三阶段 | V2 |
| 议题引擎 | /sub: 命令 | V2 |
| 群规则 | 6 大类默认规则 | V2 |
