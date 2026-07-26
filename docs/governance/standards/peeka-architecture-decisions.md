# ADR: Peeka 身份系统架构决策

## ADR-001: Peeka 合并到 SettingsView

**状态**: Accepted (2026-07-26)

**背景**: v1 创建了独立的 `/peeka` overlay（9 个 tab），但用户测试发现与 `/settings`（15 个 tab）有 4 处功能重叠（API服务/更新/设置/帮助）。

**决策**: 删除 `/peeka` overlay，将 Peeka 身份管理作为 "Peeka" nav group 整合进 SettingsView。

**理由**:
- `/settings` 是成熟的 overlay 系统，天然支持多数据源
- 单一入口减少用户认知负担
- SettingsView 的子导航和 `?tab=` 参数路由可复用
- 避免两套 overlay 的维护负担

**替代方案**:
- 保持独立 overlay → 用户面对两套设置，功能重复
- Peeka 独立窗口 → 增加 Electron window 管理复杂度

---

## ADR-002: 身份系统使用 localStorage（非服务端 session）

**状态**: Accepted (2026-07-26)

**背景**: Peeka 登录/切换账号依赖 localStorage 中的 `mim-identities`（JSON 数组）+ `mim-active-uid`。

**决策**: 保持 localStorage 方案，不引入服务端 session。

**理由**:
- Gateway 是本地 WebSocket (`127.0.0.1:9200`)，无公网攻击面
- 桌面单用户场景，无多用户并发
- localStorage 跨 tab 通过 `window 'storage'` 事件同步
- 服务端 session 需要 token 管理基础设施，ROI 低

**风险/缓解**:
- 服务端无会话验证 → 所有 RPC 靠传 uid 识别调用者
- 缓解：4 个 delete 函数强制 `requester_uid` 参数 + 权限检查（`_is_squad_admin`）

---

## ADR-003: 18 个 CRUD handler 使用工厂模式

**状态**: Accepted (2026-07-26)

**背景**: `_make_org_handler(org_fn_name)` 工厂函数批量为 org.py 的 CRUD 函数生成 RPC handler。

**决策**: 保留工厂模式，但修正函数名映射。

**关键修复** (v3):
- v2 的 bug: `_make_org_handler` 用 `rpc_name.replace('winpeek_', '')` 推导 org 函数名，导致 17/18 handler 调用错误的函数
- v3 修复: 直接传入正确的 org 函数名（第二个 tuple 元素）
- 补充 4 个缺失 handler: `machine_detail`, `scan_register`, `mim_set_master`, `get_invite_code`

**理由**:
- 工厂模式避免 18 个手写 handler 的重复代码
- 每个 handler 自动处理参数映射（`inspect.signature`）
- 统一错误处理（ImportError + Exception）

---

## 双套注册机制

新 RPC 需要在两个地方注册：

1. `tools/winpeek_tools.py` → `registry.register()` — Agent LLM 工具
2. `tui_gateway/server.py` → `@method()` 装饰器 — Desktop WebSocket 分发

漏了第二步就会报 "unknown method"。

## 验证检查清单

- [x] `python -m py_compile tools/winpeek_tools.py` — 语法通过
- [x] `npx tsc --noEmit` — 零新增 TS 错误（仅 2 个已有 Badge variant）
- [x] Handler 名映射验证: `_handle_squad_list({})` → 调用 `list_squads()` 成功（非 AttributeError）
- [x] 4 个 delete @method 已注册: `squad_delete`, `person_delete`, `machine_delete`, `agent_delete`
- [x] `delete_agent` 表名修正: `agents` → `ai_agents`
- [x] `link_account` SQL 修正: INSERT 语句 + 正确占位数
- [x] `list_accounts_for_person` SQL 修正: 正确的表别名和 JOIN
