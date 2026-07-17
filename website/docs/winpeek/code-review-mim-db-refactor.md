---
sidebar_position: 90
title: "Code Review: MIM DB 连接重构（2026-07-18）"
description: "QODER 对 commit 65938d8 的审查意见与 CC 修复 commit 6982e97 的复查验证记录 — 供 CC / Trae / 其他 agent 参考"
---

# Code Review：MIM DB 连接重构闭环记录

> **审查者**: QODER · **修复者**: CC · **分支**: `DEV` · **日期**: 2026-07-18
>
> **面向读者**: CC / Trae / 其他协作 agent。本文是一次完整的 review → fix → verify 闭环记录，
> 包含可复用的验证方法和遗留事项，后续改动 `gateway/winpeek_hub/` 时请先读本文的"遗留观察项"。

## TL;DR

- `65938d8` 把 chat/identity/hub_bridge 的 DB 连接统一收敛到 `db.get_conn()`，方向正确，但引入 2 个 Major 问题。
- CC 在 `6982e97` 全部修复，QODER 复查通过（静态 + 运行时双重验证），**该提交已放行**。
- 遗留：`tenant.py` 仍未收敛（独立 `_DB_CONFIG` + `mysql.connector` 驱动），认领前请看文末。

## 提交链

| Commit | 说明 |
|--------|------|
| `43bc053` | merge 引入 `db.py`（延迟导入 + None 降级设计），`archive.py` 首个接入 `db.get_conn()` |
| `65938d8` | refactor(mim): 统一 DB 连接 — 审查发现 2 Major + 1 Minor + 1 Nit |
| `6982e97` | fix(mim): 补完 DB 连接重构 — CC 修复全部审查问题，本文复查对象 |

## 审查问题清单与修复状态

### M1（Major）：`get_conn()` 返回 None 但 7 个调用点未检查 — 已修复

两种错误契约的不兼容合并：旧 `_get_conn()` 失败即抛 pymysql 异常；新 `db.get_conn()`
失败吞异常返回 `None`。而 `chat.py` / `identity.py` 的调用点仍按旧契约写
`conn.cursor()` + `finally: conn.close()`，导致 DB 不可达时：

1. 退化为误导性的 `AttributeError: 'NoneType' object has no attribute 'close'`；
2. `finally` 中的二次异常会**覆盖 except 分支的优雅降级返回值**（Python 语义）。

修复：7 个调用点入口加 `if conn is None` guard，按各函数契约返回错误值。

| 文件 | 函数 | Guard 位置 | 降级返回值 |
|------|------|-----------|-----------|
| `chat.py` | `send_message` | L62-64 | `{"ok": False, "error": "DB unavailable"}` |
| `chat.py` | `get_history` | L121-123 | `[]` |
| `chat.py` | `get_user_contacts` | L162-164 | `[]` |
| `identity.py` | `register` | L32-34 | `None` |
| `identity.py` | `login` | L75-77 | `None` |
| `identity.py` | `get_by_uid` | L113-115 | `None` |
| `identity.py` | `list_all` | L132-134 | `[]` |

全目录 grep 复核：`archive.py`（`if not conn`）、`hub_bridge.py`（`if conn`）既有 guard 保持，无遗漏调用点。

### M2（Major）：pymysql 提升为模块级导入 — 已修复

`pymysql` **不在任何依赖清单中**（pyproject.toml / setup.py / requirements 均无），
是可选依赖。`65938d8` 将其提升为 `db.py` 顶层导入，传染链：

```text
db.py (顶层 import pymysql 失败)
  → archive.py (顶层 from .db import get_conn)
    → __init__.py (顶层 from .archive import archive_message)
      → 整个 gateway.winpeek_hub 包 ImportError
```

后果：`HUB_ARCHIVE_ENGINE=jsonl/off` 模式（本不需要 MySQL）连 import 都过不去；
`tenant.py` / `routing.py` 等无关模块被连坐。

修复：恢复函数内延迟导入 + `except ImportError` 分支（含 `pip install pymysql` 指引日志），
并在 docstring 中明确"失败返回 None — 调用方必须检查"的契约。

### m1（Minor）：悬空 `import os` — 已修复

`chat.py` / `identity.py` 的 `import os` 因 `_DB_CONFIG` 删除而悬空（ruff F401），已删除。
`db.py` 的 `import os` 因 `os.getenv` 在用而合法保留。

## 复查验证证据

### 静态验证

| 检查 | 结果 |
|------|------|
| `git fetch` + status | 本地与 `origin/DEV` 完全同步（HEAD = `6982e97`） |
| `ruff check`（chat/db/identity） | All checks passed!（ruff 0.15.10） |
| `py -m py_compile`（5 文件） | exit=0 通过 |
| grep 全部 `get_conn()` 调用点 | 13 处匹配，guard 全覆盖 |

### 行为验证（模拟 pymysql 缺失环境）

用 `importlib.abc.MetaPathFinder` 拦截 pymysql 导入模拟未安装场景，验证三项：

| 测试 | 结果 |
|------|------|
| 整包导入 `gateway.winpeek_hub` | PASS — 不再被 ImportError 连坐 |
| `get_conn()` 降级 | PASS — 返回 `None` + 安装指引日志 |
| M1 调用方契约（send/history/login/list） | PASS — `ok=False` / `[]` / `None` 全部成立 |

结果：`ALL TESTS PASSED`，exit=0。

## 给协作 agent 的经验教训

1. **契约合并要彻底**：把"失败抛异常"和"失败返 None"两种连接契约合并时，必须同步改造**所有**调用点，
   不能只改一半（`65938d8` 改了 hub_bridge 却漏了 chat/identity 共 7 处）。
2. **可选依赖必须延迟导入**：`gateway/winpeek_hub/` 中 pymysql 是可选依赖，任何新模块
   **禁止在模块顶层 `import pymysql`**，一律在函数内导入并处理 `ImportError`。
3. **`py_compile` 不是验证**：它只查语法，查不出契约不匹配和 unused import。
   连接层改动至少要跑 `ruff check` + 一条"DB 不可达路径"行为测试。
4. **Windows 环境陷阱**：本机 PATH 中 `python` 指向 WindowsApps stub（静默失败、ExitCode 1 无输出），
   验证命令请用 `py` launcher（Python 3.12.3）。

## 遗留观察项（欢迎认领）

| 项 | 说明 | 优先级 |
|----|------|--------|
| `tenant.py` 收敛 | 仍持有独立 `_DB_CONFIG` 且使用 `mysql.connector` 驱动，与"统一到 `db.get_conn()`"目标不符 | 中 |
| 默认凭据外置 | `db.py` 默认配置含内网硬编码凭据（可被 `WINPEEK_DB_*` 环境变量覆盖），建议迁移至安全配置源 | 低 |

---

*本文由 QODER 生成于 review 闭环完成时。改动 `gateway/winpeek_hub/` 前请通读；*
*修复遗留项后请更新上表状态并注明 commit。*
