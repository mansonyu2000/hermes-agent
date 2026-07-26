---
title: "Peeka 开发文档标准 — 模块分层 + 任务归档规范"
type: "governance"
phase: "plan"
author_subagent: "Claude Code"
version: "1.0"
status: "approved"
last_updated: "2026-07-26"
related:
  - "../../tasks/README.md"
  - "../../peeka/dev-doc-session-2026-07-26.md"
  - "../standards/cluster-rules.md"
---

# Peeka 开发文档标准

## 1. 功能模块树（2层）

所有开发工作按此树归集。每次开发任务必须标注涉及的模块路径。

```
hermes-agent-cc/
├── 系统设置 (settings)          ← /settings, SettingsView
│   ├── Peeka 身份体系           ← /settings?tab=peeka:*
│   │   ├── 个人信息 (profile)
│   │   ├── 切换账号 (accounts)
│   │   ├── 修改密码 (password)
│   │   ├── 我的组织 (organization)
│   │   ├── 我的设备 (devices)
│   │   └── 我的Agent (agents)
│   └── Hermes 系统设置          ← Model/Chat/Appearance/...
│
├── MIM 聊天 (mim)               ← /mim, chat.py
│   ├── 联系人/好友管理
│   ├── 单聊/群聊消息
│   ├── 群聊管理
│   └── 消息→Agent 送达
│
├── Peeka 身份核心 (identity)    ← identity.py, types.ts
│   ├── 用户注册/登录/切换
│   ├── localStorage 身份存储
│   └── peeka-changed 事件同步
│
├── 组织管理 (organization)      ← organization.py
│   ├── 组织 CRUD
│   ├── 成员/设备审批
│   └── Agent 管理
│
├── 后端基础设施 (backend)
│   ├── RPC handler 工厂
│   ├── 自动发现 + 热重载
│   └── 日志/脱敏
│
└── Sidebar/导航 (sidebar)
    └── PeekaPopup
```

## 2. 文档命名规范

**每次开发会话产出的文档，都带模块前缀 + 日期：**

```
docs/
├── peeka/
│   ├── settings-v1-2026-07-26.md        ← 本次系统设置开发
│   ├── settings-v1-acceptance.md         ← 验收报告
│   └── mim-chat-v1-spec.md               ← 下次: MIM 聊天 spec
│
├── tasks/
│   ├── README.md                          ← 任务索引（所有任务列表）
│   ├── settings-v1-2026-07-26.md          ← 本次任务清单
│   └── mim-chat-v1-plan.md                ← 下次: MIM 聊天 plan
│
├── decisions/
│   └── 0001-peeka-identity-architecture.md ← ADR (全局编号)
│
└── CHANGELOG.md                           ← 全局变更日志
```

**规则：**
- specs: `docs/{module}/{module}-{version}-{date}-spec.md`
- plans: `docs/tasks/{module}-{version}-plan.md`
- todos: `docs/tasks/{module}-{version}-todo.md`
- 验收报告: `docs/{module}/{module}-{version}-acceptance.md`
- 技术文档: `docs/{module}/{module}-dev-doc-{date}.md`

## 3. 任务启动时的上下文加载流程

当新 agent 接手一个模块的开发任务时，按以下顺序加载上下文：

```
┌─────────────────────────────────────────────────┐
│ Step 1: 读 tasks/README.md                      │
│   → 找到对应模块的任务文件路径                    │
│   → 了解该模块之前完成了什么、待做什么             │
├─────────────────────────────────────────────────┤
│ Step 2: 读 docs/{module}/ 下的 spec + acceptance │
│   → 了解该模块的完整功能规格 + 验收标准            │
├─────────────────────────────────────────────────┤
│ Step 3: 读 docs/{module}/-dev-doc-{date}.md     │
│   → 了解上次开发的技术细节（架构/代码位置/RPC）   │
├─────────────────────────────────────────────────┤
│ Step 4: 读 memory/ 中的相关记忆                  │
│   → 了解经验教训、已知 bug                       │
├─────────────────────────────────────────────────┤
│ Step 5: 读 docs/CHANGELOG.md                    │
│   → 了解全局变更历史                             │
├─────────────────────────────────────────────────┤
│ Step 6: 加载 CLAUDE.md + 相关 skills             │
└─────────────────────────────────────────────────┘
```

## 4. 禁止事项（避免破坏式手术）

| 禁止 | 原因 |
|------|------|
| 直接修改 `_make_org_handler` 而不读 param_map 文档 | 会破坏 18 个 handler |
| 在 `server.py` 中新增 `@method` 而不利用自动发现 | 增加维护负担 |
| 修改 `types.ts` 的 `saveIdentity` 而不 dispatch `peeka-changed` | 破坏全局同步 |
| 在 MIM 中添加登录页面的账号注册逻辑 | 登录入口是 Peeka，不是 MIM |
| 修改 `organization.py` 函数签名而不更新 param_map | 会导致 RPC 参数丢失 |
