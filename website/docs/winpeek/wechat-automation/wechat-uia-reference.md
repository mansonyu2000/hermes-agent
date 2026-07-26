---
sidebar_position: 9
title: "WeChat UIA AutomationId 参考"
description: "微信桌面版 Qt 控件的稳定 AutomationId 清单：窗口、输入框、导航栏、消息列表、联系人"
---

> 参考：[winpeek-prod/10-uia-automationids.md](https://github.com/winpeek-prod)
> 📍 [返回文档索引](README) | 最后更新：2026-07-18

---

## 背景

微信 Windows 桌面版使用 Qt (`mmui::` 命名空间) 构建。通过 Windows UIA COM 接口暴露稳定的 `AutomationId`。`uiautomation` Python 包可直接访问（`pywinauto` 对 Qt 窗口的 `descendants()` 返回空）。

## 主窗口

| 属性 | 值 |
|------|---|
| Name | `微信` |
| ClassName | `mmui::MainView` |
| 查找 | `auto.WindowControl(Name="微信")` |

## 消息输入

| AutomationId | 类型 | 操作 |
|---|---|---|
| `chat_input_field` | EditControl | `Click()` + `SendKeys()` |

```python
inp = wechat.Control(AutomationId="chat_input_field")
inp.Click(); inp.SendKeys("{Ctrl}a{Delete}")  # 清空
inp.SendKeys("hello"); inp.SendKeys("{Enter}") # 发送
```

## 联系人信息

| AutomationId (完整路径) | 获取 |
|---|---|
| `content_view.top_content_view.title_h_view.left_v_view.left_content_v_view.left_ui_.big_title_line_h_view.current_chat_name_label` | `.Name` |

## 导航栏

| AutomationId | 子按钮 |
|---|---|
| `MainView.main_tabbar` | 微信、通讯录、收藏、朋友圈、视频号、搜一搜、游戏中心、小程序面板 |

```python
navbar = wechat.Control(AutomationId="MainView.main_tabbar")
for btn in navbar.GetChildren():
    if btn.Name == "通讯录": btn.Click()
```

## 消息列表

| AutomationId | 说明 |
|---|---|
| `chat_message_page` | 聊天页面容器 |
| `chat_message_list` | 消息列表 |
| `chat_message_list.qt_scrollarea_viewport.chat_bubble_item_view` | 消息气泡（Name=内容） |

日期分隔符：ListItemControl 但 `AutomationId=""` (空)。

## 关键 AutomationId 速查表

| 元素 | AutomationId | 操作 |
|------|-------------|------|
| 输入框 | `chat_input_field` | Click + SendKeys |
| 消息列表 | `chat_message_list` | GetChildren 遍历 |
| 导航栏 | `MainView.main_tabbar` | GetChildren 找按钮 |
| 会话列表 | `session_list` | GetChildren 遍历 |
| 联系人列表 | `contact_list` | 遍历 CellGroupView |
| 搜索框 | `search_box` | Ctrl+F 定位 |
| 联系人项 | `session_item_<wxid>` | 点击打开对话 |
| handoff 按钮 | `MainView.main_tabbar.tabbar_handoff` | Click |
| 设置按钮 | `MainView.main_tabbar.tabbar_setting` | Click |
