# Pipeline: Session Start

This rule loads automatically at session start. It activates the meta-skill and declares available pipeline commands.

## Activated Skills

- `using-agent-skills` — Skill discovery flowchart (`.agents/skills/using-agent-skills/SKILL.md`)
- `hermes-workflow` — Hermes-specific MIM/ZenTao/DocManager integration

## Available Pipeline Commands

Throughout this session, you can invoke these pipeline stages:

| Command | Skill | Purpose |
|---------|-------|---------|
| `pipeline:spec` | spec-driven-development | Write a specification before coding |
| `pipeline:plan` | planning-and-task-breakdown | Break work into small verifiable tasks |
| `pipeline:build` | incremental-implementation + TDD | Implement one task at a time (RED→GREEN→REFACTOR) |
| `pipeline:build:auto` | full pipeline (plan+build) | Run the whole plan in one approved pass |
| `pipeline:test` | test-driven-development | Write failing test, implement, verify |
| `pipeline:review` | code-review-and-quality | Five-axis code review |
| `pipeline:code-simplify` | code-simplification | Simplify code without changing behavior |
| `pipeline:ship` | shipping-and-launch + fan-out | Pre-launch review → go/no-go decision |

## Pipeline Flow (Sequential)

```
pipeline:spec → pipeline:plan → pipeline:build → pipeline:test → pipeline:review → pipeline:ship
```

Each stage is user-initiated. The user runs the next command when ready.

## Parallel Fan-Out

`pipeline:ship` spawns 3 subagents in parallel (use Task tool):
1. `code-reviewer` (use general_purpose_task with code-review-and-quality)
2. `security-auditor` (use general_purpose_task with security-and-hardening)
3. `test-engineer` (use general_purpose_task with test-driven-development)

Then merge their reports into a go/no-go decision.
