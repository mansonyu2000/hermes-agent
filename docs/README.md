# 文档总索引

> 自动维护 · 最后更新: 2026-07-22

## 技能栈

```
agent-skills (24 skills)     ← 工程技能: Define→Plan→Build→Verify→Review→Ship
  ├── .agents/skills/        ← 24 个 SKILL.md (Claude Code 自动发现)
  └── skills/                ← 项目级副本

superpowers-zh               ← 流程技能: brainstorm, TDD, debug, review
  └── ~/github/superpowers-zh/skills/

agent-coding-workflow        ← 本项目桥接层: 文档治理+双系统同步+集群规则
  └── skills/agent-coding-workflow/SKILL.md
```

## 功能集群

| 集群 | 路径 | 状态 |
|------|------|:--:|
| 发消息 | `messaging/` | 🔶 待启动 |
| 自动化任务 | `wechat-automation/` | ⬜ 规划中 |
| 人头画像 | `wechat-portrait/` | ⬜ 规划中 |
| 信息同步 | `wechat-sync/` | ⬜ 规划中 |
| 系统设置 | `system-common/` | ⬜ 规划中 |
| Peeka 身份 | `peeka/` | ✅ v4 已交付 |

### 集群治理

见 [governance/standards/cluster-rules.md](governance/standards/cluster-rules.md)

## 本次会话成果

见 [agent-coding-workflow/](agent-coding-workflow/) — v3 架构文档（历史参考）

## Peeka 用户中心 (v4)

Peeka 是 Hermes 的多实例身份与通讯系统，2026-07-26 交付 v4。
**状态：代码完成，待 Gateway 重启加载新模块。**

### 架构决策

见 [decisions/0001-peeka-identity-architecture.md](decisions/0001-peeka-identity-architecture.md) — 3 个 ADR。Peeka 身份管理**合并进 SettingsView**（`/settings?tab=peeka:*`），不再作为独立 overlay。

**技术文档**: [peeka/settings-v1-dev-doc.md](peeka/settings-v1-dev-doc.md) — 完整架构/代码位置/RPC清单/身份同步/编译验证。
**验收报告**: [peeka/settings-v1-acceptance.md](peeka/settings-v1-acceptance.md) — 15/15 E2E 通过。
**MIM Spec**: [peeka/mim-chat-v1-spec.md](peeka/mim-chat-v1-spec.md) — MIM聊天系统V1需求规格。
**任务索引**: [tasks/README.md](../tasks/README.md) — 按模块分层的任务清单。

### v4 Bug 修复清单

| Bug | 文件 | 影响 |
|-----|------|------|
| `_make_org_handler` `**kwargs` 丢弃 | `winpeek_tools.py` | `upsert_*` 所有额外字段（industry/role/address）被静默丢弃 |
| `param_map` 方向错误 | `winpeek_tools.py` | `org_status`/`delete_squad` 参数名不匹配导致调用失败 |
| `_is_squad_admin` 用错表 | `organization.py` | `users.master_uid` vs `winpeek_accounts.person_id` |
| `is_owner` 始终 `true` | `organization.py` | `LIMIT 1` 无序返回旧 person_id |
| `delete_agent` 表名错误 | `organization.py` | `agents` → 应为 `ai_agents` |

### 日志追踪（v4 新增）

所有 21 个 Peeka handler 入口记录 `logger.info("RPC call: %s", rpc_name)`，异常记录 `logger.exception(...)` 含完整 traceback。
日志路径：`~/.hermes/logs/agent.log`。
修改 `tools/winpeek_tools.py` 或 `server.py` 后需**重启 Gateway** 加载新代码。

### Peeka Nav Group（5 tabs）

| Tab | 路由 | 功能 |
|-----|------|------|
| Personal Info | `peeka:profile` | 查看/编辑昵称、角色、性别、职位、简介、技能，显示组织卡片 |
| Account Switch | `peeka:accounts` | 多账号列表（按登录时间排序）、设为默认、切换、添加、移除、登录历史 |
| Change Password | `peeka:password` | 旧密码验证 + 新密码确认，强度指示器 |
| Organization | `peeka:organization` | **完整 CRUD**：创建/加入/编辑/删除组织，成员审批/移除/转交所有权，设备审批/移除，审批中心，邀请码复制 |
| My Agents | `peeka:agents` | Agent 列表 + 编辑/移除，在线状态指示器，搜索过滤 |

### 后端 RPC 映射

18 个 CRUD handler（`tools/winpeek_tools.py`）→ `@method`（`tui_gateway/server.py`）→ `gateway/winpeek_hub/organization.py`：

| 前端调用 | Handler | org.py |
|----------|---------|--------|
| `winpeek_squad_list` | `_handle_squad_list` | `list_squads()` |
| `winpeek_squad_upsert` | `_handle_squad_upsert` | `upsert_squad()` |
| `winpeek_squad_delete` | `_handle_squad_delete` | `delete_squad()` |
| `winpeek_squad_search` | `_handle_squad_search` | `search_squads()` |
| `winpeek_person_list` | `_handle_person_list` | `list_persons()` |
| `winpeek_person_upsert` | `_handle_person_upsert` | `upsert_person()` |
| `winpeek_person_delete` | `_handle_person_delete` | `delete_person()` |
| `winpeek_person_approve` | `_handle_person_approve` | `approve_person()` |
| `winpeek_machine_list` | `_handle_machine_list` | `list_machines()` |
| `winpeek_machine_delete` | `_handle_machine_delete` | `delete_machine()` |
| `winpeek_machine_approve` | `_handle_machine_approve` | `approve_machine()` |
| `winpeek_agent_list` | `_handle_agent_list` | `list_agents()` |
| `winpeek_agent_upsert` | `_handle_agent_upsert` | `upsert_agent()` |
| `winpeek_agent_delete` | `_handle_agent_delete` | `delete_agent()` |
| `winpeek_org_tree` | `_handle_org_tree` | `get_org_tree()` |
| `winpeek_org_status` | `_handle_org_status` | `get_org_status()` |
| `winpeek_pending_list` | `_handle_pending_list` | `get_pending()` |
| `winpeek_join_squad` | `_handle_join_squad` | `join_squad()` |

### 数据库表关系

```
squads (组织)
  ├── 1:N → persons (人员)
  │            ├── 1:N → winpeek_accounts (绑定 Peeka uid)
  │            └── 1:N → machines (电脑设备)
  ├── invite_code (邀请码)
  └── owner_person_id → persons.id

users (Peeka 账号)
  ├── uid (全局唯一)
  ├── peeka_name (复合标识: name-hostname-ip)
  ├── identity_type: 'mim-user' (真人) | 'mim-agent' (AI Agent)
  ├── gender: 'male' | 'female'
  └── master_uid → users.uid (Agent 归属的真人用户)

machines (电脑设备)
  ├── hostname, os_name, os_version, cpu_model
  ├── squad_id → squads.id
  └── winpeek_uid → users.uid

ai_agents (AI Agent)
  ├── 属于 person/squad/machine
  └── agent_type, role
```

### 关键文件

| 文件 | 作用 |
|------|------|
| `apps/desktop/src/app/settings/index.tsx` | SettingsView 主体 + Peeka nav group 渲染 |
| `apps/desktop/src/app/winpeek/peeka/*.tsx` | 5 个 tab 面板组件 |
| `apps/desktop/src/app/chat/sidebar/index.tsx` | PeekaPopup（6 项快速入口） |
| `tools/winpeek_tools.py` | 18 个 CRUD handler + 4 个 identity handler |
| `tui_gateway/server.py` | 24 个 @method 装饰器 |
| `gateway/winpeek_hub/organization.py` | 25 个业务逻辑函数（完整 CRUD） |
| `gateway/winpeek_hub/identity.py` | 身份管理（register/login/get_by_uid/set_password） |

## 设计参考

- agent-skills 24 skills: `.agents/skills/`
- 集群治理: [governance/standards/cluster-rules.md](governance/standards/cluster-rules.md)
- 流水线状态: [governance/pipeline-status.json](governance/pipeline-status.json)
- 禅道映射: `.zentao/mapping.json`
- Multica 映射: `.multica/mapping.json`
