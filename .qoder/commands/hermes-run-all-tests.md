---
name: hermes-run-all-tests
description: Run complete test suite for both Python backend and frontend, report results and coverage.
---

Run complete test suite for Hermes Agent (Python + Frontend):

## 1. Python Backend Tests

```bash
cd /root/hermes-agent
source .venv/bin/activate

# Run all tests (~3000 tests, ~3 min)
python -m pytest tests/ -q

# With verbose output
python -m pytest tests/ -v

# With coverage
python -m pytest tests/ --cov=. --cov-report=term-missing
```

## 2. Frontend Tests (if configured)

```bash
cd /root/hermes-agent/web

# Run tests
npm run test:run

# With coverage
npm run test:coverage
```

## 3. Report Results

Provide comprehensive report:
- Total tests run (backend + frontend)
- Pass/fail counts
- Coverage percentage
- Any failures with:
  - File and line number
  - Error message
  - Suggested fix
- Execution time

## 4. If Tests Fail

Provide:
- Specific test names that failed
- Full error tracebacks
- Root cause analysis
- Step-by-step fix instructions
- Commands to re-run failed tests only

## 5. Coverage Analysis

If coverage is low (< 80%), identify:
- Untested modules
- Critical paths without tests
- Recommendations for priority testing
