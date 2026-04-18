# AI-Supervisor 插件完整架构

## 📦 项目结构

```
ai-supervisor/                              # 完整的 AI 监督插件
│
├── index.ts                                # 插件入口 (260 行)
│   ├── 注册 Tool (supervisor + desktop)
│   ├── 注册 Service (后台守护)
│   └── 注册 HTTP Handler (Dashboard + API)
│
├── src/                                    # 插件核心代码
│   ├── desktop-tools.ts                   # 🎯 桌面工具 (1012 行, 20+ 工具)
│   │   ├── desktop_screenshot
│   │   ├── desktop_click / double_click / right_click
│   │   ├── desktop_type / keypress / scroll
│   │   ├── desktop_mouse_move
│   │   ├── desktop_launch
│   │   ├── desktop_windows / window_*
│   │   ├── desktop_vision_* (ocr/detect/analyze/find)
│   │   ├── desktop_find_icon
│   │   ├── desktop_ui_* (tree/click/invoke)
│   │   └── desktop_settings_*
│   │
│   ├── supervisor-tool.ts                 # 监督工具 (6.5KB)
│   │   └── AI 任务监督和协调
│   │
│   ├── task-store.ts                      # 任务存储 (10.9KB)
│   │   ├── 任务创建/更新/查询
│   │   └── MySQL/SQLite 存储
│   │
│   ├── observer.ts                        # 任务观察者 (8.0KB)
│   │   ├── 后台监控任务执行
│   │   └── 自动纠正错误
│   │
│   ├── analyzer.ts                        # 分析器 (6.8KB)
│   │   └── 分析任务执行结果
│   │
│   ├── corrector.ts                       # 校正器 (5.1KB)
│   │   └── 自动纠正执行错误
│   │
│   ├── screenshot.ts                      # 截图工具 (6.3KB)
│   │   └── 截图处理和标注
│   │
│   └── types.ts                           # 类型定义 (3.2KB)
│       └── TypeScript 类型
│
├── desktop-agent/                          # 🖥️ 桌面执行器（独立进程）
│   ├── main.mjs                           # Electron 主进程 (535 行)
│   │   ├── 创建悬浮窗（透明、置顶）
│   │   ├── 创建面板窗口（对话+任务）
│   │   ├── 系统托盘图标
│   │   └── IPC 通信
│   │
│   ├── server.mjs                         # HTTP API 服务器 (3840 行!)
│   │   ├── HTTP 端点 (30+)
│   │   │   ├── /health
│   │   │   ├── /screenshot
│   │   │   ├── /click, /double-click, /right-click
│   │   │   ├── /mouse-move
│   │   │   ├── /type, /keypress, /scroll
│   │   │   ├── /windows, /window/*
│   │   │   ├── /launch, /open-explorer
│   │   │   ├── /files
│   │   │   ├── /vision/* (health/ocr/detect/analyze/find)
│   │   │   └── /human-click
│   │   │
│   │   ├── WebSocket 客户端
│   │   │   └── 连接 Gateway
│   │   │
│   │   ├── 日志系统
│   │   │   └── 文件轮转 (5MB)
│   │   │
│   │   └── .env 加载
│   │
│   ├── vision.mjs                         # 视觉识别服务 (664 行)
│   │   ├── L0:   Win32 API (桌面图标)
│   │   ├── L0.5: OpenCV 模板匹配
│   │   ├── L2:   PaddleOCR (文字识别)
│   │   ├── L1:   OmniParser (UI 元素)
│   │   └── L3:   Qwen2.5-VL (语义理解)
│   │
│   ├── win32.mjs                          # Windows API FFI (15.2KB)
│   │   ├── koffi 调用 user32.dll
│   │   ├── 窗口列表/操作
│   │   └── 坐标获取
│   │
│   ├── uia.mjs                            # UI Automation (11.0KB)
│   │   ├── UI 元素树
│   │   ├── 元素查找/点击
│   │   └── 值设置/获取
│   │
│   ├── human-ops.mjs                      # 人类操作模拟 (16.8KB)
│   │   ├── 平滑鼠标移动
│   │   ├── 随机延迟
│   │   └── 自然操作
│   │
│   ├── software-scanner.mjs               # 软件扫描器 (21.2KB)
│   │   └── 扫描已安装软件
│   │
│   ├── grid.mjs                           # 网格覆盖层 (6.4KB)
│   │   └── 屏幕网格坐标
│   │
│   ├── settings.mjs                       # 设置管理 (8.1KB)
│   │   └── 配置读写
│   │
│   ├── panel.html                         # 面板 UI (1384 行)
│   │   ├── 对话标签（Markdown 渲染）
│   │   ├── 任务标签
│   │   ├── 设置标签
│   │   └── 健康信息标签
│   │
│   ├── floating.html                      # 悬浮窗 (4.2KB)
│   │   └── 3D 机器人动画
│   │
│   ├── dashboard.html                     # 监控面板 (14.9KB)
│   │   └── 实时状态监控
│   │
│   ├── vision-test.html                   # 视觉测试 (21.0KB)
│   │   └── 视觉识别测试界面
│   │
│   ├── preload.cjs / preload.mjs          # Electron 预加载
│   │
│   └── 其他工具脚本
│       ├── start.ps1                      # Windows 启动脚本
│       ├── env-check.ps1                  # 环境检查
│       ├── service-install.mjs            # 安装 Windows 服务
│       ├── approve-pairing.mjs            # 配对审批
│       └── ...
│
├── web/
│   └── dashboard.html                     # Web 监控面板
│
├── openclaw.plugin.json                   # 插件配置
├── package.json                           # NPM 配置
└── tsconfig.json                          # TypeScript 配置
```

---

## 🎯 核心功能模块

### 1. 插件入口 (index.ts)

**职责：** 注册所有组件到 OpenClaw

```typescript
export default function register(api: ClawdbotPluginApi) {
  // 1. 注册工具
  api.registerTool(createSupervisorTool(pluginCfg));
  for (const tool of createDesktopTools(pluginCfg)) {
    api.registerTool(tool);
  }
  
  // 2. 注册后台服务
  api.registerService({
    id: "ai-supervisor",
    start: async (ctx) => { /* 启动观察者 */ },
    stop: async (ctx) => { /* 停止观察者 */ },
  });
  
  // 3. 注册 HTTP Handler
  api.registerHttpHandler(async (req, res) => {
    // /supervisor/health
    // /supervisor/tasks
    // /supervisor/tasks/:id
    // ...
  });
}
```

---

### 2. 桌面工具 (desktop-tools.ts)

**20+ 个桌面操控工具：**

```typescript
// 鼠标操作
desktop_screenshot          // 截图
desktop_click               // 单击
desktop_double_click        // 双击
desktop_mouse_move          // 平滑移动

// 键盘操作
desktop_type                // 输入文字
desktop_keypress            // 按键组合
desktop_scroll              // 滚动

// 窗口管理
desktop_windows             // 列出窗口
desktop_window_activate     // 激活窗口
desktop_window_maximize     // 最大化
desktop_window_minimize     // 最小化
desktop_window_close        // 关闭窗口
desktop_reset               // 回到桌面

// 程序启动
desktop_launch              // 启动程序
desktop_open_explorer       // 打开文件夹

// 视觉识别
desktop_vision_ocr          // OCR 文字识别
desktop_vision_detect       // UI 元素检测
desktop_vision_analyze      // 语义分析
desktop_vision_find         // 级联查找
desktop_find_icon           // 图标定位

// UI Automation
desktop_ui_tree             // UI 树
desktop_ui_click            // UI 点击
desktop_ui_invoke           // UI 触发
desktop_ui_set_value        // 设置值

// 设置
desktop_settings_get        // 读取设置
desktop_settings_set        // 修改设置
```

---

### 3. 桌面执行器 (desktop-agent/)

**独立进程，提供 HTTP API：**

```javascript
// server.mjs - HTTP API 服务器
const PORT = 18791;

// 端点清单
GET  /health               → 健康检查
GET  /screenshot           → 截取桌面
POST /click                → 鼠标单击
POST /double-click         → 鼠标双击
POST /mouse-move           → 移动鼠标
POST /type                 → 键盘输入
POST /keypress             → 按键
GET  /windows              → 列出窗口
POST /window/activate      → 激活窗口
POST /launch               → 启动程序
GET  /vision/health         → 视觉服务状态
GET  /vision/ocr            → OCR 识别
POST /vision/analyze        → 语义分析
POST /vision/find           → 级联查找
POST /human-click           → 人类操作全流程
// ... 30+ 端点
```

---

### 4. 视觉识别系统 (vision.mjs)

**5 层级联识别：**

```
桌面图标查找：
  L0 (Win32 API) → L0.5 (OpenCV) → L3 (Qwen-VL)
  ~500ms           ~300ms           ~600ms

通用 UI 查找：
  L2 (PaddleOCR) → L1 (OmniParser) → L3 (Qwen-VL)
  ~250ms           ~3s                ~600ms
```

---

## 🔄 Hermes 集成方式

### 当前方案：HTTP 调用

```
Hermes Agent
    ↓ HTTP 调用
tools/desktop_agent.py (13 个工具)
    ↓ HTTP :18791
ai-supervisor/desktop-agent/server.mjs
    ↓ 执行
桌面（鼠标、键盘、视觉）
```

### 未来增强：完整插件集成

```
Hermes Agent
    ↓ 直接调用
ai-supervisor/src/desktop-tools.ts (20+ 工具)
    ↓ HTTP :18791
ai-supervisor/desktop-agent/server.mjs
    ↓ 执行
桌面（鼠标、键盘、视觉）
```

---

## 📊 代码统计

| 模块 | 文件数 | 代码行数 | 说明 |
|------|--------|---------|------|
| **插件核心** | 8 | ~55KB | src/ 目录 |
| **桌面执行器** | 31 | ~400KB | desktop-agent/ 目录 |
| **总计** | 39 | ~455KB | 完整的 AI 监督系统 |

---

## 🚀 启动流程

```bash
# 1. 启动 Desktop Agent (HTTP 服务)
cd external/openclaw/extensions/ai-supervisor/desktop-agent
node server.mjs

# 2. (可选) 启动 Electron UI
npm start

# 3. Hermes 通过 HTTP 调用
curl http://localhost:18791/health
```

---

## 💡 关键设计

1. **双进程架构**
   - 插件进程（TypeScript，OpenClaw 内）
   - 执行器进程（Node.js，独立）

2. **HTTP API 契约**
   - 清晰的 REST 接口
   - 30+ 端点
   - JSON 响应

3. **视觉识别级联**
   - 从快到慢
   - 从精准到语义
   - 自动选择最佳方案

4. **人类操作模拟**
   - 平滑鼠标移动
   - 随机延迟
   - 自然操作模式

5. **任务监督系统**
   - 任务存储（MySQL/SQLite）
   - 后台观察者
   - 自动纠正

---

## 📝 总结

**ai-supervisor 是一个完整的 AI 监督系统：**

- ✅ **20+ 桌面工具** - 全面的桌面操控
- ✅ **5 层视觉识别** - 从图标到语义
- ✅ **任务监督** - 自动监控和纠正
- ✅ **Electron UI** - 悬浮窗 + 面板
- ✅ **HTTP API** - 30+ 端点
- ✅ **人类模拟** - 自然操作模式

**Hermes 集成只需要：**
- ✅ HTTP 调用 desktop-agent/:18791
- ✅ 使用 tools/desktop_agent.py (13 个工具)
- ✅ 未来可扩展到完整插件
