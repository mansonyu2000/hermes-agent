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
