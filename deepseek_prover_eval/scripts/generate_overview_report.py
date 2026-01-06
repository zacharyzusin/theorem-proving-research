#!/usr/bin/env python3
"""
Generate a single overview report (Markdown) from merged metrics.

The report includes:
- Overall counts (problems, successes, failures), Pass@K
- Timing stats (avg/median/p90) for generation, lean check, total
- Failure breakdown (timeout vs lean_error vs generation_error vs incorrect)
- First-success attempt distribution
- Top slowest problems by average total time

Usage:
  python scripts/generate_overview_report.py \
    --metrics data/results/minif2f_merged/metrics/<merged_file>.json \
    --out-dir data/reports/minif2f_run
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple


def median(values: List[float]) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    n = len(s)
    mid = n // 2
    if n % 2 == 1:
        return float(s[mid])
    return float((s[mid - 1] + s[mid]) / 2)


def percentile(values: List[float], p: float) -> float:
    if not values:
        return 0.0
    assert 0.0 <= p <= 1.0
    s = sorted(values)
    if len(s) == 1:
        return float(s[0])
    idx = int(round(p * (len(s) - 1)))
    return float(s[idx])


def generate_report(metrics_path: Path, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    with metrics_path.open("r") as f:
        m = json.load(f)

    dataset = m.get("dataset", "unknown")
    mode = m.get("mode", "unknown")
    total = int(m.get("total_problems", 0))
    passed = int(m.get("problems_passed", 0))
    failed = int(m.get("problems_failed", total - passed))
    pass_at_1 = float(m.get("pass_at_1", 0.0))
    pass_at_8 = float(m.get("pass_at_8", 0.0))
    pass_at_all = float(m.get("pass_at_all", 0.0))
    num_samples = int(m.get("num_samples", 0))
    total_timeouts = int(m.get("total_timeouts", 0))
    problems_with_timeouts = int(m.get("problems_with_timeouts", 0))
    total_eval_seconds = float(m.get("total_evaluation_time", 0.0))
    shards_merged = int(m.get("shards_merged", 0))

    problems: List[Dict[str, Any]] = m.get("problem_results", [])

    # Flatten attempts for timing stats
    gen_times: List[float] = []
    lean_times: List[float] = []
    total_times: List[float] = []

    # Failure breakdown
    fail_timeout = 0
    fail_lean_error = 0
    fail_generation_error = 0
    fail_incorrect = 0

    # First success attempt distribution
    first_success_hist: Dict[int, int] = {}

    # Per-problem average total time
    per_problem_avg_total: List[Tuple[str, float]] = []

    for pr in problems:
        attempts: List[Dict[str, Any]] = pr.get("attempts", [])
        # times
        for a in attempts:
            gen_times.append(float(a.get("generation_time", 0.0)))
            lean_times.append(float(a.get("lean_check_time", 0.0)))
            total_times.append(float(a.get("total_time", 0.0)))

        # successes
        success_indices = [a.get("attempt_number", 0) for a in attempts if a.get("success") is True]
        if success_indices:
            first_idx = int(min(success_indices))
            first_success_hist[first_idx] = first_success_hist.get(first_idx, 0) + 1
        else:
            # failure reasons
            any_timeout = any(a.get("timeout_occurred") for a in attempts)
            any_lean_err = any(bool(a.get("lean_error")) for a in attempts)
            any_gen_err = any(bool(a.get("generation_error")) for a in attempts)
            if any_timeout:
                fail_timeout += 1
            elif any_lean_err:
                fail_lean_error += 1
            elif any_gen_err:
                fail_generation_error += 1
            else:
                fail_incorrect += 1

        # per-problem average total
        if attempts:
            avg_tot = sum(float(a.get("total_time", 0.0)) for a in attempts) / len(attempts)
            per_problem_avg_total.append((pr.get("problem_id", "unknown"), avg_tot))

    # Compute timing stats
    def stats_block(values: List[float]) -> Dict[str, float]:
        if not values:
            return {"avg": 0.0, "median": 0.0, "p90": 0.0, "p95": 0.0}
        avg = sum(values) / len(values)
        return {
            "avg": avg,
            "median": median(values),
            "p90": percentile(values, 0.90),
            "p95": percentile(values, 0.95),
        }

    gen_stats = stats_block(gen_times)
    lean_stats = stats_block(lean_times)
    total_stats = stats_block(total_times)

    # Top slowest problems by average total time
    per_problem_avg_total.sort(key=lambda x: x[1], reverse=True)
    top_slowest = per_problem_avg_total[:10]

    # Build markdown
    out_md = out_dir / "OVERVIEW.md"
    lines: List[str] = []
    lines.append(f"# {dataset.upper()} ({mode.upper()}) - Overview")
    lines.append("")
    lines.append("## Summary")
    lines.append(f"- Problems: {total}")
    lines.append(f"- Passed: {passed} ({passed/total:.2%})")
    lines.append(f"- Failed: {failed} ({failed/total:.2%})")
    lines.append(f"- Pass@1: {pass_at_1:.2%}")
    lines.append(f"- Pass@8: {pass_at_8:.2%}")
    if num_samples and num_samples != 8:
        lines.append(f"- Pass@{num_samples}: {pass_at_all:.2%}")
    lines.append(f"- Shards merged: {shards_merged}")
    lines.append(f"- Total evaluation time (sum across shards): {total_eval_seconds:.2f}s ({total_eval_seconds/3600:.2f} h)")
    lines.append("")

    lines.append("## Failures")
    lines.append(f"- Total failures: {failed}")
    lines.append(f"  - Timeout-related: {fail_timeout}")
    lines.append(f"  - Lean errors: {fail_lean_error}")
    lines.append(f"  - Generation errors: {fail_generation_error}")
    lines.append(f"  - Incorrect (no explicit error): {fail_incorrect}")
    lines.append(f"- Attempts that timed out (all attempts): {total_timeouts}")
    lines.append(f"- Problems with any timeout: {problems_with_timeouts}")
    lines.append("")

    lines.append("## Timing (per attempt)")
    lines.append(f"- Generation time: avg {gen_stats['avg']:.2f}s, median {gen_stats['median']:.2f}s, p90 {gen_stats['p90']:.2f}s, p95 {gen_stats['p95']:.2f}s")
    lines.append(f"- Lean check time: avg {lean_stats['avg']:.2f}s, median {lean_stats['median']:.2f}s, p90 {lean_stats['p90']:.2f}s, p95 {lean_stats['p95']:.2f}s")
    lines.append(f"- Total time: avg {total_stats['avg']:.2f}s, median {total_stats['median']:.2f}s, p90 {total_stats['p90']:.2f}s, p95 {total_stats['p95']:.2f}s")
    lines.append("")

    if first_success_hist:
        lines.append("## First Success Attempt Distribution")
        for k in sorted(first_success_hist.keys()):
            count = first_success_hist[k]
            lines.append(f"- Attempt {k}: {count} problems")
        lines.append("")

    if top_slowest:
        lines.append("## Top 10 Slowest Problems (by avg total time per attempt)")
        for pid, avg_tot in top_slowest:
            lines.append(f"- {pid}: {avg_tot:.2f}s/attempt")
        lines.append("")

    lines.append("## Files")
    lines.append("- summary.csv: per-problem summary")
    lines.append("- successes/: first-success attempt code and metadata")
    lines.append("- failures/: diagnostics for failed problems")
    lines.append("")

    out_md.write_text("\n".join(lines), encoding="utf-8")
    return out_md


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate overview report (Markdown) from merged metrics")
    ap.add_argument("--metrics", required=True, help="Path to merged metrics JSON")
    ap.add_argument("--out-dir", required=True, help="Directory where OVERVIEW.md will be written")
    args = ap.parse_args()

    out_path = generate_report(Path(args.metrics), Path(args.out_dir))
    print(f"Wrote overview: {out_path}")


if __name__ == "__main__":
    main()

