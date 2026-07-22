# Security Checklist

> Comprehensive security review checklist for all code changes.

## Threat Modeling

- [ ] What trust boundaries does this change cross?
- [ ] What's the worst outcome if this code is exploited?
- [ ] Are there privilege escalation paths?
- [ ] Is sensitive data exposed in logs, errors, or responses?

## Pre-Commit Checks

- [ ] No secrets committed (API keys, tokens, passwords)
- [ ] `.env` files and credentials in `.gitignore`
- [ ] No hardcoded URLs pointing to production
- [ ] Dependency diffs reviewed for known vulnerabilities

## Authentication

- [ ] All authenticated endpoints enforce auth middleware
- [ ] Session tokens are properly validated and expire
- [ ] Password changes invalidate existing sessions
- [ ] Rate limiting on login endpoints

## Authorization

- [ ] Principle of least privilege enforced
- [ ] Role/permission checks on every protected action
- [ ] No IDOR (Insecure Direct Object Reference) — verify ownership
- [ ] Admin-only actions gated behind admin role check

## Input Validation

- [ ] All user input validated (type, length, format, range)
- [ ] SQL/NoSQL injection prevention (parameterized queries)
- [ ] No eval() or dynamic code execution from user input
- [ ] File upload size, type, and content validated
- [ ] Path traversal prevented

## Security Headers

- [ ] Content-Security-Policy (CSP)
- [ ] X-Content-Type-Options: nosniff
- [ ] X-Frame-Options: DENY or SAMEORIGIN
- [ ] Strict-Transport-Security (HSTS)
- [ ] Referrer-Policy

## CORS

- [ ] Origin whitelist — no wildcard in production
- [ ] Credentials flag only when needed
- [ ] Preflight cache duration appropriate

## Data Protection

- [ ] Sensitive data encrypted at rest and in transit
- [ ] PII masked in logs and error messages
- [ ] Data retention/deletion policies followed
- [ ] Secrets managed via vault/secret store (not code)

## Dependency Security

- [ ] `npm audit` / `snyk test` / equivalent passes
- [ ] No pinned vulnerable versions
- [ ] Transitive dependencies reviewed for supply-chain risk

## AI / LLM Security

- [ ] Prompt injection mitigations in place
- [ ] Output validation before executing LLM-generated code
- [ ] No sensitive data sent to external LLM APIs
- [ ] Rate limiting on LLM endpoint calls

## Error Handling

- [ ] No stack traces exposed to users
- [ ] Error messages don't leak internal state
- [ ] Unhandled rejections caught globally

## OWASP Top 10 Quick Reference

| # | Category | Key Check |
|---|----------|-----------|
| A01 | Broken Access Control | Verify every endpoint |
| A02 | Cryptographic Failures | Use modern algorithms |
| A03 | Injection | Parameterize all queries |
| A04 | Insecure Design | Threat model at design time |
| A05 | Security Misconfiguration | Harden defaults |
| A06 | Vulnerable Components | Keep deps updated |
| A07 | Auth Failures | MFA, rate limiting |
| A08 | Data Integrity Failures | Verify supply chain |
| A09 | Logging Failures | Audit trails |
| A10 | SSRF | Validate URLs |

## Hermes Addition

- [ ] Security findings documented in ZenTao as bugs or tasks
