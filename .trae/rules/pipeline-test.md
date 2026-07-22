# Pipeline: Test — test-driven-development

## When to Use
- Writing tests for new features
- Fixing bugs (use Prove-It pattern)

## Process: New Feature

1. **Write tests** that describe expected behavior (must FAIL)
2. **Implement code** to make them pass
3. **Refactor** while keeping tests green

## Process: Bug Fix (Prove-It)

1. **Write test** that reproduces the bug (must FAIL)
2. **Confirm** test fails
3. **Implement fix**
4. **Confirm** test passes
5. **Run full suite** for regressions

## Browser Issues
For browser-related issues, also use `browser-testing-with-devtools` skill.
