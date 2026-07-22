# Pipeline: Build — incremental-implementation + TDD

## When to Use
- Have a plan (tasks/todo.md), need to implement code

## Modes

- `pipeline:build` — implement the **next pending task** only
- `pipeline:build:auto` — execute **every task** in dependency order after one approval

## Process (per task)

1. **Pick next pending task** from `tasks/todo.md`
2. **Read acceptance criteria**
3. **Load relevant context** (existing code, patterns, types)
4. **RED** — Write a failing test for expected behavior
5. **GREEN** — Implement minimum code to pass
6. **Regression** — Run full test suite
7. **Build** — Verify compilation
8. **Commit** — Descriptive message, one commit per task
9. **Mark task complete** and stop (single mode) or continue (auto mode)

## Risk Gates (auto mode)

Stop and ask user when:
- Test can't pass / build breaks without obvious fix → use `debugging-and-error-recovery`
- Spec is ambiguous / decision needed
- Task is high-risk: auth, payments, data migrations, secrets, deploys → use `doubt-driven-development`
