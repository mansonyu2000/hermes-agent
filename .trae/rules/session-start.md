# Pipeline: Session Start

This rule loads at session start. It activates the meta-skill discovery system and declares the complete three-layer architecture: **Pipeline Rules → Skills → Personas & References**.

## Activated Meta-Skill

`using-agent-skills` — Skill discovery flowchart (`.agents/skills/using-agent-skills/SKILL.md`)

Read it now. It is the single entry point for deciding which skill applies to any task.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                   Pipeline Rules                      │
│           (.trae/rules/pipeline-*.md)                 │
│   The "when" layer — user-facing workflow entries     │
├─────────────────────────────────────────────────────┤
│                      Skills                            │
│           (.agents/skills/*/SKILL.md)                 │
│   The "how" layer — step-by-step process workflows    │
├─────────────────────────────────────────────────────┤
│     Personas              References                  │
│  (.agents/personas/)    (.agents/references/)         │
│   The "who" layer          The "what" layer           │
│   Reusable agents          Shared checklists          │
└─────────────────────────────────────────────────────┘
```

---

## Available Pipeline Stages

Throughout this session, invoke pipeline stages by name. Each stage reads from `.trae/rules/pipeline-<name>.md` as its entry point, which chains to the corresponding skill:

| Stage | Pipeline Rule | Source Skill(s) | Purpose |
|-------|---------------|-----------------|---------|
| `pipeline:spec` | [pipeline-spec.md](file:///c:/work/hermes/hermes-agent/.trae/rules/pipeline-spec.md) | `spec-driven-development` | Write structured specification |
| `pipeline:plan` | [pipeline-plan.md](file:///c:/work/hermes/hermes-agent/.trae/rules/pipeline-plan.md) | `planning-and-task-breakdown` | Break work into verifiable tasks |
| `pipeline:build` | [pipeline-build.md](file:///c:/work/hermes/hermes-agent/.trae/rules/pipeline-build.md) | `incremental-implementation` + TDD | Implement one task (RED→GREEN→REFACTOR) |
| `pipeline:build:auto` | Same as build | Same | Execute all tasks after one approval |
| `pipeline:test` | [pipeline-test.md](file:///c:/work/hermes/hermes-agent/.trae/rules/pipeline-test.md) | `test-driven-development` | Write failing tests first |
| `pipeline:review` | [pipeline-review.md](file:///c:/work/hermes/hermes-agent/.trae/rules/pipeline-review.md) | `code-review-and-quality` | Five-axis code review |
| `pipeline:code-simplify` | [pipeline-code-simplify.md](file:///c:/work/hermes/hermes-agent/.trae/rules/pipeline-code-simplify.md) | `code-simplification` | Reduce complexity, preserve behavior |
| `pipeline:ship` | [pipeline-ship.md](file:///c:/work/hermes/hermes-agent/.trae/rules/pipeline-ship.md) | `shipping-and-launch` | Parallel fan-out + go/no-go |
| `pipeline:webperf` | [pipeline-webperf.md](file:///c:/work/hermes/hermes-agent/.trae/rules/pipeline-webperf.md) | `web-performance-auditor` | Web performance audit |

**When a pipeline stage is requested:**
1. Read the corresponding `.trae/rules/pipeline-<name>.md` rule file
2. Follow its workflow — it will invoke the relevant skill(s)
3. Read the full `SKILL.md` before executing — do not skip steps, Common Rationalizations, Red Flags, or Verification checklists

---

## Personas (Reusable Agents)

Located in [`.agents/personas/`](file:///c:/work/hermes/hermes-agent/.agents/personas/):

| Persona | File | Purpose | Invoked By |
|---------|------|---------|------------|
| Code Reviewer | [code-reviewer.md](file:///c:/work/hermes/hermes-agent/.agents/personas/code-reviewer.md) | Five-axis code review | `pipeline:review`, `pipeline:ship` |
| Security Auditor | [security-auditor.md](file:///c:/work/hermes/hermes-agent/.agents/personas/security-auditor.md) | Vulnerability & threat model | `pipeline:ship` |
| Test Engineer | [test-engineer.md](file:///c:/work/hermes/hermes-agent/.agents/personas/test-engineer.md) | Test strategy & coverage analysis | `pipeline:ship` |
| Web Performance Auditor | [web-performance-auditor.md](file:///c:/work/hermes/hermes-agent/.agents/personas/web-performance-auditor.md) | Core Web Vitals & optimization | `pipeline:webperf` |

**Orchestration rules:**
- Only pipeline stages invoke personas — personas do not invoke other personas
- `pipeline:ship` uses parallel fan-out (code-reviewer + security-auditor + test-engineer concurrently)
- See [orchestration-patterns.md](file:///c:/work/hermes/hermes-agent/.agents/references/orchestration-patterns.md) for full patterns reference

---

## References (Shared Checklists)

Located in [`.agents/references/`](file:///c:/work/hermes/hermes-agent/.agents/references/):

| Checklist | File | Used By |
|-----------|------|---------|
| Definition of Done | [definition-of-done.md](file:///c:/work/hermes/hermes-agent/.agents/references/definition-of-done.md) | All skills — final gate |
| Testing Patterns | [testing-patterns.md](file:///c:/work/hermes/hermes-agent/.agents/references/testing-patterns.md) | `test-driven-development` |
| Security Checklist | [security-checklist.md](file:///c:/work/hermes/hermes-agent/.agents/references/security-checklist.md) | `security-and-hardening`, `code-review-and-quality` |
| Performance Checklist | [performance-checklist.md](file:///c:/work/hermes/hermes-agent/.agents/references/performance-checklist.md) | `performance-optimization`, `pipeline:webperf` |
| Accessibility Checklist | [accessibility-checklist.md](file:///c:/work/hermes/hermes-agent/.agents/references/accessibility-checklist.md) | `frontend-ui-engineering` |
| Observability Checklist | [observability-checklist.md](file:///c:/work/hermes/hermes-agent/.agents/references/observability-checklist.md) | `observability-and-instrumentation` |
| Orchestration Patterns | [orchestration-patterns.md](file:///c:/work/hermes/hermes-agent/.agents/references/orchestration-patterns.md) | `doubt-driven-development`, multi-agent workflows |

---

## Hermes Integration

On top of the standard agent-skills pipeline, apply Hermes-specific tooling throughout every stage:

### Tooling
- **ZenTao CLI** — Sync artifacts to pm.test.com (story/task/bug/release)
- **MIM** (`winpeek_mim_send`) — Notify collaborators via Agent messaging
- **Peeka Router** — Incoming message classification + auto-reply (see `website/docs/winpeek/mim-design/`)

### Stage-Specific Integration

| Stage | ZenTao Action | MIM Action |
|-------|---------------|------------|
| `pipeline:spec` | Create story | Notify PM on approval |
| `pipeline:plan` | Create tasks linked to story | Notify assignees |
| `pipeline:build` | Update task status per increment | Notify on task completion |
| `pipeline:test` | Link test results to task | Notify on regression pass/fail |
| `pipeline:review` | Create bugs for Critical findings | Notify author of review completion |
| `pipeline:ship` | Create release if GO | Notify team of release decision |
| `pipeline:code-simplify` | (optional) Task for major refactors | Notify if significant simplification |
| `pipeline:webperf` | Task for performance regressions | Share scorecard |

### Reference
See `website/docs/winpeek/mim-design/hermes-workflow-skill.md` for the full Hermes workflow and MIM protocol specification.
