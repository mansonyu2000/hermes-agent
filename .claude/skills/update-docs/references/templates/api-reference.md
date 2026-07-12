# API / Tool Reference Template

Copy this template for Hermes tool reference docs under `website/docs/winpeek/reference/`.

---

```markdown
---
sidebar_position: N
title: "Tool Name"
description: "Schema, parameters, and usage examples for this Hermes tool"
---

# Tool Name

Toolset: `winpeek_rpa`. Registered in `tools/winpeek_tools.py`.

## Schema

```json
{
  "name": "tool_name",
  "description": "What this tool does",
  "parameters": {
    "type": "object",
    "properties": {
      "param1": {
        "type": "string",
        "description": "What param1 is"
      },
      "param2": {
        "type": "integer",
        "default": 42,
        "description": "What param2 is"
      }
    },
    "required": ["param1"]
  }
}
```

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `param1` | `string` | ✅ | — | What it does |
| `param2` | `integer` | ❌ | `42` | What it does |

## Returns

```json
{
  "ok": true,
  "data": { ... }
}
```

On error:
```json
{
  "ok": false,
  "error": "Human-readable error message"
}
```

## Usage Example

### Agent Chat

```
User: Send a message to 许国勇
Agent: [calls tool_name with param1="许国勇", param2=42]
```

### Direct Python Call

```python
from tools.winpeek_tools import _handle_xxx
result = _handle_xxx({"param1": "许国勇", "param2": 42})
```

## Related Tools

- [tool_name_2](./tool-name-2.md) — companion tool
- [Architecture](../developer-guide/xxx.md) — how this fits in
```
