---
title: "Peeka MIM + 身份系统验收报告"
type: "test"
phase: "test"
author_subagent: "Claude Code"
version: "1.0"
status: "approved"
last_updated: "2026-07-26"
---

# Peeka MIM 聊天 + 身份系统 — 验收报告

## 测试环境

- 日期: 2026-07-26
- uid: 2033 (Claude Code)
- 数据库: winpeek-db2 (MySQL)
- 后端: Python 3.12, tools/winpeek_tools.py v4

## 验收结果: ✅ 15/15 通过

### MIM 聊天 (3/3)
| 测试 | 结果 |
|------|:--:|
| 登录已有账号 | ✅ |
| 联系人列表加载 | ✅ 44 contacts |
| 新用户注册（含性别） | ✅ |

### 组织 CRUD (7/7)
| 测试 | 结果 |
|------|:--:|
| 创建组织 | ✅ |
| 读取组织状态（is_owner=true） | ✅ |
| 编辑组织（改名→UPDATE，非INSERT） | ✅ |
| 搜索组织 | ✅ |
| 成员列表 | ✅ |
| 设备列表 | ✅ |
| 待审批列表 | ✅ |
| 删除组织 | ✅ |

### Agent CRUD (2/2)
| 测试 | 结果 |
|------|:--:|
| 创建 Agent | ✅ |
| 删除 Agent | ✅ |

### 个人信息 + 密码 (2/2)
| 测试 | 结果 |
|------|:--:|
| 更新资料（含性别） | ✅ |
| 修改密码 | ✅ |

### 编译验证 (1/1)
| 检查 | 结果 |
|------|:--:|
| TypeScript (npx tsc) | ✅ 零新增错误 |
| Python (py_compile) | ✅ 3 文件通过 |

## 已修复的 Bug (v4)

1. `upsert_squad` 改名创建新行 → 修复: 按 `squad_id` 匹配
2. MIM 聊天被 org 注册页面挡住 → 修复: 删除 `needRegistration` 检查
3. `_make_org_handler` `**kwargs` 丢弃 → 修复: 重写参数映射
4. `is_owner` 始终 true → 修复: 从 `machines.person_id` 取值
5. `_is_squad_admin` 用错表 → 修复: 查 `winpeek_accounts` 而非 `users.master_uid`
6. 注册功能调用 login → 修复: 调 `winpeek_mim_user_register` + 性别选择器
7. 11 个 handler 静默吞异常 → 修复: 全部加 `logger.exception`
8. 每次加 RPC 需改 server.py → 修复: 自动发现 + mtime 热重载

## 架构决策 (ADR)

见 `docs/decisions/0001-peeka-identity-architecture.md`:
- ADR-001: Peeka 合并到 SettingsView
- ADR-002: localStorage 身份方案
- ADR-003: CRUD handler 工厂模式
- 日志追踪机制
- RPC 自动发现机制
