# Pipeline: Plan — planning-and-task-breakdown

## When to Use
- After SPEC.md exists, need to decompose into tasks
- Have a clear scope, need execution order

## Process

1. **Read SPEC.md** and relevant codebase sections
2. **Enter plan mode** — read only, no code changes
3. **Identify dependency graph** between components
4. **Slice work vertically** — one complete path per task (not horizontal layers like "all DB work first")
5. **Write tasks with**:
   - Acceptance criteria
   - Verification steps
   - Dependencies
6. **Add checkpoints** between phases
7. **Present plan** for human review

## Output Files
- `tasks/plan.md` — Full plan with dependency graph
- `tasks/todo.md` — Ordered task list with status markers
