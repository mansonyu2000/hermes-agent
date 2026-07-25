---
title: "MIM Desktop 身份自动登录与注册"
status: draft
date: 2026-07-27
---

# Spec: MIM Desktop 身份自动登录与注册

## Objective

Desktop EXE 启动时引导 Peeka User 注册/登录，然后注册本机 MIM Agent 身份。User 登录后可查看其所有 Agent；Squad 用户可查看组织所有成员及 Agent。

### 核心规则

1. **MIM Agent 必须属于一个 Peeka User（真人）** — 主人关系，可变更
2. **User 可直接登录 Desktop** — 登录后查看自己拥有的所有 Agent
3. **User 登录 = Daemon 最高权限** — 可管理本机所有 Agent
4. **Squad 用户** — 可查看 Squad 内所有成员及其 Agent

### 身份四层模型

```
Squad (组织, 有4位注册码)
  │
  ▼
Peeka User (真人, 男/女) ─── 主人 ──→ MIM Agent (无性别)
  │                                      │
  ├── Device (电脑)                      ├── 必须属于一个 User
  │     └── Desktop EXE 登录             ├── 可更换主人
  │         = 本机 Daemon (最高权限)       └── 继承 User 的 Squad
  │
  └── 可登录 Desktop — 查看自己所有 Agent
      Squad 用户 — 查看 Squad 全部成员 + 全部 Agent
```

### 登录流程

```
Desktop EXE 启动
  │
  ├── Step 0: 是否已注册 Peeka User？
  │   ├── YES → 选已有 User → Step 2
  │   └── NO  → Step 1 (注册新 Peeka User)
  │
  ├── Step 1: 注册 Peeka User（真人）
  │       1. 填名字 + 选性别（男/女）
  │       2. 密码: a@123321
  │       3. 注册成功 → Step 2
  │
  └── Step 2: 注册本机 MIM Agent
          1. 自动生成用户名: hostname + 3位随机数 (如 yu2123)
          2. 密码: a@123321 (可见)
          3. 自动绑定到 Step 0 选择的 Peeka User
          4. 注册 Device (hostname+OS+CPU 信息进 machines 表)
          5. 登录 → 进入 MIM 聊天界面
```

### User 登录后的视图

```
User 登录 Desktop:
  ├── 联系人列表: 我的所有 Agent（跨所有电脑）+ Squad 成员 + Squad 成员的 Agent
  ├── Profile: 我的信息 + 我的 Agent 清单
  └── 权限: 本机最高 Daemon 权限
```

## Success Criteria

1. Desktop EXE 首次 → 2 步引导（User → MIM）→ 自动绑定 → 登录成功
2. User 再次登录 → 选已有 User → 自动进入（无需重复注册 MIM）
3. User 登录 → 可查看自己拥有的所有 Agent
4. Squad 用户 → 可查看组织内全部成员及 Agent
5. 联系人列表区分 User (🚹/🚺) vs Agent (🤖)

## Implementation Tasks

- [x] **T1**: `identity.py` — `register_user()` + `check_device()` + `register_device()`
- [x] **T2**: `winpeek_tools.py` — `user_register`, `device_check`, `device_register`, `my_device` RPCs
- [x] **T3**: `daemon.py` — Agent 注册时绑定 `master_uid = device owner`
- [x] **T4**: `index.tsx` — LoginPanel 改为 2 步（Peeka User → MIM）
- [x] **T5**: `index.tsx` — 联系人性别 (🚹/🚺/🤖)
- [ ] **T6**: `chat.py` — `get_contacts` 返回 `gender`/`identity_type` + User 模式返回全部 Agent
- [ ] **T7**: `winpeek_tools.py` — 新增 `winpeek_mim_my_agents` RPC（查 User 的所有 Agent）
- [ ] **T8**: E2E 手动验证 + commit
