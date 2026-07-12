---
sidebar_label: "Develop WinPeek Features"
title: "Develop a WinPeek Feature"
description: "Step-by-step guide to adding a new feature to WinPeek — where code goes, how to register tools, write docs, and pass quality checks"
---

# Develop a WinPeek Feature

This guide walks through adding a feature to WinPeek. Follow the same pattern for every feature regardless of complexity.

WinPeek has three module types. Pick the one that matches what you're building:

| If you're adding… | Module type | Backend location |
|-------------------|-------------|-----------------|
| A new desktop automation platform (e.g. Douyin) | **Automation platform** | `plugins/winpeek_rpa/platforms/{name}/` |
| A feature to the messaging system (e.g. file transfer) | **MIM feature** | `gateway/winpeek_hub/` |
| A computer management tool (e.g. process monitor) | **Assets feature** | `plugins/winpeek_rpa/shared/{name}.py` |

## Before You Start

Read the [WinPeek architecture](../developer-guide/winpeek.md) for the big picture — three modules, where each lives, how they relate.

Run `python scripts/winpeek-quality-check.py` to confirm your environment is set up. The CI pipeline blocks MRs that don't pass.

## Step 1: Pick your module and create the backend directory

### Automation platform

```bash
mkdir plugins/winpeek_rpa/platforms/{name}/
touch plugins/winpeek_rpa/platforms/{name}/__init__.py
```

Copy the structure from `wechat/` — the most complete reference:

```
platforms/{name}/
├── README.md      # Requirements + technical design for this platform
├── __init__.py
├── uia.py         # UIA driver: window detection, nav, click, type
├── db.py          # Data storage (SQLite by default)
├── api.py         # Eyes/Hands/Engine 3-layer orchestrator
├── collect.py     # Content collector
└── analyze.py     # AI analysis (jieba + LLM, if applicable)
```

### MIM feature

Files go into `gateway/winpeek_hub/`. Read the existing files first — `identity.py` for identity patterns, `mqtt_adapter.py` for MQTT patterns.

### Assets feature

Create one Python module per sub-feature in `plugins/winpeek_rpa/shared/`:

```bash
touch plugins/winpeek_rpa/shared/{name}.py
```

## Step 2: Register Hermes tools

All WinPeek tools go into one file: `tools/winpeek_tools.py`.

```python
# Add at the bottom of tools/winpeek_tools.py

registry.register(
    name="winpeek_{platform}_{action}",
    toolset="winpeek_rpa",
    schema={
        "name": "winpeek_{platform}_{action}",
        "description": "What this tool does — be specific, the LLM reads this",
        "parameters": {
            "type": "object",
            "properties": {
                "param1": {
                    "type": "string",
                    "description": "What param1 is",
                },
            },
            "required": ["param1"],
        },
    },
    handler=lambda args, **kw: _handle_{action}(args),
    check_fn=lambda: True,  # Or gate on available software
    requires_env=[],
    description="One-line description for /tools listing",
)
```

Rules:
- Name: `winpeek_{module}_{action}` (e.g. `winpeek_douyin_publish`, `winpeek_mim_send`, `winpeek_scan_software`)
- Handler: signature `def handler(args: dict, **kwargs) -> str`. Always return JSON string. Never raise.
- Schema: put real instructions in `description` — the LLM reads it to decide whether to call this tool.

Reference: `tools/winpeek_tools.py` (232 lines, 4 existing tools)

## Step 3: Write the Agent skill

Agent operational knowledge goes in `skills/`:

```bash
mkdir -p skills/{name}-automation/
touch skills/{name}-automation/SKILL.md
```

```markdown
---
name: {name}-automation
description: Operating rules for {name} desktop automation
---

# {Name} Automation Rules

## When to use
- Trigger words: "publish to {name}", "check {name} analytics"

## How to operate
1. Tool: winpeek_{name}_publish
2. Wait for confirmation before publishing
3. Never publish without user review
```

The agent loads this when a user mentions the platform. No manual registration needed.

## Step 4: Add the frontend panel

### Automation platform

Add a panel component and register it in the platform switcher:

```tsx
// apps/desktop/src/app/winpeek/automation/index.tsx

// 1. Import your panel
import { DouyinPanel } from './douyin'

// 2. Add it to the PLATFORMS list (already defined)
// 3. The tab bar renders automatically

function DouyinPanel() {
  return <div>Douyin automation — coming soon</div>
}
```

### MIM feature

Add to `apps/desktop/src/app/winpeek/mim/index.tsx`.

### Assets feature

Add a tab in `apps/desktop/src/app/winpeek/assets/index.tsx`:

```tsx
const TABS = [
  { key: 'software', label: 'Software' },
  { key: 'disk', label: 'Disk' },
  { key: 'files', label: 'Files' },
  { key: 'hardware', label: 'Hardware' },
  { key: 'processes', label: 'Processes' },
  { key: '{new}', label: '{New Feature}' },   // ← Add here
]
```

## Step 5: Write documentation

### Module README

Every backend directory gets a README.md with requirements + design:

```
plugins/winpeek_rpa/platforms/{name}/README.md
gateway/winpeek_hub/README.md (update existing)
plugins/winpeek_rpa/shared/README.md (create for assets backends)
```

Template:

```markdown
# {Feature Name}

## Requirements

| Feature | Priority | Status |
|---------|----------|--------|
| ... | P0 | 🆕 |

## Technical Design

### Architecture

(ASCII diagram)

### Database

(Schema if applicable)

### Key Files

| File | Purpose |
|------|---------|
| ... | ... |
```

### User Guide

Create one file in the matching section:

| Feature type | Document location |
|-------------|-------------------|
| Automation platform | `website/docs/user-guide/features/automation-{name}.md` |
| MIM feature | `website/docs/user-guide/features/mim-chat.md` (update existing) |
| Assets feature | `website/docs/user-guide/features/assets.md` (update existing) |

Template:

```markdown
---
sidebar_position: N
title: "Feature Name"
description: "One-line description"
---

# Feature Name

What it does. Who it's for.

## Quick Start

```bash
# One command to get started
```

## Features

### Feature 1

...

## Related

- [Architecture](../developer-guide/winpeek.md)
```

### Register in sidebar

Add the new page to `website/sidebars.ts`. Find the WinPeek section and add a line:

```typescript
'user-guide/features/automation-{name}',
```

## Step 6: Run quality checks

Before committing:

```bash
python scripts/winpeek-quality-check.py
```

This checks: TypeScript, CSS tokens, Python ruff, frontmatter, file naming, dead links.

All 6 must pass. The CI pipeline (`winpeek-quality-block`) will reject your MR if any fail.

## Step 7: Commit

```bash
git checkout -b feature/{name}
git add .
git commit -m "feat(tools): add {name} platform/feature

- Backend: {file paths}
- Tools: winpeek_{name}_*
- Frontend: {panel/tab added}
- Docs: {doc file}

evidence: none

Co-Authored-By: Claude <noreply@anthropic.com>"
git push local feature/{name}
```

Create MR → DEV. CI will run automatically. Merge when approved.

## Complete Feature Checklist

- [ ] Backend directory created with `README.md`
- [ ] Hermes tools registered in `tools/winpeek_tools.py`
- [ ] Agent skill written in `skills/{name}-*/SKILL.md`
- [ ] Frontend panel added
- [ ] User guide written in `website/docs/`
- [ ] Sidebar updated in `website/sidebars.ts`
- [ ] `python scripts/winpeek-quality-check.py` passes
- [ ] MR created with conventional commit message
