---
name: software-self-learning
description: |
  One-shot desktop software learning: record an operation via computer_use,
  analyze the trajectory, and produce a reusable MCP workflow template.
version: 1.0.0
platforms: [windows]
metadata:
  hermes:
    tags: [rpa, self-learning, template-generation, computer-use]
    category: desktop
    requires_toolsets: [computer_use]
---

# Software Self-Learning (一次学习，永久复用)

## 角色定位

你是一名 **RPA 自动化工程师**。你的目标不是每次都重新思考如何操作软件，而是**通过一次完整的录制操作，分析、提炼、生成一个可复用的工作流模板**，让后续同类任务只需 1 次 MCP 调用即可完成。

## 核心原则

- **录制一次，复用无限次**：第一次慢不要紧，目标是产出模板
- **提取 UIA 控件标识**：从录制的截图中提取 AutomationId / 控件角色名称
- **标记参数变量**：把联系人名、消息内容等标记为 `$变量`
- **标注重点/难点/验证点**：告诉模板使用者哪里容易出错

## 执行流程（5 阶段）

### 阶段 1：录制操作轨迹

**任务**：给微信好友列表中的"许国勇"发送一条问候消息。

**环境**：Windows 桌面，微信客户端已登录，"许国勇"在好友列表可见。


### 阶段 1.1：确认环境 & 录制方式

**视觉分析模型**：你已配置 `auxiliary.vision` → `qwen2.5vl:7b`（Ollama）。分析截图时使用 `vision_analyze` 工具（而非 `computer_use` 的 capture）。

**录制方式**：

不需要录视频。cua-driver 每步自动生成:
- `screenshot.png` — 窗口截图（PNG）
- `uia_tree.json` — UIA 无障碍树（结构化文本）
- `action.json` — 操作参数

这 3 个文件足够 AI 分析。视频（recording.mp4）可选，仅供人看。

**手动录制方案**（如果 cua-driver MCP 录制不可用）：

用 `write_file` 每步追加到 `~/.hermes/winpeek/traces/wechat_send_message/trace.jsonl`。每步记录: `{step, intent, action, args, result, key_elements, duration_ms}`。

截图通过 `computer_use(action="capture", capture_after=True)` 自动产生，在对话上下文中可见。

### 阶段 1.2：确认微信环境

1. 用 `computer_use(action="list_apps")` 确认微信在运行
2. 用 `computer_use(action="capture", mode="som", app="微信")` 捕获微信窗口当前状态
3. 记录微信进程的 pid 和主窗口信息

### 阶段 1.3：执行操作（每步带 capture_after=True）

**边做边记** — 每做完一步，立即用 `write_file` 追加到 `~/.hermes/winpeek/traces/wechat_send_message/trace.jsonl`：

每条记录的格式：
```json
{"step":N, "intent":"...", "action":"...", "args":{...}, "result":"...", "key_elements":[...], "duration_ms":N}
```

按以下顺序操作：

```
Step 1: 确保在微信主窗口，如果在聊天窗口，先返回大厅
Step 2: 定位搜索框 → 点击
Step 3: 输入联系人名 "许国勇"
Step 4: 等待搜索结果出现（wait 0.5~1 秒）
Step 5: 在搜索结果中定位"许国勇" → 点击打开聊天
Step 6: 验证聊天窗口已打开（chat_input_field 可见）
Step 7: 定位输入框 → 点击聚焦
Step 8: 输入消息 "你好，问候一下"
Step 9: 点击发送按钮（或按回车）
Step 10: 验证消息已发送（最后一条消息内容 = "你好，问候一下"）
```

### 阶段 1.4：停止录制

操作全部完成后，用 `read_file` 读取 `~/.hermes/winpeek/traces/wechat_send_message/trace.jsonl` 确认所有步骤已记录。

---

### 阶段 2：整理轨迹数据

将 `trace.jsonl` 中的每行 JSON 汇总为一个完整的 JSON 文件。

用 `write_file` 保存到 `~/.hermes/winpeek/traces/wechat_send_message_trace.json`，格式：

```json
{
  "app": "微信",
  "task": "给许国勇发送你好",
  "date": "2026-07-07",
  "total_steps": 10,
  "total_duration_ms": 45000,
  "steps": [
    {
      "step": 1,
      "intent": "确保在微信主窗口",
      "action": "capture",
      "args": {"mode": "som", "app": "微信"},
      "result": "会话列表可见，在微信大厅",
      "key_elements": [
        {"index": 1, "aid": "search_box", "role": "Edit", "label": "搜索"},
        {"index": 3, "aid": "session_list", "role": "List", "children_count": 25}
      ],
      "duration_ms": 1200
    }
  ]
}
```

---

### 阶段 3：分析轨迹 → 提取操作知识

读取 trace JSON，**分两步分析**：

#### 3.1 视觉分析（用 Qwen2.5VL）

对每一步的截图，调用 `vision_analyze`（已配置 `auxiliary.vision` → `qwen2.5vl:7b`）：

```
vision_analyze(截图, "描述这张微信截图中可见的 UI 元素：按钮、输入框、列表项的位置和文字。重点识别搜索框、联系人列表、聊天输入框、发送按钮。")
```

目标：提取每步截图中可交互元素的**角色+文字标签+大致位置**。

#### 3.2 结构化分析（从 UIA 树 / capture 返回的 elements）

从 `computer_use(action="capture", mode="ax")` 返回的 elements 数组中直接提取：
- AutomationId（如 `search_box`、`chat_input_field`、`send_button`）
- 控件类型（Edit/Button/ListItem）
- 精确坐标（BoundingRectangle）

| 合并前步骤 | 合并后 | 原因 |
|-----------|--------|------|
| Step1-2: 定位窗口+截图 | 1步: `locate_window` | 可合并为一次性操作 |
| Step2-3: 点搜索框+输入 | 1步: `search_contact` | 点完立即输入，不需要中间思考 |
| Step7-9: 点输入框+输入+发送 | 3步保持 | 需要验证输入内容 |

#### 3.2 提取关键控件

```json
{
  "微信主窗口": {"aid": "MainWindow", "detect": "session_list"},
  "搜索框": {"aid": "search_box", "role": "Edit", "action": "click + type"},
  "搜索结果列表": {"aid": "search_result_list", "wait_after": "type"},
  "搜索结果项": {"aid_pattern": "search_result_item_*", "match": "contact_name"},
  "聊天输入框": {"aid": "chat_input_field", "detect": "聊天窗口已打开"},
  "发送按钮": {"aid": "send_button", "alternative": "key(return)"}
}
```

#### 3.3 参数变量

| 变量名 | 来源 | 示例值 |
|--------|------|--------|
| `$contact_name` | 用户输入 | "许国勇" |
| `$message` | 用户输入 | "你好，问候一下" |

#### 3.4 重点/难点/验证点

| 类型 | 描述 |
|------|------|
| 🔴 **重点** | 搜索结果可能有多个同名联系人，默认取第一个 |
| 🔴 **重点** | 搜索后需要等待 500-1000ms 让结果列表加载 |
| 🟡 **难点** | 如果微信窗口最小化，需要先 `focus_app` 恢复 |
| 🟡 **难点** | 聊天窗口可能已有未读消息，输入框位置不变 |
| 🟢 **验证点** | `chat_input_field` 出现 = 聊天窗口已打开 |
| 🟢 **验证点** | 发送后最后一条消息内容 = `$message` |

---

### 阶段 4：生成工作流模板

基于以上分析，生成一个完整的 MCP 模板 JSON：

```json
{
  "name": "wechat_send_message",
  "version": 1,
  "description": "给微信好友发送消息",
  "learned_from": "trace_2026-07-07_wechat_send_message",
  "inputs": ["contact_name", "message"],
  "steps": [
    {"id": 1, "tool": "locate_window", "args": {"app": "微信"}, "as": "win"},
    {"id": 2, "tool": "click", "args": {"window": "$win", "aid": "search_box"}, "as": "c1"},
    {"id": 3, "tool": "type", "args": {"window": "$win", "text": "$contact_name"}, "as": "t1"},
    {"id": 4, "tool": "wait_for", "args": {"window": "$win", "aid": "search_result_list", "timeout_ms": 3000}, "as": "w1"},
    {"id": 5, "tool": "click", "args": {"window": "$win", "aid_match": "search_result_item_*", "match_text": "$contact_name"}, "as": "c2"},
    {"id": 6, "tool": "wait_for", "args": {"window": "$win", "aid": "chat_input_field", "timeout_ms": 5000}, "as": "w2"},
    {"id": 7, "tool": "click", "args": {"window": "$win", "aid": "chat_input_field"}, "as": "c3"},
    {"id": 8, "tool": "type", "args": {"window": "$win", "text": "$message"}, "as": "t2"},
    {"id": 9, "tool": "click", "args": {"window": "$win", "aid": "send_button"}, "as": "done"}
  ],
  "checkpoints": {
    "before": ["微信窗口存在"],
    "middle": ["chat_input_field 可见 = 聊天已打开"],
    "after": ["最后一条消息内容 = $message"]
  },
  "error_handlers": {
    "contact_not_found": "尝试重新搜索或提示用户检查联系人名",
    "window_not_found": "尝试 focus_app('微信') 或提示用户打开微信"
  }
}
```

将这个模板保存到 `~/.hermes/winpeek/templates/wechat_send_message.json`。

---

### 阶段 5：测试验证

用保存的模板测试 2 次：

```
测试 1: wechat_send_message(contact_name="许国勇", message="第二次测试")
测试 2: wechat_send_message(contact_name="文件传输助手", message="模板测试")
```

如果 2 次都成功 → 模板可用，标记 `confidence: 0.95`。
如果失败 → 分析失败原因，修正模板，重新测试。

---

## 最终交付物

执行完成后，你应该产出以下文件：

| 文件 | 路径 |
|------|------|
| 操作轨迹 | `~/.hermes/winpeek/traces/wechat_send_message_trace.json` |
| 控件映射 | `~/.hermes/winpeek/maps/wechat_uia_map.json` |
| 工作流模板 | `~/.hermes/winpeek/templates/wechat_send_message.json` |
| 测试报告 | `~/.hermes/winpeek/reports/wechat_send_message_test.md` |

全部完成后，告知用户产出物路径和测试结果。
