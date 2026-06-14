# Hermes Agent - 完整开发规矩

> 本文档定义了 Hermes Agent 项目开发过程中必须遵守的规矩和最佳实践。
> 适用于所有开发人员和 AI 助手（Qoder CLI）。
> **本文档已索引到项目知识库。**
> 最后更新: 2026-04-18

---

## 📚 文档导航

### 相关文档

| 文档 | 路径 | 说明 |
|------|------|------|
| **项目知识库** | [../HERMES_AGENT_KNOWLEDGE_BASE.md](../HERMES_AGENT_KNOWLEDGE_BASE.md) | 知识库主入口 |
| **开发指南** | [../AGENTS.md](../AGENTS.md) | AI助手开发指南 |
| **记忆系统指南** | [./memory-system-guide.md](./memory-system-guide.md) | Hindsight完整指南 |
| **测试模板** | [./test-templates.md](./test-templates.md) | 测试模板和案例 |
| **Skills/Commands** | [../.qoder/README.md](../.qoder/README.md) | Skills和Commands索引 |

---

## 📑 目录

- [一、核心架构规则](#一核心架构规则)
- [二、代码规范](#二代码规范)
- [三、工具开发规则](#三工具开发规则)
- [四、技能系统规则](#四技能系统规则)
- [五、测试规则](#五测试规则)
- [六、Git 工作流规则](#六git-工作流规则)
- [七、Qoder CLI 集成规则](#七qoder-cli-集成规则)
- [八、Skills 开发指南](#八skills-开发指南)
- [九、Commands 开发指南](#九commands-开发指南)
- [十、配置管理规则](#十配置管理规则)
- [十一、文档维护规则](#十一文档维护规则)
- [十二、安全检查清单](#十二安全检查清单)
- [十三、记忆系统规则](#十三记忆系统规则)

---

## 一、核心架构规则

### 1.1 Profile 隔离规则

**必须遵守：**
```python
# ✅ 正确做法
from hermes_constants import get_hermes_home, display_hermes_home

config_path = get_hermes_home() / "config.yaml"
print(f"配置已保存到 {display_hermes_home()}/config.yaml")
```

**严格禁止：**
```python
# ❌ 错误做法 - 会破坏 Profile 隔离
config_path = Path.home() / ".hermes" / "config.yaml"
print("配置已保存到 ~/.hermes/config.yaml")
```

**测试中的 Profile 隔离：**
```python
@pytest.fixture
def profile_env(tmp_path, monkeypatch):
    """Profile 测试 fixture - 必须同时 mock 两项"""
    home = tmp_path / ".hermes"
    home.mkdir()
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setenv("HERMES_HOME", str(home))
    return home
```

### 1.2 Prompt 缓存保护规则

**允许修改上下文的唯一场景：**
- 对话开始前构建系统提示
- 上下文压缩触发时
- 会话初始化阶段

**严格禁止：**
- 对话中途修改已发送的上下文消息
- 动态变更工具集（enabled_toolsets / disabled_toolsets）
- 重新加载记忆或重建系统提示
- 修改 conversation_history 中的历史消息

**原因：** 缓存失效会导致 API 成本增加 3-10 倍。

### 1.3 异步桥接规则

**正确使用 `_run_async()`：**
```python
# ✅ 工具中调用异步代码
from model_tools import _run_async

async def my_async_operation():
    return await some_api_call()

def my_tool():
    result = _run_async(my_async_operation())
    return json.dumps({"result": result})
```

**三种异步场景理解：**
1. **CLI 主线程** → 使用 `_get_tool_loop()` 的持久 loop
2. **工作线程（子 agent 并行）** → 使用 `_get_worker_loop()` 的线程独立 loop
3. **Gateway/RL 环境** → 已有运行中的 loop，通过 ThreadPoolExecutor 桥接

**严格禁止：**
- 在工具中直接调用 `asyncio.run()`
- 忽略线程上下文直接创建新 loop
- 在主线程外使用 `asyncio.get_event_loop()`

### 1.4 SQLite 并发规则

**写操作必须使用随机退避：**
```python
# ✅ 正确模式
class MyDB:
    _WRITE_MAX_RETRIES = 15
    _WRITE_RETRY_MIN_S = 0.020
    _WRITE_RETRY_MAX_S = 0.150
    
    def _execute_write(self, fn):
        for attempt in range(self._WRITE_MAX_RETRIES):
            try:
                with self._lock:
                    self._conn.execute("BEGIN IMMEDIATE")
                    result = fn(self._conn)
                    self._conn.commit()
                return result
            except sqlite3.OperationalError as exc:
                if "locked" in str(exc).lower():
                    jitter = random.uniform(0.020, 0.150)
                    time.sleep(jitter)
                    continue
                raise
```

**原因：** 打破 SQLite 内置确定性退避的车队效应。

---

## 二、代码规范

### 2.1 终端输出规范

**禁止使用 ANSI erase-to-EOL：**
```python
# ❌ 错误 - 在 prompt_toolkit 下会泄漏为 ?[K
print(f"\r{line}\033[K")

# ✅ 正确 - 使用空格填充
print(f"\r{line}{' ' * padding}")
```

**交互式菜单使用 curses：**
```python
# ✅ 使用标准库 curses
import curses

def show_menu(options):
    # 使用 ncurses 实现
    pass

# ❌ 禁止使用 simple_term_menu
from simple_term_menu import TerminalMenu  # 在 tmux/iTerm2 中有渲染 bug
```

### 2.2 防御性编程

**标准输出安全包装：**
```python
class _SafeWriter:
    """透明包装 stdio，捕获 broken pipe 错误"""
    def write(self, data):
        try:
            return self._inner.write(data)
        except (OSError, ValueError):
            return len(data) if isinstance(data, str) else 0
```

**工具依赖检查：**
```python
def check_requirements() -> bool:
    """工具可用性检查"""
    return bool(os.getenv("REQUIRED_API_KEY"))

registry.register(
    name="my_tool",
    check_fn=check_requirements,
    requires_env=["REQUIRED_API_KEY"],
    # ...
)
```

### 2.3 命名规范

**Python 代码：**
- 函数/变量：`snake_case`
- 类名：`PascalCase`
- 常量：`UPPER_SNAKE_CASE`
- 私有方法：`_leading_underscore`

**工具名称：**
- 使用 `snake_case`（如 `web_search`, `file_read`）
- 避免缩写（如使用 `browser_navigate` 而非 `browser_nav`）

**Slash 命令：**
- 使用小写（如 `/model`, `/skills`）
- 别名使用缩写（如 `("bg",)` 代表 `background`）

---

## 三、工具开发规则

### 3.1 工具注册流程

**仅需修改 2 个文件：**

**文件 1：`tools/your_tool.py`**
```python
import json
import os
from tools.registry import registry

def check_requirements() -> bool:
    """检查工具依赖"""
    return bool(os.getenv("EXAMPLE_API_KEY"))

def example_tool(param: str, task_id: str = None) -> str:
    """工具实现 - 必须返回 JSON 字符串"""
    result = {"success": True, "data": f"Processed: {param}"}
    return json.dumps(result)

# 注册工具
registry.register(
    name="example_tool",
    toolset="example",
    schema={
        "name": "example_tool",
        "description": "处理某个参数的示例工具",
        "parameters": {
            "type": "object",
            "properties": {
                "param": {
                    "type": "string",
                    "description": "输入参数"
                }
            },
            "required": ["param"]
        }
    },
    handler=lambda args, **kw: example_tool(
        param=args.get("param", ""),
        task_id=kw.get("task_id")
    ),
    check_fn=check_requirements,
    requires_env=["EXAMPLE_API_KEY"],
)
```

**文件 2：`toolsets.py`**
```python
# 添加到 _HERMES_CORE_TOOLS 或创建新 toolset
_HERMES_CORE_TOOLS = [
    # ... 现有工具
    "example_tool",
]
```

### 3.2 工具 Handler 规范

**必须返回 JSON 字符串：**
```python
# ✅ 正确
def my_tool() -> str:
    return json.dumps({"success": True, "result": "data"})

# ❌ 错误 - 返回 dict 会导致序列化错误
def my_tool() -> dict:
    return {"success": True, "result": "data"}
```

**路径引用规范：**
```python
from hermes_constants import get_hermes_home, display_hermes_home

# ✅ 存储状态文件
cache_dir = get_hermes_home() / "cache"

# ✅ Schema 描述中提示用户
schema = {
    "description": f"输出文件保存到 {display_hermes_home()}/outputs/"
}
```

### 3.3 跨工具引用规则

**禁止在 schema 描述中硬编码其他工具名：**
```python
# ❌ 错误 - browser_navigate 可能不可用
schema = {
    "description": "优先使用 browser_navigate 打开网页"
}

# ✅ 正确 - 在 model_tools.py 中动态添加
# 在 get_tool_definitions() 中后处理
if "browser_navigate" in available_tools:
    schema["description"] += " (也可使用 browser_navigate)"
```

**原因：** 工具可能因缺少 API Key 或被禁用而不可用，硬编码引用会导致模型幻觉调用。

### 3.4 工具自动发现机制

**AST 静态分析原理：**
```python
# tools/registry.py 自动检测
def _module_registers_tools(module_path: Path) -> bool:
    """通过 AST 分析检测模块是否有 registry.register() 调用"""
    source = module_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(module_path))
    return any(_is_registry_register_call(stmt) for stmt in tree.body)
```

**优势：** 零配置扩展，新工具文件自动被发现和注册，无需手动维护导入列表。

---

## 四、技能系统规则

### 4.1 技能生成机制

**重要理解：**
- **不是运行时自我学习**，而是**构建时文档爬取自动化**
- 从官方文档自动爬取生成 `SKILL.md`
- 脚本：`scripts/build_skills_index.py`

**真正的学习机制是 Hindsight 记忆插件：**
```
retain(存储) → recall(检索) → reflect(推理综合)
```

### 4.2 技能目录结构

**标准技能结构：**
```
skills/your-skill/
├── SKILL.md              # 必需：技能主文件
├── REFERENCE.md          # 可选：详细参考文档
├── EXAMPLES.md           # 可选：使用示例
├── scripts/              # 可选：辅助脚本
│   └── helper.py
└── templates/            # 可选：模板文件
    └── template.txt
```

### 4.3 SKILL.md 格式规范

**Frontmatter 字段：**
```yaml
---
name: skill-name
description: 清晰具体的描述，包含使用时机和触发关键词（最多 1024 字符）
---
```

**命名规范：**
- 仅使用小写字母、数字、连字符
- 最多 64 字符
- 建议文件名与 name 字段一致

**Description 编写规范：**
```yaml
# ✅ 推荐：具体明确
description: >
  Analyze log files to identify errors, patterns, and performance issues.
  Use when debugging logs, investigating errors, or monitoring application behavior.
  Trigger keywords: log analysis, debug error, investigate crash.

# ❌ 不推荐：模糊宽泛
description: Helps with logs
```

### 4.4 技能存储位置

| 类型 | 路径 | 作用域 | 适用场景 |
|------|------|--------|----------|
| 用户级 | `~/.qoder/skills/{skill-name}/SKILL.md` | 当前用户的所有项目 | 个人工作流、实验性技能 |
| 项目级 | `.qoder/skills/{skill-name}/SKILL.md` | 仅当前项目 | 团队工作流、项目特定知识 |
| Hermes 内置 | `skills/` 目录 | 所有 Hermes 实例 | 核心技能、官方技能 |

**优先级：** 项目级 > 用户级 > Hermes 内置

### 4.5 技能最佳实践

**保持专注：**
```
✅ 推荐：
- log-analyzer - 日志分析
- security-auditor - 安全审计
- database-migrator - 数据库迁移

❌ 不推荐：
- coding-helper - 功能过于宽泛
- general-tools - 职责不清
```

**共享前测试：**
- 验证预期场景能正确触发
- 确保指令清晰无歧义
- 覆盖常见边界情况
- 测试失败场景的降级处理

**记录版本变更：**
```markdown
## 版本历史

- v2.0.0 (2026-04-18): API 重大变更，新增异步支持
- v1.1.0 (2026-03-15): 新增错误处理流程
- v1.0.0 (2026-01-01): 首次发布
```

---

## 五、测试规则

### 5.1 测试编写规范

**必须使用隔离 fixture：**
```python
import pytest
from pathlib import Path

@pytest.fixture
def isolate_hermes_home(tmp_path, monkeypatch):
    """测试隔离 fixture - 重定向 HERMES_HOME"""
    home = tmp_path / ".hermes"
    home.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(home))
    return home

def test_my_feature(isolate_hermes_home):
    # 测试代码不会污染真实的 ~/.hermes
    pass
```

**Profile 测试必须 mock 两项：**
```python
@pytest.fixture
def profile_env(tmp_path, monkeypatch):
    """Profile 测试 - 必须同时 mock Path.home() 和设置 HERMES_HOME"""
    home = tmp_path / ".hermes"
    home.mkdir()
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setenv("HERMES_HOME", str(home))
    return home
```

### 5.2 测试运行规范

**完整测试套件：**
```bash
cd /root/hermes-agent
source .venv/bin/activate

# 运行所有测试（~3000 个，约 3 分钟）
python -m pytest tests/ -q

# 特定模块测试
python -m pytest tests/test_model_tools.py -q    # 工具集解析
python -m pytest tests/test_cli_init.py -q       # CLI 配置加载
python -m pytest tests/gateway/ -q               # 网关测试
python -m pytest tests/tools/ -q                 # 工具测试
```

**提交前必须：**
- [ ] 运行完整测试套件
- [ ] 验证新增测试通过
- [ ] 确认未破坏现有测试
- [ ] 检查测试覆盖率（如适用）

### 5.3 测试禁止事项

**严格禁止：**
- 测试中硬编码 `~/.hermes/` 路径
- 测试写入真实配置文件
- 跳过测试直接提交代码
- 使用 `sleep()` 代替异步等待
- Mock 过于宽泛导致测试无意义

---

## 六、Git 工作流规则

### 6.1 分支管理

**分支命名规范：**
```
feature/add-new-tool          # 新功能
fix/resolve-profile-bug       # Bug 修复
docs/update-skills-guide      # 文档更新
refactor/simplify-async-code  # 重构
test/add-gateway-tests        # 测试补充
```

**主要分支：**
- `main` - 稳定版本
- `develop` - 开发分支
- `release/*` - 发布候选

### 6.2 提交规范

**遵循 Conventional Commits：**
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Type 类型：**
- `feat` - 新功能
- `fix` - Bug 修复
- `docs` - 文档更新
- `style` - 代码格式（不影响功能）
- `refactor` - 重构
- `test` - 测试相关
- `chore` - 构建/工具链变更

**示例：**
```bash
feat(tools): add web_scraper tool for parallel scraping

- Implement async web scraping with rate limiting
- Add schema validation for scraped content
- Register tool in web toolset

Closes #123
```

### 6.3 提交前检查清单

**必须完成：**
- [ ] 运行 `python -m pytest tests/ -q`
- [ ] 验证 Profile 隔离未破坏
- [ ] 确认 Prompt 缓存保护逻辑完整
- [ ] 代码通过 lint 检查（如配置）
- [ ] 更新相关文档（如适用）
- [ ] 提交信息遵循 Conventional Commits

---

## 七、Qoder CLI 集成规则

### 7.1 项目初始化

**使用 `/init` 命令：**
```bash
qodercli -p '/init'
```

**生成 AGENTS.md 的作用：**
- 记录项目架构和依赖链
- 定义开发规范和最佳实践
- 为 AI 助手提供上下文指导

### 7.2 代码审查

**使用 `/review` 命令：**
```bash
# TUI 模式
/review

# Headless 模式
qodercli -p '/review 重点检查 Profile 隔离和 Prompt 缓存保护'
qodercli -p '/review 重点检查注释覆盖情况'
```

**审查重点：**
- Profile 隔离合规性
- Prompt 缓存保护
- 工具注册规范性
- 异步桥接正确性
- 测试覆盖率

### 7.3 会话管理

**常用命令：**
```bash
/clear          # 清除当前对话，开始新对话
/resume         # 恢复之前的会话
/compact        # 压缩对话历史
/export         # 导出会话到文件
/status         # 查看会话状态
```

### 7.4 模型管理

**切换模型：**
```bash
/model          # 查看和管理模型
```

**模型选择建议：**
- 复杂架构决策 → 使用高性能模型
- 简单代码修改 → 使用快速模型
- 代码审查 → 使用高精度模型

---

## 八、Skills 开发指南

### 8.1 Hermes Agent 常用 Skills 清单

以下为 Hermes Agent 项目推荐的 Skills，可直接用于 Qoder CLI 工作流：

#### 1. **hermes-test-runner** - 测试运行与验证

```yaml
---
name: hermes-test-runner
description: >
  Run and validate Hermes Agent test suites. Use when running tests,
  verifying code changes, checking test coverage, or debugging test failures.
  Trigger keywords: run tests, pytest, test suite, verify tests.
---

# Hermes Test Runner

## Instructions

1. Identify the test scope:
   - Full suite: `python -m pytest tests/ -q`
   - Specific module: `python -m pytest tests/<module>/ -q`
   - Single file: `python -m pytest tests/test_file.py -q`

2. Ensure virtual environment is activated:
   ```bash
   cd /root/hermes-agent
   source .venv/bin/activate
   ```

3. Run appropriate test command based on scope

4. Analyze test output:
   - If tests pass: confirm success
   - If tests fail: identify failure patterns
   - Provide actionable debugging suggestions

## Common Test Commands

```bash
# Full test suite (~3000 tests, ~3 min)
python -m pytest tests/ -q

# Tool resolution tests
python -m pytest tests/test_model_tools.py -q

# CLI config loading tests
python -m pytest tests/test_cli_init.py -q

# Gateway tests
python -m pytest tests/gateway/ -q

# Tool-level tests
python -m pytest tests/tools/ -q

# Verbose output for debugging
python -m pytest tests/ -v

# Run specific test
python -m pytest tests/test_file.py::test_function -v
```

## Profile Test Requirements

When testing profile-related code:
- Verify both `Path.home()` mock AND `HERMES_HOME` env var are set
- Use the `profile_env` fixture pattern
- Confirm isolation from real `~/.hermes`

## Troubleshooting

- Tests writing to `~/.hermes/` → Check `_isolate_hermes_home` fixture
- SQLite locked errors → Normal, retry logic handles this
- Import errors → Verify `.venv` activation
```

**存储位置：** `.qoder/skills/hermes-test-runner/SKILL.md`

#### 2. **hermes-git-commit** - Git 提交规范

```yaml
---
name: hermes-git-commit
description: >
  Review all git changes in Hermes Agent repository and generate Conventional Commits
  formatted commit messages. Use before committing code, after completing features,
  or when preparing commits. Trigger keywords: git commit, commit changes, review changes.
---

# Hermes Git Commit Helper

## Instructions

1. Examine all git changes:
   ```bash
   git status
   git diff
   git diff --cached
   ```

2. Analyze changes by category:
   - New features → `feat`
   - Bug fixes → `fix`
   - Documentation → `docs`
   - Code refactoring → `refactor`
   - Test updates → `test`
   - Build/tooling → `chore`

3. Identify affected scope:
   - tools, agent, gateway, hermes_cli, tests, etc.

4. Generate commit message following Conventional Commits format:
   ```
   <type>(<scope>): <subject>

   <body>

   <footer>
   ```

## Commit Message Rules

**Subject line:**
- Maximum 50 characters
- Use imperative mood ("add" not "added")
- No period at end
- Be specific about what changed

**Body (if needed):**
- Explain what changed and why
- Wrap lines at 72 characters
- Use bullet points for multiple changes

**Footer (if applicable):**
- Reference issues: `Closes #123`
- Breaking changes: `BREAKING CHANGE: description`

## Examples

```bash
# Good commits
feat(tools): add web_scraper tool for parallel scraping
fix(agent): resolve prompt cache invalidation issue
docs(skills): update skill creation guidelines
test(gateway): add telegram platform adapter tests

# Bad commits
fix: fixed stuff
update
WIP
```

## Hermes-Specific Checks

Before committing, verify:
- [ ] Profile isolation not broken (no hardcoded ~/.hermes)
- [ ] Prompt cache protection maintained
- [ ] Tool registration follows 2-file pattern
- [ ] Tests pass: `python -m pytest tests/ -q`
- [ ] No debug code or print statements left

## Multi-Commit Strategy

If changes span multiple logical units:
1. Stage related changes: `git add <files>`
2. Commit with descriptive message
3. Repeat for each logical unit
4. Never mix unrelated changes in one commit
```

**存储位置：** `.qoder/skills/hermes-git-commit/SKILL.md`

#### 3. **hermes-tool-creator** - 工具创建向导

```yaml
---
name: hermes-tool-creator
description: >
  Guide through creating new Hermes Agent tools following the 2-file pattern.
  Use when adding new tools, registering capabilities, or extending toolsets.
  Trigger keywords: create tool, add tool, new tool, register tool.
---

# Hermes Tool Creator

## Tool Creation Process

Creating a tool requires changes in exactly 2 files:

### Step 1: Create tools/your_tool.py

```python
import json
import os
from tools.registry import registry

def check_requirements() -> bool:
    """Check if tool dependencies are met"""
    return bool(os.getenv("REQUIRED_API_KEY"))

def your_tool(param: str, task_id: str = None) -> str:
    """Tool implementation - MUST return JSON string"""
    try:
        # Your logic here
        result = {"success": True, "data": f"Processed: {param}"}
    except Exception as e:
        result = {"success": False, "error": str(e)}
    
    return json.dumps(result)

# Register the tool
registry.register(
    name="your_tool",
    toolset="your_toolset",
    schema={
        "name": "your_tool",
        "description": "Clear description of what the tool does",
        "parameters": {
            "type": "object",
            "properties": {
                "param": {
                    "type": "string",
                    "description": "Parameter description"
                }
            },
            "required": ["param"]
        }
    },
    handler=lambda args, **kw: your_tool(
        param=args.get("param", ""),
        task_id=kw.get("task_id")
    ),
    check_fn=check_requirements,
    requires_env=["REQUIRED_API_KEY"],  # Optional
)
```

### Step 2: Add to toolsets.py

Add to `_HERMES_CORE_TOOLS` (all platforms) or create new toolset:

```python
# toolsets.py
_HERMES_CORE_TOOLS = [
    # ... existing tools
    "your_tool",
]
```

## Critical Rules

1. **Handler MUST return JSON string** - not dict
2. **Use get_hermes_home()** for state file paths
3. **Use display_hermes_home()** in schema descriptions
4. **Never hardcode cross-tool references** in schema
5. **AST auto-discovery** - no manual import list needed

## Schema Best Practices

- Clear, specific description
- Include all required parameters
- Provide type hints
- Example values in descriptions

## Testing New Tools

After creation:
```bash
# Test tool registration
python -m pytest tests/test_model_tools.py -q

# Test in isolation
python -c "from tools.your_tool import *; print('OK')"
```

## Common Mistakes

❌ Returning dict instead of JSON string
❌ Hardcoding ~/.hermes paths
❌ Referencing other tools by name in schema
❌ Forgetting to add to toolsets.py
❌ Missing check_requirements for API-dependent tools
```

**存储位置：** `.qoder/skills/hermes-tool-creator/SKILL.md`

#### 4. **hermes-slash-command** - Slash 命令创建

```yaml
---
name: hermes-slash-command
description: >
  Guide through adding new slash commands to Hermes Agent following the central
  registry pattern. Use when creating CLI commands, gateway commands, or extending
  the command system. Trigger keywords: slash command, add command, new command.
---

# Hermes Slash Command Creator

## Command Addition Process

### Step 1: Add CommandDef to hermes_cli/commands.py

Add entry to `COMMAND_REGISTRY` list:

```python
from hermes_cli.commands import CommandDef

COMMAND_REGISTRY = [
    # ... existing commands
    CommandDef(
        name="mycommand",              # Canonical name without slash
        description="What it does",    # Human-readable description
        category="Session",            # One of: Session, Configuration, Tools & Skills, Info, Exit
        aliases=("mc",),               # Optional: alternative names
        args_hint="[arg]",             # Optional: argument placeholder
        cli_only=False,                # Optional: CLI-only
        gateway_only=False,            # Optional: Gateway-only
        gateway_config_gate=None,      # Optional: config dotpath for gateway gating
    ),
]
```

### Step 2: Add handler in cli.py

In `HermesCLI.process_command()`:

```python
elif canonical == "mycommand":
    self._handle_mycommand(cmd_original)
```

Then implement the handler:

```python
def _handle_mycommand(self, original: str):
    """Handle /mycommand"""
    # Parse arguments
    # Execute logic
    # Display output
    pass
```

### Step 3: Gateway handler (if applicable)

In `gateway/run.py`:

```python
if canonical == "mycommand":
    return await self._handle_mycommand(event)
```

## CommandDef Fields

| Field | Required | Description |
|-------|----------|-------------|
| name | Yes | Canonical name (e.g., "background") |
| description | Yes | Human-readable description |
| category | Yes | Session/Configuration/Tools & Skills/Info/Exit |
| aliases | No | Tuple of alternative names |
| args_hint | No | Argument placeholder shown in help |
| cli_only | No | Only available in CLI |
| gateway_only | No | Only available in messaging platforms |
| gateway_config_gate | No | Config dotpath for conditional gateway availability |

## Adding Aliases

To add an alias, ONLY modify the `aliases` tuple on existing CommandDef:

```python
# Before
aliases=(),

# After
aliases=("bg", "b"),
```

All consumers update automatically:
- CLI dispatch
- Gateway dispatch
- Help text
- Telegram menu
- Slack mapping
- Autocomplete

## Category Guidelines

- **Session**: Session management (/clear, /resume, /export)
- **Configuration**: Settings (/model, /skin, /profile)
- **Tools & Skills**: Tool/skill management (/skills, /tools)
- **Info**: Information (/help, /status, /doctor)
- **Exit**: Exit commands (/quit, /exit)

## Testing Commands

```bash
# Test in CLI
hermes chat
/mycommand

# Test completion
# Type /my<TAB> in CLI
```
```

**存储位置：** `.qoder/skills/hermes-slash-command/SKILL.md`

#### 5. **hermes-debug-helper** - 调试助手

```yaml
---
name: hermes-debug-helper
description: >
  Debug Hermes Agent issues including Profile isolation problems, Prompt cache
  invalidation, tool registration errors, and async bridge failures. Use when
  investigating bugs, tracking down errors, or analyzing logs.
  Trigger keywords: debug, investigate error, troubleshoot, find bug.
---

# Hermes Debug Helper

## Common Issue Categories

### 1. Profile Isolation Issues

**Symptoms:**
- Config leaking between profiles
- State files in wrong location
- `~/.hermes` appearing in user messages

**Debug steps:**
```bash
# Search for hardcoded paths
grep -r "Path.home() / \".hermes\"" --include="*.py" .

# Check HERMES_HOME usage
grep -r "get_hermes_home()" --include="*.py" .
grep -r "display_hermes_home()" --include="*.py" .
```

**Fix:** Replace all `Path.home() / ".hermes"` with `get_hermes_home()`

### 2. Prompt Cache Invalidation

**Symptoms:**
- Unexpected API cost spikes
- Context changes mid-conversation
- Toolset changes during session

**Check for:**
- Modifying conversation_history after sending
- Changing enabled_toolsets mid-session
- Reloading memories during conversation

**Rule:** ONLY alter context during:
- Session initialization
- Context compression

### 3. Tool Registration Failures

**Symptoms:**
- Tool not found when called
- Schema validation errors
- Handler returns dict instead of JSON string

**Debug:**
```python
# Test tool import
python -c "from tools.your_tool import *; print('OK')"

# Check registration
python -c "from tools.registry import registry; print(registry.list_tools())"
```

### 4. Async Bridge Errors

**Symptoms:**
- `RuntimeError: Event loop is closed`
- `no running event loop`
- Tools hanging indefinitely

**Check:**
- Using `_run_async()` from model_tools.py
- Not creating new loops with `asyncio.run()`
- Understanding 3 scenarios: CLI main thread / worker thread / gateway

### 5. SQLite Lock Issues

**Symptoms:**
- `sqlite3.OperationalError: database is locked`

**Normal behavior:** Random retry with jitter handles this
**If persistent:** Check for long-running transactions

## Debug Tools

```bash
# View gateway logs
tail -f /tmp/hermes-gateway.log

# Check session database
sqlite3 ~/.hermes/sessions.db ".tables"

# Test config loading
python -c "from hermes_cli.config import load_config; print(load_config())"

# Verify virtual environment
which python
python --version
```

## Logging

Enable debug logging:
```bash
export HERMES_LOG_LEVEL=DEBUG
hermes chat
```

Check logs:
```bash
tail -f ~/.hermes/hermes.log
```
```

**存储位置：** `.qoder/skills/hermes-debug-helper/SKILL.md`

#### 6. **hermes-config-manager** - 配置管理

```yaml
---
name: hermes-config-manager
description: >
  Manage Hermes Agent configuration including config.yaml settings, .env variables,
  and platform-specific configs. Use when modifying settings, adding environment
  variables, or troubleshooting configuration issues.
  Trigger keywords: config, configuration, settings, .env, api key.
---

# Hermes Config Manager

## Configuration Systems

### Two Separate Config Loaders

| Loader | Used By | Location |
|--------|---------|----------|
| `load_cli_config()` | CLI mode | `cli.py` |
| `load_config()` | Tools, setup | `hermes_cli/config.py` |
| Direct YAML load | Gateway | `gateway/run.py` |

### Config Files

- `~/.hermes/config.yaml` - User settings
- `~/.hermes/.env` - API keys and secrets

## Adding Configuration

### config.yaml Options

1. Add to `DEFAULT_CONFIG` in `hermes_cli/config.py`:
```python
DEFAULT_CONFIG = {
    # ... existing config
    "new_option": "default_value",
}
```

2. Bump `_config_version` (currently 5) to trigger migration:
```python
_config_version = 6  # Increment to migrate existing users
```

### .env Variables

Add to `OPTIONAL_ENV_VARS` in `hermes_cli/config.py`:
```python
OPTIONAL_ENV_VARS = {
    "NEW_API_KEY": {
        "description": "What it's for",
        "prompt": "Display name",
        "url": "https://example.com/get-key",
        "password": True,  # Mask in output
        "category": "tool",  # provider/tool/messaging/setting
    },
}
```

## Common Configuration Tasks

### Set API Keys

```bash
# Edit .env file
nano ~/.hermes/.env

# Or use setup wizard
hermes setup
```

### View Current Config

```bash
# CLI
hermes status

# Dashboard
hermes dashboard
```

### Profile-Specific Config

Each profile has isolated config:
```
~/.hermes/profiles/<name>/config.yaml
~/.hermes/profiles/<name>/.env
```

## Troubleshooting

### Config Not Loading

```bash
# Check YAML syntax
python -c "import yaml; yaml.safe_load(open('~/.hermes/config.yaml'))"

# Verify file location
ls -la ~/.hermes/config.yaml
```

### Migration Issues

If config version mismatch:
1. Backup config: `cp ~/.hermes/config.yaml ~/.hermes/config.yaml.bak`
2. Let migration run automatically
3. Verify settings preserved

### Environment Variables Not Picked Up

- Restart Hermes after .env changes
- Check HERMES_HOME points to correct profile
- Verify .env syntax (KEY=VALUE, no spaces around =)
```

**存储位置：** `.qoder/skills/hermes-config-manager/SKILL.md`

---

## 九、Commands 开发指南

### 9.1 Command vs Skill 区别

| 特性 | Skill | Command |
|------|-------|---------|
| 触发方式 | 模型自动判断 或 `/skill-name` | 必须输入 `/command-name` |
| 主要用途 | 专业领域知识、复杂工作流 | 快速执行预设任务 |
| 存储位置 | `skills/` 目录 | `commands/` 目录 |
| 权限确认 | 需要确认 | 不需要 |
| 适用场景 | 复杂多步骤任务 | 简单快捷操作 |

### 9.2 Hermes 项目 Commands 示例

#### 1. **hermes-full-test** - 完整测试运行

**文件：** `.qoder/commands/hermes-full-test.md`

```markdown
---
name: hermes-full-test
description: Run the complete Hermes Agent test suite (~3000 tests) and report results.
---

Run the full Hermes Agent test suite and provide a comprehensive report:

1. Activate virtual environment:
   ```bash
   cd /root/hermes-agent
   source .venv/bin/activate
   ```

2. Run complete test suite:
   ```bash
   python -m pytest tests/ -q
   ```

3. Report:
   - Total tests run
   - Pass/fail counts
   - Any failures with error details
   - Execution time
   - Recommendations for any failures

If tests fail, provide:
- Specific test names that failed
- Error messages
- Suggested fixes
- Commands to re-run failed tests only
```

#### 2. **hermes-quick-review** - 快速代码审查

**文件：** `.qoder/commands/hermes-quick-review.md`

```markdown
---
name: hermes-quick-review
description: Quick code review focusing on Hermes Agent critical rules: Profile isolation, Prompt cache, and tool registration.
---

Perform a quick code review of recent changes focusing on Hermes-critical rules:

1. Check recent changes:
   ```bash
   git diff HEAD~5
   ```

2. Review for critical issues:

   **Profile Isolation:**
   - [ ] No hardcoded `~/.hermes` paths
   - [ ] Uses `get_hermes_home()` for code paths
   - [ ] Uses `display_hermes_home()` for user messages

   **Prompt Cache Protection:**
   - [ ] No mid-conversation context modification
   - [ ] No dynamic toolset changes
   - [ ] No memory reload during session

   **Tool Registration:**
   - [ ] Tools return JSON strings (not dicts)
   - [ ] Added to toolsets.py
   - [ ] No hardcoded cross-tool references

   **Async Bridge:**
   - [ ] Uses `_run_async()` properly
   - [ ] No direct `asyncio.run()` in tools

3. Report any violations with:
   - File and line number
   - Severity (critical/warning/info)
   - Suggested fix
```

#### 3. **hermes-prepare-release** - 准备发布

**文件：** `.qoder/commands/hermes-prepare-release.md`

```markdown
---
name: hermes-prepare-release
description: Prepare Hermes Agent for release by running tests, checking docs, and creating release notes.
---

Prepare Hermes Agent for release:

1. Run complete test suite:
   ```bash
   cd /root/hermes-agent
   source .venv/bin/activate
   python -m pytest tests/ -q
   ```

2. Check documentation:
   - [ ] AGENTS.md up to date
   - [ ] HERMES_AGENT_KNOWLEDGE_BASE.md updated
   - [ ] README.md reflects new features
   - [ ] Release notes created (RELEASE_vX.X.X.md)

3. Verify version numbers:
   - pyproject.toml version
   - Config version bumped if needed
   - Skills index rebuilt if skills changed

4. Check for common issues:
   - [ ] No debug code or print statements
   - [ ] No TODO comments left in critical paths
   - [ ] All new tools registered
   - [ ] All new commands in registry

5. Generate release checklist:
   - New features
   - Bug fixes
   - Breaking changes
   - Migration notes
   - Contributors

6. Create git tag (if all checks pass):
   ```bash
   git tag -a vX.X.X -m "Release vX.X.X"
   ```
```

#### 4. **hermes-env-setup** - 环境检查

**文件：** `.qoder/commands/hermes-env-setup.md`

```markdown
---
name: hermes-env-setup
description: Verify Hermes Agent development environment is properly configured.
---

Check if the Hermes Agent development environment is properly set up:

1. Python environment:
   ```bash
   python --version
   which python
   ls -la /root/hermes-agent/.venv/bin/activate
   ```

2. Dependencies:
   ```bash
   cd /root/hermes-agent
   source .venv/bin/activate
   pip list | grep -E "fastapi|uvicorn|pytest|rich"
   ```

3. Git configuration:
   ```bash
   git remote -v
   git status
   ```

4. Hermes config:
   ```bash
   ls -la ~/.hermes/config.yaml
   ls -la ~/.hermes/.env
   ```

5. Test environment:
   ```bash
   python -m pytest tests/ --co -q  # Collect tests without running
   ```

6. Report any issues:
   - Missing dependencies
   - Incorrect Python version
   - Config files missing
   - Git not configured
   - Permission issues

7. Provide fix commands for any issues found
```

---

## 十、配置管理规则

### 10.1 配置版本迁移

**规则：**
- 修改 `DEFAULT_CONFIG` 必须升级 `_config_version`
- 编写迁移逻辑处理旧版本配置
- 测试迁移过程不丢失用户设置

### 10.2 环境变量规范

**必需元数据：**
```python
"API_KEY": {
    "description": "Clear description of purpose",
    "prompt": "User-friendly display name",
    "url": "Link to obtain the key",
    "password": True,  # 敏感信息掩码
    "category": "provider",  # provider/tool/messaging/setting
}
```

### 10.3 Profile 配置隔离

**每个 Profile 独立包含：**
- `config.yaml` - 配置
- `.env` - API 密钥
- `sessions.db` - 会话数据
- `memory/` - 记忆数据
- `skills/` - 技能配置

---

## 十一、文档维护规则

### 11.1 文档更新时机

**必须更新文档的场景：**
- 架构变更 → 更新 `HERMES_AGENT_KNOWLEDGE_BASE.md`
- 添加工具 → 更新工具系统章节
- 新增命令 → 更新命令注册章节
- 修复已知问题 → 更新问题与解决方案章节
- Skills 变更 → 更新技能系统章节

### 11.2 文档质量标准

**文档必须包含：**
- 清晰的标题和结构
- 代码示例（✅ 正确 / ❌ 错误对比）
- 常见问题和解决方案
- 更新日志或版本历史

**禁止：**
- 创建未请求的文档文件
- 留下过时的技术文档
- 重复或矛盾的信息

### 11.3 AGENTS.md 维护

**AGENTS.md 应包含：**
- 项目结构和依赖链
- 核心类和方法签名
- 开发环境设置
- 测试运行方式
- 已知陷阱和避免方法

---

## 十二、安全检查清单

### 12.1 代码安全

**提交前检查：**
- [ ] 无硬编码的 API 密钥或密码
- [ ] 无敏感的调试信息泄露
- [ ] 工具依赖的 API Key 通过环境变量管理
- [ ] 文件操作有适当的权限检查
- [ ] 命令执行有注入保护

### 12.2 数据安全

**Profile 数据安全：**
- [ ] 每个 Profile 数据完全隔离
- [ ] 会话数据库访问有锁保护
- [ ] 敏感配置（.env）不被意外提交
- [ ] 日志中不记录 API 密钥

### 12.3 依赖安全

**依赖管理：**
- [ ] 使用 `uv` 锁定依赖版本
- [ ] 定期审计依赖漏洞
- [ ] 不引入不必要的依赖
- [ ] 测试依赖与生产依赖分离

---

## 十三、记忆系统规则

### 13.1 三层记忆架构

Hermes Agent 的记忆系统是其**核心优势**，实现了自动整理、持久化、跨会话记忆。

**必须理解：**
```
会话级记忆 (SQLite) → 用户级记忆 (MEMORY.md) → 插件级记忆 (Hindsight)
```

### 13.2 SQLite 会话记忆规则

**必须遵守：**
- 使用 `SessionDB` 类进行会话存储
- 利用 FTS5 全文搜索功能
- 写操作使用随机退避策略

**禁止：**
- 直接操作 SQLite 文件（使用 SessionDB API）
- 忽略 WAL 模式的并发优势

### 13.3 Hindsight 记忆插件规则

#### 三阶段学习循环

```
retain(存储) → recall(检索) → reflect(推理综合)
```

**Retain（存储）规则：**
- 自动存储：默认每轮对话自动保存
- 手动存储：调用 `hindsight_retain` 工具
- 存储内容：用户偏好、项目决策、重要知识点

**Recall（检索）规则：**
- 自动 Prefetch：每次对话前自动检索相关记忆
- 手动检索：调用 `hindsight_recall` 工具
- 多策略搜索：语义 + 实体图谱 + 关键词

**Reflect（推理综合）规则：**
- 用于需要深度推理的问题
- 调用 `hindsight_reflect` 工具
- 跨记忆推理，生成综合回答

#### 记忆模式选择

| 模式 | 适用场景 | 工具暴露 | 自动注入 |
|------|---------|---------|---------|
| **hybrid** | 默认推荐 | ✅ | ✅ |
| **context** | 仅需自动记忆 | ❌ | ✅ |
| **tools** | 完全手动控制 | ✅ | ❌ |

**推荐配置：**
```json
{
  "memory_mode": "hybrid",
  "auto_retain": true,
  "auto_recall": true,
  "retain_every_n_turns": 1,
  "retain_async": true
}
```

### 13.4 记忆持久化规则

**会话级持久化：**
```python
# 每次对话自动保存
db.save_message(session_id, role, content)
```

**用户级持久化：**
```
~/.hermes/MEMORY.md    # 用户级记忆（所有会话共享）
~/.hermes/USER.md      # 用户偏好和配置
```

**跨会话记忆流程：**
```
会话 1: 用户说"我喜欢深色主题"
  ↓ hindsight_retain 自动存储
  ↓ 提取实体：用户、深色主题
  ↓ 存入知识图谱

会话 2: 用户问"推荐一个主题"
  ↓ hindsight_recall 自动检索
  ↓ 找到记忆: "用户偏好使用深色主题"
  ↓ 自动注入到上下文
  ↓ AI 回答: "根据您之前的偏好，推荐深色主题"
```

### 13.5 记忆系统配置规则

**配置文件位置：**
```
~/.hermes/hindsight/config.json
```

**必需配置项：**
```json
{
  "mode": "cloud",
  "apiKey": "your-api-key",
  "bank_id": "hermes",
  "memory_mode": "hybrid"
}
```

**环境变量：**
```bash
HINDSIGHT_API_KEY=xxx
HINDSIGHT_LLM_API_KEY=xxx  # 本地 LLM
```

### 13.6 记忆系统最佳实践

**自动记忆配置：**
```json
{
  "auto_retain": true,           // 开启自动存储
  "retain_every_n_turns": 1,     // 每轮都存储
  "retain_async": true,          // 异步处理（不阻塞）
  "auto_recall": true,           // 开启自动检索
  "recall_max_tokens": 4096      // 限制返回大小
}
```

**标签管理：**
```json
{
  "tags": ["hermes-agent"],          // 存储时自动添加
  "recall_tags": ["architecture"],   // 检索时过滤
  "recall_tags_match": "any"         // 匹配模式
}
```

**本地 LLM（隐私优先）：**
```json
{
  "llm_provider": "ollama",
  "llm_model": "qwen/qwen3.5-9b",
  "llm_base_url": "http://localhost:11434/v1"
}
```

### 13.7 Profile 记忆隔离

**每个 Profile 独立的记忆系统：**
```
~/.hermes/profiles/<name>/
├── hindsight/config.json    # Profile 级 Hindsight 配置
├── MEMORY.md                # Profile 级记忆
└── sessions.db              # Profile 级会话数据库
```

**规则：**
- 使用 `get_hermes_home()` 获取路径
- 不同 Profile 的记忆完全隔离
- 配置独立，互不干扰

### 13.8 记忆系统调试

**查看记忆状态：**
```bash
# SQLite 会话数据库
sqlite3 ~/.hermes/sessions.db ".tables"
sqlite3 ~/.hermes/sessions.db "SELECT COUNT(*) FROM messages;"

# 用户级记忆文件
cat ~/.hermes/MEMORY.md

# Hindsight 配置
cat ~/.hermes/hindsight/config.json
```

**启用调试日志：**
```bash
export HERMES_LOG_LEVEL=DEBUG
hermes chat
tail -f ~/.hermes/hermes.log | grep -i hindsight
```

### 13.9 记忆系统独特优势

1. **自动整理** - 无需手动管理，AI 自动提取和归纳
2. **持久化存储** - SQLite + 文件双重保障
3. **跨会话记忆** - 新会话自动加载历史记忆
4. **多策略检索** - 语义搜索 + 实体图谱 + 关键词匹配
5. **推理综合** - 不仅检索，还能推理和总结
6. **Profile 隔离** - 每个 Profile 独立记忆系统
7. **可插拔架构** - 支持多种记忆插件

### 13.10 完整文档

详细的记忆系统指南：[`.rules/memory-system-guide.md`](./memory-system-guide.md)

包含内容：
- 三层记忆架构详解
- Hindsight 三阶段学习完整示例
- 配置指南和最佳实践
- 实际工作流示例
- 调试和监控方法
- 常见问题解决方案

---

## 附录：快速参考

### A. 常用命令速查

```bash
# 开发环境
cd /root/hermes-agent && source .venv/bin/activate

# 测试
python -m pytest tests/ -q
python -m pytest tests/test_model_tools.py -q

# 运行
hermes chat
hermes dashboard --host 0.0.0.0 --port 9119 --no-open --insecure

# 网关
python -m gateway.run

# Git
git status
git diff
git commit -m "feat(tools): add new tool"
```

### B. 关键路径速查

```python
# 路径获取
from hermes_constants import get_hermes_home, display_hermes_home

# 配置加载
from hermes_cli.config import load_config, load_cli_config

# 工具注册
from tools.registry import registry

# 异步桥接
from model_tools import _run_async
```

### C. 测试 Fixture 速查

```python
# 标准隔离
@pytest.fixture
def isolate_hermes_home(tmp_path, monkeypatch):
    home = tmp_path / ".hermes"
    home.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(home))
    return home

# Profile 测试
@pytest.fixture
def profile_env(tmp_path, monkeypatch):
    home = tmp_path / ".hermes"
    home.mkdir()
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setenv("HERMES_HOME", str(home))
    return home
```

---

## 总结

本文档定义了 Hermes Agent 项目的完整开发规矩，涵盖：

1. **核心架构** - Profile 隔离、Prompt 缓存保护、异步桥接
2. **代码规范** - 终端输出、防御性编程、命名规范
3. **工具开发** - 注册流程、Handler 规范、自动发现
4. **技能系统** - SKILL.md 格式、存储位置、最佳实践
5. **测试规则** - 隔离 fixture、运行规范、禁止事项
6. **Git 工作流** - 分支管理、提交规范、检查清单
7. **Qoder 集成** - 初始化、代码审查、会话管理
8. **Skills 开发** - 6 个实用 Skills 完整实现
9. **Commands 开发** - 4 个实用 Commands 完整实现
10. **配置管理** - 版本迁移、环境变量、Profile 隔离
11. **文档维护** - 更新时机、质量标准、AGENTS.md 维护
12. **安全检查** - 代码安全、数据安全、依赖安全
13. **记忆系统** - 三层记忆架构、Hindsight 三阶段学习、跨会话记忆

**所有开发人员和 AI 助手必须严格遵守这些规矩。**

---

## 相关文档

- **项目知识库**: [`HERMES_AGENT_KNOWLEDGE_BASE.md`](../HERMES_AGENT_KNOWLEDGE_BASE.md)
  - 第十一章：Qoder CLI 集成与 Skills/Commands
  - 第十二章：记忆系统详解
- **记忆系统指南**: [`.rules/memory-system-guide.md`](./memory-system-guide.md)
  - 三层记忆架构详解
  - Hindsight 完整使用指南
  - 实际工作流示例
- **Qoder Skills/Commands 索引**: [`.qoder/README.md`](../.qoder/README.md)
  - 6 个 Skills 使用说明
  - 4 个 Commands 使用说明

---

**文档维护**: 本文档应随项目发展持续更新。  
**最后更新**: 2026-04-18  
**维护者**: Hermes Agent 开发团队
