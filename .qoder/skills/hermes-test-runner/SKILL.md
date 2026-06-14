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
