# Pipeline: Code Simplify — code-simplification

## When to Use
- Code is too complex, nested, or duplicated
- Need to improve maintainability without changing behavior

## Process

1. **Read project conventions** (CLAUDE.md, .trae/rules/)
2. **Identify target** — recent changes or specified scope
3. **Understand before touching** — purpose, callers, edge cases, coverage
4. **Scan for opportunities**:
   - Deep nesting → guard clauses or extracted helpers
   - Long functions → split by responsibility
   - Nested ternaries → if/else or switch
   - Generic names → descriptive names
   - Duplicated logic → shared functions
   - Dead code → remove after confirming
5. **Apply incrementally** — run tests after each change
6. **Verify** — all tests pass, build succeeds, diff is clean

If tests fail after simplification → revert that change and reconsider.
