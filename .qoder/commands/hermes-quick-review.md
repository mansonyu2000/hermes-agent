---
name: hermes-quick-review
description: Quick code review focusing on Hermes Agent critical rules: Profile isolation, Prompt cache, and tool registration.
---

Perform a quick code review of recent changes focusing on Hermes-critical rules:

1. Check recent changes:
   ```bash
   git diff HEAD~5
   ```

2. Review for critical issues:

   **Profile Isolation:**
   - [ ] No hardcoded `~/.hermes` paths
   - [ ] Uses `get_hermes_home()` for code paths
   - [ ] Uses `display_hermes_home()` for user messages

   **Prompt Cache Protection:**
   - [ ] No mid-conversation context modification
   - [ ] No dynamic toolset changes
   - [ ] No memory reload during session

   **Tool Registration:**
   - [ ] Tools return JSON strings (not dicts)
   - [ ] Added to toolsets.py
   - [ ] No hardcoded cross-tool references

   **Async Bridge:**
   - [ ] Uses `_run_async()` properly
   - [ ] No direct `asyncio.run()` in tools

3. Report any violations with:
   - File and line number
   - Severity (critical/warning/info)
   - Suggested fix
