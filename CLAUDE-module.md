<!--
  ╔══════════════════════════════════════════════════════════════════════╗
  ║  🛑  你是 Agent，你正在读 CLAUDE.md。请先读完下面所有规则。  ║
  ╚══════════════════════════════════════════════════════════════════════╝

  CLAUDE.md 文件结构（从上到下）：
    上半部 = 本文件 CLAUDE-module.md（git 管理，**永久规则**）
    下半部 = agent-role.py 动态生成（身份头 uid/nick/role/mqtt）

  ❌ 禁止用 Write/Edit 修改 CLAUDE.md — 它是被动产物，重启后全部丢失。
  ✅ 要改规则 → 改本文件 CLAUDE-module.md。要改身份 → 改 agent.conf。
-->

## ① 身份证

header 由 `python bin/agent-role.py` 启动时自动生成，包含 uid/nick/role/mqtt。

## ② 基本生存技能（6 条铁律）

**1. 通讯** — 收到 `● 名字[uid] said: 内容` → 用 `say <对方uid> "回复内容"` 回复。
  - `say` 是唯一标准命令，所有 Agent 通用。
  - 禁止用 `send_message()` — 绕过 Hub 无归档。

**2. 改代码** — Hermes Agent monorepo，动手前先查影响面：
  - 用 `codebase-memory` 的 `search_graph` / `trace_path` / `search_code` 分析代码结构。
  - 只改任务要求的部分，不顺手重构。
  - 同主题第 3 次 commit 失败 → 停手写根因分析。

**3. 学技能** — 收到任务先查下表，匹配触发词 → 调用 `Skill` 工具加载对应技能：

### 工程技能（agent-skills — 24 skills, Addy Osmani）

| 阶段 | 触发词 | Skill |
|------|--------|-------|
| 定义 | 新功能/新项目/需求不清/规格/"要做什么" | `interview-me` → `spec-driven-development` |
| 计划 | 拆任务/估算/排期/依赖分析 | `planning-and-task-breakdown` |
| 构建 | 写代码/实现/开发/编码 | `incremental-implementation` + `test-driven-development` |
| 构建 | UI/前端/页面/组件/样式 | `frontend-ui-engineering` |
| 构建 | API/接口/后端 | `api-and-interface-design` |
| 验证 | 测试/debug/报错/不工作 | `debugging-and-error-recovery` |
| 验证 | 浏览器测试/DOM/console | `browser-testing-with-devtools` |
| 审查 | review/审查/合并前检查 | `code-review-and-quality` |
| 审查 | 简化/重构/清理代码 | `code-simplification` |
| 审查 | 安全检查/漏洞/注入 | `security-and-hardening` |
| 交付 | 部署/上线/发布/ship | `shipping-and-launch` + `ci-cd-and-automation` |
| 交付 | 文档/ADR/决策记录 | `documentation-and-adrs` |
| 通用 | commit/分支/合并/PR | `git-workflow-and-versioning` |
| 通用 | 性能优化/慢查询/N+1 | `performance-optimization` |
| 通用 | 废弃/迁移/旧API下线 | `deprecation-and-migration` |
| 通用 | 日志/监控/告警/追踪 | `observability-and-instrumentation` |
| 通用 | 上下文配置/规则文件 | `context-engineering` |
| 通用 | 参考官方文档/源码验证 | `source-driven-development` |
| 通用 | 不确定/高风险/生产关键 | `doubt-driven-development` |

### 流程技能（superpowers-zh）

| 触发词 | Skill |
|--------|-------|
| 新想法/头脑风暴/设计方案 | `brainstorming` → `writing-plans` |
| 启动/运行/执行 | `subagent-driven-development` 或 `dispatching-parallel-agents` |
| 好了/完成/搞定/可以了 | `verification-before-completion` |
| 合并/PR/提交/push | `finishing-a-development-branch` |
| 收到代码审查反馈 | `receiving-code-review` |

### 本项目独特技能

| 触发词 | Skill |
|--------|-------|
| 功能集群/多阶段/全流程/发消息/自动化任务 | `agent-coding-workflow` |

> `agent-coding-workflow` 不重造轮子——桥接上述 24+ 技能，叠加本项目的文档治理+双系统同步+集群规则。
> 24 个技能装在本项目 `.agents/skills/`，Claude Code 自动发现。

**4. 交作业** — commit message 必须含证据标记：
- `feat:` → `brainstorm:` + `tdd:` + `verified:`
- `fix:` → `debug:` + `tdd:` + `verified:`
- `chore/docs/refactor:` → `evidence: none`

**5. 遇问题** — 先自查（`search_graph` / `npm test` / `npm run lint`）→ 解决不了再 `say` supervisor。
  联系人：于杨敏(2022)PM / 于大海(101)架构 / 易清清(102)开发 / 许国勇(103)开发。

**6. 文件治理** — 每个文件属于一个类别，不同类别有不同的创建/修改/删除规则：

| 类别 | 创建 | 修改 | 删除 |
|------|------|------|------|
| 系统依赖 (pyproject.toml/package.json/uv.lock等) | ❌ | ❌ 需指令 | ❌ |
| 环境配置 (.env/config.yaml等) | ❌ | 需审批 | ❌ |
| 核心代码 (agent/apps/tools/gateway/plugins等) | 先搜后建 | `trace_path` 先查 | 确认无引用 |
| 技能文件 (skills/) | ✅ 按模板 | 可以 | 可以 |
| 实验文件 (dev-doc/experiments/) | ✅ 标记过期 | 可以 | 鼓励 |
| 文档 (docs/website) | 先搜主题 | 可以 | 可以 |
| 测试 (tests/) | TDD | 随代码 | 随代码 |
| 生成文件 (node_modules/venv/build等) | ❌ | ❌ | ❌ |

## ③ 项目结构速览

| 目录 | 说明 |
|------|------|
| `agent/` | Agent 核心逻辑（provider 适配器、记忆、缓存） |
| `apps/desktop/` | Electron 桌面应用（React + Vite） |
| `gateway/` | 消息网关（Telegram/Discord/Slack 等） |
| `tools/` | 工具实现（自动注册） |
| `plugins/` | 插件系统（memory/kanban/image_gen 等） |
| `skills/` | 内置技能 |
| `cron/` | 定时任务调度 |
| `web/` | Web Dashboard（React + Vite） |
| `tests/` | 测试套件（pytest ~17k 测试） |

## ④ 华为援引（关键架构决策）

1. **Prompt 缓存是神圣的** — 任何对话中改变上下文、切换工具集、重建 system prompt 的操作都会使缓存失效，导致 API 成本增加 3-10 倍。
2. **核心是窄腰，能力在边缘** — 新增核心工具门槛高，优先走 CLI 命令 + skill、服务门控工具、plugin、MCP 的方式。
3. **Hermes 源码根目录是 hermes-agent/**，通过 `hermes_constants.get_hermes_home()` 获取用户数据目录（默认 `~/.hermes/`）。
