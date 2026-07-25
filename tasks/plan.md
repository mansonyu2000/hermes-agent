# Implementation Plan: MIM Desktop Identity

## Overview

Desktop EXE 启动自动完成 MIM 登录：首次引导注册 Device + 选 User，后续自动登录。
新增 User 注册入口（真人+性别）。Agent 必选 User 作为主人。

## Architecture Decisions

1. **用 `identity_type` 区分 User vs Agent** — `users` 表已有 `identity_type`: 新增值 `'mim-user'` 表示真人, `'mim-agent'` 表示 Agent。向后兼容 `'mim'` 值。

2. **性别字段** — `users` 表新增 `gender` 列: 'male'/'female'/NULL。NULL = Agent（无性别）。

3. **Device 注册** — 复用已有 `machines` 表。`hostname` 为唯一键。`winpeek_uid` 指向 users.uid。

4. **Agents 已注册的不用改** — 已有 uid=2033(Claude Code)、uid=2034(Hermes Agent) 保留现状，只限制新 Agent 注册时必须设 master_uid。

## Task List

### Phase 1: DB Schema (T1)

- [ ] **T1**: `users` 表 — 新增 `gender` 列 (ENUM 'male','female' NULL)；`identity_type` 规范化

### Phase 2: Backend API (T2-T3)

- [ ] **T2**: `identity.py` — user 注册/device 检测/machine 创建
- [ ] **T3**: `winpeek_tools.py` — 新 RPC: user_register, device_check, squad_list/join/create

### Phase 3: Daemon Agent 绑定 (T4)

- [ ] **T4**: `daemon.py` — Agent 注册必选 master_uid

### Phase 4: Frontend (T5-T6)

- [ ] **T5**: LoginPanel — Device 自动检测 + 首次引导
- [ ] **T6**: User/Squad 注册面板 + 联系人区分

### Phase 5: E2E (T7)

- [ ] **T7**: 手动验证 + commit

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| `users` 表新增 gender 列影响已有查询 | Low | NULL 默认值，所有 SELECT * 不受影响 |
| 已有 Agent 没 master_uid | Low | 向后兼容，只限制新注册 |
