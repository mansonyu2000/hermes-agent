# Pipeline: Ship — shipping-and-launch with parallel fan-out

## When to Use
- Ready to deploy, need final sign-off
- Change is production-bound

**Skip fan-out only if:** ≤2 files, ≤50 lines diff, and doesn't touch auth/payments/data/config.

## Phase A — Parallel Fan-Out

Spawn **3 subagents concurrently** using Task tool (general_purpose_task):

1. **code-reviewer** — Five-axis review of staged changes
2. **security-auditor** — OWASP audit: secrets, auth/authz, dependency CVEs
3. **test-engineer** — Coverage analysis: happy path, edge cases, error paths

## Phase B — Merge in Main Context

Synthesize all reports:

1. **Code Quality** — Aggregate Critical/Important findings
2. **Security** — Promote any Critical findings to launch blockers
3. **Performance** — Cross-check with code-reviewer's performance axis
4. **Accessibility** — Keyboard nav, screen reader, contrast
5. **Infrastructure** — Env vars, migrations, monitoring, feature flags
6. **Documentation** — README, ADRs, changelog

## Phase C — Decision

```markdown
## Ship Decision: GO | NO-GO

### Blockers (must fix before ship)
### Recommended fixes (should fix before ship)
### Acknowledged risks (shipping anyway)
### Rollback plan
- Trigger conditions:
- Rollback procedure:
- RTO:
```

**Critical finding → default NO-GO** unless user explicitly accepts risk.
