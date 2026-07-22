# Pipeline: Session Start

This rule loads at session start. It activates the meta-skill discovery system and declares the available pipeline stages.

## Activated Skill

`using-agent-skills` — Skill discovery flowchart (`.agents/skills/using-agent-skills/SKILL.md`)

Read it now. It is the single entry point for deciding which skill applies to any task.

## Available Pipeline Stages

Throughout this session, invoke pipeline stages by name. Each stage reads the **original SKILL.md** from `.agents/skills/<name>/SKILL.md`:

| Stage | Source skill | Read |
|-------|-------------|------|
| `pipeline:spec` | `.agents/skills/spec-driven-development/SKILL.md` | Full spec workflow |
| `pipeline:plan` | `.agents/skills/planning-and-task-breakdown/SKILL.md` | Dependency graph + vertical slices |
| `pipeline:build` | `.agents/skills/incremental-implementation/SKILL.md` (+ TDD) | RED→GREEN→REFACTOR per task |
| `pipeline:build:auto` | Same, but execute every task after one approval | Autonomous mode |
| `pipeline:test` | `.agents/skills/test-driven-development/SKILL.md` | Failing test first |
| `pipeline:review` | `.agents/skills/code-review-and-quality/SKILL.md` | Five-axis review |
| `pipeline:code-simplify` | `.agents/skills/code-simplification/SKILL.md` | Preserve behavior, reduce complexity |
| `pipeline:ship` | `.agents/skills/shipping-and-launch/SKILL.md` | Parallel fan-out + go/no-go |

**When a pipeline stage is requested, read the full SKILL.md before executing.** Do not skip steps, Common Rationalizations, Red Flags, or Verification checklists.

## Hermes Integration

On top of the standard skills, apply Hermes-specific tooling:

- **ZenTao CLI** — Sync artifacts to pm.test.com (story/task/bug/release)
- **MIM** — Notify collaborators via Agent messaging (`winpeek_mim_send`)
- **Peeka Router** — Incoming message classification + auto-reply

See `website/docs/winpeek/mim-design/hermes-workflow-skill.md` for full Hermes integration reference.
