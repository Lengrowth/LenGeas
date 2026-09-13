# Availability-zone loss

Confirm ECS tasks are distributed across three AZs, managed draining is enabled, and the general/realtime/critical-worker capacity boundaries remain intact. Remove or isolate one AZ only in staging/exercise environments.

Verify replacement capacity, service health, ALB target distribution, task placement, queue age, and trace continuity. Stop if data services lose quorum or if a task receives a public address. Record timings and rollback actions.
