#!/usr/bin/env python3
"""Merge sharded MiniF2F results into a single unified directory.

This script:
1. Copies all problem JSON files from all shards into one proofs/ directory
2. Merges all metrics into a single aggregated metrics file
3. Creates a unified results directory structure

Usage:
  python scripts/merge_shards.py data/results/minif2f_sharded_16 data/results/minif2f_merged
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any
from datetime import datetime


def load_latest_metrics(metrics_dir: Path) -> dict[str, Any]:
    """Load the most recent metrics file from a directory."""
    files = sorted(metrics_dir.glob("*.json"))
    if not files:
        raise FileNotFoundError(f"No metrics files in {metrics_dir}")
    with files[-1].open("r") as f:
        return json.load(f)


def merge_shards(sharded_root: Path, output_dir: Path, mode: str | None = None) -> None:
    """Merge all shard results into a single directory."""
    sharded_root = Path(sharded_root)
    output_dir = Path(output_dir)
    
    # Create output directories
    output_dir.mkdir(parents=True, exist_ok=True)
    proofs_dir = output_dir / "proofs"
    metrics_dir = output_dir / "metrics"
    proofs_dir.mkdir(exist_ok=True)
    metrics_dir.mkdir(exist_ok=True)
    
    # Find all shard directories
    shard_dirs = sorted([p for p in sharded_root.glob("shard_*") if p.is_dir()])
    if not shard_dirs:
        raise SystemExit(f"No shard_*/ directories found under {sharded_root}")
    
    print(f"Found {len(shard_dirs)} shards to merge...")
    
    # Collect all problem results and metrics
    all_problem_results: list[dict[str, Any]] = []
    all_metrics: list[dict[str, Any]] = []
    problem_ids_seen: set[str] = set()
    total_problems = 0
    total_passed = 0
    
    for shard_dir in shard_dirs:
        shard_proofs_dir = shard_dir / "proofs"
        shard_metrics_dir = shard_dir / "metrics"
        
        # Copy all problem JSON files
        problem_files = sorted(shard_proofs_dir.glob("*.json"))
        for problem_file in problem_files:
            problem_id = problem_file.stem
            if problem_id in problem_ids_seen:
                print(f"WARNING: Duplicate problem_id {problem_id} found, skipping...")
                continue
            
            problem_ids_seen.add(problem_id)
            
            # Copy file to unified directory
            dest_file = proofs_dir / problem_file.name
            shutil.copy2(problem_file, dest_file)
            
            # Load and collect problem result
            with problem_file.open("r") as f:
                problem_data = json.load(f)
                all_problem_results.append(problem_data)
                total_problems += 1
                if problem_data.get("passed"):
                    total_passed += 1
        
        # Load metrics from this shard
        if shard_metrics_dir.exists():
            try:
                metrics = load_latest_metrics(shard_metrics_dir)
                if mode is None or metrics.get("mode") == mode:
                    all_metrics.append(metrics)
            except FileNotFoundError:
                pass
    
    print(f"\nCopied {total_problems} problem results to {proofs_dir}")
    
    # Compute aggregated metrics
    if not all_problem_results:
        raise SystemExit("No problem results found to aggregate")
    
    # Compute Pass@K metrics
    pass1 = sum(1 for p in all_problem_results if p.get("attempts") and p["attempts"][0].get("success") is True)
    pass8 = 0
    pass_all = 0
    max_attempts = 0
    
    for p in all_problem_results:
        attempts = p.get("attempts", [])
        max_attempts = max(max_attempts, len(attempts))
        if any(a.get("success") is True for a in attempts[:8]):
            pass8 += 1
        if any(a.get("success") is True for a in attempts):
            pass_all += 1
    
    # Compute timing statistics
    all_gen_times = [a.get("generation_time", 0) for p in all_problem_results for a in p.get("attempts", [])]
    all_lean_times = [a.get("lean_check_time", 0) for p in all_problem_results for a in p.get("attempts", [])]
    all_total_times = [a.get("total_time", 0) for p in all_problem_results for a in p.get("attempts", [])]
    
    avg_gen_time = sum(all_gen_times) / len(all_gen_times) if all_gen_times else 0.0
    avg_lean_time = sum(all_lean_times) / len(all_lean_times) if all_lean_times else 0.0
    avg_total_time = sum(all_total_times) / len(all_total_times) if all_total_times else 0.0
    
    # Count timeouts
    total_timeouts = sum(1 for p in all_problem_results for a in p.get("attempts", []) if a.get("timeout_occurred"))
    problems_with_timeouts = sum(1 for p in all_problem_results 
                                 if any(a.get("timeout_occurred") for a in p.get("attempts", [])))
    
    # Sum total_evaluation_time from all shards
    total_evaluation_time = sum(m.get("total_evaluation_time", 0) for m in all_metrics)
    
    # Create merged metrics
    # Determine actual number of samples (max attempts)
    num_samples = max_attempts if max_attempts > 0 else 8
    
    merged_metrics = {
        "dataset": "minif2f",
        "mode": all_problem_results[0].get("mode", "noncot") if all_problem_results else "noncot",
        "total_problems": total_problems,
        "problems_passed": total_passed,
        "problems_failed": total_problems - total_passed,
        "num_samples": num_samples,  # Store actual number of samples
        "pass_at_1": pass1 / total_problems if total_problems > 0 else 0.0,
        "pass_at_8": pass8 / total_problems if total_problems > 0 else 0.0,
        "pass_at_all": pass_all / total_problems if total_problems > 0 else 0.0,
        # For backward compatibility, set pass_at_32 only if we actually ran 32 samples
        "pass_at_32": pass_all / total_problems if num_samples >= 32 and total_problems > 0 else None,
        "total_timeouts": total_timeouts,
        "problems_with_timeouts": problems_with_timeouts,
        "avg_generation_time": avg_gen_time,
        "avg_lean_check_time": avg_lean_time,
        "avg_total_time": avg_total_time,
        "total_generation_time": sum(all_gen_times),
        "total_lean_check_time": sum(all_lean_times),
        "total_evaluation_time": total_evaluation_time,
        "timestamp": datetime.now().isoformat(),
        "shards_merged": len(shard_dirs),
        "problem_results": all_problem_results,  # Include all problem results in metrics
    }
    
    # Save merged metrics
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    metrics_filename = f"minif2f_{merged_metrics['mode']}_merged_{timestamp}.json"
    metrics_filepath = metrics_dir / metrics_filename
    
    with metrics_filepath.open("w") as f:
        json.dump(merged_metrics, f, indent=2, default=str)
    
    print(f"\nMerged metrics saved to: {metrics_filepath}")
    
    # Print summary
    print("\n" + "=" * 80)
    print("MERGED RESULTS SUMMARY")
    print("=" * 80)
    print(f"Shards merged: {len(shard_dirs)}")
    print(f"Total problems: {total_problems}")
    print(f"Problems passed: {total_passed}")
    print(f"Problems failed: {total_problems - total_passed}")
    print(f"\nPass@1:  {pass1}/{total_problems} = {pass1/total_problems:.2%}")
    if max_attempts >= 8:
        print(f"Pass@8:  {pass8}/{total_problems} = {pass8/total_problems:.2%}")
    print(f"Pass@{max_attempts}: {pass_all}/{total_problems} = {pass_all/total_problems:.2%}")
    print(f"\nAverage Generation Time: {avg_gen_time:.2f}s")
    print(f"Average Lean Check Time: {avg_lean_time:.2f}s")
    print(f"Average Total Time: {avg_total_time:.2f}s")
    print(f"Total Evaluation Time: {total_evaluation_time:.2f}s ({total_evaluation_time/3600:.2f} hours)")
    print(f"\nTotal Timeouts: {total_timeouts} attempts")
    print(f"Problems with Timeouts: {problems_with_timeouts}/{total_problems}")
    print("=" * 80)
    print(f"\nUnified results directory: {output_dir}")
    print(f"  - Problem results: {proofs_dir}")
    print(f"  - Metrics: {metrics_filepath}")


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Merge sharded evaluation results into a single directory"
    )
    ap.add_argument(
        "sharded_root",
        type=str,
        help="Root directory containing shard_*/ subdirectories"
    )
    ap.add_argument(
        "output_dir",
        type=str,
        help="Output directory for merged results"
    )
    ap.add_argument(
        "--mode",
        type=str,
        default=None,
        help="Optional: require metrics['mode']==this"
    )
    args = ap.parse_args()
    
    merge_shards(args.sharded_root, args.output_dir, args.mode)


if __name__ == "__main__":
    main()
