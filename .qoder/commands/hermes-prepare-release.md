---
name: hermes-prepare-release
description: Prepare Hermes Agent for release by running tests, checking docs, and creating release notes.
---

Prepare Hermes Agent for release:

1. Run complete test suite:
   ```bash
   cd /root/hermes-agent
   source .venv/bin/activate
   python -m pytest tests/ -q
   ```

2. Check documentation:
   - [ ] AGENTS.md up to date
   - [ ] HERMES_AGENT_KNOWLEDGE_BASE.md updated
   - [ ] README.md reflects new features
   - [ ] Release notes created (RELEASE_vX.X.X.md)

3. Verify version numbers:
   - pyproject.toml version
   - Config version bumped if needed
   - Skills index rebuilt if skills changed

4. Check for common issues:
   - [ ] No debug code or print statements
   - [ ] No TODO comments left in critical paths
   - [ ] All new tools registered
   - [ ] All new commands in registry

5. Generate release checklist:
   - New features
   - Bug fixes
   - Breaking changes
   - Migration notes
   - Contributors

6. Create git tag (if all checks pass):
   ```bash
   git tag -a vX.X.X -m "Release vX.X.X"
   ```
