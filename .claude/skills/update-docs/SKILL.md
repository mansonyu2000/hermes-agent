---
name: update-docs
description: Update WinPeek documentation based on code changes. Use when the user says "更新文档", "同步文档", "检查文档", "文档更新", "update docs", "docs check", "what docs need updating", or mentions "docs/" with a code change.
---

# WinPeek Documentation Updater

Guides you through updating website documentation when code changes. Based on Next.js update-docs skill, adapted for Hermes Agent / WinPeek.

## Quick Start

1. **Analyze changes**: `git diff DEV...HEAD --stat` to see what files changed
2. **Map to docs**: Check `references/CODE-TO-DOCS-MAPPING.yaml` for affected docs
3. **Review each doc**: Walk through updates, confirm with user
4. **Validate**: `python scripts/winpeek-quality-check.py` must pass
5. **Commit**: Documentation changes alongside code changes

## Workflow: Identify Affected Docs

### Step 1: Get the diff

```bash
git diff DEV...HEAD --stat
```

### Step 2: Load the mapping

Read `references/CODE-TO-DOCS-MAPPING.yaml` and find all docs whose `source` path matches a changed file.

### Step 3: Report to user

```
Code changes on this branch:

  plugins/winpeek_rpa/platforms/wechat/db.py          (+45 lines)
  tools/winpeek_tools.py                              (+30 lines)

Affected documentation (from CODE-TO-DOCS-MAPPING.yaml):

  website/docs/winpeek/developer-guide/wechat-database.md     ← wechat/db.py
  website/docs/winpeek/reference/schemas.md                   ← wechat/db.py
  website/docs/winpeek/reference/tools.md                     ← tools/winpeek_tools.py

3 documents need review. Start with wechat-database.md?
```

## Workflow: Update a Document

### Step 1: Read the current doc

Read the existing documentation to understand:
- Current structure and sections
- Frontmatter fields (`sidebar_position`, `title`, `description`)
- Existing examples and API references

### Step 2: Identify what needs updating

| Change Type | Doc Update |
|-------------|-----------|
| New method/function | Add to API reference section |
| New parameter/prop | Add to parameter table |
| Changed behavior | Update description + examples |
| Deprecated feature | Add deprecation notice |
| New schema/table | Add to schemas reference |
| New Hermes tool | Add to tools reference |

### Step 3: Apply updates

For each change:
1. Show the user what you plan to change
2. Wait for confirmation
3. Apply the edit
4. Show the diff

### Step 4: Validate

```bash
python scripts/winpeek-quality-check.py
```

This checks: frontmatter, dead links, file naming, CSS tokens, Python ruff.

## Workflow: Scaffold New Documentation

Use when adding docs for entirely new features.

### Step 1: Determine doc type and location

| Feature Type | Location | Template |
|-------------|----------|----------|
| User guide (功能说明) | `website/docs/winpeek/user-guide/` | `references/templates/user-guide.md` |
| Developer guide (架构/引擎/数据库) | `website/docs/winpeek/developer-guide/` | `references/templates/developer-guide.md` |
| API / Tool reference | `website/docs/winpeek/reference/` | `references/templates/api-reference.md` |
| Quickstart / Tutorial | `website/docs/winpeek/` | `references/templates/tutorial.md` |

### Step 2: Create with proper naming

- Lowercase + hyphens: `wechat-portrait.md`
- No uppercase: not `WECHAT-PORTRAIT.md`
- In subdirectories, use `_category_.json` for sidebar ordering

### Step 3: Fill frontmatter

```yaml
---
sidebar_position: N
title: "Page Title"
description: "One-line description for search results"
---
```

### Step 4: Validate

```bash
python scripts/winpeek-quality-check.py
```

## Document Templates

See `references/templates/` for full templates:
- `user-guide.md` — Feature guide with screenshots, steps, tips
- `developer-guide.md` — Architecture, data flow, API reference
- `api-reference.md` — Tool schema, parameters, examples
- `tutorial.md` — Quickstart with code blocks

## Key Rules

1. **Every .md must have YAML frontmatter** — `sidebar_position` + `title` minimum
2. **Filenames lowercase-hyphens** — no uppercase letters
3. **Links must be relative paths within website/docs/** — no `../../docs/design/` cross-references
4. **Code examples use actual running code** — not made-up examples
5. **Docs update goes in the same commit as the code change** — not a separate "docs" commit

## Integration with Quality Gate

This skill pairs with `scripts/winpeek-quality-check.py`. After updating docs, always run:

```bash
python scripts/winpeek-quality-check.py
```

The CI pipeline (`winpeek-quality-block`) enforces these same checks on every MR. If docs don't pass, the MR is blocked.
