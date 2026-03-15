# Latency-Only Focus (MVP)

If you want to build this the right way, our focus is **latency and latency only**.

## One-line direction
**Every technical and business decision must improve or protect end-to-end latency.**

## What this means in practice
- Choose only strategies that are latency-sensitive.
- Reject features that do not reduce reaction time, execution delay, or tail latency.
- Optimize for p99/p999 latency, not just average latency.
- Keep the architecture minimal: fewer network hops, fewer services, fewer abstractions.
- Co-locate trading systems as close to venue infrastructure as possible.

## Latency-first priorities
1. **Market data path**: fastest possible feed handling and timestamping.
2. **Decision path**: lock-free / low-allocation strategy runtime.
3. **Execution path**: minimal order routing overhead and deterministic state machine.
4. **Infrastructure**: CPU pinning, kernel/network tuning, precise clock sync.
5. **Observability**: always-on latency telemetry for tick-to-trade and order ack timings.

## Non-goals for this MVP
- Rich dashboards and non-critical UX work.
- Multi-venue expansion before single-venue latency targets are met.
- Complex platform features that add overhead without latency gains.

## Success criteria
- Track and improve p50/p95/p99/p999 for:
  - market-data-ingest -> strategy decision
  - strategy decision -> order sent
  - order sent -> exchange ack
- Run regular latency regression tests and fail releases that degrade targets.
