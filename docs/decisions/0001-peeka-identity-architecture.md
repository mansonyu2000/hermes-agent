---
title: "ADR-001/002/003: Peeka 身份系统架构决策"
type: "governance"
phase: "develop"
author_subagent: "Claude Code"
version: "2.0"
status: "approved"
last_updated: "2026-07-26"
related: ["../governance/standards/peeka-architecture-decisions.md"]
---

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

**决策**: 保持 localStorage 方案，不引入服务端 session。

**理由**: Gateway 本地 WebSocket、桌面单用户场景、跨 tab 同步。

**风险**: 服务端无会话验证；缓解：delete 函数强制 `requester_uid` + `_is_squad_admin`。

---

## ADR-003: CRUD handler 使用工厂模式

**状态**: Accepted (2026-07-26)

**决策**: `_make_org_handler(org_fn_name, param_map)` 工厂函数批量为 org.py CRUD 函数生成 RPC handler。

**关键修复** (v4):
- v2 bug: `rpc_name.replace('winpeek_', '')` 导致 17/18 函数名映射错误
- v3 fix: 传入正确 `org_fn_name`
- v4 fix: 添加 `param_map` 处理前后端参数名不一致 + `**kwargs` 传递

---

## 双套注册机制

新 RPC 需要两个地方注册：
1. `tools/winpeek_tools.py` → `registry.register()` — Agent LLM 工具
2. `tui_gateway/server.py` → `@method()` 装饰器 — Desktop WebSocket 分发

## 日志追踪机制

- `hermes_logging.py` → `setup_logging()` 总入口
- 所有 handler 入口记录 `logger.info("RPC call: %s", rpc_name)`
- 所有异常记录 `logger.exception(...)` 含 traceback
- 脱敏: `_sanitize()` + `RedactingFormatter`
- 日志路径: `~/.hermes/logs/agent.log` + `~/.hermes/logs/errors.log`

## 重启 Gateway 指令

修改 `tools/winpeek_tools.py` 或 `tui_gateway/server.py` 后必须重启 Gateway 才能加载新代码：
```bash
# 在桌面端操作: 关闭并重新启动 Hermes 桌面应用
# 或如果使用 CLI Gateway:
hermes gateway restart
```
