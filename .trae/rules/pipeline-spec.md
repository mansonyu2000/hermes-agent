# Pipeline: Spec — spec-driven-development

## When to Use
- Starting a new project or feature
- Requirements are ambiguous or incomplete
- Change touches multiple files or modules
- About to make an architectural decision
- Task takes more than 30 minutes

**NOT for:** single-line fixes, typo corrections, unambiguous changes.

## Process

1. **Read the project rules** (CLAUDE.md, .trae/rules/) for project conventions
2. **Ask clarifying questions** about:
   - Objective and target users
   - Core features and acceptance criteria
   - Tech stack preferences and constraints
   - Boundaries (what to always do, ask first, never do)
3. **Generate structured spec** covering:
   - Objective — what and why
   - Commands — build/test/lint/run
   - Project structure — directory meaning
   - Code style — conventions
   - Testing strategy — what and how to test
   - Boundaries — always do / ask first / never do
4. **Save as SPEC.md** in project root
5. **Get user approval** before proceeding to next stage
