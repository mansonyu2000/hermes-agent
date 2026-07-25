---
title: "MIM Desktop 身份自动登录与注册"
status: draft
date: 2026-07-26
---

# Spec: MIM Desktop 身份自动登录与注册

## Objective

Desktop EXE 启动时自动完成 MIM 登录：首次自动注册 Device + 引导选 User，后续自动取已注册身份直接登录。新增 User 注册入口，支持 User → Squad 组织归属。修正 Agent 必须属于 User 的主人关系。

### 身份四层模型

```
Squad (组织, 有4位注册码)
  │
  ▼
User (真人, 男/女) — 主人
  │
  ├── Device (电脑, hostname+OS+CPU+GPU)
  │     └── Desktop EXE 登录 = 本机 Daemon
  │
  └── Agent (MIM Agent, 无性别)
        └── 必属于一个 User, 可更换主人
```

### 登录流程

```
Desktop EXE 启动
  │
  ├── hostname 已在 machines 表?
  │   ├── YES → 取 winpeek_uid → login → 进入 MIM
  │   │
  │   └── NO → 首次引导:
  │       1. 注册 Device: hostname + OS + CPU + GPU
  │       2. 生成本机登录名: hostname + 3位随机数 (如 yu2123)
  │       3. 密码: a@123321 (可见)
  │       4. 选 User: 已有列表 or 新建 User
  │       5. 注册本机 UID → login → 进入 MIM
  └──
```

## Tech Stack

- Backend: Python (`gateway/winpeek_hub/identity.py`, `tools/winpeek_tools.py`)
- Frontend: React + TypeScript (`apps/desktop/src/app/winpeek/mim/index.tsx`)
- DB: MySQL `winpeek-db2` — 已有表 `users`, `machines`, `persons`, `squads`
- MQTT: `192.168.3.23:1883` — 身份通知

## Commands

```bash
# Backend tests
python -m pytest tests/ -x -q

# Desktop dev
cd apps/desktop && npm run dev

# Syntax check all changed files
python -c "import py_compile; [py_compile.compile(f, doraise=True) for f in ['gateway/winpeek_hub/identity.py', 'tools/winpeek_tools.py', 'apps/winpeek_injector/daemon.py']]"
```

## Project Structure

```
gateway/winpeek_hub/
  identity.py          ← 改造: register/login/get_by_uid → 支持 user_type
  organization.py      ← 已有: squads/persons/machines CRUD
  chat.py              ← 已有: get_contacts 区分 User/Agent
tools/
  winpeek_tools.py     ← 改造: _handle_mim_login + 新增 _handle_user_register
apps/desktop/src/app/winpeek/mim/
  index.tsx            ← 改造: LoginPanel + 新增 UserRegisterPanel + DeviceRegisterPanel
apps/winpeek_injector/
  daemon.py            ← 改造: Agent 注册必选 master_uid
DB: winpeek-db2
  users                ← 已有: uid/nickname/role/master_uid
  machines             ← 已有: hostname/person_id/winpeek_uid/cpu/gpu
  persons              ← 已有: id/name/squad_id
  squads               ← 已有: id/name/invite_code
```

## Code Style

已有代码风格——匹配现有 `identity.py` 和 `index.tsx` 的命名和组织方式，不引入新范式。

```python
# identity.py 风格：函数式 + Optional 返回 + logging
def register(nickname: str, role: str = "Developer", host: str = "local", password: str = "") -> dict | None:
    ...

# react 风格：useCallback + useMemo + 现有组件体系
const handleLogin = useCallback(async (name: string, password: string) => { ... }, [])
```

## Testing Strategy

- 语法检查: `py_compile.compile(doraise=True)` 对每个 .py 文件
- 手动 E2E: Desktop EXE 启动 → 首次引导 → 登录 → 聊天
- Unit (V2): identity.py 的 register/login 已有 DB 直连测试
- 本次不写自动化测试——前端是 manual E2E，后端改的不多

## Boundaries

- **Always:** 匹配现有 identity.py 风格、不改 machines/persons/squads 表结构
- **Ask first:** 改 `users` 表 DDL（如需加 user_type 列）
- **Never:** 删已有用户/机器数据、改现有 API 签名（除非向后兼容）

## Success Criteria

1. Desktop EXE 首次启动 → 自动检测 hostname → 引导注册 Device → 选 User → 登录成功
2. Desktop EXE 再次启动 → 自动取 winpeek_uid → login → 无任何提示，直接进 MIM
3. 新增 User 注册入口 → 填名+选性别 → 注册成功 → 可选创建/加入 Squad
4. Daemon 注册 Agent 时 → must have master_uid → 继承 User 的 Squad
5. 联系人列表区分 User (男/女) vs Agent (无性别图标)

## Implementation Tasks

- [ ] **T1**: `identity.py` — 新增 `user_type` 字段支持（User/Agent）, `register_user()` 独立注册
- [ ] **T2**: `winpeek_tools.py` — 新增 `winpeek_user_register` RPC, `_handle_mim_login` 改为 login-or-register
- [ ] **T3**: `daemon.py` — Agent 注册时传 `master_uid`, 读取已在本机登录的 User uid
- [ ] **T4**: `index.tsx` — LoginPanel 改成 Device 自动检测 + User 选择/注册流程
- [ ] **T5**: `index.tsx` — 联系人列表 + Profile 面板显示性别/User类型图标
- [ ] **T6**: `chat.py` — `get_contacts` 返回 `user_type` 字段区分 User/Agent
- [ ] **T7**: E2E 手动验证 + commit
