# Tutorial / Quickstart Template

Copy this template for getting-started guides under `website/docs/winpeek/`.

---

```markdown
---
sidebar_position: N
title: "Quickstart Name"
description: "X minutes to get Feature Y working"
---

# Feature Y Quickstart

X minutes to your first working result.

## Prerequisites

- **OS**: Windows / macOS / Linux
- **Software**: Hermes Agent v0.x+, Python 3.10+
- **Credentials**: API key for X (if needed)

## Step 1: Install

```bash
# Install dependencies
pip install xxx
```

## Step 2: Configure

```bash
# Set required env vars
export VAR_NAME=value
```

## Step 3: First Run

```bash
# Run the command
hermes xxx
```

Expected output:
```
✅ Connected
Ready for action
```

## Step 4: Verify

```bash
# Verify it works
hermes doctor xxx
```

## Common Issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| Connection refused | Service not running | Start the service first |
| Permission denied | Missing API key | Set the env var |

## Next Steps

- [Full user guide](../user-guide/xxx.md)
- [API reference](../reference/xxx.md)
```
