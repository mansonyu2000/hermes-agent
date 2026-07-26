---
title: "Claude Code 消息投递 — 空投注入方案"
type: "design"
phase: "plan"
module: "mim"
version: "v1"
status: "planning"
last_updated: "2026-07-27"
related:
  - "./mim-message-delivery-spec.md"
  - "./mim-architecture-dev-doc.md"
---

# Claude Code 消息投递 — 空投注入方案

> CC 是闭源终端程序，无法修改 chatbox。采用 RPA 窗口注入方式（模拟人工打字）。

## 1. 当前方案: standalone bridge-agent.py

**文件**: `apps/desktop/src/dialog_bridge/dialog_bridge_form_yiqingqing/bridge-agent.py` (979行)

独立 Python 进程，订阅 MQTT → 消息到达 → 窗口注入。

```
MQTT comms/inbox/{agent_name}
  │
  ▼
bridge-agent.py (独立进程):
  1. aiomqtt 监听 MQTT
  2. activate_cc_window() — 激活 CC 窗口
     ├─ pywinauto UIA 直接标题匹配
     ├─ UIA TabItem 搜索（多tab同窗口）
     └─ 兜底: pygetwindow + Ctrl+Alt+N 快捷键
  3. inject_message() — RPA 注入
     ├─ pyautogui.click(click_x, click_y) — 点击输入框
     ├─ Ctrl+A Del — 清空现有文字
     ├─ pyperclip.copy + Ctrl+V — 粘贴消息（支持中文）
     └─ pyautogui.press("enter") — 回车触发 LLM
```

**依赖**: `pyautogui`, `pywinauto`, `pyperclip`, `aiomqtt`, `tkinter`

**配置**: `~/.dialog_bridge/agents.json` (窗口标题, 输入框坐标, tab索引)

### 1.1 核心函数

| 函数 | 行号 | 用途 |
|------|:--:|------|
| `activate_cc_window(title)` | 245-418 | 3级窗口激活 (标题匹配→UIA TabItem→快捷键兜底) |
| `inject_message(cx, cy, text)` | 422-449 | 点击→清空→粘贴→回车 |
| `_check_multi_tab_conflict()` | 239-242 | 检测同窗口多agent tab |
| `calibrate()` | 79-235 | Tkinter 校准工具 (框选输入框位置) |
| `main()` | 452-979 | MQTT 监听主循环 |

## 2. 计划: Daemon 接管 bridge-agent 功能

**目标**: 废弃独立 `bridge-agent.py` 进程，投递逻辑内建到 Peeka Daemon。

**Daemon 新增 CC 投递线程**:
```
L3消息到达 → Daemon 检查收件人 agent_type
  └─ agent_type == "claude-code":
       1. ConPTY 注入 (优先, `conpty_inject.py` 已有, 无需窗口激活)
       2. 失败 → RPA 空投:
            activate_cc_window() → click输入框 → paste文本 → Enter
```

### 2.1 开发任务

| # | 任务 | 来源 | 状态 |
|---|------|------|:--:|
| 1 | Daemon 新增 CC 投递线程入口 | 新 | ⏳ |
| 2 | 迁移 `activate_cc_window()` 到 `engine.py` | bridge-agent.py:245-418 | ⏳ |
| 3 | 迁移 `inject_message()` 到 `engine.py` | bridge-agent.py:422-449 | ⏳ |
| 4 | 迁移配置 `agents.json` 到 Daemon 配置 | bridge-agent.py:46-60 | ⏳ |
| 5 | ConPTY 优先 + RPA 兜底 | 已有 `conpty_inject.py` | ✅ |
| 6 | 移除 standalone bridge-agent.py | ⏳ |

### 2.2 配置迁移

```
旧: ~/.dialog_bridge/agents.json
    { "agent-3": { "window_title": "Claude Code", "click_x": 500, "click_y": 900, ... } }

新: ~/.peeka/agents/{uid}/cc-config.json (由 Daemon 管理)
```

## 3. 参考代码

| 文件 | 关键行 | 内容 |
|------|:--:|------|
| `bridge-agent.py` | 245-418 | 窗口激活 (3级策略) |
| `bridge-agent.py` | 422-449 | RPA 注入 (click→paste→enter) |
| `engine.py:deliver_to_agent()` | 342-373 | 已有 3 种注入模式 (rpa/backend/conpty) |
| `conpty_inject.py` | 587-654 | ConPTY 句柄直接写入 |
