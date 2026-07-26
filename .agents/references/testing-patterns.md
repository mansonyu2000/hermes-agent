# Testing Patterns Reference

> Cross-stack patterns for writing reliable, maintainable tests.

## Test Structure (AAA)

```
// Arrange — set up inputs, mocks, and preconditions
// Act     — execute the behavior under test
// Assert — verify the result matches expectations
```

- One `describe` block per unit/feature
- One `it` block per behavior
- Avoid multiple logical assertions in one test

## Naming Conventions

```
describe('ClassName')
  it('should [expected behavior] when [condition/scenario]')

describe('POST /api/tasks')
  it('should return 201 when payload is valid')
  it('should return 400 when title is missing')
```

## Common Assertions

| Assertion | Use Case |
|-----------|----------|
| `toEqual` / `toStrictEqual` | Deep equality |
| `toBe` | Primitive/reference identity |
| `toMatchObject` | Partial object match |
| `toThrow` / `toThrowError` | Expected exceptions |
| `toHaveBeenCalledWith` | Mock call verification |
| `toBeWithin` | Floating-point range checks |

## Mock Patterns

- Mock at the boundary, not internals
- Use dependency injection to make mocks seamless
- Prefer fake objects over mocks for simple dependencies
- Always verify mock expectations (assert on calls made)
- Reset mocks between tests to avoid leakage

## React / Component Testing

- Test behavior, not implementation
- Use `screen.getByRole` for accessibility-aware queries
- Prefer `userEvent` over `fireEvent` (simulates real interaction)
- Test loading, empty, error, and edge-case states
- Avoid testing internal state directly; test rendered output

## API / Integration Testing

- Use real HTTP requests against a test server instance
- Clean up test data between runs
- Test authentication/authorization paths
- Validate response structure, not just status codes
- Include negative tests (invalid input, missing auth, etc.)

## E2E Testing

- Focus on critical user journeys (login, purchase, etc.)
- Keep tests independent — no shared state
- Use data-testid sparingly (prefer semantic queries)
- Run against a dedicated test environment

## Anti-Patterns

- ❌ Testing implementation details
- ❌ Flaky tests (time-dependent, order-dependent)
- ❌ Over-mocking (testing the mock, not the code)
- ❌ Giant test files — split by domain
- ❌ Skipped tests without a reason/ticket

## Hermes Addition

- When testing MIM notification flows, use `winpeek_mim_send` mock to verify message delivery
- Ensure test teardown cleans any test MIM messages sent
