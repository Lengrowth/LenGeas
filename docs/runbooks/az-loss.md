# Availability-zone loss

Deferred production exercise: after the rollout gate, confirm ECS tasks are distributed across three AZs, managed draining is enabled, and the general/realtime/critical-worker capacity boundaries remain intact. Remove or isolate one AZ only in staging/exercise environments. The Phase 02 development host is single-AZ and cannot pass this scenario.

Verify replacement capacity, service health, ALB target distribution, task placement, queue age, and trace continuity. Stop if data services lose quorum or if a task receives a public address. Record timings and rollback actions.
