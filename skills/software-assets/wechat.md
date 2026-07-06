---
name: wechat-software-asset
description: |
  WeChat desktop client software asset — registered names, paths, process info, 
  and window identification on Windows. Auto-discovered from system registry, 
  process list, and file system on 2026-07-07.
version: 1.0.0
platforms: [windows]
metadata:
  hermes:
    tags: [wechat, software-asset, inventory]
    category: desktop
    related_skills: [wechat-automation-rules, trace-to-template]
---

# 微信桌面版 — 软件资产卡

> 自动发现时间: 2026-07-07 | 数据来源: 系统进程列表 + 注册表 + 文件系统

---

## 基本信息

| 属性 | 值 |
|------|-----|
| 产品名 | **Weixin** |
| 公司 | Tencent (腾讯) |
| 版本 | **4.1.11.24** |
| 窗口标题 | `微信` |
| 语言 | 简体中文 |

---

## 进程标识

| 属性 | 值 |
|------|-----|
| 进程名 | **Weixin** (不是 WeChat!) |
| PID | 99212 (主窗口进程) |
| 主窗口句柄 (HWND) | `0x10A80` (68224) |
| 启动时间 | 2026-07-03 |
| 后台进程数 | 5 个 Weixin.exe |

```json
// mcp_winpeek_app_list 返回的识别信息
{
  "processName": "Weixin",
  "processId": 99212,
  "hwnd": "0x10A80",
  "title": "微信"
}
```

**注意**: 进程名是 `Weixin`，不是 `WeChat`。`WeChatAppEx.exe` 是小程序/公众号子进程。

---

## 安装路径

| 属性 | 值 |
|------|-----|
| 安装目录 | `D:\Program Files\Weixin\` |
| 可执行文件 | `D:\Program Files\Weixin\Weixin.exe` (3.1 MB) |
| 版本子目录 | `D:\Program Files\Weixin\4.1.11.24\` |
| 卸载程序 | `D:\Program Files\Weixin\Uninstall.exe` |
| 快捷方式 | `D:\Program Files\Weixin\微信.lnk` |

---

## 窗口识别方式

| 方法 | 匹配值 | 可靠性 |
|------|--------|--------|
| 进程名 | `Weixin` | 🟢 最可靠 |
| 窗口标题 | `微信` | 🟢 |
| HWND | `0x10A80` | 🔴 每次启动会变 |
| PID | `99212` | 🔴 每次启动会变 |

**推荐识别方式**: 用 `mcp_winpeek_app_list` 搜 `processName='Weixin'`，取 `hwnds[0]`。

---

## 子进程

| 进程名 | 用途 | 示例 HWND |
|--------|------|----------|
| `Weixin.exe` | 主进程 (聊天/通讯录/发现) | `0x10A80` |
| `WeChatAppEx.exe` | 小程序/公众号子窗口 | `0x???` (独立窗口) |

**自动化时注意**: 如果误入小程序，新窗口会以 `WeChatAppEx.exe` 进程打开。需要切回主 `Weixin.exe` 窗口。

---

## 窗口版面

```
微信桌面版 三栏布局:

┌──────────┬──────────────────────────┬──────────┐
│ 左栏(70px)│ 中栏(可变)                │ 右栏(可变) │
│          │                          │          │
│ 📱 微信   │ 会话列表                   │ 聊天窗口   │
│ 👥 通讯录 │ 或 搜索结果                │ 或 资料卡  │
│ 🔍 发现   │                          │          │
│ ⚙️ 更多   │                          │          │
└──────────┴──────────────────────────┴──────────┘

微信 Qt 渲染引擎: mmui (自定义, 非标准 Qt 控件)
  - 渲染容器: MMUIRenderSubWindow (pane)
  - 主视图: mmui::MainView (group)
  - 搜索弹窗: mmui::SearchContentPopover (window)
```

---

## 启动方式

| 方式 | 命令/路径 |
|------|----------|
| 命令行启动 | `"D:\Program Files\Weixin\Weixin.exe"` |
| Shell 启动 | `Start-Process "D:\Program Files\Weixin\Weixin.exe"` |
| 如果未运行 | 直接启动 Weixin.exe (已登录状态会自动恢复) |
