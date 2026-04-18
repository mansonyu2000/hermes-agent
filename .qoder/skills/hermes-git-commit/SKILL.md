---
name: hermes-git-commit
description: >
  Review all git changes in Hermes Agent repository and generate Conventional Commits
  formatted commit messages. Use before committing code, after completing features,
  or when preparing commits. Trigger keywords: git commit, commit changes, review changes.
---

# Hermes Git Commit Helper

## Instructions

1. Examine all git changes:
   ```bash
   git status
   git diff
   git diff --cached
   ```

2. Analyze changes by category:
   - New features → `feat`
   - Bug fixes → `fix`
   - Documentation → `docs`
   - Code refactoring → `refactor`
   - Test updates → `test`
   - Build/tooling → `chore`

3. Identify affected scope:
   - tools, agent, gateway, hermes_cli, tests, etc.

4. Generate commit message following Conventional Commits format:
   ```
   <type>(<scope>): <subject>

   <body>

   <footer>
   ```

## Commit Message Rules

**Subject line:**
- Maximum 50 characters
- Use imperative mood ("add" not "added")
- No period at end
- Be specific about what changed

**Body (if needed):**
- Explain what changed and why
- Wrap lines at 72 characters
- Use bullet points for multiple changes

**Footer (if applicable):**
- Reference issues: `Closes #123`
- Breaking changes: `BREAKING CHANGE: description`

## Examples

```bash
# Good commits
feat(tools): add web_scraper tool for parallel scraping
fix(agent): resolve prompt cache invalidation issue
docs(skills): update skill creation guidelines
test(gateway): add telegram platform adapter tests

# Bad commits
fix: fixed stuff
update
WIP
```

## Hermes-Specific Checks

Before committing, verify:
- [ ] Profile isolation not broken (no hardcoded ~/.hermes)
- [ ] Prompt cache protection maintained
- [ ] Tool registration follows 2-file pattern
- [ ] Tests pass: `python -m pytest tests/ -q`
- [ ] No debug code or print statements left

## Multi-Commit Strategy

If changes span multiple logical units:
1. Stage related changes: `git add <files>`
2. Commit with descriptive message
3. Repeat for each logical unit
4. Never mix unrelated changes in one commit
