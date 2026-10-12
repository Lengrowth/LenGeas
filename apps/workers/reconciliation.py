"""Celery task for periodic value integrity reconciliation."""

from __future__ import annotations

import asyncio
import os
from typing import Any

from celery import Celery  # type: ignore[import-untyped]
from pymongo import AsyncMongoClient

celery_app = Celery(
    "lengeas_reconciliation",
    broker=os.environ.get("CELERY_BROKER_URL"),
    backend=os.environ.get("CELERY_RESULT_BACKEND") or None,
)
celery_app.conf.update(
    task_default_queue="maintenance",
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_track_started=True,
)


async def _run_reconciliation(studio_id: str | None) -> dict[str, Any]:
    from packages.persistence.mongodb.reconciliation import MongoReconciliationRepository

    uri = os.environ.get("MONGODB_URI", "").strip()
    if not uri:
        raise RuntimeError("MONGODB_URI is required for reconciliation")
    client: Any = AsyncMongoClient(uri, tz_aware=True)
    try:
        database = client[os.environ.get("MONGODB_DATABASE", "lengeas")]
        report = await MongoReconciliationRepository(database).run(studio_id=studio_id)
        return {
            "checked_at": report.checked_at.isoformat(),
            "findings": len(report.findings),
            "quarantined": len(report.findings),
            "repair_proposals": len(report.repair_proposals),
            "finding_ids": [finding.finding_id for finding in report.findings],
        }
    finally:
        await client.close()


@celery_app.task(  # type: ignore[misc]
    bind=True,
    name="lengeas.reconciliation.run",
    queue="maintenance",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
    max_retries=8,
    soft_time_limit=900,
    time_limit=960,
)
def reconcile_values(self: Any, studio_id: str | None = None) -> dict[str, Any]:
    del self
    return asyncio.run(_run_reconciliation(studio_id))
