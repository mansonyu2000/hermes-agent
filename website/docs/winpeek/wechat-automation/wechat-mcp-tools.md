---
sidebar_position: 8
title: "WeChat RPA MCP 工具清单"
description: "微信自动化全部 MCP 工具：感知层（眼睛）、操作层（手）、对应的 Python 实现、定位策略三层"
---

> 参考：[winpeek-prod/09-mcp-tools.md](https://github.com/winpeek-prod)
> 📍 [返回文档索引](README) | 最后更新：2026-07-18

---

## 感知层（👁️ 眼睛）

| MCP 工具 | 用途 | Token |
|---------|------|:--:|
| `ui_snapshot(title="微信")` | UIA 元素树（40+元素，name/class/bounds/aid） | 零 |
| `window_capture(title="微信")` | 窗口截图 + OCR 定点 | 零 |
| `vision_analyze(imagePath, prompt)` | Qwen2.5VL 看图理解 | LLM |
| `windows_list` | 枚举所有顶层窗口 | 零 |
| `app_list` | 运行中应用列表 | 零 |
| `screens_list` | 显示器信息 | 零 |

## 操作层（🤖 手）

| MCP 工具 | 用途 | Token |
|---------|------|:--:|
| `ui_click(name)` | 按 UIA 元素名点击 | 零 |
| `snapshot_click(snapshotId, name)` | 快照索引点击 | 零 |
| `mouse_click(x, y)` | 屏幕坐标点击 | 零 |
| `element_scroll(label, direction, ticks)` | UIA 元素上滚轮 | 零 |
| `scroll(x, y, direction, ticks)` | 屏幕坐标滚轮 | 零 |
| `press_keys(keys)` | 按键组合 | 零 |
| `hotkey_press(keys)` | 快捷键 | 零 |
| `type_text(text)` | 输入文本 | 零 |
| `input_background(hwnd, action, ...)` | PostMessage 后台输入 | 零 |
| `window_focus(title)` | 窗口置顶 | 零 |

## Python 实现对应

| MCP 工具 | Python 实现 |
|---------|-----------|
| `ui_snapshot` | `uiautomation` Control.GetChildren() |
| `ui_click(name)` | `bg_input.click()` (PostMessage) |
| `element_scroll` | `pyautogui.scroll()` + `bg_input.scroll()` |
| `press_keys` | `pyautogui.press()` |
| `vision_analyze` | `brain.ask()` → Qwen2.5VL |

## 定位策略三层

```
Tier 1: UIA AutomationId   → 精准快（日常操作，0.1s）
Tier 2: 网格地图 (Grid)    → 通用兜底（UIA 失效时的大方向，0.2s）
Tier 3: 像素锚点 (Pixel)   → 最后手段（固定像素坐标，0.3s）
```

## 微信专用 MCP 工具

| 工具 | 参数 | 返回 |
|------|------|------|
| `winpeek_wechat_search` | `name: string` | `{found, grid_x, grid_y}` |
| `winpeek_wechat_open_chat` | `name` / `grid_x, grid_y` | `{opened, chat_title}` |
| `winpeek_wechat_send` | `text: string` | `{sent, message_id}` |
| `winpeek_wechat_read_context` | `limit: int` | `{messages: [...]}` |
