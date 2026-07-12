# Developer Guide Template

Copy this template for architecture/engine/internal docs under `website/docs/winpeek/developer-guide/`.

---

```markdown
---
sidebar_position: N
title: "Subsystem Name"
description: "Internal architecture and design of this subsystem"
---

# Subsystem Name

What this subsystem does and where it sits in the overall architecture.

## Architecture

```
Component A → Component B → Component C
     │            │
     ▼            ▼
  Database    External API
```

## Data Flow

1. Step 1 — what triggers it
2. Step 2 — what processes it
3. Step 3 — what gets output

## Key Files

| File | Purpose |
|------|---------|
| `path/to/file.py` | What it does |

## API Reference

### `function_name(param1, param2)`

Description of what this function does.

| Parameter | Type | Description |
|-----------|------|-------------|
| `param1` | `str` | What it is |
| `param2` | `int` | What it is |

Returns: `dict` with keys `ok`, `data`, `error`

**Example:**

```python
from module import function_name
result = function_name("hello", 42)
# → {"ok": true, "data": {...}}
```

## Database Tables

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `table_name` | What it stores | `id`, `col1`, `col2` |

## Error Handling

| Error | Cause | Recovery |
|-------|-------|----------|
| `ValueError` | Invalid input | Check parameters |

## References

- [Design doc](../../../docs/design/xxx.md) — original design rationale
- [User guide](../user-guide/xxx.md) — how users interact with this
```
