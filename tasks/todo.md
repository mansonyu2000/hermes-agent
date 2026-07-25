# MIM Desktop Identity — Task List

## Phase 1: DB Schema

- [ ] **T1**: DB — users 表新增 gender 列, identity_type 规范化
  - Acceptance: `ALTER TABLE users ADD COLUMN gender`; 现有数据不变
  - Verify: `DESCRIBE users` 确认列存在
  - Files: raw SQL (通过 identity.py 执行)
  - Size: XS

## Phase 2: Backend API

- [ ] **T2**: identity.py — user 注册/device 检测/machine 创建
  - Acceptance: `identity.register_user(name, gender, password)` 返回 uid; `identity.check_device(hostname)` 返回 machine info
  - Verify: Python 直接调用测试
  - Files: `gateway/winpeek_hub/identity.py`
  - Size: M

- [ ] **T3**: winpeek_tools.py — 新 RPC: user_register, device_check, squad_list/join/create
  - Acceptance: `winpeek_user_register({name,gender})` 可调; `winpeek_device_check({hostname})` 返回已有或 null
  - Verify: gatewayRequest 调用返回 ok
  - Files: `tools/winpeek_tools.py`
  - Size: M

## Phase 3: Agent 绑定

- [ ] **T4**: daemon.py — Agent 注册必设 master_uid
  - Acceptance: register_and_inject 从本机 User 获取 uid 作为 master_uid
  - Verify: daemon 重新注册已有 Agent, 打印 master_uid
  - Files: `apps/winpeek_injector/daemon.py`
  - Size: S

## Phase 4: Frontend

- [ ] **T5**: LoginPanel — Device 自动检测 + 首次引导
  - Acceptance: 首次打开 MIM → 显示 "首次使用,正在检测电脑..." → 自动注册 Device → 选 User
  - Verify: 清空 localStorage, 打开 MIM 页面
  - Files: `apps/desktop/src/app/winpeek/mim/index.tsx`
  - Size: M

- [ ] **T6**: User/Squad 注册面板 + 联系人性别区分
  - Acceptance: 有 User 注册入口; Squad 创建/加入; 联系人列表显示性别图标
  - Verify: 点击注册 User → 填名+选性别 → 成功; 联系人显示 🚹/🚺/🤖
  - Files: `apps/desktop/src/app/winpeek/mim/index.tsx`
  - Size: M

## Phase 5: E2E

- [ ] **T7**: 手动验证 + commit
  - Acceptance: 全流程 pass
  - Verify: 见 checklist
  - Files: none
  - Size: XS
