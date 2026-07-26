# Changelog

## [Peeka v4] — 2026-07-26

### Added
- Peeka 身份系统集成到 SettingsView (`/settings?tab=peeka:*`) — 6 tabs: profile, accounts, password, organization, devices, agents
- 全局身份同步机制: `peeka-changed` CustomEvent
- 设备管理页 (DevicesTab): 本机信息 + 注册 + 设备列表
- 组织管理增强: `org_type`, `business_scope`, `founded_at` 字段
- 18 CRUD handler + 4 delete @method + RPC 自动发现
- 15 处 `logger.exception` + 敏感字段脱敏
- PeekaLoginPanel: 登录/注册双模式 + 身份类型选择
- AccountsTab: 多账号管理 + 登录历史 + 添加老账户 vs 注册新号
- PasswordTab: 密码强度指示器
- AgentsTab: 在线状态 + 编辑/删除
- ADR: `docs/decisions/0001-peeka-identity-architecture.md`
- 验收报告: `docs/peeka/acceptance-report.md`
- 技术文档: `docs/peeka/dev-doc-session-2026-07-26.md`

### Fixed
- `upsert_squad` 用 name 匹配导致改名→新增（改为 squad_id 匹配）
- MIM 联系人列表为空（双重嵌套解析）
- 聊天历史参数顺序错误（limit 被当成 gid）
- 登录绕过密码（`login or register`→严格 login only）
- `isOwner` 始终 true（person_id 取错）
- `_is_squad_admin` 用错表（users.master_uid→winpeek_accounts.person_id）
- `delete_agent` 表名错误（agents→ai_agents）
- `_make_org_handler` **kwargs 丢弃
- 前端→后端参数名不匹配（uid vs requester_uid）
- MIM 被组织注册检查挡住
- PeekaPopup swapAccount 不同步

### Changed
- Peeka 功能全部收敛到 `/settings` → Peeka nav group（不污染 Hermes 核心）
- MIM 不再强制要求加入组织
- `_handle_mim_login` 不再自动注册用户
- `window.dispatchEvent('storage')` → `CustomEvent('peeka-changed')` 用于同页同步

### Known Issues (Next Session)
- MIM 好友管理（添加/删除/请求）未实现
- 消息→Agent 送达（LLM 读信功能）未实现
- 未提交测试文件（`test-driven-development` 要求）
- Git 零提交 — 代码仍在 working tree
