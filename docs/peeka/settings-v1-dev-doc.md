---
title: "Peeka 身份同步 + MIM 聊天 — 技术文档 (2026-07-26 会话)"
type: "reference"
phase: "develop"
author_subagent: "Claude Code"
version: "1.0"
status: "approved"
last_updated: "2026-07-26"
related:
  - "../decisions/0001-peeka-identity-architecture.md"
  - "../governance/standards/peeka-architecture-decisions.md"
  - "acceptance-report.md"
---

# Peeka 身份同步 + MIM 聊天 — 技术文档

## 1. 架构总览

```
┌────────────────────────────────────────────────────────────┐
│                    Hermes Desktop (Electron)                │
│                                                            │
│  ┌──────────┐   ┌──────────┐   ┌───────────────────────┐  │
│  │ Sidebar   │   │  MIM     │   │  SettingsView         │  │
│  │ PeekaPopup│   │  /mim    │   │  /settings            │  │
│  │           │   │          │   │  ┌─ Peeka nav group ─┐│  │
│  │ 👤 个人信息│   │ 联系人列表 │   │  │ profile           ││  │
│  │ 🤖 Agent │   │ 聊天窗口  │   │  │ accounts          ││  │
│  │ 🔑 密码   │   │ 群聊     │   │  │ password          ││  │
│  │ 🏢 组织   │   │          │   │  │ organization      ││  │
│  │ ⇄ 切换   │   │          │   │  │ devices ← NEW     ││  │
│  │ ⤻ 退出   │   │          │   │  │ agents            ││  │
│  └──────────┘   └──────────┘   │  └───────────────────┘│  │
│       │               │        └───────────────────────┘  │
│       └───────┬───────┘              │                    │
│               │                      │                    │
│         peeka-changed event    loadSavedIdentity()        │
│               │                      │                    │
│         localStorage                 │                    │
│    mim-identities / mim-active-uid ──┘                    │
└────────────────────────────────────────────────────────────┘
                              │
                         WebSocket
                              │
┌────────────────────────────────────────────────────────────┐
│                  tui_gateway/server.py                      │
│  ┌─ @method() explicit ─────────────────────────────────┐ │
│  │ winpeek_mim_login, winpeek_mim_user_register, ...    │ │
│  └──────────────────────────────────────────────────────┘ │
│  ┌─ auto-discover (_auto_discover_winpeek) ─────────────┐ │
│  │ winpeek_squad_*, winpeek_person_*, winpeek_agent_*   │ │
│  │ winpeek_machine_*, winpeek_org_*, winpeek_pending_*  │ │
│  └──────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────┘
                              │
                    tools/winpeek_tools.py
                    (21 handlers + registry + logger)
                              │
                 gateway/winpeek_hub/
                 ├── identity.py (8 functions)
                 ├── organization.py (25 functions)
                 ├── chat.py (message engine)
                 └── db.py (MySQL connection)
                              │
                          MySQL
                    (winpeek-db2)
```

## 2. 身份同步机制

### 核心原则
**全局唯一身份。** `localStorage` 的 `mim-identities` 数组 + `mim-active-uid` 是唯一的身份来源。所有组件共享同一个身份状态。

### 事件流
```
任何登录/切换/退出操作
  → saveIdentity() / removeIdentity()  (types.ts)
    → 写入 localStorage
    → dispatch CustomEvent('peeka-changed')
      ├── SettingsView 监听到 → refreshPeeka()
      ├── MIM 监听到 → setIdentity() / clear identity
      └── PeekaPopup 监听到 → sync()
```

### 关键代码位置
| 组件 | 文件 | 行数 |
|------|------|------|
| saveIdentity + removeIdentity | `winpeek/peeka/types.ts` | 25-42 |
| SettingsView peeka-changed listener | `settings/index.tsx` | 63-71 |
| MIM peeka-changed listener | `winpeek/mim/index.tsx` | 672-678 |
| PeekaPopup swapAccount | `chat/sidebar/index.tsx` | 247-266 |
| PeekaLoginPanel dispatch | `winpeek/peeka/index.tsx` | 41, 55 |

## 3. 后端 RPC 体系

### 注册机制
- **显式 @method**: 21 个 handler 在 `server.py` 中手写 `@method` 装饰器
- **自动发现**: `_auto_discover_winpeek` — 首次收到 `winpeek_*` RPC 时从 `registry._tools` 加载
- **mtime 热重载**: 编辑 `winpeek_tools.py` 保存后，下次调用自动重新加载

### RPC 清单
| 类别 | RPC | org.py 函数 |
|------|-----|-----------|
| Squad CRUD | `winpeek_squad_list/upsert/delete/search` | `list_squads/upsert_squad/delete_squad/search_squads` |
| Person CRUD | `winpeek_person_list/upsert/delete/approve` | `list_persons/upsert_person/delete_person/approve_person` |
| Machine CRUD | `winpeek_machine_list/delete/approve/detail` | `list_machines/delete_machine/approve_machine/get_machine_detail` |
| Agent CRUD | `winpeek_agent_list/upsert/delete` | `list_agents/upsert_agent/delete_agent` |
| Org | `winpeek_org_tree/status` | `get_org_tree/get_org_status` |
| Other | `winpeek_pending_list/join_squad/register_with_squad` | `get_pending/join_squad/register_with_squad` |

### 参数映射 (param_map)
| RPC | 映射 |
|-----|------|
| `winpeek_squad_delete` | `{"requester_uid": "uid"}` |
| `winpeek_org_status` | `{"winpeek_uid": "uid"}` |
| `winpeek_pending_list` | `{"requester_uid": "uid"}` |
| `winpeek_agent_upsert` | `{"id": "agent_id"}` |

## 4. 前端页面结构

### Peeka nav group (SettingsView 内)
```
SettingsView (/settings)
  └── Peeka nav group
      ├── peeka:profile      — 个人信息 (查看/编辑昵称/性别/角色/职位/简介/技能)
      ├── peeka:accounts     — 切换账号 (多账号列表/切换/默认/添加/注册/登录历史)
      ├── peeka:password     — 修改密码 (旧密码+新密码+强度)
      ├── peeka:organization — 我的组织 (完整CRUD+成员/设备/审批)
      ├── peeka:devices      — 我的设备 (本机信息/注册/列表)
      └── peeka:agents       — 我的Agent (列表/在线状态/编辑/删除)
```

### PeekaPopup (sidebar 底部)
```
PeekaPopup
  ├── 👤 个人信息 → /settings?tab=peeka:profile
  ├── 🤖 管理我的 Agent → /settings?tab=peeka:agents (mim-user only)
  ├── 🔑 修改密码 → /settings?tab=peeka:password
  ├── 🏢 我的组织 → /settings?tab=peeka:organization (mim-user only)
  ├── ⇄ 切换账号 → 子菜单 (身份列表)
  └── ⤻ 退出登录 → 清除 localStorage + reload
```

## 5. 关键文件清单

| 文件 | 作用 | 改动类型 |
|------|------|---------|
| `apps/desktop/src/app/settings/index.tsx` | SettingsView Peeka nav group + state | 修改 |
| `apps/desktop/src/app/chat/sidebar/index.tsx` | PeekaPopup 菜单 + swapAccount | 修改 |
| `apps/desktop/src/app/winpeek/mim/index.tsx` | MIM contacts/chat/login fix | 修改 |
| `apps/desktop/src/app/winpeek/peeka/types.ts` | saveIdentity/load/remove/recordLogin | **新增** |
| `apps/desktop/src/app/winpeek/peeka/index.tsx` | Barrel + PeekaLoginPanel | **新增** |
| `apps/desktop/src/app/winpeek/peeka/profile-tab.tsx` | 个人信息 tab | **新增** |
| `apps/desktop/src/app/winpeek/peeka/accounts-tab.tsx` | 切换账号 tab | **新增** |
| `apps/desktop/src/app/winpeek/peeka/password-tab.tsx` | 改密码 tab | **新增** |
| `apps/desktop/src/app/winpeek/peeka/organization-tab.tsx` | 组织管理 tab | **新增** |
| `apps/desktop/src/app/winpeek/peeka/agents-tab.tsx` | Agent 管理 tab | **新增** |
| `apps/desktop/src/app/winpeek/peeka/devices-tab.tsx` | 设备管理 tab | **新增** |
| `apps/desktop/src/app/winpeek/register/index.tsx` | RegistrationWizard + org_status fix | 修改 |
| `tools/winpeek_tools.py` | 21 handlers + registry + logging | 修改 |
| `tui_gateway/server.py` | auto-discover + dispatch logging | 修改 |
| `gateway/winpeek_hub/organization.py` | CRUD + delete + is_owner + org fields | 修改 |
| `gateway/winpeek_hub/identity.py` | 无改动（已有能力被 RPC 化） | 无改动 |
| `docs/decisions/0001-peeka-identity-architecture.md` | ADR | **新增** |
| `docs/peeka/acceptance-report.md` | 验收报告 | **新增** |
| `docs/peeka/dev-doc-session-2026-07-26.md` | 本文档 | **新增** |

## 6. 日志追踪体系

- 所有 handler 入口: `logger.info("RPC call: %s uid=%s", rpc_name, uid)`
- 所有 handler 异常: `logger.exception(...)` (15 处)
- server.py dispatch: `logger.debug("RPC dispatching: method=%s")` + `logger.warning("unknown method")`
- 敏感字段脱敏: `_sanitize()` / `_safe_args()` + `RedactingFormatter`
- 日志文件: `~/.hermes/logs/agent.log` + `~/.hermes/logs/errors.log`

## 7. 编译验证命令

```bash
# TypeScript
cd apps/desktop && npx tsc --noEmit --pretty

# Python
python -m py_compile tools/winpeek_tools.py
python -m py_compile gateway/winpeek_hub/organization.py
python -m py_compile tui_gateway/server.py

# E2E
python -c "
from tools.winpeek_tools import _handle_register_with_squad, _handle_org_status, ...
# see docs/peeka/acceptance-report.md for full test
"
```

## 8. 下次会话入口

1. 加载记忆: `peeka-identity-state` + `peeka-dev-lessons` + `mim-chat-llm-next`
2. 阅读本文档了解架构
3. 继续 MIM 聊天→Agent 消息传达功能（见 `fizzy-watching-donut.md` spec）
