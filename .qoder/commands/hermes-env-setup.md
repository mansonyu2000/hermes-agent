---
name: hermes-env-setup
description: Verify Hermes Agent development environment is properly configured.
---

Check if the Hermes Agent development environment is properly set up:

1. Python environment:
   ```bash
   python --version
   which python
   ls -la /root/hermes-agent/.venv/bin/activate
   ```

2. Dependencies:
   ```bash
   cd /root/hermes-agent
   source .venv/bin/activate
   pip list | grep -E "fastapi|uvicorn|pytest|rich"
   ```

3. Git configuration:
   ```bash
   git remote -v
   git status
   ```

4. Hermes config:
   ```bash
   ls -la ~/.hermes/config.yaml
   ls -la ~/.hermes/.env
   ```

5. Test environment:
   ```bash
   python -m pytest tests/ --co -q  # Collect tests without running
   ```

6. Report any issues:
   - Missing dependencies
   - Incorrect Python version
   - Config files missing
   - Git not configured
   - Permission issues

7. Provide fix commands for any issues found
