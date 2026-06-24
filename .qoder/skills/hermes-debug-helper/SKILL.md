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
