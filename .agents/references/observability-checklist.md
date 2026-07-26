# Observability Checklist

> Production observability practices for reliable operations.

## On-Call Questions

Before shipping, ask: if this breaks at 3 AM, can I answer these?

- [ ] Is the failure mode obvious from logs?
- [ ] Are there metrics that will show degradation?
- [ ] Is there a dashboard for this service?
- [ ] Does an alert exist for the failure scenario?
- [ ] Can I trace a request from entry to exit?

## Structured Logging

- [ ] Logs are JSON-structured with consistent fields
- [ ] Every log entry has: `timestamp`, `level`, `service`, `trace_id`, `message`
- [ ] Log levels used correctly: DEBUG (dev), INFO (normal), WARN (anomaly), ERROR (failure)
- [ ] No sensitive data in logs
- [ ] Request-scoped context propagated (trace ID, user ID, correlation ID)

## Metrics (RED / USE)

| Pattern | Focus | Examples |
|---------|-------|---------|
| **RED** | For services | Rate, Errors, Duration |
| **USE** | For resources | Utilization, Saturation, Errors |

- [ ] Request rate (requests/sec) per endpoint
- [ ] Error rate (5xx, 4xx) per endpoint
- [ ] Latency percentiles (p50, p95, p99)
- [ ] CPU / Memory / Disk utilization
- [ ] Database connection pool saturation
- [ ] Queue depth (if async processing)

## Distributed Tracing

- [ ] Trace context propagated across service boundaries
- [ ] Spans for: HTTP requests, database queries, external API calls, background jobs
- [ ] Sampling strategy defined (head-based, tail-based, or rate-based)
- [ ] Trace ID included in log entries

## Alerting

- [ ] Alerts are actionable — every alert requires a clear response
- [ ] No alert fatigue — tune thresholds to reduce noise
- [ ] Critical alerts have runbook links
- [ ] Alert severity defined: P0 (down), P1 (degraded), P2 (warning)
- [ ] Alert on symptoms, not causes (e.g., error rate, not CPU)

## Dashboards

- [ ] Service-level dashboard: RED metrics + key business metrics
- [ ] Infrastructure dashboard: USE metrics
- [ ] Dashboard annotated with deployments for correlation
- [ ] Time range selector and auto-refresh configured

## Verification

```bash
# Check service health
curl -s <service>/health | jq .

# Manual trace injection
curl -H "x-trace-id: manual-test-$(date +%s)" <endpoint>

# Check log stream
tail -f /var/log/<service>.json | jq 'select(.level == "ERROR")'
```

## Pre-Release Gates

- [ ] Health check endpoint exists and returns correct status
- [ ] Metrics endpoint exposed for Prometheus/OpenTelemetry
- [ ] Logs visible in centralized logging system
- [ ] Dashboard updated for new endpoints/workflows
- [ ] Alert rules created for critical failure modes

## Hermes Addition

- [ ] MIM alert channel configured for critical metrics
