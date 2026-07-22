# Pipeline: Review — code-review-and-quality

## When to Use
- Before merging any change
- Staged changes or recent commits exist

## Process: Five-Axis Review

1. **Correctness** — Matches spec? Edge cases? Tests adequate?
2. **Readability** — Clear names? Straightforward logic? Organized?
3. **Architecture** — Follows patterns? Clean boundaries? Right abstraction?
4. **Security** — Input validated? Secrets safe? Auth checked? (use `security-and-hardening`)
5. **Performance** — N+1 queries? Unbounded ops? (use `performance-optimization`)

## Severity Labels

- **Critical** — Blocks merge, must fix
- **Important** — Should fix before merge
- **Suggestion** — Consider for future

## Output
Structured review with `file:line` references and fix recommendations.
