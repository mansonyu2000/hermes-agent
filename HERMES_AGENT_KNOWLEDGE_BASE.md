# Hermes Agent 项目知识库

> 本文档是团队对Hermes Agent项目的理解总结，用于辅助开发和知识传承。
> **本文档是知识库的主入口，所有文档都从这里索引。**
> 最后更新: 2026-04-18

---

## 📚 文档导航

### 核心文档

| 文档 | 路径 | 说明 |
|------|------|------|
| **开发指南** | [AGENTS.md](AGENTS.md) | AI助手和开发者的开发指南（英文） |
| **项目知识库** | [HERMES_AGENT_KNOWLEDGE_BASE.md](HERMES_AGENT_KNOWLEDGE_BASE.md) | 本文档，知识库主入口 |
| **README** | [README.md](README.md) | 项目介绍和快速开始 |

### 开发规矩和指南

| 文档 | 路径 | 说明 |
|------|------|------|
| **完整开发规矩** | [.rules/development-rules.md](.rules/development-rules.md) | 13章完整开发规范（1800+行） |
| **记忆系统指南** | [.rules/memory-system-guide.md](.rules/memory-system-guide.md) | Hindsight记忆系统完整指南（500+行） |
| **测试模板和案例** | [.rules/test-templates.md](.rules/test-templates.md) | Python+前端测试模板和成功案例（580+行） |
| **文档体系总览** | [.rules/DOCUMENT_NAVIGATION.md](.rules/DOCUMENT_NAVIGATION.md) | 所有文档关系和导航图 |

### Qoder Skills 和 Commands

| 文档 | 路径 | 说明 |
|------|------|------|
| **Skills/Commands 索引** | [.qoder/README.md](.qoder/README.md) | 8个Skills + 6个Commands使用说明 |
| **Skills 目录** | [.qoder/skills/](.qoder/skills/) | 8个项目级Skills |
| **Commands 目录** | [.qoder/commands/](.qoder/commands/) | 6个项目级Commands |

### 快速访问

```bash
# 开发规矩
cat .rules/development-rules.md

# 记忆系统
cat .rules/memory-system-guide.md

# 测试模板
cat .rules/test-templates.md

# Qoder Skills/Commands
cat .qoder/README.md

# 文档体系总览（了解所有文档关系）
cat .rules/DOCUMENT_NAVIGATION.md
```

---

## 一、项目概述

### 1.1 项目定位
**Hermes Agent** 是一个自进化的AI智能体框架，由Nous Research开发。

核心特性：
- 🧠 **自学习能力**：从经验中创建和改进技能
- 🔧 **灵活的工具系统**：支持55+内置工具
- 🌐 **多平台网关**：支持Telegram/Discord/Slack/WhatsApp等
- 🎨 **技能系统**：可从文档自动生成技能
- 💾 **记忆系统**：Hindsight记忆插件实现长期学习

### 1.2 技术栈

#### 后端（核心）
- **语言**: Python 3.11+
- **Web框架**: FastAPI + uvicorn
- **异步**: asyncio（三_loop架构）
- **数据库**: SQLite（WAL模式 + FTS5全文搜索）
- **包管理**: uv（现代Python包管理器）

#### 前端（Web UI）
- **语言**: TypeScript
- **框架**: React 19
- **构建工具**: Vite 7.3.1
- **样式**: Tailwind CSS v4
- **组件策略**: 手写UI组件（零依赖）

#### 基础设施
- **部署**: KVM虚拟机（Ubuntu 22.04）
- **SSH**: 统一私钥认证
- **DNS**: 192.168.3.1 + 8.8.8.8 + 114.114.114.114

---

## 二、核心架构

### 2.1 文件结构

```
hermes-agent/
├── run_agent.py              # 核心Agent循环（11555行）
├── model_tools.py            # 工具编排层（563行）
├── toolsets.py               # 工具集定义（703行）
├── hermes_state.py           # SQLite状态存储（1239行）
├── cli.py                    # CLI主入口（459KB）
├── hermes_cli/
│   ├── main.py               # 所有hermes子命令
│   ├── web_server.py         # Web UI后端（FastAPI）
│   ├── gateway.py            # 网关管理
│   └── web_dist/             # 前端构建产物
├── agent/                    # Agent内部模块
│   ├── prompt_builder.py     # 系统提示构建
│   ├── context_compressor.py # 上下文压缩
│   ├── memory_manager.py     # 记忆管理
│   └── insights.py           # 洞察引擎
├── tools/                    # 55个工具实现
│   ├── registry.py           # 工具注册中心
│   ├── terminal_tool.py      # 终端工具
│   ├── browser_tool.py       # 浏览器自动化
│   └── mcp_tool.py           # MCP客户端
├── gateway/                  # 消息平台网关
│   ├── run.py                # 网关主循环
│   └── platforms/            # 平台适配器
├── plugins/                  # 插件系统
│   └── memory/hindsight/     # Hindsight记忆插件
├── web/                      # 前端TypeScript项目
│   ├── src/                  # React源码
│   └── package.json          # 前端依赖
└── skills/                   # 技能目录
```

### 2.2 核心依赖链

```
tools/registry.py  (无依赖，被所有工具文件导入)
       ↑
tools/*.py  (每个工具调用registry.register())
       ↑
model_tools.py  (导入tools/registry + 触发工具发现)
       ↑
run_agent.py, cli.py, batch_runner.py, environments/
```

### 2.3 独特架构设计

#### 1. AST静态分析自动发现工具
```python
# tools/registry.py
def _module_registers_tools(module_path: Path) -> bool:
    """通过AST分析检测模块是否有registry.register()调用"""
    source = module_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(module_path))
    return any(_is_registry_register_call(stmt) for stmt in tree.body)
```
**优势**: 零配置扩展，新工具文件自动被发现和注册。

#### 2. 三_loop异步桥接架构
```python
# model_tools.py
_tool_loop = None              # 主线程持久loop
_worker_thread_local = threading.local()  # 工作线程独立loop

def _run_async(coro):
    """统一的同步→异步桥接"""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    
    if loop and loop.is_running():
        # 场景1: gateway/RL环境中已有运行中的loop
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(asyncio.run, coro)
            return future.result(timeout=300)
    
    if threading.current_thread() is not threading.main_thread():
        # 场景2: 工作线程(子agent并行工具执行)
        worker_loop = _get_worker_loop()
        return worker_loop.run_until_complete(coro)
    
    # 场景3: 主线程(CLI模式)
    tool_loop = _get_tool_loop()
    return tool_loop.run_until_complete(coro)
```
**解决问题**: CLI/Gateway/子agent三种场景的异步兼容性。

#### 3. SQLite WAL + 随机退避
```python
# hermes_state.py
class SessionDB:
    _WRITE_MAX_RETRIES = 15
    _WRITE_RETRY_MIN_S = 0.020   # 20ms
    _WRITE_RETRY_MAX_S = 0.150   # 150ms
    
    def _execute_write(self, fn):
        """带随机退避的写事务"""
        for attempt in range(self._WRITE_MAX_RETRIES):
            try:
                with self._lock:
                    self._conn.execute("BEGIN IMMEDIATE")
                    result = fn(self._conn)
                    self._conn.commit()
                return result
            except sqlite3.OperationalError as exc:
                if "locked" in str(exc).lower():
                    jitter = random.uniform(0.020, 0.150)  # 随机退避
                    time.sleep(jitter)
                    continue
```
**优势**: 打破SQLite内置确定性退避的车队效应，支持高并发写入。

#### 4. 递归toolset组合系统
```python
# toolsets.py
def resolve_toolset(name: str, visited: Set[str] = None) -> List[str]:
    """递归解析toolset，支持组合和循环检测"""
    if name in visited:
        return []  # 循环依赖保护
    visited.add(name)
    
    toolset = get_toolset(name)
    tools = set(toolset.get("tools", []))
    for included_name in toolset.get("includes", []):
        included_tools = resolve_toolset(included_name, visited)
        tools.update(included_tools)
    return sorted(tools)
```
**特性**: 支持toolset继承、别名、菱形依赖优化、循环依赖检测。

---

## 三、关键系统

### 3.1 工具系统

#### 工具注册流程
1. 工具文件定义在 `tools/*.py`
2. 每个工具调用 `registry.register()` 注册
3. `discover_builtin_tools()` 通过AST静态分析自动发现
4. `model_tools.py` 加载并编排工具

#### 添加工具的步骤（仅需2个文件）
1. 创建 `tools/your_tool.py`
2. 添加到 `toolsets.py` 的 `_HERMES_CORE_TOOLS` 或新toolset

### 3.2 技能系统

#### 技能生成机制
- **不是运行时自我学习**，而是**构建时文档爬取自动化**
- 从官方文档自动爬取生成 `SKILL.md`
- 脚本：`scripts/build_skills_index.py`

#### Hindsight记忆插件（真正的学习机制）
```
retain(存储) → recall(检索) → reflect(推理综合)
```
三阶段学习循环，实现长期记忆和知识积累。

### 3.3 记忆系统

#### SessionDB（SQLite）
- WAL模式支持多读单写并发
- FTS5全文搜索（自动触发器同步）
- 随机退避策略（打破车队效应）
- 路径安全：使用 `get_hermes_home()` 支持Profile隔离

### 3.4 前端构建流程

```
web/ (TypeScript项目)
  ↓ npm run build
  ↓ tsc -b && vite build
hermes_cli/web_dist/ (静态SPA)
  ↓ pyproject.toml打包
Python wheel (包含前端)
  ↓ FastAPI服务
http://host:9119
```

---

## 四、开发环境

### 4.1 服务器信息

| 项目 | 配置 |
|------|------|
| **虚拟机** | ubtcow4t (192.168.3.18) |
| **宿主机** | htubs242 (192.168.3.3) |
| **系统** | Ubuntu 22.04.5 LTS |
| **CPU** | 4核 |
| **内存** | 8GB |
| **磁盘** | 98GB (已用19GB) |

### 4.2 环境配置

```bash
# Python
Python 3.11.15 @ /usr/bin/python3.11
虚拟环境: /root/hermes-agent/.venv

# Node.js
v20.20.2

# uv
0.11.7

# Git
2.34.1
远程仓库: git@gitlab.test.com:mansonyu/hermes-agent.git (端口8022)

# 项目路径
/root/hermes-agent/

# 配置路径
~/.hermes/config.yaml    # 用户配置
~/.hermes/.env           # API密钥
```

### 4.3 SSH配置

```bash
# 本地 ~/.ssh/config
Host ubtcow4t
    HostName 192.168.3.18
    User root
    Port 22
    IdentityFile ~/.ssh/hkjys_id_rsa_2025-08-13-19-55-00

Host gitlab.test.com
    HostName 192.168.3.23
    Port 8022
    User git
    IdentityFile ~/.ssh/hkjys_id_rsa_2025-08-13-19-55-00
```

### 4.4 DNS配置

```bash
# 多DNS服务器配置
resolvectl dns enp1s0 192.168.3.1 8.8.8.8 114.114.114.114
```

---

## 五、运行模式

### 5.1 Web UI Dashboard

```bash
cd /root/hermes-agent
source .venv/bin/activate
hermes dashboard --host 0.0.0.0 --port 9119 --no-open --insecure
```

访问: http://192.168.3.18:9119

功能:
- 配置管理（config.yaml可视化编辑）
- API密钥管理（.env文件管理）
- 会话监控
- 模型配置
- 工具/技能管理

### 5.2 CLI交互模式

```bash
cd /root/hermes-agent
source .venv/bin/activate
hermes chat
```

### 5.3 消息网关

```bash
# 直接启动（避免systemd --user问题）
cd /root/hermes-agent
source .venv/bin/activate
nohup python -m gateway.run > /tmp/hermes-gateway.log 2>&1 &

# 查看日志
tail -f /tmp/hermes-gateway.log
```

### 5.4 常见命令

```bash
hermes chat                    # 交互对话
hermes model                   # 模型管理
hermes gateway start           # 启动网关
hermes setup                   # 初始设置
hermes status                  # 查看状态
hermes skills                  # 技能管理
hermes tools                   # 工具管理
hermes dashboard               # Web UI
hermes doctor                  # 诊断检查
```

---

## 六、已知问题与解决方案

### 6.1 systemd --user权限问题

**问题**: `Failed to connect to bus: Operation not permitted`

**原因**: root用户使用systemctl --user需要特殊配置

**解决**: 直接用Python启动
```bash
python -m gateway.run
```

### 6.2 DNS解析问题

**问题**: 192.168.3.1无法解析外网域名

**解决**: 添加公共DNS
```bash
resolvectl dns enp1s0 192.168.3.1 8.8.8.8 114.114.114.114
```

### 6.3 GitLab SSH端口

**注意**: GitLab使用8022端口（不是标准22）

```bash
# ~/.ssh/config配置
Host gitlab.test.com
    Port 8022
```

### 6.4 PyPI连接超时

**问题**: 默认PyPI源连接超时

**解决**: 使用国内镜像
```bash
uv pip install --index-url https://mirrors.aliyun.com/pypi/simple <package>
```

---

## 七、重要设计原则

### 7.1 Prompt缓存保护
- **规则**: 对话中途不修改上下文
- **原因**: 避免缓存失效导致成本剧增
- **例外**: 仅在上下文压缩时允许

### 7.2 Profile隔离
- 使用 `get_hermes_home()` 获取路径
- 禁止硬编码 `~/.hermes`
- 支持多实例完全隔离

### 7.3 防御性编程
```python
class _SafeWriter:
    """透明包装stdio，捕获broken pipe错误"""
    def write(self, data):
        try:
            return self._inner.write(data)
        except (OSError, ValueError):
            return len(data) if isinstance(data, str) else 0
```

### 7.4 工作目录行为
- **CLI**: 使用当前目录（`.` → `os.getcwd()`）
- **Gateway**: 使用 `MESSAGING_CWD` 环境变量

---

## 八、测试

```bash
cd /root/hermes-agent
source .venv/bin/activate

# 完整测试套件
python -m pytest tests/ -q

# 特定测试
python -m pytest tests/test_model_tools.py -q    # 工具集解析
python -m pytest tests/test_cli_init.py -q       # CLI配置加载
python -m pytest tests/gateway/ -q               # 网关测试
python -m pytest tests/tools/ -q                 # 工具测试
```

---

## 九、开发工作流

### 9.1 本地开发（推荐）

1. **Qoder Remote SSH连接**
   - 主机: 192.168.3.18
   - 用户: root
   - 私钥: `~/.ssh/hkjys_id_rsa_2025-08-13-19-55-00`

2. **打开项目**
   ```
   /root/hermes-agent/
   ```

3. **选择Python解释器**
   ```
   /root/hermes-agent/.venv/bin/python
   ```

### 9.2 添加新功能

#### 添加工具
1. 创建 `tools/my_tool.py`
2. 调用 `registry.register()`
3. 添加到 `toolsets.py`

#### 添加Slash命令
1. 在 `hermes_cli/commands.py` 添加 `CommandDef`
2. 在 `cli.py` 的 `process_command()` 添加handler
3. 如果是gateway命令，在 `gateway/run.py` 添加handler

#### 添加配置
1. 添加到 `hermes_cli/config.py` 的 `DEFAULT_CONFIG`
2. 如果是.env变量，添加到 `OPTIONAL_ENV_VARS`

---

## 十、关键文件索引

| 文件 | 作用 | 行数 |
|------|------|------|
| `run_agent.py` | 核心Agent循环 | 11555 |
| `cli.py` | CLI主入口 | ~12000 |
| `model_tools.py` | 工具编排 | 563 |
| `toolsets.py` | 工具集定义 | 703 |
| `hermes_state.py` | SQLite状态存储 | 1239 |
| `tools/registry.py` | 工具注册中心 | 483 |
| `hermes_cli/web_server.py` | Web UI后端 | 2351 |
| `hermes_cli/gateway.py` | 网关管理 | 2947 |
| `plugins/memory/hindsight/__init__.py` | 记忆插件 | 884+ |

---

## 十一、Qoder CLI 集成与 Skills/Commands

### 11.1 项目级 Skills 和 Commands

项目已在 `.qoder/` 目录配置了完整的 Skills 和 Commands 体系，用于提升 AI 助手和开发者的工作效率。

#### Skills（自动触发）

| 技能名称 | 触发关键词 | 用途 |
|---------|-----------|------|
| **hermes-test-runner** | run tests, pytest, test suite | 运行和验证测试套件 |
| **hermes-git-commit** | git commit, commit changes | 生成规范的 Git 提交信息 |
| **hermes-tool-creator** | create tool, add tool, new tool | 创建新工具（2文件模式） |
| **hermes-slash-command** | slash command, add command | 添加斜杠命令 |
| **hermes-debug-helper** | debug, investigate error, troubleshoot | 调试 Hermes 问题 |
| **hermes-config-manager** | config, configuration, .env, api key | 管理配置文件 |

**使用方式：**
```bash
# 自动触发 - 直接描述需求
"运行测试验证刚才的修改"           → 自动使用 hermes-test-runner
"准备提交代码"                     → 自动使用 hermes-git-commit
"创建一个新的 web scraper 工具"    → 自动使用 hermes-tool-creator
"调试这个 Profile 隔离问题"        → 自动使用 hermes-debug-helper

# 手动触发
/hermes-test-runner
/hermes-git-commit
```

#### Commands（手动触发）

| 命令名称 | 用途 |
|---------|------|
| **hermes-full-test** | 运行完整测试套件并报告 |
| **hermes-quick-review** | 快速代码审查（关键规则检查） |
| **hermes-prepare-release** | 准备发布（测试+文档+版本） |
| **hermes-env-setup** | 验证开发环境配置 |

**使用方式：**
```bash
# TUI 模式
/hermes-full-test
/hermes-quick-review

# Headless 模式
qodercli -p '/hermes-full-test'
qodercli -p '/hermes-quick-review 重点检查 Profile 隔离'
```

#### Skills vs Commands 区别

| 特性 | Skill | Command |
|------|-------|---------|
| 触发方式 | 模型自动判断 或 `/skill-name` | 必须输入 `/command-name` |
| 主要用途 | 专业领域知识、复杂工作流 | 快速执行预设任务 |
| 存储位置 | `.qoder/skills/` 目录 | `.qoder/commands/` 目录 |
| 权限确认 | 需要确认 | 不需要 |

#### 目录结构

```
.qoder/
├── README.md                          # 索引文档
├── skills/                            # Skills（自动触发）
│   ├── hermes-test-runner/SKILL.md
│   ├── hermes-git-commit/SKILL.md
│   ├── hermes-tool-creator/SKILL.md
│   ├── hermes-slash-command/SKILL.md
│   ├── hermes-debug-helper/SKILL.md
│   └── hermes-config-manager/SKILL.md
└── commands/                          # Commands（手动触发）
    ├── hermes-full-test.md
    ├── hermes-quick-review.md
    ├── hermes-prepare-release.md
    └── hermes-env-setup.md
```

### 11.2 开发规矩文档

完整的开发规矩文档位于：`.rules/development-rules.md`（1632 行）

包含内容：
- 12 个核心章节（架构规则、代码规范、工具开发、技能系统等）
- 6 个 Skills 完整实现
- 4 个 Commands 完整实现
- 大量代码示例和最佳实践
- 安全检查清单和快速参考

---

## 十二、记忆系统详解

### 12.1 Hermes 记忆系统架构

Hermes Agent 的记忆系统是其核心优势之一，实现了**自动整理、持久化、跨会话记忆**。

#### 多层记忆架构

```
┌─────────────────────────────────────────┐
│         会话级记忆 (SQLite)              │
│  - 会话历史（FTS5全文搜索）              │
│  - 当前上下文                            │
│  - 临时状态                              │
└─────────────────────────────────────────┘
              ↓ 持久化
┌─────────────────────────────────────────┐
│       用户级记忆 (MEMORY.md)             │
│  - 用户偏好                              │
│  - 项目决策                              │
│  - 重要知识点                            │
└─────────────────────────────────────────┘
              ↓ 跨会话
┌─────────────────────────────────────────┐
│     插件级记忆 (Hindsight等)             │
│  - 知识图谱                              │
│  - 语义搜索                              │
│  - 自动归纳                              │
└─────────────────────────────────────────┘
```

### 12.2 SQLite 会话记忆

**核心实现：** `hermes_state.py` 的 `SessionDB` 类

**特性：**
- **WAL 模式**：支持多读单写并发
- **FTS5 全文搜索**：自动触发器同步，支持语义搜索
- **随机退避策略**：打破 SQLite 内置确定性退避的车队效应
- **路径安全**：使用 `get_hermes_home()` 支持 Profile 隔离

**数据表结构：**
```sql
sessions          -- 会话元数据
messages          -- 消息内容
sessions_fts      -- FTS5 全文搜索索引
```

**使用方式：**
```python
from hermes_state import SessionDB

db = SessionDB()
db.save_message(session_id, "user", "Hello")
results = db.search_messages("search query")
```

### 12.3 Hindsight 记忆插件（真正的学习机制）

**核心实现：** `plugins/memory/hindsight/__init__.py`

Hindsight 是 Hermes Agent 的**核心记忆插件**，实现了真正的跨会话学习和知识积累。

#### 三阶段学习循环

```
retain(存储) → recall(检索) → reflect(推理综合)
```

**1. Retain（存储）**
```python
# 工具：hindsight_retain
# 功能：自动提取结构化事实、解析实体、索引存储
# 触发：自动（每 N 轮对话）或手动

hindsight_retain(
    content="用户偏好使用深色主题",
    context="user preference"
)
```

**2. Recall（检索）**
```python
# 工具：hindsight_recall
# 功能：多策略搜索（语义+实体图谱+关键词+重排序）
# 触发：自动（每次对话前）或手动

hindsight_recall(
    query="用户喜欢什么主题？"
)
# 返回：按相关性排序的记忆列表
```

**3. Reflect（推理综合）**
```python
# 工具：hindsight_reflect
# 功能：跨记忆推理综合，生成连贯回答
# 触发：手动（需要深度推理时）

hindsight_reflect(
    query="根据历史对话，总结用户的开发偏好"
)
# 返回：综合推理后的回答
```

#### 记忆模式（memory_mode）

| 模式 | 说明 | 工具暴露 | 自动注入 |
|------|------|---------|---------|
| **hybrid** | 自动注入 + 工具可用 | ✅ | ✅ |
| **context** | 仅自动注入 | ❌ | ✅ |
| **tools** | 仅工具可用 | ✅ | ❌ |

#### 自动 Prefetch 机制

Hindsight 在后台线程中自动预取相关记忆：

```python
# 对话开始时自动触发
hindsight.queue_prefetch(user_message)

# 后台执行
- 语义搜索
- 实体图谱遍历
- 结果缓存到 _prefetch_result

# 注入到系统提示
# Hindsight Memory (persistent cross-session context)
# Use this to answer questions about the user and prior sessions.
```

#### 配置选项

**配置文件：** `~/.hermes/hindsight/config.json`

```json
{
  "mode": "cloud",
  "apiKey": "your-api-key",
  "api_url": "https://api.hindsight.ai",
  "bank_id": "hermes",
  "budget": "mid",
  "memory_mode": "hybrid",
  "auto_retain": true,
  "auto_recall": true,
  "retain_every_n_turns": 1,
  "retain_async": true,
  "recall_max_tokens": 4096,
  "recall_max_input_chars": 800
}
```

**环境变量：**
```bash
HINDSIGHT_API_KEY=xxx
HINDSIGHT_LLM_API_KEY=xxx  # 用于本地 LLM
```

#### 本地 LLM 支持

Hindsight 支持使用本地 LLM 进行记忆处理：

```json
{
  "llm_provider": "ollama",  # openai/anthropic/gemini/ollama/lmstudio
  "llm_model": "qwen/qwen3.5-9b",
  "llm_base_url": "http://192.168.1.10:8080/v1"
}
```

#### 系统提示集成

```python
# hybrid 模式的系统提示
# Hindsight Memory
# Active. Bank: hermes, budget: mid.
# Relevant memories are automatically injected into context.
# Use hindsight_recall to search, hindsight_reflect for synthesis,
# hindsight_retain to store facts.
```

### 12.4 其他记忆插件

Hermes 支持多种记忆插件（`plugins/memory/` 目录）：

| 插件 | 特点 |
|------|------|
| **hindsight** | 知识图谱 + 语义搜索 + 三阶段学习 |
| **byterover** | 轻量级向量记忆 |
| **holographic** | 全息记忆编码 |
| **honcho** | 用户画像记忆 |
| **mem0** | 开源记忆层 |
| **openviking** | Viking 记忆协议 |
| **retaindb** | 持久化关系数据库 |
| **supermemory** | 超级记忆网络 |

### 12.5 记忆持久化策略

#### 会话级持久化

```python
# 每次对话自动保存
db.save_message(session_id, role, content)

# 会话结束时同步到长期记忆
hindsight.sync_turn(session_id)
```

#### 用户级持久化

```
~/.hermes/
├── MEMORY.md              # 用户级记忆（所有会话共享）
├── USER.md                # 用户偏好和配置
└── profiles/<name>/
    ├── MEMORY.md          # Profile 级记忆
    └── sessions.db        # Profile 级会话数据库
```

#### 跨会话记忆流程

```
会话 1: 用户说"我喜欢深色主题"
  ↓ hindsight_retain 自动存储
  ↓ 提取实体：用户、深色主题
  ↓ 存入知识图谱

会话 2（新会话）: 用户问"我上次说了什么？"
  ↓ hindsight_recall 自动检索
  ↓ 语义搜索：用户 + 偏好
  ↓ 返回："用户偏好使用深色主题"
  ↓ 自动注入到上下文

会话 3: 用户问"推荐一个主题"
  ↓ hindsight_reflect 推理综合
  ↓ 结合历史记忆：深色主题
  ↓ 生成回答："根据您之前的偏好，推荐深色主题"
```

### 12.6 记忆系统的独特优势

1. **自动整理**：无需手动管理，AI 自动提取和归纳
2. **持久化存储**：SQLite + 文件双重保障
3. **跨会话记忆**：新会话自动加载历史记忆
4. **多策略检索**：语义搜索 + 实体图谱 + 关键词匹配
5. **推理综合**：不仅检索，还能推理和总结
6. **Profile 隔离**：每个 Profile 独立记忆系统
7. **可插拔架构**：支持多种记忆插件

---

## 十三、下一步计划

- [ ] 配置 OPENROUTER_API_KEY
- [ ] 测试 AI 对话功能
- [ ] 配置消息平台（可选）
- [ ] 探索技能系统
- [ ] 测试工具调用
- [ ] 深入了解记忆系统
- [ ] 配置 Hindsight 记忆插件
- [ ] 测试跨会话记忆功能

---

## 十四、参考资料

- 官方文档: `AGENTS.md` (开发指南)
- README: `README.md`
- 配置示例: `cli-config.yaml.example`, `.env.example`
- 测试: `tests/` 目录 (~3000个测试)
- 开发规矩: `.rules/development-rules.md`
- Skills/Commands: `.qoder/README.md`
- Hindsight 文档: `plugins/memory/hindsight/README.md`

---

**文档维护**: 本文档应随项目理解深入持续更新。
**最后更新**: 2026-04-18
**维护者**: 开发团队
