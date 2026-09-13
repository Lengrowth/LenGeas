# Simulation, Balance, Experiments, and Analytics

## Headless simulation

The simulator calls the same pure runtime and mechanics packages as production. A run specification pins definition digest, engine/package digests, save schema, seed set, synthetic cohort, strategy, duration, session schedule, spending/ad behavior, network behavior, and requested metrics.

Runs execute as Celery workflows on the simulation ECS capacity provider. Inputs, logs, aggregated results, sampled traces, and environment metadata are stored in R2. Identical specifications return the existing content-addressed result unless `force_recompute` is authorized.

## Synthetic profiles

v1 ships deterministic strategies for casual, regular, heavy, no-spend, rewarded-ad, purchaser, completionist, optimizer, churn-risk, offline-heavy, and adversarial players. Strategies select actions from visible state and declared goals; they do not read hidden future rewards.

## Required metrics

- time to first action, upgrade, unlock, content node, session end, and prestige;
- milestone percentiles and completion rate;
- resource faucet, sink, balance, inflation, and stranded-value curves;
- affordability, wait time, dead-end, and difficulty-wall detection;
- quest and achievement pacing;
- session count, duration, and return timing;
- ad opportunities and offer exposure without revenue prediction claims;
- purchase value distribution and paywall detection;
- action denial, overflow, timer backlog, and state-size growth;
- CPU time, memory, events, effects, and persisted bytes per simulated hour.

## Balance assertions

Definitions store measurable targets as ranges, cohort, percentile, sample size, and severity. A blocking assertion fails publication. A warning requires an approval comment. Baselines use digest-addressed simulation results; comparisons include confidence intervals and effect sizes.

## Experiments

An experiment defines hypothesis, owner, game, eligible population, mutually exclusive layer, variants, allocation, metrics, guardrails, start/end, minimum sample, analysis plan, and decision rule. Assignment uses HMAC-SHA256 of experiment ID and StudioPlayer ID with a secret version, producing stable buckets. Assignment is stored before exposure.

Variants resolve only schema-declared experiment fields. A player remains in one variant. Exposure is recorded when behavior first observes a variant, not at assignment creation. Operators stop an experiment automatically on integrity, crash, latency, economy, or purchase guardrail breach.

## Analytics contract

Standard events cover session, action, resource, inventory, progression, quest, achievement, ad, purchase, offer, experiment, match, social, sync, error, and performance domains. Each event has owner, schema, sensitivity, purpose, retention, sampling rule, and definition digest.

The ingestion service validates and pseudonymizes events, rejects forbidden PII, adds trusted server context, and writes partitioned Parquet to R2 by environment/game/date/hour/event. Server-authored business events are the authority for economy and purchase analysis. Client events are explicitly marked untrusted.

## Data quality

Daily checks verify schema validity, duplicates, event-time lag, missing partitions, impossible sequences, server/client disagreement, experiment sample ratios, and ledger-to-analytics totals. Failed quality gates mark affected dashboards and experiment results as invalid.

## Access and privacy

Analytics uses pseudonymous player IDs derived per environment. Re-identification is restricted to audited support workflows. Studio analysts see only their studio/game data. Small cohort results below the configured privacy threshold are suppressed.

## AI consumption

Agents query governed aggregates and sampled redacted traces through the analytics API. Direct unrestricted R2 access is forbidden. Every analysis stores query digest, dataset partitions, model, prompt digest, output, and reviewer decision.
