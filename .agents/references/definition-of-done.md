# Definition of Done (DoD)

> Project-wide checklist for marking work as complete. Every item must be checked before a story/task is considered done.

## Correctness

- [ ] Code compiles/builds without errors
- [ ] All existing tests pass
- [ ] New code has appropriate test coverage (unit, integration, or E2E)
- [ ] Edge cases and error paths are handled
- [ ] No regression in existing functionality

## Quality

- [ ] Code follows project style guide and linting rules
- [ ] No dead code, commented-out code, or debug artifacts
- [ ] No hardcoded secrets, tokens, or environment-specific values
- [ ] Code is reviewed by at least one other person/agent
- [ ] Complexity is justified — no over-engineering

## Integration

- [ ] Changes merged to target branch with no conflicts
- [ ] CI/CD pipeline passes
- [ ] Dependent services/systems are compatible
- [ ] Database migrations (if any) are forward- and backward-compatible

## Documentation

- [ ] Public APIs have docstrings or type signatures
- [ ] README or relevant docs updated if behavior changed
- [ ] ADR created for significant architectural decisions
- [ ] Changelog entry added (if applicable)

## Release Readiness

- [ ] Feature flag properly configured (if gated)
- [ ] Monitoring/alerting covers the new code path
- [ ] Rollback plan exists
- [ ] Performance impact assessed
- [ ] Security implications reviewed
- [ ] **ZenTao story/task status updated to reflect completion**

## Red Flags

- ❌ "I'll fix it later" — fix it now or create a tracked task
- ❌ "It works on my machine" — verify in CI/staging
- ❌ Untested error paths — they _will_ fire in production
- ❌ Skipped tests — each skipped test needs a ticket
- ❌ Magic numbers or hardcoded strings without explanation
