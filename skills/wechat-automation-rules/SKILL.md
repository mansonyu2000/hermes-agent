---
name: wechat-automation-rules
description: |
  WeChat desktop automation best practices, pitfalls, and proven patterns.
  Load this before ANY WeChat automation task.
version: 1.0.0
platforms: [windows]
metadata:
  hermes:
    tags: [wechat, rpa, best-practices, pitfalls]
    category: desktop
---

# 微信桌面自动化操作守则

> 基于 4 次实战操作（许国勇/于杨敏/于大海/易清清）总结的血泪教训。
> **执行任何微信自动化任务前，必须先加载本文。**

---

## 一、致命陷阱（做错一步，全盘皆输）

### 🔴 ESC 键不是返回键！

| 你的意图 | 错误做法 | 正确做法 |
|---------|---------|---------|
| 从聊天窗口返回大厅 | ❌ 按 Esc | ✅ 点左上角返回按钮 |
| 关闭搜索弹窗 | ❌ 按 Esc | ✅ 点弹窗外空白区域 |
| 退出某个页面 | ❌ 按 Esc | ✅ 找到并点击返回/关闭按钮 |

**Esc 会隐藏整个微信窗口到托盘！** 之后所有操作全部失效。

### 🔴 搜索结果是混合类型

微信搜索结果**不仅仅是好友**，还包括：

| 结果类型 | AutomationId 特征 | 处理方式 |
|---------|------------------|---------|
| 好友/联系人 | `search_item_{姓名}` → 打开聊天 | ✅ 目标 |
| 群聊 | `search_item_{群名}` → 打开群聊 | ⚠️ 区分 |
| 群成员 | `search_item_{群名:成员名}` → 可能无响应 | ❌ 跳过 |
| 公众号 | `search_item_{公众号名}` → 打开文章列表 | ❌ 跳过 |
| 小程序 | `search_item_{小程序名}` → **打开新窗口！** | 🔴 陷阱！ |
| 搜一搜/网络结果 | 点击进入搜索世界 | 🔴 新窗口！ |
| 相似名联系人 | 多个同名结果 | ⚠️ 选第一个或精确匹配 |

**策略：搜索时优先用纯姓名，不带任何后缀。** 如搜"于大海"而非"于大海互动软件"。

### 🔴 误入小程序/搜索世界

如果点进了小程序窗口（新进程 `WeChatAppEx.exe`）：

```
脱出步骤:
  1. mcp_winpeek_window_focus(hwnd="0x10A80")  ← 先切回主微信
  2. 找到返回/关闭按钮 → 点击退出
  3. 回到微信大厅，重新开始
```

---

## 二、软件版面功能区分析（截图前必做）

微信桌面版是**三栏布局**：

```
┌──────────┬──────────────────────┬──────────┐
│ 左栏      │ 中栏                  │ 右栏      │
│ 导航区     │ 主内容区              │ 功能面板   │
│ (70px)    │ (可变)                │ (可变)    │
│           │                      │           │
│ 微信       │ 会话列表/搜索结果      │ 聊天窗口   │
│ 通讯录     │                      │ 或资料卡   │
│ 发现       │                      │           │
│ ...       │                      │           │
└──────────┴──────────────────────┴──────────┘
```

### 通用软件 5 大功能区

| 区域 | 微信对应 | 截图目标 |
|------|---------|---------|
| 菜单区 | 顶部标题栏 | 验证窗口标题 |
| 导航区 | 左侧 70px 导航栏 | 确认在哪个 Tab |
| 工具区 | 搜索框区域 | 验证搜索状态 |
| 主工作区 | 聊天/会话列表 | 验证操作结果 |
| 状态区 | 底部状态栏 | 验证发送状态 |

### 截图定位法

用 `a(l1, t1, r2, b2)` 两点定位法——只需左上角和右下角坐标：

```
不要截全屏（太大，浪费 token 和时间）
只截目标功能区（精确，快速）

举例:
  只截搜索框区域:   a(搜索框.left, 搜索框.top, 搜索框.right, 搜索结果.bottom)
  只截聊天区:       a(聊天区.left, 聊天区.top, 聊天区.right, 输入框.bottom)
```

---

## 三、操作顺序铁律

```
每条工作流都有一个固定的序号顺序:

  wechat_send_message 操作顺序:
  ① locate_window      确认微信在运行
  ② find_searchbox     定位搜索框
  ③ click_searchbox    点击搜索框
  ④ type_contact       输入联系人名
  ⑤ wait_search        等待搜索结果 (500ms-1s)
  ⑥ click_result       点击搜索结果
  ⑦ verify_chat_open   验证聊天窗口已打开
  ⑧ click_input        点击输入框
  ⑨ type_message       输入消息
  ⑩ send               发送
  ⑪ verify_sent        验证已发送

永远不要从 ① 以外的步骤开始。
如果中途失败，回到最近的「验证点」重新来。
```

---

## 四、输入文字注意事项

### 乱码问题

| 现象 | 原因 | 解决 |
|------|------|------|
| type_text 中文乱码 | 微信定制渲染不响应 WM_CHAR | 剪贴板粘贴 (Ctrl+A → Ctrl+V) |
| 输入框已有内容 | 上次操作残留 | `clear: true` 先清空 |
| 输入到错误位置 | 焦点不在输入框 | 先 `ui_click(chat_input_field)` 再输入 |

### 剪贴板 fallback

```powershell
# 当 type_text 无效时的备用方案
powershell -Command "
  Add-Type -AssemblyName System.Windows.Forms
  [System.Windows.Forms.Clipboard]::SetText('消息内容')
"
# 然后发送 Ctrl+V
press_keys('^v')
```

---

## 五、已验证的微信 UIA 控件可靠性表

| 控件 | AutomationId | 可靠性 | 发现轮次 | 备注 |
|------|-------------|--------|---------|------|
| 搜索框 | **空字符串** | 🟢 90% | R1 | 用 `name='搜索'+Edit` 替代 |
| 搜索结果列表 | **`search_list`** | 🟢 95% | R3 | 在 SearchContentPopover 弹窗内 |
| 搜索结果项 | **`search_item_{name}`** | 🟡 70% | R2 | 可能开小程序 |
| 聊天输入框 | **`chat_input_field`** | 🟢 98% | R1 | 最稳定的控件 |
| 发送 (回车) | `{Enter}` | 🟢 99% | R1 | 比点按钮更可靠 |
| 发送按钮 | **无** | 🔴 20% | R1 | 不可靠，用回车替代 |
| 会话列表 | `session_list` | 🟢 90% | - | 微信大厅 |
| 搜索弹窗 | `SearchContentPopover` | 🟡 80% | R3 | className 匹配 |

---

## 六、每次操作后的验证检查清单

```
□ 截图确认目标区域状态
□ 检查 AutomationId 是否存在（找到 = 页面正确）
□ 检查最后一条消息是否 = $message（发送成功）
□ 检查是否有弹窗/错误提示
□ 如果失败，记录缺陷到 ~/.hermes/winpeek/reports/defects.jsonl
```
