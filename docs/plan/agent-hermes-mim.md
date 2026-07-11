# Hermes-htubs24 — MIM 多平台即时通讯 开发计划

> 代码范围: `apps/desktop/.../winpeek/mim/` + `gateway/winpeek_hub/`
>
> PRD: [docs/requirements/mim-prd.md](../requirements/mim-prd.md)
>
> Hub Schema: [plugins/winpeek_rpa/shared/hub_schema.sql](../../plugins/winpeek_rpa/shared/hub_schema.sql)

---

## 代码范围现状

| 层 | 文件 | 当前 | 目标 |
|----|------|------|------|
| 前端 | `mim/index.tsx` | 371行, mock数据 | 真实 MQTT + WebSocket + API |
| 后端 | `hub/identity.py` | ✅ 注册/登录/查询 (JSONL) | HTTP 端点暴露 |
| 后端 | `hub/archive.py` | MySQL 归档 (未联通) | 联通 + 历史查询 API |
| 后端 | `hub/mqtt_adapter.py` | 发送 say | 双向收发 + WebSocket 推送 |
| 后端 | `hub/routing.py` | 跨平台路由 | 完善 |
| 后端 | `hub/tenant.py` | 多租户 | HTTP API 暴露 |
| DB | `hub_schema.sql` | 4 表设计完成 | MySQL 建表 |

---

## 身份系统现状

**后端已验证通过**（Python 直接调用）：

```python
from gateway.winpeek_hub import identity
identity.register('name', 'Developer')   # → {uid, nickname, role, ...}
identity.login('name')                    # → identity or None
identity.list_all()                       # → 所有用户
```

数据存储在 `~/.hermes/winpeek/identities.jsonl`。已注册用户：`test_user`(uid=2001), `yuyangmin`(uid=2002)。

**前端**：localStorage 做客户端身份，可随时对接后端。

**待解决**：Gateway Dashboard auth 拦截了 `/api/mim/*` 路由，需绕过或单独注册。

---

## 版本计划

| 版本 | 内容 | 交付物 |
|------|------|--------|
| **V1.0** | MIM 实时聊天 (MQTT ↔ WebSocket ↔ 前端) + 身份系统 + 消息历史 | 可用聊天 |
| **V2.0** | 跨平台消息路由 + 文件传输 + 群聊 | 完整通讯 |

---

## V1.0 任务

### 设计

| # | 任务 | 依赖 |
|---|------|------|
| B1 | MIM 需求文档 (PRD) | ✅ 已完成 |

### 后端 DB

| # | 任务 | 依赖 |
|---|------|------|
| B1.1 | 执行 hub_schema.sql 建 4 表 | - |
| B1.2 | hub_users 加 `last_heartbeat`, `is_online` | B1.1 |
| B1.3 | hub_messages 加 `is_read`, `ack_at` + FULLTEXT 索引 | B1.1 |
| B1.4 | 新建 `hub_sessions` token 表 | B1.1 |

### 后端 API

| # | 任务 | 依赖 |
|---|------|------|
| B2 | `POST /api/mim/register` — 注册身份 | B1 (需绕过 Dashboard auth) |
| B3 | `POST /api/mim/login` — 登录 | B1 |
| B4 | `GET /api/mim/identity/:uid` — 查询 | B1 |
| B5 | `GET /api/mim/identities` — 列表 | B1 |
| B6 | `GET /api/mim/contacts` — 联系人列表 (含在线状态) | B1.2 |
| B7 | `POST /api/mim/send` — 发送消息 → MQTT publish | - |
| B8 | `GET /api/mim/messages?uid=X` — 历史消息 (分页) | B1.1 |
| B9 | MQTT → WebSocket 推送 (实时消息到前端) | - |
| B10 | 消息已读/送达回执 | B1.3 |

### 前端

| # | 任务 | 依赖 |
|---|------|------|
| B11 | 联系人列表对接 `GET /api/mim/contacts` (替换 mock) | B6 |
| B12 | 聊天窗口对接 `GET /api/mim/messages` + WebSocket 实时 | B8, B9 |
| B13 | 注册页对接 `POST /api/mim/register` (替换 localStorage) | B2 |
| B14 | 登录页对接 `POST /api/mim/login` (替换 localStorage) | B3 |
| B15 | 在线状态动态更新 (心跳 → 绿点/灰点) | B9 |

### 文档

| # | 任务 | 依赖 |
|---|------|------|
| B16 | MIM API 文档 | B2-B10 |

---

## 关键决策

| # | 问题 | 决定 | 原因 |
|---|------|------|------|
| 1 | identity 存 JSONL 还是 MySQL | V1.0 保持 JSONL | 零依赖, hub_users 留给多平台绑定用 |
| 2 | token 是否有必要 | V1.0 暂不实现 | Gateway auth 没打通前用 header uid |
| 3 | Dashboard auth 拦截 | MIM 端点注册为公开路由 | Hub 是独立子系统 |

---

## V2.0 延期

| 功能 | 延期原因 |
|------|----------|
| 跨平台路由 (微信→MIM→钉钉) | V1.0 先通 MIM 内部 |
| 文件/图片传输 | V1.0 聚焦纯文本 |
| 群聊 | V1.0 聚焦点对点 |
| 消息撤回 | V1.0 MVP |
