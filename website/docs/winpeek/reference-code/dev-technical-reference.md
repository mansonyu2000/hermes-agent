---
title: "WinPeek 开发技术参考手册"
description: "群聊/软件扫描/组织管理 — 全模块接口、数据模型、部署指南"
date: 2026-07-20
status: done
type: reference
---

# WinPeek 开发技术参考手册

> 版本: v1.0 · 日期: 2026-07-20

## 一、项目概览

WinPeek 是 Hermes Agent monorepo 下的多 Agent 协作平台，包含：

| 子系统 | 状态 | 代码量 |
|--------|:--:|:--:|
| MIM 单聊消息 | ✅ 已完成 | `chat.py` (240行) |
| MIM 群聊 | ✅ 已完成 | `group.py` (920行) |
| 软件资产扫描 | ✅ 已完成 | `scanner.py` (330行) + `software.py` (280行) |
| 组织管理 | ✅ 已完成 | `organization.py` (1080行) |
| 前端 UI（群聊+注册+资产） | ✅ 已完成 | 4 个页面 |

## 二、代码结构

```
gateway/winpeek_hub/
├── chat.py         # 消息引擎 (send/get_history/get_contacts/poll)
├── group.py        # 群聊 CRUD (groups/group_members 复用已有表)
├── scanner.py      # Windows 注册表软件扫描 + 硬件信息
├── software.py     # software + software_account 管理
├── organization.py # squads/persons/machines/winpeek_accounts/ai_agents
├── mqtt_adapter.py # MQTT 连接, comms/group/# 订阅
├── db.py           # MySQL 连接 (get_conn)
├── identity.py     # 用户注册/登录
├── hub.py          # 在线状态 + 心跳
├── hub_bridge.py   # 生命周期钩子
├── routing.py      # 跨平台消息路由
├── tenant.py       # 多租户
└── archive.py      # 消息归档

tools/winpeek_tools.py  # 37 个 RPC 注册层
tui_gateway/server.py   # HTTP 方法注册层

apps/desktop/src/app/winpeek/
├── mim/index.tsx     # 群聊 UI (消息Tab + 通讯录Tab)
├── register/index.tsx # 组织注册向导 + 审批面板
├── hwinfo/index.tsx   # 本机资产页面
└── wechat/index.tsx   # 微信通讯录管理
```

## 三、数据库表清单

| 表名 | 作用 | 状态 |
|------|------|:--:|
| `users` | Hermes 用户 | 已有 |
| `chat` | 消息记录（含 gid 列） | 已有 |
| `contacts` | 联系人 | 已有 |
| `groups` | 群聊（PeekabooWin 遗留） | 已有 |
| `group_members` | 群成员 | 已有 |
| `squads` | 组织/公司 | 新增 |
| `persons` | 真人 | 新增 |
| `machines` | 设备 (PC/手机/容器) | 新增 |
| `winpeek_accounts` | 真人↔WinPeek 账号 | 新增 |
| `ai_agents` | AI Agent | 新增 |
| `winpeek_software` | 已安装软件 | 已有（扩建） |
| `winpeek_software_account` | 软件登录账号 | 已有（扩建） |

## 四、接口清单（37 个）

### 4.1 MIM 消息

| RPC | 参数 | 返回 |
|-----|------|------|
| `winpeek_mim_login` | nickname, password | identity |
| `winpeek_mim_send` | body, to_uid\|gid | ok, mid |
| `winpeek_mim_poll` | uid | messages[] |
| `winpeek_mim_contacts` | uid | contacts[], groups[] |
| `winpeek_mim_history` | peer_uid\|gid, limit | messages[] |
| `winpeek_mim_online` | — | nodes |
| `winpeek_mim_user_info` | uid | user |

### 4.2 群聊

| RPC | 参数 | 权限 |
|-----|------|------|
| `winpeek_mim_group_create` | title, member_uids[] | 任何人 |
| `winpeek_mim_group_list` | — | 任何人（返回我的群） |
| `winpeek_mim_group_info` | gid | 群成员 |
| `winpeek_mim_group_invite` | gid, uids[] | owner/admin |
| `winpeek_mim_group_update` | gid, title?, announcement? | owner/admin |
| `winpeek_mim_group_transfer` | gid, new_owner_uid | owner |
| `winpeek_mim_group_leave` | gid | 任何人 |
| `winpeek_mim_announcement_delete` | gid, an_id | owner/admin |

### 4.3 软件资产

| RPC | 参数 |
|-----|------|
| `winpeek_software_list` | — |
| `winpeek_software_upsert` | name, install_path, exe_path, ... |
| `winpeek_software_by_category` | — |
| `winpeek_account_list` | uid, software_id |
| `winpeek_account_upsert` | software_id, uid, wxid, auth_type, auth_value |
| `winpeek_account_set_active` | account_id, uid |
| `winpeek_account_delete` | account_id |
| `winpeek_hwinfo` | — |
| `winpeek_scan_sync` | — |

### 4.4 组织管理

| RPC | 参数 | 权限 |
|-----|------|------|
| `winpeek_squad_list` | — | 任何人 |
| `winpeek_squad_upsert` | name, description | 任何人(创建)/owner(更新) |
| `winpeek_squad_search` | q (模糊搜索) | 任何人 |
| `winpeek_org_status` | — | 登录用户 |
| `winpeek_register_with_squad` | is_new_squad, squad_name?, invite_code?, ... | 任何人 |
| `winpeek_join_squad` | squad_id | 登录用户 |
| `winpeek_my_invite_codes` | — | owner |
| `winpeek_person_list` | squad_id | squad 成员 |
| `winpeek_person_upsert` | name, squad_id, email, phone | 同 squad |
| `winpeek_person_approve` | person_id, action | squad admin |
| `winpeek_machine_list` | person_id | squad 成员 |
| `winpeek_machine_detail` | machine_id | owner/同squad |
| `winpeek_machine_approve` | machine_id, action | squad admin |
| `winpeek_pending_list` | squad_id | squad admin |
| `winpeek_scan_register` | — | 登录用户 |
| `winpeek_org_tree` | — | squad 成员 |
| `winpeek_agent_list` | squad_id, machine_id | squad 成员 |
| `winpeek_agent_upsert` | name, agent_type, machine_id | 同 squad |

## 五、前端路由

| 路径 | 页面 | 组件 |
|------|------|------|
| `/mim` | MIM 聊天 | `MimView` |
| `/winpeek-wechat` | 微信通讯录 | `WechatPanel` |
| `/winpeek-hwinfo` | 本机资产 | `HwInfoView` |
| 内嵌 | 注册向导 | `RegistrationWizard` |
| 内嵌 | 审批面板 | `ApprovalPanel` |

## 六、注册流程

```
1. 用户登录 WinPeek
2. 自动注册机器（hostname + device_type=pc，pending）
3. 检查 org_status：
   ├─ linked → 正常使用
   └─ unlinked → 注册向导
       ├─ 创建组织：输入名称 → 自动生成4位邀请码 → 发给同事
       ├─ 邀请码加入：输入4位码 → 直通 ✅
       └─ 搜索加入：搜公司名 → 选择 → 等待审批
4. 管理员在审批中心 → 通过/拒绝
5. 审批通过 → linked → 正常使用
```

## 七、安全模型

| 层 | 机制 |
|-----|------|
| 身份 | 所有 handler 使用 `active_uid()` |
| Squad | `_can_access_squad(uid, squad_id)` |
| Machine | owner 或同 squad |
| Person | 同 squad |
| Agent | 同 squad |
| 审批 | `_is_squad_admin` → owner_person_id 校验 |
| 邀请码 | `secrets.randbelow(10000)` 安全随机, 不通过搜索泄露 |

## 八、部署

```bash
# 启动后端
cd hermes-agent-cc
python -m hermes_cli.main serve --port 9120

# 启动前端
cd apps/desktop
npm run dev
```

## 九、文档索引

| 文档 | 路径 |
|------|------|
| 本技术参考 | `website/docs/winpeek/reference-code/dev-technical-reference.md` |
| 组织注册手册 | `website/docs/winpeek/reference-code/org-registration-guide.md` |
| 群聊需求分析 | `website/docs/winpeek/mim-design/group-chat-requirements.md` |
| 功能清单 | `website/docs/winpeek/mim-design/feature-inventory.md` |
| 聊天 UI 规范 | `website/docs/winpeek/mim-design/chat-ui-final-spec.md` |
| 人际关系管理器 | `website/docs/winpeek/reference-code/README.md` |
