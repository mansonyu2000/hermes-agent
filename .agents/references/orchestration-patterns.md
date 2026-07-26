# Orchestration Patterns

> Agent orchestration patterns for multi-agent workflows.

## Endorsed Patterns

### Direct Invocation
```
Agent → Tool → Result
```
- Simplest pattern; one agent calls a tool directly
- Use when the task is self-contained and no delegation needed

### Single-Persona Slash Command
```
User → Slash Command → Persona Handler → Result
```
- User triggers a specific persona via `/persona-name`
- Persona executes within its domain expertise
- Use for well-scoped, domain-specific tasks

### Parallel Fan-Out + Merge
```
          ┌→ Sub-agent A ─┐
User → Agent ┼→ Sub-agent B ┼→ Merge → Result
          └→ Sub-agent C ─┘
```
- Parent agent delegates independent sub-tasks in parallel
- Merge step combines results
- Use for tasks with clear independent sub-work items

### User-Driven Sequential Pipeline
```
User → Stage 1 → review → Stage 2 → review → Stage 3 → Done
```
- User reviews output at each stage before proceeding
- Stages: spec → plan → build → test → review → ship
- Use when each stage depends on previous output and needs human validation

### Research Isolation
```
Agent → Research Agent (sandboxed) → Results → Main Agent
```
- Research sub-agent runs in isolated context with web access
- Results returned to main agent for integration
- Use when task requires web research without contaminating main context

## Anti-Patterns

- ❌ **Router Persona** — A persona that only routes to other personas; use direct invocation instead
- ❌ **Persona Calling Persona** — Persona delegates to another persona; creates unnecessary depth
- ❌ **Transpiled Sequential Orchestrator** — Simulating sequential execution within a single parallel round
- ❌ **Deep Persona Trees** — More than 2 levels of persona hierarchy; leads to context loss and confusion

## Decision Flow

```
Is the task self-contained?
  ├─ Yes → Direct Invocation
  └─ No → Can it be split into independent sub-tasks?
       ├─ Yes → Parallel Fan-Out + Merge
       └─ No → Does each stage need human review?
            ├─ Yes → User-Driven Sequential Pipeline
            └─ No → Use minimal orchestration needed
```

## Hermes Addition

- MIM notification follows the Parallel Fan-Out pattern: the agent sends a notification via `winpeek_mim_send` as a sub-task running concurrently with the main workflow
- MIM notifications should include trace IDs for correlation with ZenTao artifacts
