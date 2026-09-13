# Phase 00 Performance Baseline

Status: `accepted`

Phase 00 creates no runtime or infrastructure. The authoritative targets carried forward are:

| Target | Threshold | Source |
|---|---|---|
| Public API latency | p95 <= 250 ms; p99 <= 750 ms | `docs/00-product-charter.md#success-metrics` |
| Player/API availability | 99.95% monthly | `docs/18-observability-sre-disaster-recovery.md#slos` |
| Studio availability | 99.9% monthly | `docs/18-observability-sre-disaster-recovery.md#slos` |
| Realtime input | p99 <= 50 ms in-region | `docs/18-observability-sre-disaster-recovery.md#slos` |
| Regional recovery | RTO <= 4 hours; RPO <= 15 minutes | `docs/18-observability-sre-disaster-recovery.md#disaster-recovery` |

No performance claim is made from this documentation-only phase. Measurement begins in the documented later phases.
