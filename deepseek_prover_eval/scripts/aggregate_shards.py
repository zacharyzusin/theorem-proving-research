#!/usr/bin/env python3
"""Aggregate sharded MiniF2F results into a single metrics summary.

Usage:
  python scripts/aggregate_shards.py data/results/minif2f_sharded --mode noncot

It loads the latest metrics JSON from each shard directory (shard_0..shard_{N-1}),
unions the per-problem results, and prints overall Pass@1/8/32.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class ProblemAgg:
    problem_id: str
    attempts: list[dict[str, Any]]


def load_latest_metrics(metrics_dir: Path) -> dict[str, Any]:
    files = sorted(metrics_dir.glob("*.json"))
    if not files:
        raise FileNotFoundError(f"No metrics files in {metrics_dir}")
    with files[-1].open("r") as f:
        return json.load(f)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("sharded_root", type=str, help="Root containing shard_*/ subdirs")
    ap.add_argument("--mode", type=str, default=None, help="Optional: require metrics['mode']==this")
    ap.add_argument("--num-samples", type=int, default=None, help="Override NUM_SAMPLES for Pass@K calculation (default: infer from attempts)")
    args = ap.parse_args()

    root = Path(args.sharded_root)
    shard_dirs = sorted([p for p in root.glob("shard_*") if p.is_dir()])
    if not shard_dirs:
        raise SystemExit(f"No shard_*/ directories found under {root}")

    by_problem: dict[str, ProblemAgg] = {}

    for shard in shard_dirs:
        metrics_dir = shard / "metrics"
        metrics = load_latest_metrics(metrics_dir)

        if args.mode is not None and metrics.get("mode") != args.mode:
            raise SystemExit(f"Mode mismatch in {shard}: {metrics.get('mode')} != {args.mode}")

        for pr in metrics.get("problem_results", []):
            pid = pr.get("problem_id")
            if not pid:
                continue
            if pid in by_problem:
                raise SystemExit(f"Duplicate problem_id {pid} across shards; check sharding setup")
            by_problem[pid] = ProblemAgg(problem_id=pid, attempts=pr.get("attempts", []))

    problems = list(by_problem.values())
    total = len(problems)
    if total == 0:
        raise SystemExit("No problems found in shard metrics")

    pass1 = sum(1 for p in problems if p.attempts and p.attempts[0].get("success") is True)
    pass8 = 0
    pass_all = 0
    max_attempts = 0
    for p in problems:
        attempts = p.attempts or []
        max_attempts = max(max_attempts, len(attempts))
        if any(a.get("success") is True for a in attempts[:8]):
            pass8 += 1
        if any(a.get("success") is True for a in attempts):
            pass_all += 1
    
    # Determine K from actual attempts or user override
    if args.num_samples:
        k = args.num_samples
    else:
        k = max_attempts if max_attempts > 0 else 8

    print("=" * 60)
    print(f"Aggregated shards under: {root}")
    print(f"Shards found: {len(shard_dirs)}")
    print(f"Total problems: {total}")
    print(f"Pass@1:  {pass1}/{total} = {pass1/total:.2%}")
    if k >= 8:
        print(f"Pass@8:  {pass8}/{total} = {pass8/total:.2%}")
    if k > 8:
        print(f"Pass@{k}: {pass_all}/{total} = {pass_all/total:.2%}")
    else:
        print(f"Pass@{k}: {pass_all}/{total} = {pass_all/total:.2%}")
    print("=" * 60)


if __name__ == "__main__":
    main()
