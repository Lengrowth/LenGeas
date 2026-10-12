from __future__ import annotations

from apps.workers.reconciliation import celery_app, reconcile_values


def test_reconciliation_task_is_routed_to_maintenance_queue_with_bounded_retries() -> None:
    assert celery_app.conf.task_default_queue == "maintenance"
    assert reconcile_values.name == "lengeas.reconciliation.run"
    assert reconcile_values.max_retries == 8
    assert reconcile_values.soft_time_limit == 900
