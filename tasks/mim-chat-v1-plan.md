---
title: "MIM 聊天 V1 — 实现计划"
type: "plan"
phase: "plan"
module: "mim"
version: "v1"
status: "in_progress"
last_updated: "2026-07-26"
zentao_product: 11
zentao_project: 29
zentao_execution: 30
zentao_stories: [117, 118, 119, 120]
related:
  - "../docs/peeka/mim-chat-v1-spec.md"
  - "../docs/peeka/settings-v1-dev-doc.md"
  - "../docs/decisions/0001-peeka-identity-architecture.md"
---

# MIM 聊天 V1 实现计划

## 架构决策

1. **不新建独立页面** — MIM 功能增强全部在现有 `apps/desktop/src/app/winpeek/mim/index.tsx` 中扩展
2. **后端沿用 chat.py + winpeek_tools.py 模式** — 新增 RPC handler 走 `_make_org_handler` 工厂，自动发现
3. **消息→Agent 送达复用 peeka_router.py 的三层转发架构** — 不新建消息通道
4. **好友请求表 `contact_requests` 和路由日志表 `message_routes` 需新建** — 见 spec §4 数据模型

## 依赖图

```
F1 (好友管理) ──→ F4 (用户目录)
     │
     └──→ F2 (聊天消息) ──→ F3 (Agent送达)
```

- F1 是基础：没有好友体系，F2/F3 无数据源
- F2 不依赖 F3，可并行
- F3 依赖 F2 的消息模型和 F1 的用户体系

## 实现顺序

| Phase | 功能 | 依赖 | Zentao Tasks |
|-------|------|------|:--:|
| P1 | F1.1-F1.6 好友管理 | 无 | #45-#50 |
| P2 | F4.1-F4.4 用户目录 | F1 | #50 |
| P3 | F2.3-F2.4 消息增强 | F1 | #51-#53 |
| P4 | F3.1-F3.4 Agent送达 | F1+F2 | #54-#57 |

## 验证检查点

1. **P1 完成**: 搜索用户 → 发送好友请求 → 对方同意 → 联系人列表可见
2. **P2 完成**: 用户目录按类型/组织/在线筛选正确
3. **P3 完成**: 消息已读/未读状态正确，关键词搜索能定位历史消息
4. **P4 完成**: 发消息 → Agent inbox 有文件 → Agent 读信 → Agent 回复 → 消息回到聊天窗口
5. **P5 完成**: TypeScript 0 新增错误，Python 测试通过

## 关键文件

| 文件 | 改动类型 |
|------|---------|
| `gateway/winpeek_hub/chat.py` | 新增 5 个函数 |
| `tools/winpeek_tools.py` | 新增 6 个 handler |
| `gateway/winpeek_hub/peeka_router.py` | 增强 route_incoming |
| `apps/desktop/src/app/winpeek/mim/index.tsx` | 大量扩展 |
| `apps/winpeek_injector/daemon.py` | Agent inbox 轮询 |
