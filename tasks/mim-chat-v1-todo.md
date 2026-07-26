---
title: "MIM 聊天 V1 — 任务清单"
type: "todo"
phase: "build"
module: "mim"
version: "v1"
status: "in_progress"
last_updated: "2026-07-26"
zentao_product: 11
zentao_project: 29
zentao_execution: 30
zentao_stories: [117, 118, 119, 120]
---

# MIM 聊天 V1 任务清单

> Zentao: 产品 #11 (peeka数字机器人) | 项目 #29 | Sprint #30

## Phase P1: 好友/联系人管理 (F1) → Story #118

- [ ] F1.1 联系人列表增强 — 按最近消息排序 `[zentao:#45]`
  - 文件: `apps/desktop/src/app/winpeek/mim/index.tsx`
  - 通讯录 tab: 单聊+群聊混合列表，按最近消息时间排序

- [ ] F1.2 搜索添加联系人 — 按昵称/UID/角色/组织搜索 `[zentao:#46]`
  - 后端: `gateway/winpeek_hub/chat.py` → `search_users(q, filters)`
  - 工具: `tools/winpeek_tools.py` → `winpeek_mim_search_users`
  - 前端: 通讯录 tab 搜索框 + 搜索结果列表

- [ ] F1.3 好友请求系统 — 发送/接收/同意/拒绝 `[zentao:#47]`
  - 后端: `chat.py` → `add_contact()`, `list_contact_requests()`
  - 数据库: 新建 `contact_requests` 表
  - 前端: 好友请求通知 + 同意/拒绝按钮

- [ ] F1.4 删除联系人功能 `[zentao:#48]`
  - 后端: `chat.py` → `remove_contact()`
  - 前端: 联系人右键菜单 → 删除确认

- [ ] F1.5 联系人详情页 — 完整信息展示 `[zentao:#49]`
  - 前端: 点击联系人头像 → 展示昵称/性别/角色/组织/职位/技能/简介

- [ ] F1.6 系统用户目录 — 按类型/组织/在线筛选 `[zentao:#50]`
  - 前端: 新增"用户目录"tab → 筛选器 + 用户列表 + 一键添加

## Phase P2: 聊天消息增强 (F2) → Story #119

- [ ] F2.3 消息状态 — 已读/未读/送达指示 `[zentao:#51]`
  - 后端: `chat.py` → 消息状态更新 + 查询
  - 前端: 消息气泡旁显示 ✓/✓✓ 状态图标

- [ ] F2.4 消息搜索 — 按关键词搜索历史消息 `[zentao:#52]`
  - 后端: `chat.py` → `search_history(uid, q, peer_uid, gid)`
  - 前端: 聊天窗口搜索框 + 搜索结果高亮

- [ ] F2.5 消息引用回复 (V2) `[zentao:#53]`
  - 后端: `chat.py` → 引用消息关联
  - 前端: 回复消息显示被引用原文

## Phase P3: 消息→Agent 送达 (F3) → Story #120

- [x] F3.1 Agent inbox — 消息路由到文件系统 `[zentao:#54]` ✅
  - 后端: `chat.py` → `send_message()` → `route_incoming()` L3 → `write_to_inbox()`
  - 格式: `~/.hermes/winpeek/inbox/{agent_uid}/unread/{mid}.json`

- [x] F3.2 Agent 自主读信 — peeka_router 3层转发 `[zentao:#55]` ✅
  - RPC: `winpeek_mim_check_inbox` + `winpeek_mim_poll` (读内存队列+文件inbox)
  - 后端: `peeka_router.py` → Layer 3 → `assemble_context()`
  - daemon: inbox 管理 + reliability 追踪 + chase 催问

- [x] F3.3 Agent 自动回复 — LLM自由回复 + 模板 `[zentao:#56]` ✅
  - RPC: `winpeek_mim_send` → `chat.send_message()` → 完整路由
  - 新增: `winpeek_mim_read_digest` (启动时读取L1/L2摘要)
  - 新增: `winpeek_mim_mark_replied` (标记已回复,关闭追踪)

- [x] F3.4 前端状态指示 — Agent已读/回复状态 `[zentao:#57]` ✅
  - RPC: `winpeek_mim_agent_status` (在线状态+inbox数+pending chase)
  - RPC: `winpeek_mim_local_agents` (本地Agent发现,已暴露@method)

## Phase P4: 安全 + 测试

- [x] 安全: 修复 _handle_mim_update_profile IDOR 漏洞 ✅ (已修复, `57b7b7a0f`)
  - 文件: `tools/winpeek_tools.py`
  - 方案: password 认证, fail-closed

- [ ] 测试: MIM 聊天端到端测试
  - 文件: `tests/test_mim_chat.py`

- [ ] 测试: 好友请求流程测试
  - 文件: `tests/test_mim_contacts.py`

## Phase P5: 文档

- [ ] CHANGELOG 更新
- [ ] 验收报告: `docs/peeka/mim-chat-v1-acceptance.md`
- [ ] 技术文档更新
