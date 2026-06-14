---
name: hermes-full-test
description: Run the complete Hermes Agent test suite (~3000 tests) and report results.
---

Run the full Hermes Agent test suite and provide a comprehensive report:

1. Activate virtual environment:
   ```bash
   cd /root/hermes-agent
   source .venv/bin/activate
   ```

2. Run complete test suite:
   ```bash
   python -m pytest tests/ -q
   ```

3. Report:
   - Total tests run
   - Pass/fail counts
   - Any failures with error details
   - Execution time
   - Recommendations for any failures

If tests fail, provide:
- Specific test names that failed
- Error messages
- Suggested fixes
- Commands to re-run failed tests only
