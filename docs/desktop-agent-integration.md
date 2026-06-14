# Hermes Desktop Agent 集成指南

## 📋 概述

Hermes Desktop Agent 让 Hermes Agent 能够控制桌面：
- 🖱️ 鼠标操作（点击、移动、滚动）
- ⌨️ 键盘输入
- 📸 截图
- 👁️ 视觉识别（5 层级联）
- 🪟 窗口管理
- 🚀 启动程序

## 🏗️ 架构

```
Hermes Agent (AI 大脑)
    ↓ HTTP 调用 (:18791)
OpenClaw AI-Supervisor 插件
    ├── src/desktop-tools.ts      (20+ 桌面工具)
    ├── src/supervisor-tool.ts    (监督工具)
    ├── src/task-store.ts         (任务存储)
    ├── src/observer.ts           (任务观察者)
    └── desktop-agent/            (桌面执行器)
        ├── main.mjs              (Electron 主进程)
        ├── server.mjs            (HTTP API 服务器)
        ├── vision.mjs            (5 层视觉识别)
        └── ...
    ↓ 控制
桌面（鼠标、键盘、视觉）
```

**关键设计：**
- ✅ **引用完整的 ai-supervisor 插件** - 不只是 desktop-agent
- ✅ Desktop Agent 作为**独立进程**运行
- ✅ Hermes 通过 **HTTP API** 调用
- ✅ 代码通过 **Git Submodule** 引用（不复制）
- ✅ 单一维护点，易于同步更新

## 📦 安装

### 1. 创建 OpenClaw hermes 分支

在你的 Fork 仓库中创建定制分支：

```bash
cd /root/www/openclaw-cn

# 创建 hermes 分支
git checkout -b hermes

# 推送远程
git push origin hermes
```

### 2. 初始化 Git Submodule

```bash
cd /root/hermes-agent

# 添加 OpenClaw 作为 submodule（指定 hermes 分支）
git submodule add -b hermes git@gitlab.test.com:mansonyu/openclaw-cn.git external/openclaw

# 或如果已添加，初始化
git submodule update --init --recursive

# 验证 ai-supervisor 存在
ls -la external/openclaw/extensions/ai-supervisor/
# 应该看到：
#   index.ts
#   src/
#   desktop-agent/
#   web/

# 验证分支
cd external/openclaw
git branch --show-current  # 应显示 "hermes"
```

### 3. 安装 Desktop Agent 依赖

```bash
cd external/openclaw/extensions/ai-supervisor/desktop-agent
npm install
```

### 4. 验证 Hermes 工具

Desktop Agent 工具已添加到 Hermes：
- ✅ `tools/desktop_agent.py` - 工具实现
- ✅ `toolsets.py` - 工具集定义

## 🚀 使用

### 启动 Desktop Agent

```bash
# 方式 1: 仅 HTTP 服务（推荐，无 UI）
./scripts/start-desktop-agent.sh

# 方式 2: 仅 HTTP（调试）
./scripts/start-desktop-agent.sh --http-only

# 方式 3: 完整 Electron UI（悬浮窗 + 面板）
./scripts/start-desktop-agent.sh --electron
```

### 在 Hermes 中使用

启动 Desktop Agent 后，Hermes 自动检测并使用桌面工具：

```python
# Hermes 对话示例
用户: "帮我打开 QQ"
Hermes: [调用 desktop_launch(exe="C:/Program Files/Tencent/QQ/Bin/QQ.exe")]

用户: "点击发送按钮"
Hermes: [调用 desktop_human_click(target="发送按钮")]

用户: "截个图看看"
Hermes: [调用 desktop_screenshot()]
```

### 可用的工具

| 工具 | 功能 | 示例 |
|------|------|------|
| `desktop_click` | 点击坐标 | `desktop_click(x=1234, y=567)` |
| `desktop_double_click` | 双击 | `desktop_double_click(x=100, y=200)` |
| `desktop_mouse_move` | 移动鼠标 | `desktop_mouse_move(x=500, y=300)` |
| `desktop_type` | 输入文字 | `desktop_type(text="Hello")` |
| `desktop_keypress` | 按键 | `desktop_keypress(keys="ctrl+c")` |
| `desktop_screenshot` | 截图 | `desktop_screenshot()` |
| `desktop_vision_find` | 视觉查找 | `desktop_vision_find(target="QQ图标")` |
| `desktop_vision_analyze` | 视觉分析 | `desktop_vision_analyze(prompt="描述屏幕")` |
| `desktop_list_windows` | 列出窗口 | `desktop_list_windows()` |
| `desktop_activate_window` | 激活窗口 | `desktop_activate_window(title="QQ")` |
| `desktop_launch` | 启动程序 | `desktop_launch(exe="...")` |
| `desktop_human_click` | 人类点击 | `desktop_human_click(target="发送按钮")` |
| `desktop_reset` | 回到桌面 | `desktop_reset()` |

## 🔧 配置

### 环境变量

```bash
# Desktop Agent 配置
export GATEWAY_WS_URL="ws://127.0.0.1:18789"  # Gateway 地址
export NODE_ID="hermes-desktop"                 # 节点 ID
export NO_WS=1                                  # 禁用 WebSocket（仅 HTTP）
```

### Hermes 配置

在 `~/.hermes/config.yaml` 中启用 desktop 工具集：

```yaml
tools:
  enabled:
    - desktop  # 启用桌面自动化工具
```

## 📊 视觉识别系统

Desktop Agent 使用 **5 层级联视觉识别**：

```
L0:   Win32 API (SysListView32)     → 桌面图标 ~500ms
L0.5: OpenCV 模板匹配               → 图标搜索 ~300ms
L2:   PaddleOCR                     → 文字识别 ~250ms
L1:   OmniParser                    → UI 元素 ~3s
L3:   Qwen2.5-VL-7B (Ollama)       → 语义理解 ~600ms

桌面图标查找：L0 → L0.5 → L3
通用 UI 查找：L2 → L1 → L3
```

## 🎯 使用场景

### 场景 1: 自动回复 QQ 消息

```
用户: "帮我回复 QQ 上的最新留言"
Hermes:
  1. desktop_launch(exe="QQ.exe")
  2. desktop_vision_find(target="消息列表")
  3. desktop_human_click(target="最新留言")
  4. desktop_vision_analyze(prompt="读取消息内容")
  5. [AI 生成回复]
  6. desktop_type(text="回复内容")
  7. desktop_human_click(target="发送按钮")
```

### 场景 2: 自动化工作流

```
用户: "每天早上 9 点打开企业微信，检查未读消息"
Hermes:
  1. [设置 cronjob]
  2. desktop_launch(exe="WeCom.exe")
  3. desktop_vision_find(target="消息图标")
  4. desktop_human_click(target="消息图标")
  5. desktop_vision_analyze(prompt="检查未读消息数量")
  6. [如果有未读，通知用户]
```

### 场景 3: 智能桌面操作

```
用户: "找到桌面上的 Excel 文件并打开"
Hermes:
  1. desktop_vision_find(target="Excel文件", mode="desktop")
  2. desktop_human_click(target="Excel文件", action="double_click")
```

## 🔍 故障排查

### Desktop Agent 未启动

```bash
# 检查服务状态
curl http://localhost:18791/health

# 查看日志
tail -f ~/.openclaw/desktop-agent/logs/agent.log
```

### 工具不可用

```python
# 在 Hermes 中检查
from tools.desktop_agent import check_desktop_agent
print(check_desktop_agent())  # 应返回 True
```

### 视觉识别失败

```bash
# 检查视觉服务状态
curl http://localhost:18791/vision/health

# 测试 OCR
curl http://localhost:18791/vision/ocr
```

## 📁 目录结构

```
hermes-agent/
├── tools/
│   └── desktop_agent.py          # 🆕 Hermes 工具（HTTP 客户端）
├── toolsets.py                    # 🆕 添加 desktop 工具集
├── scripts/
│   └── start-desktop-agent.sh    # 🆕 启动脚本
├── docs/
│   └── desktop-agent-integration.md  # 🆕 集成文档
├── external/
│   └── openclaw/                  # 📦 Git Submodule（整个仓库）
│       └── extensions/
│           └── ai-supervisor/     # 🎯 完整的 AI 监督插件
│               ├── index.ts       # 插件入口
│               ├── src/           # 插件核心代码
│               │   ├── desktop-tools.ts      (20+ 工具)
│               │   ├── supervisor-tool.ts    (监督)
│               │   ├── task-store.ts         (任务)
│               │   ├── observer.ts           (观察者)
│               │   ├── analyzer.ts           (分析)
│               │   └── corrector.ts          (校正)
│               ├── desktop-agent/ # 桌面执行器（独立进程）
│               │   ├── main.mjs
│               │   ├── server.mjs
│               │   ├── vision.mjs
│               │   └── ...
│               └── web/           # 监控面板
│                   └── dashboard.html
└── ... (其他 Hermes 文件)
```

## 🔄 更新 Desktop Agent

### 同步策略

我们使用 **Fork + 分支** 策略，支持双向同步：

```
OpenClaw 官方仓库
    ↑ 定期同步
    │
你的 Fork (mansonyu/openclaw-cn)
    │
    ├─ main              # 跟踪官方更新
    └─ hermes            # Hermes 定制分支
         ↑ 双向同步
         │
Hermes Agent
    └── external/openclaw/  # 引用 hermes 分支
```

### 日常同步

```bash
# 使用同步脚本（推荐）
./scripts/sync-openclaw.sh

# 选择操作：
#   1) 同步 Fork (main → hermes)
#   2) 更新 Hermes 引用
#   3) 完整同步 (1 + 2 + 提交)
#   4) 查看变更
#   5) 显示状态
```

### 手动同步

```bash
# 1. 同步官方更新到你的 Fork
cd /root/www/openclaw-cn
git checkout main
git pull origin main
git checkout hermes
git merge main
git push origin hermes

# 2. 更新 Hermes 中的引用
cd /root/hermes-agent/external/openclaw
git checkout hermes
git pull origin hermes

# 3. 提交更新
cd /root/hermes-agent
git add external/openclaw
git commit -m "chore: update openclaw hermes branch"
```

### 从 Hermes 贡献回 OpenClaw

如果你在 hermes 分支上开发了通用功能：

```bash
# 1. 在 Fork 仓库中开发
cd /root/www/openclaw-cn
git checkout hermes
# ... 开发新功能 ...
git add .
git commit -m "feat: add new feature"
git push origin hermes

# 2. 如果功能通用，合并到 main
git checkout main
git merge hermes
git push origin main

# 3. 或者保留在 hermes 分支（Hermes 专用）
```

## 💡 最佳实践

1. **优先使用 `desktop_human_click`** - 自动查找 + 点击，一步到位
2. **限定搜索区域** - 提高视觉识别速度
3. **添加延迟** - 操作之间留时间让 UI 响应
4. **错误处理** - 检查返回值，失败时重试
5. **日志记录** - 记录每次操作，方便调试

## 🚀 下一步

- [ ] 添加更多视觉模板
- [ ] 集成 Hermes 记忆系统
- [ ] 创建桌面操作 Skills
- [ ] 支持手机 Agent

## 📞 支持

遇到问题？查看：
- Desktop Agent 日志：`~/.openclaw/desktop-agent/logs/agent.log`
- Hermes 日志：`~/.hermes/logs/`
- 视觉服务日志：检查 wuserver 上的服务
