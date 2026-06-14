---
name: hermes-write-test
description: Guide through writing unit tests for new Python or TypeScript code following project patterns and best practices.
---

Guide through writing comprehensive unit tests for new code:

## Step 1: Identify What to Test

Ask about the code to be tested:
- Is it Python backend or TypeScript frontend?
- What are the main functions/components?
- What are the edge cases?
- What dependencies need mocking?

## Step 2: Python Tests

For Python code, follow project patterns:

### Create Test File

```bash
# Place in appropriate tests/ subdirectory
tests/tools/test_your_tool.py
tests/agent/test_your_module.py
tests/hermes_cli/test_your_command.py
```

### Test Structure

```python
"""Tests for feature_name - brief description."""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

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
```

### Key Patterns to Follow

1. **Use existing fixtures** from `tests/conftest.py`
2. **Mock external dependencies** (APIs, file system, etc.)
3. **Test Profile isolation** - use `profile_env` fixture
4. **Test error handling** - verify graceful failures
5. **Use parametrization** for multiple scenarios

## Step 3: Frontend Tests (TypeScript + React)

For React components:

### Create Test File

```typescript
// Place next to component
src/components/YourComponent.test.tsx
```

### Test Structure

```typescript
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { YourComponent } from './YourComponent'

describe('YourComponent', () => {
  it('renders correctly', () => {
    render(<YourComponent prop="value" />)
    
    expect(screen.getByText(/expected/i)).toBeInTheDocument()
  })

  it('handles user interaction', async () => {
    const user = userEvent.setup()
    render(<YourComponent />)
    
    await user.click(screen.getByRole('button'))
    expect(screen.getByText(/clicked/i)).toBeInTheDocument()
  })
})
```

## Step 4: Run Tests

```bash
# Python tests
python -m pytest tests/path/to/test_file.py -v

# Frontend tests
npm test -- YourComponent.test.tsx
```

## Step 5: Verify Coverage

```bash
# Python coverage
python -m pytest tests/ --cov=path.to.module --cov-report=term-missing

# Frontend coverage
npm run test:coverage
```

## Best Practices to Enforce

✅ **DO:**
- Name tests descriptively
- Follow AAA pattern (Arrange-Act-Assert)
- Test behavior, not implementation
- Mock external dependencies
- Test edge cases and errors
- Use existing project patterns

❌ **DON'T:**
- Write tests that depend on each other
- Test implementation details
- Skip error cases
- Hardcode paths (use tmp_path)
- Forget to clean up mocks

## Provide:
1. Complete test file(s) ready to use
2. Commands to run the tests
3. Explanation of what each test covers
4. Suggestions for additional test scenarios
