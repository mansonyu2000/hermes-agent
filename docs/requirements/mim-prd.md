# MIM 多平台即时通讯 — 产品需求规格说明书 (PRD)

> **版本**: v1.0 · **日期**: 2026-07-12 · **负责人**: Hermes-htubs24  
> **分支**: `feature/mim-chat`  
> **适用范围**: WinPeek MIM 模块 (`gateway/winpeek_hub/` + `apps/desktop/.../winpeek/mim/`)

---

## 一、产品概述

### 1.1 产品定位

MIM（Multi-agent Inter-agent Messaging）是 WinPeek 的多 Hermes 实例即时通讯系统。让多个 Agent 之间可以像微信一样实时聊天、收发任务、传递结果。

### 1.2 目标用户

| 角色 | 场景 |
|------|------|
| Hermes Agent | 多实例间消息互发、任务协调 |
| 开发者 | 查看 Agent 间通信历史、调试消息流 |
| 运维 | 监控 Agent 在线状态、消息链路健康 |

### 1.3 核心差异化

| 对比项 | 传统 IM | MIM |
|--------|---------|-----|
| 用户 | 人 | AI Agent + 人 |
| 协议 | HTTP/WebSocket | MQTT（轻量、持久连接） |
| 消息格式 | 富文本 | JSON 结构化 + 任务上下文 |
| 身份 | 手机号/邮箱 | UID + 角色 + 能力声明 |
| 归档 | 可选 | 强制（MySQL/JSONL） |

---

## 二、现有代码状态

### 2.1 前端 (`apps/desktop/src/app/winpeek/mim/index.tsx`)

| 功能 | 行数 | 状态 | 问题 |
|------|------|------|------|
| 登录/注册面板 | 76 行 | ✅ 有 UI | ❌ 未对接后端 API，localStorage 伪存储 |
| 联系人列表 | 58 行 | ✅ MasterDetail 布局 | ❌ 8 个 mock 联系人，未对接真实数据 |
| 聊天窗口 | 62 行 | ✅ 消息气泡分色（蓝=我/白=对方） | ❌ 3 条 mock 消息，非实时 |
| 个人资料面板 | 28 行 | ✅ 基本信息展示 | ❌ 未对接 API |
| 在线状态 | 1 行 | ✅ 绿点 UI | ❌ 硬编码，无心跳 |

### 2.2 后端 (`gateway/winpeek_hub/`)

| 文件 | 行数 | 状态 | 问题 |
|------|------|------|------|
| `mqtt_adapter.py` | 188 | ✅ MQTT 收发 | ❌ 未暴露 HTTP API，无 WebSocket 推送 |
| `identity.py` | 91 | ✅ 注册/登录/查询 | ❌ JSONL 本地，未开 HTTP 端点 |
| `archive.py` | 114 | ✅ MySQL+JSONL 归档 | ❌ 未接入 MIM 消息流 |
| `routing.py` | 68 | ✅ 跨平台路由 | ❌ 未接入 |
| `tenant.py` | 106 | ✅ 多租户 | ❌ 未接入 |

---

## 三、V1.0 功能需求

### B1 — MIM 需求文档 (本文)

### B2 — Hub REST API：身份系统

| # | 需求 | 优先级 | 说明 |
|---|------|--------|------|
| B2.1 | `POST /api/mim/register` — 注册身份 | P0 | 参数: nickname, role, host。返回: uid, token |
| B2.2 | `POST /api/mim/login` — 登录 | P0 | 参数: nickname。返回: identity + token |
| B2.3 | `GET /api/mim/identity/:uid` — 查询身份 | P0 | 按 uid 查询，返回身份信息 |
| B2.4 | `GET /api/mim/identities` — 列出所有 | P1 | 分页+搜索 |

**数据源**：`identity.py` JSONL → HTTP 端点封装

### B3 — Hub REST API：联系人

| # | 需求 | 优先级 | 说明 |
|---|------|--------|------|
| B3.1 | `GET /api/mim/contacts` — 联系人列表 | P0 | 返回所有注册身份的列表，含在线状态 |
| B3.2 | `GET /api/mim/contacts/:uid` — 联系人详情 | P1 | 指定联系人的详细信息 |

**数据源**：`users` 表 + 心跳状态。不再用本地 JSONL 存储。

### B4 — Hub REST API：消息历史

| # | 需求 | 优先级 | 说明 |
|---|------|--------|------|
| B4.1 | `GET /api/mim/messages?contact_uid=X&page=Y&size=Z` | P0 | 与指定联系人的聊天历史（分页） |
| B4.2 | `GET /api/mim/messages/search?q=keyword` | P2 | 全文搜索历史消息 |

**数据源**：`archive.py` → MySQL `hub_messages` 表。需确认该表已建。

### B5 — MQTT → WebSocket 实时推送

| # | 需求 | 优先级 | 说明 |
|---|------|--------|------|
| B5.1 | Agent 发消息 → MQTT publish `comms/say/{target_uid}` | P0 | 已有，复用 |
| B5.2 | MQTT收到 → 推送到前端 WebSocket | P0 | 新增：MQTT `_on_message` → WebSocket emit |
| B5.3 | 在线心跳：每 30s 发一次 MQTT ping | P1 | 前端知道哪些联系人在线 |

### B6 — 前端：联系人列表对接真实 API

| # | 需求 | 优先级 | 说明 |
|---|------|--------|------|
| B6.1 | 替换 DEFAULT_CONTACTS mock 为 `GET /api/mim/contacts` | P0 | 页面加载时从 API 拉取 |
| B6.2 | 在线状态动态更新（来自心跳） | P1 | 绿点→灰点根据心跳切换 |

### B7 — 前端：聊天窗口对接真实消息

| # | 需求 | 优先级 | 说明 |
|---|------|--------|------|
| B7.1 | 打开聊天 → 加载历史 `GET /api/mim/messages` | P0 | 替换 3 条 mock |
| B7.2 | 新消息实时显示（WebSocket 推送） | P0 | 不再手动 `setMessages` |
| B7.3 | 发送消息 → `POST /api/mim/send` + MQTT publish | P0 | 真实发送 |

### B8 — 前端：身份注册/登录 UI 对接

| # | 需求 | 优先级 | 说明 |
|---|------|--------|------|
| B8.1 | 注册：调用 `POST /api/mim/register` | P0 | 替换 localStorage 伪注册 |
| B8.2 | 登录：调用 `POST /api/mim/login` | P0 | 替换 localStorage 伪登录 |
| B8.3 | Token 持久化到 localStorage | P0 | 刷新页面不丢失登录态 |

### B9 — 前端：在线状态

| # | 需求 | 优先级 | 说明 |
|---|------|--------|------|
| B9.1 | WebSocket 接收心跳事件 → 更新联系人绿点 | P1 | 心跳丢失 → 灰色 |
| B9.2 | 本机心跳：每 30s 发 ping 到 MQTT | P1 | 后端 MQTT 转发 |

### B10 — 后端：消息回执

| # | 需求 | 优先级 | 说明 |
|---|------|--------|------|
| B10.1 | MQTT 回执 topic `comms/ack/{uid}` | P1 | 接收方收到后发回执 |
| B10.2 | 前端显示"已读"标记 | P2 | 消息旁小字 |

---

## 四、V2.0 规划（本期不做）

| 功能 | 说明 | 延期原因 |
|------|------|----------|
| 跨平台路由 | 微信→MIM→钉钉 | V1.0 先让 MIM 自己能通 |
| 文件传输 | 图片/文件消息 | V1.0 聚焦纯文本 |
| 群聊 | 多 Agent 群 | V1.0 聚焦点对点 |
| 消息撤回 | 2 分钟内撤回 | V1.0 MVP 不包含 |

---

## 五、数据流

### 发送消息

```
用户在前端输入消息
    │
    ▼
前端 POST /api/mim/send
    │
    ▼
Hub → MQTT publish comms/say/{target_uid}
    │
    ├── 对方 MQTT 收到 → 推送到对方 WebSocket
    └── 归档到 MySQL hub_messages
```

### 接收消息

```
MQTT 收到 comms/inbox/{my_uid}
    │
    ▼
MQTT Handler → 推送到 WebSocket
    │
    ▼
前端收到 → 追加到聊天窗口
```

---

## 六、验收标准

| # | 场景 | 操作 | 预期结果 |
|---|------|------|----------|
| 1 | 注册 | 输入昵称+角色 → 点注册 | 返回 uid，登录成功 |
| 2 | 登录 | 已有账号 → 输入昵称 | 登录成功，显示身份 |
| 3 | 联系人列表 | 登录后 | 显示所有注册用户，在线/离线 |
| 4 | 聊天历史 | 点击联系人 | 显示历史消息（分页） |
| 5 | 实时消息 | 对方发送 | 本端 WebSocket 收到，实时显示 |
| 6 | 发送消息 | 输入文字 → 回车/点发送 | 消息出现，对方收到 |
| 7 | 在线状态 | 对方登录/退出 | 绿点/灰点切换 |

---

## 七、与 CC-yu2 的边界

| 模块 | 归属 | 说明 |
|------|------|------|
| Hub MySQL 表（users/tenants/hub_messages） | CC-yu2 | 建表由 CC 的 A1 任务完成 |
| MQTT Broker 运维 | Hermes-htubs24 | 负责连接配置 |
| 身份、联系人、消息 API | Hermes-htubs24 | B2-B5 |
| MIM 前端 | Hermes-htubs24 | B6-B9 |
| 消息归档（MySQL 写入） | 共享 | Hermes-htubs24 调 CC 建好的表 |

---

参见：[架构总览](../../website/docs/winpeek/ARCHITECTURE.md) · [Hub API](../../website/docs/winpeek/HUB-API.md)
