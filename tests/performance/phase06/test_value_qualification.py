from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.dev.value_qualification import aggregate, run_partition


class Phase06QualificationTests(unittest.TestCase):
    def test_bounded_partition_records_seed_range_counts_and_digest(self) -> None:
        report = run_partition(0, 2, 1000)
        self.assertEqual(report["operation_count"], 1000)
        self.assertEqual(sum(report["operation_counts"].values()), 1000)
        self.assertEqual(report["asset_total"], 0)
        self.assertEqual(sum(report["account_totals"].values()), 0)
        self.assertEqual(len(report["digest_sha256"]), 64)

    def test_aggregate_requires_contiguous_complete_partition_set(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            for index in range(2):
                record = run_partition(index, 2, 5)
                (directory / f"partition-{index}.json").write_text(json.dumps(record))
            summary = aggregate(list(directory.glob("partition-*.json")), 2, 10)
        self.assertEqual(summary["operation_count"], 10)
        self.assertFalse(summary["raw_operations_retained"])

    def test_aggregate_rejects_missing_partition_range(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            report = run_partition(1, 2, 5)
            (directory / "partition-1.json").write_text(json.dumps(report))
            with self.assertRaisesRegex(ValueError, "partition_report_count_mismatch"):
                aggregate(list(directory.glob("partition-*.json")), 2, 10)


if __name__ == "__main__":
    unittest.main()
