---
name: trace-to-template
description: |
  Analyze a WeChat computer_use operation trace from the conversation history
  and generate a reusable MCP workflow template JSON for WeChat desktop automation.
version: 2.0.0
platforms: [windows]
metadata:
  hermes:
    tags: [wechat, rpa, template-generation, trace-analysis]
    category: desktop
    requires_toolsets: [computer_use]
---

# Trace → Template — 微信操作历史 → 工作流模板

## 任务

你刚才用 computer_use 操作了微信桌面客户端，完成了某个任务（如给好友发消息）。

现在回顾你的操作历史，提炼出一个**可复用的 MCP 工作流模板**，让后续同类任务只需调用模板即可完成。

## 微信已知的 UIA 控件（参考）

这些是微信桌面版常见的 AutomationId，分析时优先匹配：

| 控件 | AutomationId | 所在页面 | 操作 |
|------|-------------|---------|------|
| 会话列表 | `session_list` | 微信大厅 | 读取 |
| 搜索框 | `search_box` | 微信大厅 | click + type |
| 搜索结果列表 | `search_result_list` | 微信大厅 | 读取 |
| 搜索结果项 | `search_result_item_*` | 微信大厅 | click |
| 聊天消息列表 | `chat_message_list` | 聊天窗口 | 验证页面 |
| 聊天输入框 | `chat_input_field` | 聊天窗口 | click + type |
| 发送按钮 | `send_button` | 聊天窗口 | click |
| 导航-微信 | `tab_wechat` | 底部导航 | click |
| 导航-通讯录 | `tab_contacts` | 底部导航 | click |
| 联系人列表 | `contact_list` | 通讯录 | 读取 |
| 当前聊天名 | `current_chat_name_label` | 聊天窗口 | 验证 |
| 更多选项 | `more_options_btn` | 聊天窗口 | click |

## 步骤

### 1. 回顾操作历史

从**当前对话历史**中，逐条提取你刚才用 computer_use 完成的每一步：

- 每一步的 action（capture/click/type/key/wait/scroll...）
- 每一步的参数（element=N / text="..." / coordinate=[x,y] / seconds=N）
- 每一步的意图（你当时想干什么：如"定位搜索框"、"输入联系人名"）
- capture 步骤返回的关键 UIA 元素（AutomationId、role、label）

### 2. 提取关键控件 — 精确匹配

将 capture 步骤中返回的 UIA 元素，与上方的「微信已知控件表」对照：

| 你在步骤中用到的控件 | 匹配到的 AutomationId | 说明 |
|-------------------|---------------------|------|
| element N（搜索框） | `search_box` | |
| element M（输入框） | `chat_input_field` | |
| ... | ... | |

如果某个控件不在已知表中，根据它的 role + label 推测用途，记录下来。

### 3. 标记参数变量

把操作中写死的具体值替换为 `$变量名`：

| 变量名 | 原值（你操作时用的） | 说明 |
|--------|-------------------|------|
| `$contact_name` | "许国勇" | 联系人名称 |
| `$message` | "你好，问候一下" | 消息正文 |

**规则**：文本类参数应变成变量，控件编号（element=N）应保留原数值。

### 4. 标注重点/难点/验证点

| 类型 | 描述 | 来源步骤 |
|------|------|---------|
| 🔴 **重点** | 搜索后需 wait 0.5-1s 等结果加载 | 步骤 N |
| 🟡 **难点** | 同名联系人可能有多个，默认取第一个 | 步骤 M |
| 🟢 **验证点** | `chat_message_list` 出现 = 聊天窗口打开 | 步骤 K |
| 🟢 **验证点** | 发送后最后一条消息 = `$message` | 最后一步 |

### 5. 生成模板 JSON

用 `write_file` 保存到 `~/.hermes/winpeek/templates/wechat_send_message.json`：

```json
{
  "name": "wechat_send_message",
  "version": 1,
  "app": "微信",
  "description": "给微信好友发送消息",
  "learned_from": "当前对话操作历史",
  "inputs": [
    {"name": "contact_name", "type": "string", "required": true, "description": "微信好友名或备注名"},
    {"name": "message", "type": "string", "required": true, "description": "要发送的消息内容"}
  ],
  "preconditions": ["微信客户端已登录", "联系人存在于好友/会话列表"],
  "steps": [
    {
      "id": 1, "intent": "聚焦微信，确认在主窗口",
      "tool": "computer_use", "action": "capture", "args": {"mode": "som", "app": "微信"}
    },
    {
      "id": 2, "intent": "点击搜索框",
      "tool": "computer_use", "action": "click",
      "args": {"element": "<替换为实际的搜索框编号>", "capture_after": true},
      "uia_target": {"aid": "search_box"}
    },
    {
      "id": 3, "intent": "输入联系人名搜索",
      "tool": "computer_use", "action": "type",
      "args": {"text": "$contact_name"}
    },
    {
      "id": 4, "intent": "等待搜索结果加载",
      "tool": "computer_use", "action": "wait",
      "args": {"seconds": 1}
    },
    {
      "id": 5, "intent": "点击第一个搜索结果",
      "tool": "computer_use", "action": "capture",
      "args": {"mode": "som", "app": "微信"},
      "note": "重新截图获取搜索结果列表的元素编号"
    },
    {
      "id": 6, "intent": "在搜索结果中点击联系人",
      "tool": "computer_use", "action": "click",
      "args": {"element": "<替换为搜索结果项的编号>", "capture_after": true},
      "uia_target": {"aid_pattern": "search_result_item_*"}
    },
    {
      "id": 7, "intent": "验证聊天窗口已打开",
      "tool": "computer_use", "action": "capture",
      "args": {"mode": "som", "app": "微信"},
      "verify": "chat_message_list 可见"
    },
    {
      "id": 8, "intent": "点击输入框聚焦",
      "tool": "computer_use", "action": "click",
      "args": {"element": "<替换为输入框编号>", "capture_after": true},
      "uia_target": {"aid": "chat_input_field"}
    },
    {
      "id": 9, "intent": "输入消息内容",
      "tool": "computer_use", "action": "type",
      "args": {"text": "$message"}
    },
    {
      "id": 10, "intent": "发送消息",
      "tool": "computer_use", "action": "key",
      "args": {"keys": "return"},
      "alternative": {"action": "click", "args": {"element": "<发送按钮编号>"}, "uia_target": {"aid": "send_button"}}
    }
  ],
  "checkpoints": {
    "pre_run": "微信窗口存在，在主大厅页面",
    "search_done": "搜索结果列表已出现",
    "chat_open": "chat_message_list 可见 = 聊天窗口已打开",
    "sent": "最后一条消息内容 = $message"
  },
  "error_handlers": {
    "window_not_found": "提示用户检查微信是否打开",
    "contact_not_found": "提示用户检查联系人名是否正确",
    "chat_not_open": "尝试按 Esc 返回大厅后重试"
  }
}
```

**关键**：`<替换为...>` 的部分必须填上你实际操作时用的 element 编号。不要保留占位符。

### 6. 输出摘要

完成后输出以下报告：

```
模板生成报告
───────────
模板名: wechat_send_message
应用:   微信桌面版
步骤数: 10 步
变量:   contact_name, message
验证点: 3 个 (pre_run, chat_open, sent)
路径:   ~/.hermes/winpeek/templates/wechat_send_message.json
状态:   ✅ 已保存
```

---

### 7. 迭代练习（3-5 遍）

**目标**：通过反复执行模板，发现并修复缺陷，直到成功率 ≥ 80%。

#### 7.1 测试轮次

执行 3-5 轮，每轮换不同的参数：

| 轮次 | contact_name | message | 验证目标 |
|------|-------------|---------|---------|
| 第1轮 | 许国勇 | 模板测试1 | 首次验证模板能否跑通 |
| 第2轮 | 文件传输助手 | 模板测试2 | 验证通用性（不同联系人） |
| 第3轮 | 微信团队 | 模板测试3 | 验证稳定性 |
| 第4轮 | 许国勇 | （空消息→验证错误处理）| 验证异常输入保护 |
| 第5轮 | （不存在的名字） | 测试 | 验证联系人不存在时的兜底 |

#### 7.2 缺陷记录

**每轮执行后，记录到 `~/.hermes/winpeek/reports/wechat_send_message_defects.jsonl`：**

```json
{"round": 1, "contact": "许国勇", "success": true, "steps_passed": 10, "steps_total": 10, "duration_ms": 35000, "defects": []}
{"round": 2, "contact": "文件传输助手", "success": false, "steps_passed": 6, "steps_total": 10, "duration_ms": 28000, "defects": [
  {"step": 5, "reason": "搜索结果未在1秒内出现", "fix": "wait 从 1s 改为 2s"},
  {"step": 6, "reason": "element 编号过期，需重新 capture", "fix": "在 click 前加一步 capture"}
]}
```

#### 7.3 自愈规则

遇到以下常见缺陷时，**自动修正模板**：

| 缺陷现象 | 自愈方案 |
|---------|---------|
| 搜索结果未出现 | 增加 `wait` 秒数（1s→2s→3s，最多 5s） |
| element 编号无效 (stale) | 在该步骤前插入一步 `capture` 重新获取编号 |
| 微信窗口不在前台 | 插入 `focus_app` 步骤 |
| 点击无反应 | 改用 coordinate 替代 element（按上次 capture 返回的坐标） |
| 发送按钮找不到 | 改用 `key("return")` 发送 |
| 联系人不存在 | 跳过本轮，记录为 skipped |

---

### 8. 最终验收

3-5 轮测试完成后：

1. 统计成功率 = 成功轮数 / 总轮数
2. 如果成功率 < 80%：分析缺陷模式，批量修正模板，再测 2 轮
3. 如果成功率 ≥ 80%：标记 `confidence: 0.90`，输出最终模板

#### 最终报告格式

```
技能验收报告
───────────
技能名:    wechat_send_message
测试轮次:  5 轮
成功:      4 轮
失败:      1 轮
成功率:    80%
累积缺陷:  3 个 → 全部修复
最终步骤:  11 步（原10步 + 1步优化）
置信度:    0.90
路径:      ~/.hermes/winpeek/templates/wechat_send_message.json
状态:      ✅ 验收通过，技能可用
```

如果全部通过，这个技能就是 **可信赖的、可复用的 MCP 工具**。后续任何人只需调用 `wechat_send_message(contact_name, message)` 即可完成操作。
