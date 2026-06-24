# Hermes Agent 测试模板和成功案例

> 本文档提供可直接复用的测试模板和项目中已有的成功测试案例。
> 适用于快速开始编写测试。
> **本文档已索引到项目知识库。**
> 最后更新: 2026-04-18

---

## 📚 文档导航

### 相关文档

| 文档 | 路径 | 说明 |
|------|------|------|
| **项目知识库** | [../HERMES_AGENT_KNOWLEDGE_BASE.md](../HERMES_AGENT_KNOWLEDGE_BASE.md) | 知识库主入口 |
| **开发指南** | [../AGENTS.md](../AGENTS.md) | AI助手开发指南 |
| **完整开发规矩** | [./development-rules.md](./development-rules.md) | 第五章：测试规则 |
| **记忆系统指南** | [./memory-system-guide.md](./memory-system-guide.md) | Hindsight完整指南 |
| **Python 测试 Skill** | [../.qoder/skills/hermes-python-test-expert/SKILL.md](../.qoder/skills/hermes-python-test-expert/SKILL.md) | Python 测试专家 |
| **前端测试 Skill** | [../.qoder/skills/hermes-frontend-test-expert/SKILL.md](../.qoder/skills/hermes-frontend-test-expert/SKILL.md) | 前端测试专家 |
| **Skills/Commands** | [../.qoder/README.md](../.qoder/README.md) | Skills和Commands索引 |

---

## 📋 目录

- [Python 测试模板](#python-测试模板)
- [前端测试模板](#前端测试模板)
- [成功案例索引](#成功案例索引)
- [测试模式速查](#测试模式速查)

---

## Python 测试模板

### 模板 1: 基础工具测试

**适用场景：** 测试工具函数、handler

```python
"""Tests for tool_name - brief description."""

import json
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from tools.your_tool import your_tool, check_requirements

class TestYourTool:
    """Tests for your_tool."""
    
    def test_returns_json_string(self):
        """工具必须返回 JSON 字符串"""
        result = your_tool("test_param")
        
        # 验证是有效的 JSON
        data = json.loads(result)
        assert isinstance(data, dict)
    
    def test_success_case(self):
        """测试成功场景"""
        result = your_tool("valid_input")
        data = json.loads(result)
        
        assert data["success"] is True
        assert "data" in data
    
    def test_error_handling(self):
        """测试错误处理"""
        result = your_tool("invalid_input")
        data = json.loads(result)
        
        assert data["success"] is False
        assert "error" in data
    
    def test_with_mock_dependency(self):
        """测试带 mock 依赖"""
        with patch('tools.your_tool.external_api') as mock_api:
            mock_api.return_value = {"status": "ok"}
            
            result = your_tool("test")
            data = json.loads(result)
            
            assert data["success"] is True
            mock_api.assert_called_once()

class TestToolRequirements:
    """Tests for tool requirements."""
    
    def test_check_requirements_with_env(self, monkeypatch):
        """测试环境变量检查"""
        monkeypatch.setenv("REQUIRED_API_KEY", "test-key")
        
        assert check_requirements() is True
    
    def test_check_requirements_without_env(self, monkeypatch):
        """测试缺少环境变量"""
        monkeypatch.delenv("REQUIRED_API_KEY", raising=False)
        
        assert check_requirements() is False
```

---

### 模板 2: Profile 隔离测试

**适用场景：** 测试 Profile 相关功能

```python
"""Tests for profile feature - isolation and configuration."""

import pytest
from pathlib import Path
from unittest.mock import patch

from hermes_constants import get_hermes_home, display_hermes_home

@pytest.fixture()
def profile_env(tmp_path, monkeypatch):
    """Profile 测试 fixture - 必须同时 mock 两项"""
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    default_home = tmp_path / ".hermes"
    default_home.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(default_home))
    return tmp_path

class TestProfileIsolation:
    """Tests for profile isolation."""
    
    def test_uses_get_hermes_home(self, profile_env):
        """验证使用 get_hermes_home()"""
        path = get_hermes_home()
        
        # 应该指向临时目录
        assert ".hermes" in str(path)
        assert path.exists()
        assert "profiles" not in str(path)  # 默认 profile
    
    def test_display_hermes_home(self, profile_env):
        """验证 display_hermes_home() 用于用户提示"""
        display_path = display_hermes_home()
        
        # 应该包含 ~/.hermes 格式
        assert ".hermes" in display_path
    
    def test_no_hardcoded_paths(self):
        """验证代码中没有硬编码路径"""
        import ast
        
        # 读取源代码
        source_file = Path("tools/your_tool.py")
        if source_file.exists():
            source = source_file.read_text()
            tree = ast.parse(source)
            
            # 检查是否有 Path.home() / ".hermes"
            # 这里简化处理，实际应更复杂
            assert 'Path.home() / ".hermes"' not in source
```

---

### 模板 3: 异步代码测试

**适用场景：** 测试异步函数、API 调用

```python
"""Tests for async module - async operations and error handling."""

import pytest
from unittest.mock import AsyncMock, patch

from model_tools import _run_async

@pytest.mark.asyncio
class TestAsyncOperations:
    """Tests for async operations."""
    
    async def test_async_function(self):
        """测试异步函数"""
        async def async_func():
            return "result"
        
        result = _run_async(async_func())
        assert result == "result"
    
    async def test_with_mock_client(self):
        """测试带 mock 异步客户端"""
        mock_client = AsyncMock()
        mock_client.api_call.return_value = {
            "status": "success",
            "data": "test"
        }
        
        with patch('module.get_client', return_value=mock_client):
            from module import async_function
            result = await async_function()
            
            assert result["status"] == "success"
            mock_client.api_call.assert_called_once()
    
    async def test_async_error_handling(self):
        """测试异步错误处理"""
        mock_client = AsyncMock()
        mock_client.api_call.side_effect = Exception("API Error")
        
        with patch('module.get_client', return_value=mock_client):
            from module import async_function
            
            with pytest.raises(Exception) as exc_info:
                await async_function()
            
            assert "API Error" in str(exc_info.value)
```

---

### 模板 4: 配置管理测试

**适用场景：** 测试配置加载、验证

```python
"""Tests for config management - loading and validation."""

import json
import pytest
from pathlib import Path
from unittest.mock import patch

from hermes_cli.config import load_config, DEFAULT_CONFIG

class TestConfigLoading:
    """Tests for configuration loading."""
    
    def test_load_default_config(self, tmp_path, monkeypatch):
        """测试加载默认配置"""
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        
        # 创建最小配置
        config_path = tmp_path / "config.yaml"
        config_path.write_text("model: test/model\n")
        
        config = load_config()
        
        assert "model" in config
        assert config["model"] == "test/model"
    
    def test_config_merge_with_defaults(self, tmp_path, monkeypatch):
        """测试配置与默认值合并"""
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        
        # 只设置部分配置
        config_path = tmp_path / "config.yaml"
        config_path.write_text("model: test/model\n")
        
        config = load_config()
        
        # 应该有默认值
        for key in DEFAULT_CONFIG:
            assert key in config
    
    def test_env_var_override(self, tmp_path, monkeypatch):
        """测试环境变量覆盖"""
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        monkeypatch.setenv("HERMES_MODEL", "env/model")
        
        config = load_config()
        
        # 环境变量应优先
        assert config.get("model") == "env/model"
```

---

### 模板 5: 参数化测试

**适用场景：** 测试多个输入/输出场景

```python
"""Tests with parametrization - multiple scenarios."""

import pytest

from module import validate_input, process_data

class TestParametrized:
    """Tests with multiple input combinations."""
    
    @pytest.mark.parametrize("input_value,expected", [
        ("valid", True),
        ("", False),
        (None, False),
        ("   ", False),
        ("a" * 100, True),
    ])
    def test_validation(self, input_value, expected):
        """测试输入验证"""
        assert validate_input(input_value) == expected
    
    @pytest.mark.parametrize("data,expected_result", [
        ({"key": "value"}, {"status": "ok"}),
        ({}, {"status": "error"}),
        (None, {"status": "error"}),
    ])
    def test_data_processing(self, data, expected_result):
        """测试数据处理"""
        result = process_data(data)
        assert result["status"] == expected_result["status"]
    
    @pytest.mark.parametrize("invalid_input", [
        "",
        None,
        "   ",
        "invalid!@#",
    ])
    def test_rejects_invalid_inputs(self, invalid_input):
        """测试拒绝无效输入"""
        with pytest.raises(ValueError):
            validate_input(invalid_input, strict=True)
```

---

## 前端测试模板

### 模板 1: React 组件测试

```typescript
// src/components/YourComponent.test.tsx
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { YourComponent } from './YourComponent'
import { vi } from 'vitest'

describe('YourComponent', () => {
  it('renders correctly', () => {
    render(<YourComponent title="Test Title" />)
    
    expect(screen.getByText('Test Title')).toBeInTheDocument()
  })

  it('handles user interaction', async () => {
    const handleClick = vi.fn()
    const user = userEvent.setup()
    
    render(<YourComponent onClick={handleClick} />)
    
    await user.click(screen.getByRole('button'))
    
    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it('shows loading state', () => {
    render(<YourComponent loading />)
    
    expect(screen.getByRole('button')).toBeDisabled()
    expect(screen.getByText(/loading/i)).toBeInTheDocument()
  })

  it('displays error message', async () => {
    render(<YourComponent />)
    
    // 触发错误
    await userEvent.click(screen.getByRole('button'))
    
    await waitFor(() => {
      expect(screen.getByText(/error/i)).toBeInTheDocument()
    })
  })

  it('renders with different variants', () => {
    const { rerender } = render(<YourComponent variant="primary" />)
    expect(screen.getByRole('button')).toHaveClass('btn-primary')
    
    rerender(<YourComponent variant="secondary" />)
    expect(screen.getByRole('button')).toHaveClass('btn-secondary')
  })
})
```

---

### 模板 2: Hook 测试

```typescript
// src/hooks/useYourHook.test.ts
import { renderHook, act } from '@testing-library/react'
import { useYourHook } from './useYourHook'
import { vi } from 'vitest'

describe('useYourHook', () => {
  it('initializes with default state', () => {
    const { result } = renderHook(() => useYourHook())
    
    expect(result.current.value).toBe('')
    expect(result.current.isLoading).toBe(false)
  })

  it('updates value', () => {
    const { result } = renderHook(() => useYourHook())
    
    act(() => {
      result.current.setValue('new value')
    })
    
    expect(result.current.value).toBe('new value')
  })

  it('handles async operation', async () => {
    const mockFetch = vi.fn().mockResolvedValue({ data: 'result' })
    global.fetch = mockFetch
    
    const { result } = renderHook(() => useYourHook())
    
    await act(async () => {
      await result.current.fetchData()
    })
    
    expect(result.current.data).toEqual({ data: 'result' })
    expect(mockFetch).toHaveBeenCalled()
  })

  it('handles errors', async () => {
    const mockFetch = vi.fn().mockRejectedValue(new Error('Network error'))
    global.fetch = mockFetch
    
    const { result } = renderHook(() => useYourHook())
    
    await act(async () => {
      await result.current.fetchData()
    })
    
    expect(result.current.error).toBe('Network error')
  })
})
```

---

## 成功案例索引

### Python 测试案例

| 文件 | 测试内容 | 关键模式 |
|------|---------|---------|
| `tests/test_hermes_state.py` | SQLite 会话存储 | Profile 隔离、FTS5 搜索 |
| `tests/test_model_tools.py` | 工具集解析 | Mock、参数化 |
| `tests/tools/test_file_tools_live.py` | 文件操作 | 真实环境、确定性内容 |
| `tests/hermes_cli/test_profiles.py` | Profile 管理 | profile_env fixture |
| `tests/gateway/test_session_info.py` | 网关会话 | Patch 多个依赖 |
| `tests/run_agent/test_413_compression.py` | 上下文压缩 | Mock API 错误 |

### 推荐阅读的测试文件

```bash
# 查看 Profile 测试模式
cat tests/hermes_cli/test_profiles.py

# 查看工具测试模式
cat tests/tools/test_file_tools_live.py

# 查看异步测试模式
cat tests/test_model_tools_async_bridge.py

# 查看错误处理测试
cat tests/run_agent/test_413_compression.py
```

---

## 测试模式速查

### Fixture 使用

```python
# 临时目录
def test_with_tmp(self, tmp_path):
    file = tmp_path / "test.txt"

# Mock 环境变量
def test_with_env(self, monkeypatch):
    monkeypatch.setenv("KEY", "value")

# Profile 环境
def test_profile(self, profile_env):
    # 同时 mock Path.home() 和 HERMES_HOME
    pass

# Mock 函数
def test_mock(self):
    with patch('module.func', return_value=1):
        pass
```

### 常见断言

```python
# 值比较
assert result == expected
assert result != unexpected

# 异常检查
with pytest.raises(ValueError):
    function()

with pytest.raises(Exception) as exc_info:
    function()
assert "error message" in str(exc_info.value)

# 类型检查
assert isinstance(result, dict)
assert isinstance(result, list)

# 包含检查
assert "key" in result
assert "substring" in result["text"]
```

### Mock 模式

```python
# 简单 Mock
with patch('module.func', return_value=1):
    pass

# Async Mock
with patch('module.async_func', new_callable=AsyncMock) as mock:
    mock.return_value = {"data": "result"}

# 多次调用
with patch('module.func') as mock:
    mock.side_effect = [1, 2, 3]  # 三次不同返回值

# 检查调用
mock.assert_called_once()
mock.assert_called_with(arg1, arg2)
mock.assert_called_once_with(arg1, arg2)
```

---

## 快速开始指南

### 1. 为新工具编写测试

```bash
# 1. 创建测试文件
touch tests/tools/test_your_tool.py

# 2. 复制模板
# 使用上面的"基础工具测试"模板

# 3. 运行测试
python -m pytest tests/tools/test_your_tool.py -v

# 4. 检查覆盖率
python -m pytest tests/ --cov=tools.your_tool --cov-report=term-missing
```

### 2. 为新组件编写前端测试

```bash
# 1. 创建测试文件
touch web/src/components/YourComponent.test.tsx

# 2. 复制模板
# 使用上面的"React 组件测试"模板

# 3. 运行测试
cd web
npm test -- YourComponent.test.tsx
```

### 3. 运行完整测试

```bash
# Python 测试
python -m pytest tests/ -q

# 前端测试（如果已配置）
cd web && npm run test:run

# 生成覆盖率报告
python -m pytest tests/ --cov=. --cov-report=html
open htmlcov/index.html
```

---

## 相关文档

- **Python 测试 Skill**: `/hermes-python-test-expert`
- **前端测试 Skill**: `/hermes-frontend-test-expert`
- **测试命令**: `/hermes-run-all-tests`, `/hermes-write-test`
- **pytest 配置**: `pyproject.toml` (第 131-137 行)
- **全局 fixtures**: `tests/conftest.py`
