#!/usr/bin/env python3
"""
Generate human-friendly outputs from merged evaluation metrics.

For a given merged metrics JSON, this script creates:
- summary.csv: per-problem summary (passed/failed, attempts, timings)
- successes/<problem_id>.txt: final Lean code and metadata for first successful attempt
- failures/<problem_id>.txt: error summary and attempt diagnostics for failed problems
- README.txt: brief description of directory contents

Usage:
  python scripts/generate_run_outputs.py \
    --metrics data/results/minif2f_merged/metrics/<merged_file>.json \
    --out-dir data/reports/minif2f_run
"""

from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def _safe_str(s: Optional[str], limit: int = 2000) -> str:
    if s is None:
        return ""
    s = str(s)
    if len(s) > limit:
        return s[:limit] + "\n... [truncated] ..."
    return s


def _first_success_attempt(attempts: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    for a in attempts:
        if a.get("success") is True:
            return a
    return None


def _avg(values: List[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def generate_outputs(metrics_path: Path, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    successes_dir = out_dir / "successes"
    failures_dir = out_dir / "failures"
    successes_dir.mkdir(exist_ok=True)
    failures_dir.mkdir(exist_ok=True)

    with metrics_path.open("r") as f:
        metrics = json.load(f)

    dataset = metrics.get("dataset", "unknown")
    mode = metrics.get("mode", "unknown")
    problem_results = metrics.get("problem_results", [])

    # README
    (out_dir / "README.txt").write_text(
        f"{dataset.upper()} ({mode.upper()}) run outputs\n"
        f"- summary.csv: per-problem summary with timings and outcomes\n"
        f"- successes/: first-success attempt code and metadata per solved problem\n"
        f"- failures/: diagnostics per unsolved problem (errors/timeouts)\n",
        encoding="utf-8",
    )

    # Summary CSV
    summary_path = out_dir / "summary.csv"
    with summary_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(
            [
                "problem_id",
                "passed",
                "first_success_attempt",
                "num_attempts",
                "num_successful_attempts",
                "num_timeouts",
                "avg_generation_time_s",
                "avg_lean_check_time_s",
            ]
        )

        for pr in problem_results:
            problem_id = pr.get("problem_id", "unknown")
            attempts: List[Dict[str, Any]] = pr.get("attempts", [])
            num_attempts = len(attempts)
            num_success = sum(1 for a in attempts if a.get("success") is True)
            num_timeouts = sum(1 for a in attempts if a.get("timeout_occurred"))
            avg_gen = _avg([float(a.get("generation_time", 0.0)) for a in attempts])
            avg_lean = _avg([float(a.get("lean_check_time", 0.0)) for a in attempts])
            first_success = _first_success_attempt(attempts)
            first_success_idx = (
                first_success.get("attempt_number") if first_success is not None else -1
            )
            passed = first_success is not None

            writer.writerow(
                [
                    problem_id,
                    "true" if passed else "false",
                    first_success_idx,
                    num_attempts,
                    num_success,
                    num_timeouts,
                    f"{avg_gen:.2f}",
                    f"{avg_lean:.2f}",
                ]
            )

            # Write per-problem files
            if passed and first_success is not None:
                # Success details
                fp = successes_dir / f"{problem_id}.txt"
                final_code = first_success.get("final_lean_code") or first_success.get(
                    "extracted_solution"
                )
                meta = [
                    f"Problem: {problem_id}",
                    f"Dataset: {dataset}",
                    f"Mode: {mode}",
                    f"First success attempt: {first_success.get('attempt_number')}",
                    f"Generation time (s): {first_success.get('generation_time', 0)}",
                    f"Lean check time (s): {first_success.get('lean_check_time', 0)}",
                ]
                content = (
                    "\n".join(meta)
                    + "\n\n==== Final Lean Code ====\n"
                    + (_safe_str(final_code, limit=100000) or "[no code available]")
                )
                fp.write_text(content, encoding="utf-8")
            else:
                # Failure diagnostics
                fp = failures_dir / f"{problem_id}.txt"
                lines = [
                    f"Problem: {problem_id}",
                    f"Dataset: {dataset}",
                    f"Mode: {mode}",
                    f"Attempts: {num_attempts}",
                    f"Timeout attempts: {num_timeouts}",
                    f"Successful attempts: {num_success}",
                    "",
                ]
                for a in attempts:
                    lines.append(f"--- Attempt {a.get('attempt_number', 0)} ---")
                    lines.append(f"Success: {a.get('success')}")
                    lines.append(
                        f"Times (gen/lean/total): {a.get('generation_time', 0)} / {a.get('lean_check_time', 0)} / {a.get('total_time', 0)}"
                    )
                    if a.get("timeout_occurred"):
                        lines.append("Timeout: true")
                    if a.get("lean_error"):
                        lines.append("Lean error:")
                        lines.append(_safe_str(a.get("lean_error"), limit=2000))
                    if a.get("lean_stderr"):
                        lines.append("Lean stderr:")
                        lines.append(_safe_str(a.get("lean_stderr"), limit=2000))
                    if a.get("generation_error"):
                        lines.append("Generation error:")
                        lines.append(_safe_str(a.get("generation_error"), limit=2000))
                    # Include a short snippet of final code if any
                    if a.get("final_lean_code"):
                        lines.append("Final Lean code (truncated):")
                        lines.append(_safe_str(a.get("final_lean_code"), limit=1500))
                    lines.append("")
                fp.write_text("\n".join(lines), encoding="utf-8")

    print(f"Wrote summary: {summary_path}")
    print(f"Successes dir: {successes_dir}")
    print(f"Failures dir:  {failures_dir}")


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Generate human-friendly outputs from merged metrics"
    )
    ap.add_argument(
        "--metrics",
        required=True,
        help="Path to merged metrics JSON (e.g., data/results/*_merged/metrics/*.json)",
    )
    ap.add_argument(
        "--out-dir",
        required=True,
        help="Directory to write outputs (summary.csv, successes/, failures/)",
    )
    args = ap.parse_args()

    generate_outputs(Path(args.metrics), Path(args.out_dir))


if __name__ == "__main__":
    main()

