# Tasks: Peeka 身份系统 + MIM 聊天 (2026-07-26)

## Phase 1: 后端基础设施
- [x] 重写 `_make_org_handler` — 支持 **kwargs + param_map
- [x] 18 CRUD handler 注册 + 4 delete @method
- [x] 自动发现 + mtime 热重载
- [x] 15 处 `logger.exception` + 敏感字段脱敏
- [x] `_handle_mim_login` 登录严格化（不允许自动注册）
- [x] `_handle_mim_history` 参数顺序修复
- [x] `_is_squad_admin` 表名修复
- [x] `is_owner` 计算修复
- [x] `delete_agent` 表名修复 (agents → ai_agents)

## Phase 2: 前端身份系统
- [x] `types.ts`: saveIdentity/load/remove + peeka-changed dispatch
- [x] `SettingsView`: Peeka nav group (6 tabs) + peeka-changed listener
- [x] `PeekaLoginPanel`: 登录/注册 双模式 + 身份类型选择
- [x] `ProfileTab`: 查看/编辑个人信息 + gender 持久化
- [x] `AccountsTab`: 多账号列表/切换/默认/登录历史
- [x] `PasswordTab`: 改密码 + 强度指示
- [x] `OrganizationTab`: 完整 CRUD + org_type/business_scope/founded_at
- [x] `DevicesTab`: 本机信息 + 注册 + 设备列表
- [x] `AgentsTab`: 列表/在线/编辑/删除
- [x] `PeekaPopup`: 菜单项 → SettingsView Peeka tabs
- [x] `swapAccount`: 写入 identities + mim-active-uid + reload

## Phase 3: MIM 修复
- [x] 联系人列表双重嵌套解析
- [x] 聊天历史参数顺序修复
- [x] MIM 监听 peeka-changed + 退出时清空
- [x] MIM 登录页保留（含注册）
- [x] 消息气泡颜色修复
- [x] 删除 org 注册拦截逻辑

## Phase 4: 文档
- [x] ADR: `docs/decisions/0001-peeka-identity-architecture.md`
- [x] 验收报告: `docs/peeka/acceptance-report.md`
- [x] 技术文档: `docs/peeka/dev-doc-session-2026-07-26.md`
- [x] 功能索引更新: `docs/README.md`
- [x] 经验总结: `memory/peeka-dev-lessons.md`
- [ ] CHANGELOG 更新
- [ ] Git commit

## Phase 5: 待做（下次会话）
- [ ] MIM 好友管理（添加/删除/请求）
- [ ] 消息→Agent 送达（LLM 读信功能）
- [ ] 测试文件 (`test-driven-development`)
