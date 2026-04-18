---
name: hermes-python-test-expert
description: >
  Expert guide for writing, running, and debugging Python unit tests in Hermes Agent.
  Use when creating tests, running pytest, fixing test failures, or adding test coverage.
  Covers fixtures, mocks, isolation patterns, and best practices.
  Trigger keywords: python test, pytest, unit test, test coverage, write test, add test.
---

# Hermes Agent Python Testing Expert

## 项目测试基础设施

### 现有配置

**pytest 配置** (`pyproject.toml`):
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
markers = [
    "integration: marks tests requiring external services",
]
addopts = "-m 'not integration' -n auto"  # 跳过集成测试 + 并行执行
```

**测试依赖** (`pyproject.toml`):
```toml
[project.optional-dependencies]
dev = [
    "pytest>=9.0.2,<10",
    "pytest-asyncio>=1.3.0,<2",
    "pytest-xdist>=3.0,<4",  # 并行执行
    "mcp>=1.2.0,<2"
]
```

### 测试目录结构

```
tests/
├── conftest.py                    # 全局 fixtures
├── agent/                         # Agent 模块测试 (41 个文件)
├── cli/                           # CLI 测试 (39 个文件)
├── gateway/                       # 网关测试 (153 个文件)
├── hermes_cli/                    # CLI 子命令测试 (106 个文件)
├── tools/                         # 工具测试 (128 个文件)
├── run_agent/                     # Agent 循环测试 (45 个文件)
├── plugins/                       # 插件测试
├── e2e/                           # 端到端测试
├── integration/                   # 集成测试
└── skills/                        # 技能测试
```

**总计：~3000 个测试，约 3 分钟完成**

---

## 核心测试模式

### 1. 全局隔离 Fixture

**文件：** `tests/conftest.py`

```python
@pytest.fixture(autouse=True)
def _isolate_hermes_home(tmp_path, monkeypatch):
    """Redirect HERMES_HOME to temp dir - 所有测试自动使用"""
    fake_home = tmp_path / "hermes_test"
    fake_home.mkdir()
    (fake_home / "sessions").mkdir()
    (fake_home / "cron").mkdir()
    (fake_home / "memories").mkdir()
    (fake_home / "skills").mkdir()
    monkeypatch.setenv("HERMES_HOME", str(fake_home))
    
    # 清理关键环境变量
    monkeypatch.delenv("HERMES_SESSION_PLATFORM", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
```

**关键点：**
- `autouse=True` - 自动应用于所有测试
- 每个测试获得独立的临时目录
- 不会污染真实的 `~/.hermes`

### 2. Profile 测试 Fixture

**文件：** `tests/hermes_cli/test_profiles.py`

```python
@pytest.fixture()
def profile_env(tmp_path, monkeypatch):
    """Profile 测试 - 必须同时 mock 两项"""
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    default_home = tmp_path / ".hermes"
    default_home.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(default_home))
    return tmp_path
```

**规则：** Profile 测试必须同时：
1. Mock `Path.home()`
2. 设置 `HERMES_HOME` 环境变量

### 3. Mock Config Fixture

```python
@pytest.fixture()
def mock_config():
    """返回最小化配置字典"""
    return {
        "model": "test/mock-model",
        "toolsets": ["terminal", "file"],
        "max_turns": 10,
        "terminal": {
            "backend": "local",
            "cwd": "/tmp",
            "timeout": 30,
        },
        "compression": {"enabled": False},
        "memory": {"memory_enabled": False, "user_profile_enabled": False},
    }
```

---

## 测试编写指南

### 基础测试结构

```python
"""Tests for feature_name - brief description."""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

# 导入被测模块
from module_to_test import function_to_test

class TestFeatureName:
    """Tests for feature_name."""
    
    def test_basic_functionality(self, tmp_path):
        """Test basic feature works."""
        # Arrange
        input_data = {...}
        
        # Act
        result = function_to_test(input_data)
        
        # Assert
        assert result == expected_value
    
    def test_edge_case(self):
        """Test edge case handling."""
        with pytest.raises(ValueError):
            function_to_test(invalid_input)
    
    @pytest.mark.parametrize("input,expected", [
        (1, 2),
        (2, 4),
        (3, 6),
    ])
    def test_parametrized(self, input, expected):
        """Test multiple inputs."""
        assert function_to_test(input) == expected
```

### Mocking 模式

#### 1. 简单 Mock

```python
def test_with_mock(self):
    with patch('module.function', return_value="mocked"):
        result = code_under_test()
        assert result == "mocked"
```

#### 2. Async Mock

```python
@pytest.mark.asyncio
async def test_async_function(self):
    mock_client = AsyncMock()
    mock_client.call_api.return_value = {"data": "result"}
    
    with patch('module.create_client', return_value=mock_client):
        result = await async_function()
        assert result["data"] == "result"
```

#### 3. Multiple Patches

```python
def test_multiple_mocks(self):
    with patch('module.func1', return_value=1), \
         patch('module.func2', return_value=2), \
         patch('module.func3', side_effect=ValueError):
        
        result = complex_function()
        assert result == expected
```

### 测试工具注册

```python
class TestToolRegistration:
    def test_tool_registered(self):
        """验证工具正确注册"""
        from tools.registry import registry
        
        tools = registry.list_tools()
        assert "your_tool" in tools
    
    def test_tool_schema_valid(self):
        """验证工具 schema 正确"""
        from tools.your_tool import registry
        
        schema = registry.get_schema("your_tool")
        assert schema["name"] == "your_tool"
        assert "parameters" in schema
```

### 测试文件操作

```python
def test_file_operations(self, tmp_path):
    """测试文件操作 - 使用 tmp_path"""
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")
    
    # 测试读取
    content = test_file.read_text()
    assert content == "content"
    
    # 测试处理
    result = process_file(test_file)
    assert result == expected
```

---

## 运行测试

### 完整测试套件

```bash
# 激活虚拟环境
cd /root/hermes-agent
source .venv/bin/activate

# 运行所有测试 (~3000 tests, ~3 min)
python -m pytest tests/ -q

# 并行执行 (更快)
python -m pytest tests/ -n auto -q
```

### 特定模块测试

```bash
# 工具集解析测试
python -m pytest tests/test_model_tools.py -v

# CLI 配置加载测试
python -m pytest tests/test_cli_init.py -v

# 网关测试
python -m pytest tests/gateway/ -v

# 工具测试
python -m pytest tests/tools/ -v

# Agent 测试
python -m pytest tests/agent/ -v
```

### 单个测试文件

```bash
# 运行单个文件
python -m pytest tests/tools/test_file_tools.py -v

# 运行单个测试类
python -m pytest tests/tools/test_file_tools.py::TestClass -v

# 运行单个测试函数
python -m pytest tests/tools/test_file_tools.py::TestClass::test_function -v
```

### 调试测试

```bash
# 详细输出
python -m pytest tests/ -v

# 显示打印输出
python -m pytest tests/ -s

# 遇到第一个失败停止
python -m pytest tests/ -x

# 显示最慢的 10 个测试
python -m pytest tests/ --durations=10

# 生成覆盖率报告
python -m pytest tests/ --cov=. --cov-report=html
```

---

## 测试最佳实践

### 1. 命名规范

```python
# ✅ 好的测试名称
def test_returns_json_string_for_success(self):
def test_raises_error_when_api_key_missing(self):
def test_uses_hermes_home_not_hardcoded_path(self):

# ❌ 坏的测试名称
def test1(self):
def test_basic(self):
def test_stuff(self):
```

### 2. AAA 模式 (Arrange-Act-Assert)

```python
def test_example(self):
    # Arrange - 准备测试数据
    input_data = {"key": "value"}
    
    # Act - 执行被测代码
    result = function_under_test(input_data)
    
    # Assert - 验证结果
    assert result["status"] == "success"
```

### 3. 测试隔离

```python
# ✅ 每个测试独立
@pytest.fixture(autouse=True)
def clean_state():
    yield
    # 清理全局状态
    global_var.reset()

# ❌ 测试间共享状态
shared_data = {}  # 会导致测试互相影响
```

### 4. 使用参数化

```python
# ✅ 参数化测试多个场景
@pytest.mark.parametrize("input,expected", [
    ("valid_key", True),
    ("", False),
    (None, False),
    ("invalid", False),
])
def test_validation(self, input, expected):
    assert validate(input) == expected

# ❌ 重复代码
def test_valid(self):
    assert validate("valid_key") == True

def test_empty(self):
    assert validate("") == False
```

### 5. 测试边界情况

```python
def test_boundary_conditions(self):
    # 空输入
    assert function("") == expected_empty
    
    # 超长输入
    long_input = "a" * 10000
    assert function(long_input) == expected_long
    
    # 特殊字符
    assert function("<script>alert('xss')</script>") == expected_safe
    
    # None 值
    assert function(None) == expected_none
```

---

## 常见测试场景

### 场景 1: 测试工具 Handler

```python
class TestToolHandler:
    def test_returns_json_string(self):
        """工具必须返回 JSON 字符串"""
        from tools.your_tool import your_tool
        
        result = your_tool("param")
        
        # 验证是有效的 JSON
        import json
        data = json.loads(result)
        assert "success" in data
    
    def test_handles_exception(self):
        """工具处理异常"""
        from tools.your_tool import your_tool
        
        result = your_tool("invalid")
        data = json.loads(result)
        
        assert data["success"] == False
        assert "error" in data
```

### 场景 2: 测试 Profile 隔离

```python
class TestProfileIsolation:
    def test_uses_get_hermes_home(self, profile_env):
        """验证使用 get_hermes_home()"""
        from hermes_constants import get_hermes_home
        
        path = get_hermes_home()
        
        # 应该指向临时目录，不是 ~/.hermes
        assert ".hermes" in str(path)
        assert path.exists()
    
    def test_no_hardcoded_paths(self):
        """代码中没有硬编码路径"""
        import ast
        from pathlib import Path
        
        source = Path("tools/your_tool.py").read_text()
        tree = ast.parse(source)
        
        # 检查没有 Path.home() / ".hermes"
        for node in ast.walk(tree):
            if isinstance(node, ast.BinOp):
                # 简化检查 - 实际应更复杂
                pass
```

### 场景 3: 测试异步代码

```python
@pytest.mark.asyncio
class TestAsyncTool:
    async def test_async_operation(self):
        """测试异步操作"""
        from model_tools import _run_async
        
        async def async_func():
            return "result"
        
        result = _run_async(async_func())
        assert result == "result"
    
    async def test_with_mock_client(self):
        """测试带 mock 客户端"""
        mock_client = AsyncMock()
        mock_client.api_call.return_value = {"data": "test"}
        
        with patch('module.get_client', return_value=mock_client):
            result = await async_tool_call()
            assert result["data"] == "test"
```

---

## 调试失败测试

### 1. 查看详细错误

```bash
# 完整 traceback
python -m pytest tests/ -v --tb=long

# 简化输出
python -m pytest tests/ -v --tb=short

# 仅显示第一行
python -m pytest tests/ -v --tb=line
```

### 2. 使用 PDB 调试

```bash
# 失败时进入 debugger
python -m pytest tests/ --pdb

# 在特定测试进入 debugger
python -m pytest tests/test_file.py::test_func --pdb
```

### 3. 打印调试

```bash
# 显示 print 输出
python -m pytest tests/ -s

# 或使用 logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## 测试覆盖率

### 安装覆盖率工具

```bash
pip install pytest-cov
```

### 运行覆盖率测试

```bash
# 生成文本报告
python -m pytest tests/ --cov=. --cov-report=term

# 生成 HTML 报告
python -m pytest tests/ --cov=. --cov-report=html

# 查看报告
open htmlcov/index.html
```

### 覆盖率配置

**文件：** `.coveragerc`
```ini
[run]
source = .
omit = 
    tests/*
    .venv/*
    */migrations/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise NotImplementedError
```

---

## 集成测试

### 标记集成测试

```python
@pytest.mark.integration
def test_requires_api_key():
    """需要真实 API 的测试"""
    pass
```

### 运行/跳过集成测试

```bash
# 默认跳过集成测试
python -m pytest tests/ -q

# 仅运行集成测试
python -m pytest tests/ -m integration -q

# 运行所有测试
python -m pytest tests/ -m "" -q
```

---

## 快速参考

### 测试命令速查

```bash
# 基本运行
python -m pytest tests/ -q

# 详细输出
python -m pytest tests/ -v

# 特定文件
python -m pytest tests/test_file.py -v

# 特定测试
python -m pytest tests/test_file.py::TestClass::test_method -v

# 并行执行
python -m pytest tests/ -n auto -q

# 跳过慢测试
python -m pytest tests/ --timeout=10

# 覆盖率
python -m pytest tests/ --cov=. --cov-report=html
```

### Fixture 速查

```python
# 临时目录
def test_with_tmp(self, tmp_path):
    file = tmp_path / "test.txt"

# Mock 环境变量
def test_with_env(self, monkeypatch):
    monkeypatch.setenv("KEY", "value")

# Mock 函数
def test_with_mock(self):
    with patch('module.func', return_value=1):
        pass

# 自定义 fixture
@pytest.fixture()
def my_fixture():
    return setup_data()
```

---

## 相关文档

- **完整测试策略**: 参见项目知识库测试章节
- **conftest.py**: `tests/conftest.py` (全局 fixtures)
- **pytest 配置**: `pyproject.toml` (第 131-137 行)
- **测试示例**: `tests/tools/`, `tests/gateway/`, `tests/agent/`
