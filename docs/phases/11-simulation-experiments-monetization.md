# Phase 11 — Simulation, Experiments, and Monetization

## Goal

Deliver headless scale simulation, automated balance gates, deterministic experiments, governed measurement, ads, offers, purchases, and subscriptions.

## Entry

Phase 10 is accepted.

## Tasks

- [ ] **P11-T01 — Build simulation specification.** Define pinned inputs, synthetic profiles, strategies, session/network behavior, metrics, seed sets, artifacts, cache digest, and budgets. Evidence: schema and reproducibility tests.
- [ ] **P11-T02 — Build simulation runner.** Execute production runtime on simulation ECS/Celery, checkpoint Spot jobs, aggregate results, store R2 artifacts, and report resource use. Depends on P11-T01, P10-T03. Evidence: interrupted-run recovery.
- [ ] **P11-T03 — Implement balance assertions.** Evaluate ranges, cohorts, percentiles, sample sizes, severities, confidence intervals, effect sizes, and publication blocking. Depends on P11-T02, P08-T03. Evidence: pass/warn/fail fixtures.
- [ ] **P11-T04 — Implement experiments.** Build HMAC assignment, mutually exclusive layers, exposure, variants, guardrails, sample-ratio checks, stop rules, analysis plans, and decisions. Depends on P10-T05–T07. Evidence: deterministic assignment and SRM tests.
- [ ] **P11-T05 — Implement ads/offers.** Model placements, rewarded/interstitial outcomes, frequency caps, consent, offer targeting, price localization, kill switches, and analytics. Depends on P08-T07, P10-T05. Evidence: policy/state-machine tests.
- [ ] **P11-T06 — Complete purchase/subscription flows.** Connect store product catalog, receipt verification, pending/complete/refund/chargeback, entitlement expiry, reconciliation, and support. Depends on P06-T05, P10-T03. Evidence: store sandbox E2E.
- [ ] **P11-T07 — Build balance/exploit corpus.** Simulate required player profiles, progression targets, exchange cycles, claim loops, offline abuse, paywall detection, and state growth. Depends on P11-T02–T06. Evidence: signed corpus report.
- [ ] **P11-T08 — Gate publishing on evidence.** Require simulation, balance, experiment compatibility, monetization safety, data quality, and cost budgets in release report. Depends on P11-T03–T07. Evidence: blocked and successful release scenarios.

## Exit gate

Repeated simulations match digests, balance assertions control publication, experiment assignment/exposure is trustworthy, and complete monetization lifecycles reconcile with ledgers and entitlements.

## AI execution contract

Follow [AI Phase Execution Protocol](AI-EXECUTION-PROTOCOL.md). Read Phase 10 handoff plus simulation/analytics, publishing, economy, save, security, and operations contracts.

### Exact outputs

Simulation specification/strategy/runner/metrics/assertion packages; Celery workflow and simulation ECS Terraform; R2 result manifest; experiment assignment/exposure/analysis domains; monetization catalog/offer/ad/purchase/subscription domains; API schemas/routes; analytics dashboards; Studio view models; and seeded defect fixtures.

A run is addressed by engine/schema/definition/module digests, strategy version, seeds, schedule, duration, network/payment/ad behavior, and metrics. Store specification, environment, aggregate Parquet, sampled trace, assertions, runtime/cost, and digest. Repeated specifications return stored results unless force recompute is authorized. Spot termination resumes without duplicate samples.

Assignment uses HMAC-SHA256 with a stored secret version and persists before exposure. Implement exclusive layers, eligibility snapshot, bucket, exposure, guardrails, sample ratio, stop, close, and decision. Offers and ads use bounded fields. Purchases use provider transaction idempotency and ledger/entitlement services only.

### Required benchmarks

Exercise all profiles and required milestone, economy, difficulty, quest, session, ad, offer, paywall, state-size, and runtime metrics. Seed progression-fast/slow, profitable-loop, impossible-node, excessive-ad, weak-sink, overflow, and purchase-duplication defects; assertions must catch each. Test experiment key rotation/rebucketing, sample-ratio mismatch, late exposure, overlapping layers, refunds, renewals, chargebacks, kill switch, and provider outage.

### Handoff to Phase 12

Provide Studio OpenAPI/view models, run status, artifact digests, assertion/experiment state machines, saved analytics queries, monetization catalog/bounds, dashboards, and kill-switch operations.
