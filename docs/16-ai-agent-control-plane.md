# AI Agent Control Plane

## Principle

AI operates LenGeas through bounded tools and the same Definition API used by the Studio. It does not write repositories, databases, published channels, infrastructure, or production state directly.

## Agents

- AI Director decomposes an approved design brief, assigns work, resolves dependency order, and assembles a draft release proposal.
- Game Design Agent authors blueprint, loops, resources, progression, upgrades, and quests.
- Story Agent authors worlds, characters, dialogue, choices, story graphs, and localization drafts.
- Economy Agent authors rates, costs, formulas, faucets, sinks, rewards, and monetization parameters.
- Balance Agent creates simulation specifications, reads governed results, and proposes bounded adjustments.
- QA Agent creates definition validation cases, invariant tests, exploit searches, and regression fixtures.
- LiveOps Agent drafts events, seasons, offers, cohorts, schedules, and rollback plans.
- Analytics Agent queries governed aggregates and writes cited analysis artifacts.

## Tool boundary

Each agent receives short-lived scoped credentials. Tools expose create draft, read schema, read permitted definition, patch draft, validate, simulate, compare, query governed analytics, and submit for review. There is no publish, approve, ledger mutation, player mutation, secret read, infrastructure, or arbitrary network tool.

## Run record

Every run stores agent type/version, model/provider/version, system instruction digest, user brief, tool scopes, input definition digests, tool calls and results, output patch, token/cost totals, safety results, validation/simulation links, reviewer actions, and final disposition.

Sensitive inputs are redacted before provider submission. Production player records are not supplied to models. Governed aggregates enforce cohort privacy.

## Proposal pipeline

1. Authorized human creates a brief with game, environment, scope, budget, and prohibited areas.
2. Director creates a plan against schema and module catalog.
3. Agents write to an isolated draft branch through API patches.
4. Validation runs after every patch batch.
5. QA and Balance agents produce tests and simulations from the frozen draft.
6. Director creates a structured proposal with diffs, assumptions, risks, evidence, and unresolved validation failures.
7. A human author edits or submits the draft.
8. Independent humans approve through the normal publishing pipeline.

An agent cannot review or approve its own output. Model confidence never replaces a gate.

## Safety controls

- JSON Schema validates every tool argument and output.
- Per-run tool calls, tokens, wall time, simulation compute, and monetary cost have hard budgets.
- Prompt and definition text are untrusted data and cannot alter tool policy.
- Retrieved content is tagged with origin and never interpreted as authority.
- High-risk fields covering entitlements, purchases, cross-game transfers, security, and production remote config require explicit human-authored edits.
- Output scanners detect secrets, PII, prohibited code, unsafe formulas, suspicious links, and policy evasion.
- A global kill switch disables agent execution without affecting runtime games.

## Evaluation

Offline evaluations cover schema validity, reference correctness, design-brief adherence, exploit resistance, deterministic reproduction, economic target fit, localization safety, tool-scope compliance, hallucinated IDs, and regression against accepted human baselines.

Production agent release requires a red-team suite, cost budget, quality threshold, rollback, monitoring dashboard, and named owner. Agent changes never share a deployment with runtime engine changes.
