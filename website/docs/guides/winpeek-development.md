---
sidebar_label: "Develop WinPeek Features"
title: "Develop a WinPeek Feature"
description: "How to add features to WinPeek — module types, code locations, and development workflow"
---

# Develop a WinPeek Feature

WinPeek extends Hermes Agent with three independent modules. This page tells you what they are, where their code lives, and how to start building.

## What We're Building

| Module | What it does | Type |
|--------|-------------|------|
| **Automation** | Desktop app control via Windows UIA. Multi-platform: WeChat CRM (production), Douyin, Kuaishou, Bilibili, Xiaohongshu, Shipinhao (stubs). | Hermes plugin |
| **MIM** | Real-time messaging between Hermes agents over MQTT. Identity, single/group chat, agent discovery. | Gateway extension |
| **Assets** | Computer management dashboard. Software scanner, disk usage, file browser, hardware info, process manager. | Hermes tools |

Each module is independent. They share zero code.

## Where Code Lives

| Layer | Automation | MIM | Assets |
|-------|-----------|-----|--------|
| Backend | `plugins/winpeek_rpa/platforms/{name}/` | `gateway/winpeek_hub/` | `plugins/winpeek_rpa/shared/{name}.py` |
| Tools | `tools/winpeek_tools.py` | same file | same file |
| Skills | `skills/{name}-*/SKILL.md` | `skills/mim-guidelines/SKILL.md` | `skills/software-assets/` |
| Frontend | `apps/desktop/.../winpeek/{name}/` | `apps/desktop/.../winpeek/mim/` | `apps/desktop/.../winpeek/assets/` |
| Docs | `user-guide/features/automation-{name}.md` | `user-guide/features/mim-chat.md` | `user-guide/features/assets.md` |

## How to Enter Development

Each module has its own README containing requirements and technical design. Start there:

- **Automation** → `plugins/winpeek_rpa/README.md`
- **MIM** → `gateway/winpeek_hub/README.md`
- **Assets** → `plugins/winpeek_rpa/shared/README.md` (create if missing)

Then read the architecture overview: [WinPeek Architecture](../developer-guide/winpeek.md).

## Development Workflow

1. **Read the module README** — understand requirements and current state
2. **Check existing code** — `search_graph` in codebase-memory for the module you're touching
3. **Write backend** — code in `plugins/` or `gateway/`
4. **Register tools** — `tools/winpeek_tools.py` using `registry.register()`. Follow Hermes [Adding Tools](../developer-guide/adding-tools.md) conventions
5. **Write skill** — Agent operational knowledge in `skills/`. Follow Hermes [Creating Skills](../developer-guide/creating-skills.md) conventions
6. **Build frontend** — React component in `apps/desktop/.../winpeek/`
7. **Write docs** — user guide in `website/docs/user-guide/features/`. Every `.md` needs `sidebar_position` + `title` frontmatter
8. **Add to sidebar** — `website/sidebars.ts`
9. **Run quality checks** — `python scripts/winpeek-quality-check.py`. All 6 must pass
10. **Commit and push** — conventional commits with Hermes scopes (`tools`, `gateway`, `skills`, `docs`)

## Conventions

Follow Hermes upstream, not our own:

- **Commit scope**: use Hermes scopes (`tools`, `gateway`, `skills`, `agent`, `docs`). Don't invent `winpeek` scope.
- **Branch naming**: `feat/description`, `fix/description`. Not `DEV`.
- **Skill format**: YAML frontmatter (`name`, `description`, `metadata`). Same as Hermes bundled skills.
- **Tool registration**: `registry.register()` with `schema`, `handler`, `check_fn`. Same as Hermes built-in tools.
- **Docs frontmatter**: `sidebar_position`, `title`, `description`. Same as all Hermes Docusaurus pages.
- **Docs location**: files go into Hermes standard categories (`user-guide/features/`, `developer-guide/`, `guides/`, `getting-started/`). No standalone `winpeek/` directory.

## Quality Gate

Every MR runs `scripts/winpeek-quality-check.py`:

| Check | What it catches |
|-------|----------------|
| TypeScript | Type errors |
| CSS tokens | Hard-coded colors |
| Python ruff | Missing encoding, bare except |
| Frontmatter | Missing `sidebar_position` / `title` |
| File naming | Uppercase letters in URL paths |
| Dead links | Broken relative `.md` references |

CI blocks merge on failure. Run it locally before pushing.

## Related

- [WinPeek Architecture](../developer-guide/winpeek.md)
- [Build a Hermes Plugin](build-a-hermes-plugin.md) — upstream reference
- [Adding Tools](../developer-guide/adding-tools.md) — Hermes tool registration
- [Creating Skills](../developer-guide/creating-skills.md) — Agent skill conventions
