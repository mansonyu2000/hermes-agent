# Hermes Agent — 项目知识库地图

> **分支**: `feat/winpeek` | **基座**: `main` (Hermes upstream v0.18.0)  
> **我们的代码**: 🆕 46 文件 | **Hermes 原有**: ~2000+ 文件  

---

## 一、项目全景（关键目录）

```
hermes-agent/                     # 根目录
│
├── run_agent.py                  # 🔥 核心: AIAgent 对话循环 (~12k 行)
├── cli.py                        # 🔥 核心: HermesCLI 交互入口 (~11k 行)
├── model_tools.py                # 🔥 核心: 工具分发 + discover_builtin_tools()
├── toolsets.py                   # 🔥 核心: _HERMES_CORE_TOOLS 列表
├── hermes_state.py               # 会话存储 (SQLite FTS5)
├── hermes_constants.py           # get_hermes_home(), 路径解析
├── hermes_logging.py             # 日志 (agent.log / errors.log / gateway.log)
│
├── agent/             109 文件   # Agent 内部引擎
│   ├── transports/               # API 传输层
│   ├── skill_commands.py         # 技能加载
│   ├── skill_utils.py            # 技能扫描 + 平台匹配
│   ├── context_compressor.py     # 上下文压缩
│   ├── conversation_loop.py      # 对话循环
│   └── ... (provider adapters, memory, caching)
│
├── gateway/           36 文件    # 消息网关
│   ├── run.py                    # 网关主入口 (~20k 行)
│   ├── platforms/                # 20+ IM 平台适配器
│   │   ├── telegram.py
│   │   ├── weixin.py
│   │   ├── dingtalk.py
│   │   ├── qqbot/                # 复杂平台=>子目录
│   │   └── ...
│   ├── platform_registry.py      # 平台注册表
│   ├── session.py                # 会话管理
│   ├── hooks.py                  # 钩子系统
│   └── winpeek_hub/    🆕 5 文件 # WinPeek Hub (多租户/路由/归档)
│
├── tools/             93 文件    # 工具实现
│   ├── registry.py               # 工具注册表 (自动发现)
│   ├── terminal.py               # 终端工具
│   ├── file_tools.py             # 文件读写
│   ├── browser_tools.py          # 浏览器操作
│   ├── web_search_tool.py        # 网络搜索
│   ├── computer_use_tool.py      # 桌面操控 (via cua-driver)
│   ├── computer_use/             # computer_use 实现包
│   │   ├── cua_backend.py (1819行)
│   │   └── tool.py (918行)
│   ├── environments/             # 终端后端 (local/docker/ssh)
│   └── winpeek_tools.py 🆕 1 文件 # WinPeek 工具注册
│
├── tui_gateway/                  # TUI 后端 (Python JSON-RPC)
│   └── server.py                 # TUI/Desktop 通信服务 (~13k 行)
│
├── hermes_cli/        141 文件   # CLI 子命令 + 配置向导
│   ├── main.py
│   ├── commands.py               # 命令注册表
│   └── config.py                 # 配置加载
│
├── plugins/                       # 插件系统
│   ├── memory/                   # 记忆后端 (honcho/mem0/supermemory...)
│   ├── kanban/                   # 看板多 Agent
│   ├── model-providers/          # 推理后端
│   ├── image_gen/                # 图片生成
│   └── winpeek_rpa/    🆕 18 文件 # WinPeek 自动化引擎
│
├── skills/                        # 技能知识库
│   ├── computer-use/             # 桌面操控技能
│   ├── software-development/     # 开发技能
│   ├── productivity/             # 效率技能
│   ├── trace-to-template/  🆕    # 操作历史→MCP 模板
│   ├── wechat-automation-rules/🆕# 微信操作守则
│   ├── software-self-learning/🆕 # 全流程自学习
│   └── software-assets/    🆕    # 软件资产卡
│
├── apps/                          # 应用层
│   ├── desktop/                   # Electron 桌面客户端
│   │   ├── src/app/               # React 前端
│   │   │   ├── chat/              # 聊天界面
│   │   │   ├── settings/          # 设置
│   │   │   ├── skills/            # 技能管理
│   │   │   ├── messaging/         # 消息管理
│   │   │   ├── shell/             # App Shell (布局)
│   │   │   └── winpeek/     🆕    # WinPeek 前端
│   │   ├── electron/              # Electron 主进程 (main.cjs 7664行)
│   │   └── src/store/             # nanostores 状态管理
│   └── shared/                    # 共享库 (JSON-RPC 客户端)
│
├── cron/                          # 定时任务调度
├── acp_adapter/                   # IDE 集成 (VS Code/JetBrains)
├── tests/                         # 测试套件 (~900 文件)
├── docs/                          # 文档
├── scripts/                       # 构建/发布脚本
│
└── 配置文件:
    ├── pyproject.toml             # Python 依赖
    ├── package.json               # Node.js monorepo
    ├── config.yaml.example        # 用户配置模板
    └── .env.example               # 密钥模板
```

---

## 二、启动链路

```
双击 Hermes.exe / npm run dev
    │
    ▼
electron/main.cjs (7664行)
    │  spawn Python 子进程
    ▼
hermes serve --host 127.0.0.1 --port 0
    │
    ├── HTTP Server (随机端口)
    │   ├── /              → Dashboard SPA
    │   ├── /api/status    → 健康检查
    │   └── /api/ws        → WebSocket 升级
    │
    ├── AIAgent (run_agent.py)
    │   └── handle_function_call() → tools/registry.py
    │
    ├── Gateway (gateway/run.py)
    │   └── Platform Registry → 20+ IM 适配器
    │
    └── MCP Client → 外部工具 (graphify/codebase-memory)
```

---

## 三、数据流

```
用户输入 "给许国勇发你好"
    │
    ▼
Desktop UI (React) → WebSocket JSON-RPC → tui_gateway
    │
    ▼
AIAgent 对话循环
    │
    ├── 查 skills/ → 匹配 trace-to-template
    ├── 查 tools/  → winpeek_wechat_send 可用?
    │
    ├── 有 winpeek_rpa 插件 → 直接调 wechat_uia.py (毫秒级)
    └── 无插件 → 降级 computer_use (秒级)
    │
    ▼
结果 → WebSocket → UI 实时更新
```

---

## 四、🆕 WinPeek 新增代码（46 文件，8398 行）

```
apps/desktop/src/app/winpeek/     5 文件  前端 View
gateway/winpeek_hub/              5 文件  Hub 后端
plugins/winpeek_rpa/             18 文件  Python 自动化引擎
skills/                           4 文件  AI 知识库
tools/winpeek_tools.py            1 文件  工具注册
apps/desktop/ routes + controller 2 处修改 路由注册
```

---

## 五、关键入口文件（开发常用）

| 文件 | 用途 | 行数 |
|------|------|------|
| `run_agent.py` | AIAgent 类 + 对话循环 | ~12k |
| `cli.py` | CLI 入口 | ~11k |
| `model_tools.py` | 工具注册 + 分发 | ~3k |
| `tools/registry.py` | 工具发现 | ~200 |
| `gateway/run.py` | 消息网关 | ~20k |
| `gateway/platforms/base.py` | 平台基类 | ~5.6k |
| `agent/skill_utils.py` | 技能发现 | 768 |
| `agent/skill_commands.py` | 技能加载 | 744 |
| `tui_gateway/server.py` | TUI/Desktop 后端 | ~13k |
| `apps/desktop/electron/main.cjs` | Electron 主进程 | 7664 |
| `apps/desktop/src/styles.css` | CSS Token 系统 | 1830 |
| 🆕 `apps/desktop/src/app/routes.ts` | 路由注册 (我们改过) | 110 |
| 🆕 `apps/desktop/src/app/desktop-controller.tsx` | 主控制器 (我们改过) | 1378 |
