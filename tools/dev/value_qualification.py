"""Deterministic partitioned value-operation qualification with bounded artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
TOTAL = 1_000_000_000
DEFAULT_PARTITIONS = 100
MASK = (1 << 64) - 1


def run_partition(partition: int, partitions: int, operations: int) -> dict[str, Any]:
    if partitions < 1 or not 0 <= partition < partitions or operations < 1:
        raise ValueError("partition_bounds_invalid")
    start = partition * operations
    state = (0x9E3779B97F4A7C15 ^ start ^ (partition << 32)) & MASK
    digest = hashlib.sha256()
    operation_counts = {"grant": 0, "spend": 0, "exchange": 0, "refund": 0}
    account_totals = {
        name: 0 for name in ("system_faucet", "system_sink", "system_treasury", "player")
    }
    for index in range(operations):
        state ^= (state << 13) & MASK
        state ^= state >> 7
        state ^= (state << 17) & MASK
        amount = (state % 1_000_000) + 1
        kind_index = (state >> 24) & 3
        kind = ("grant", "spend", "exchange", "refund")[kind_index]
        debit, credit = {
            "grant": ("system_faucet", "player"),
            "spend": ("player", "system_sink"),
            "exchange": ("player", "system_treasury"),
            "refund": ("system_sink", "player"),
        }[kind]
        # Apply both legs for each generated ledger operation and retain only
        # account aggregates plus a rolling digest, never raw operation rows.
        account_totals[debit] -= amount
        account_totals[credit] += amount
        operation_counts[kind] += 1
        digest.update(struct.pack("<QQQB", start + index, state, amount, kind_index))
    conserved_total = sum(account_totals.values())
    if conserved_total != 0:
        raise ValueError("partition_value_imbalance")
    return {
        "schema_version": 1,
        "partition": partition,
        "partitions": partitions,
        "seed_start": 0x9E3779B97F4A7C15 ^ start ^ (partition << 32),
        "seed_end": state,
        "operation_start": start,
        "operation_end_exclusive": start + operations,
        "operation_count": operations,
        "operation_counts": operation_counts,
        "account_totals": account_totals,
        "asset_total": conserved_total,
        "digest_sha256": digest.hexdigest(),
    }


def aggregate(paths: list[Path], expected_partitions: int, expected_total: int) -> dict[str, Any]:
    reports = [json.loads(path.read_text(encoding="utf-8")) for path in paths]
    reports.sort(key=lambda report: report["partition"])
    if len(reports) != expected_partitions:
        raise ValueError("partition_report_count_mismatch")
    counts = [int(report["operation_count"]) for report in reports]
    if [report["partition"] for report in reports] != list(range(expected_partitions)):
        raise ValueError("partition_ids_missing_or_duplicated")
    if any(report.get("partitions") != expected_partitions for report in reports):
        raise ValueError("partition_configuration_mismatch")
    if not reports or reports[0]["operation_start"] != 0:
        raise ValueError("qualification_range_must_start_at_zero")
    for previous, following in zip(reports, reports[1:], strict=False):
        if previous["operation_end_exclusive"] != following["operation_start"]:
            raise ValueError("partition_seed_range_gap_or_overlap")
    total = sum(counts)
    if (
        total != expected_total
        or reports[-1]["operation_end_exclusive"] != expected_total
        or any(report["asset_total"] != 0 for report in reports)
    ):
        raise ValueError("qualification_count_or_value_imbalance")
    aggregate_digest = hashlib.sha256(
        "".join(str(report["digest_sha256"]) for report in reports).encode()
    ).hexdigest()
    return {
        "schema_version": 1,
        "qualification": "one_billion_value_operations",
        "partition_count": expected_partitions,
        "operation_count": total,
        "seed_ranges": [
            {
                "partition": report["partition"],
                "operation_start": report["operation_start"],
                "operation_end_exclusive": report["operation_end_exclusive"],
                "seed_start": report["seed_start"],
                "seed_end": report["seed_end"],
            }
            for report in reports
        ],
        "operation_counts": {
            kind: sum(int(report["operation_counts"][kind]) for report in reports)
            for kind in ("grant", "spend", "exchange", "refund")
        },
        "account_totals": {
            account: sum(int(report["account_totals"][account]) for report in reports)
            for account in ("system_faucet", "system_sink", "system_treasury", "player")
        },
        "asset_total": sum(int(report["asset_total"]) for report in reports),
        "partition_digests": [report["digest_sha256"] for report in reports],
        "aggregate_digest_sha256": aggregate_digest,
        "raw_operations_retained": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run")
    run.add_argument("--partition", type=int, required=True)
    run.add_argument("--partitions", type=int, default=DEFAULT_PARTITIONS)
    run.add_argument("--operations", type=int, default=TOTAL // DEFAULT_PARTITIONS)
    run.add_argument("--output", type=Path, required=True)
    combine = commands.add_parser("aggregate")
    combine.add_argument("--reports", type=Path, required=True)
    combine.add_argument("--partitions", type=int, default=DEFAULT_PARTITIONS)
    combine.add_argument("--expected-total", type=int, default=TOTAL)
    combine.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "run":
            result = run_partition(args.partition, args.partitions, args.operations)
        else:
            result = aggregate(
                sorted(args.reports.glob("partition-*.json")),
                args.partitions,
                args.expected_total,
            )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"FAIL value qualification: {error}", file=sys.stderr)
        return 1
    print(f"PASS value qualification {args.command}: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
