# Performance Checklist

> Web and API performance optimization reference.

## Core Web Vitals Targets

| Metric | Good | Needs Work | Poor |
|--------|------|------------|------|
| LCP | ≤ 2.5s | 2.5–4.0s | > 4.0s |
| FID | ≤ 100ms | 100–300ms | > 300ms |
| CLS | ≤ 0.1 | 0.1–0.25 | > 0.25 |
| INP | ≤ 200ms | 200–500ms | > 500ms |
| TTFB | ≤ 800ms | 800–1800ms | > 1800ms |

## TTFB Diagnosis

- Measure TTFB: `curl -o /dev/null -s -w "TTFB: %{time_starttransfer}s\n" <url>`
- High TTFB usually indicates: slow server-side rendering, database queries, or CDN misconfiguration
- Optimize: CDN caching, server-side caching, query optimization, connection pooling

## Frontend Checklist

- [ ] Code splitting and lazy loading in place
- [ ] Images optimized (WebP/AVIF, responsive sizes, lazy loading)
- [ ] Bundle size monitored (use `vite-bundle-visualizer` or similar)
- [ ] Render-blocking resources minimized
- [ ] Long tasks (> 50ms) profiled and broken up
- [ ] Animations use `transform` and `opacity` only
- [ ] Font subsetting and `font-display: swap`

## Backend Checklist

- [ ] Database queries have appropriate indexes
- [ ] N+1 queries identified and batched
- [ ] Response pagination for list endpoints
- [ ] Caching strategy applied (Redis, CDN, HTTP cache headers)
- [ ] Connection pooling configured
- [ ] Payload size minimized (field selection, compression)
- [ ] Async processing for non-critical paths

## Measurement Commands

```bash
# Lighthouse CI
npx lighthouse <url> --view

# Bundle analysis
npx vite-bundle-visualizer

# API latency (with timing breakdown)
curl -w "\nTCP: %{time_connect}s\nTLS: %{time_appconnect}s\nTTFB: %{time_starttransfer}s\nTotal: %{time_total}s\n" <url>

# Database query profiling
EXPLAIN ANALYZE <query>;
```

## Common Anti-Patterns

- ❌ Premature optimization without profiling
- ❌ Over-fetching data (SELECT *)
- ❌ Waterfall requests (parallelize where possible)
- ❌ No caching for read-heavy endpoints
- ❌ Synchronous processing of async-eligible work
- ❌ Missing indexes on foreign keys

## Hermes Addition

- [ ] Performance regression task created in ZenTao if thresholds exceeded
