"""
Qualitative inspection tool for evaluation results.

This tool allows you to browse, filter, and inspect generated proofs
to understand model performance and identify patterns in failures.
"""
import json
import argparse
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class ProblemSummary:
    """Summary of a problem's evaluation results."""
    problem_id: str
    problem_path: str
    passed: bool
    first_success_attempt: Optional[int]
    total_attempts: int
    successful_attempts: int
    avg_generation_time: float
    avg_lean_check_time: float
    has_errors: bool
    error_types: List[str]


class ResultsInspector:
    """Tool for inspecting evaluation results."""
    
    def __init__(self, results_dir: Path):
        """
        Initialize inspector with results directory.
        
        Args:
            results_dir: Directory containing metrics JSON files and proofs subdirectory
        """
        self.results_dir = Path(results_dir)
        self.metrics_dir = self.results_dir / "metrics"
        self.proofs_dir = self.results_dir / "proofs"
        
        # Load all metrics files
        self.metrics_files = sorted(self.metrics_dir.glob("*.json"))
        self.current_metrics: Optional[Dict] = None
        self.problem_summaries: List[ProblemSummary] = []
    
    def load_latest_metrics(self) -> Optional[Dict]:
        """Load the most recent metrics file."""
        if not self.metrics_files:
            print(f"No metrics files found in {self.metrics_dir}")
            return None
        
        latest_file = self.metrics_files[-1]
        print(f"Loading metrics from: {latest_file}")
        
        with open(latest_file, 'r') as f:
            self.current_metrics = json.load(f)
        
        self._build_summaries()
        return self.current_metrics
    
    def load_metrics_file(self, filename: str) -> Optional[Dict]:
        """Load a specific metrics file."""
        filepath = self.metrics_dir / filename
        if not filepath.exists():
            print(f"Metrics file not found: {filepath}")
            return None
        
        with open(filepath, 'r') as f:
            self.current_metrics = json.load(f)
        
        self._build_summaries()
        return self.current_metrics
    
    def _build_summaries(self):
        """Build problem summaries from current metrics."""
        if not self.current_metrics:
            return
        
        self.problem_summaries = []
        for problem_result in self.current_metrics.get("problem_results", []):
            attempts = problem_result.get("attempts", [])
            successful = [a for a in attempts if a.get("success", False)]
            
            # Collect error types
            error_types = []
            for attempt in attempts:
                if attempt.get("generation_error"):
                    error_types.append("generation_error")
            if attempt.get("lean_error"):
                error_types.append("lean_error")
            if attempt.get("timeout_occurred"):
                error_types.append("timeout")
            
            avg_gen_time = sum(a.get("generation_time", 0) for a in attempts) / len(attempts) if attempts else 0
            avg_lean_time = sum(a.get("lean_check_time", 0) for a in attempts) / len(attempts) if attempts else 0
            
            summary = ProblemSummary(
                problem_id=problem_result.get("problem_id", "unknown"),
                problem_path=problem_result.get("problem_path", ""),
                passed=problem_result.get("passed", False),
                first_success_attempt=problem_result.get("first_success_attempt"),
                total_attempts=len(attempts),
                successful_attempts=len(successful),
                avg_generation_time=avg_gen_time,
                avg_lean_check_time=avg_lean_time,
                has_errors=len(error_types) > 0,
                error_types=list(set(error_types)),
            )
            self.problem_summaries.append(summary)
    
    def print_overview(self):
        """Print overview of evaluation results."""
        if not self.current_metrics:
            print("No metrics loaded. Use load_latest_metrics() first.")
            return
        
        metrics = self.current_metrics
        print("\n" + "="*80)
        print("EVALUATION OVERVIEW")
        print("="*80)
        print(f"Dataset: {metrics.get('dataset', 'unknown').upper()}")
        print(f"Mode: {metrics.get('mode', 'unknown').upper()}")
        print(f"Timestamp: {metrics.get('timestamp', 'unknown')}")
        print()
        print("ACCURACY:")
        print(f"  Total Problems: {metrics.get('total_problems', 0)}")
        print(f"  Passed: {metrics.get('problems_passed', 0)}")
        print(f"  Failed: {metrics.get('problems_failed', 0)}")
        print(f"  Pass@1:  {metrics.get('pass_at_1', 0):.2%}")
        print(f"  Pass@8:  {metrics.get('pass_at_8', 0):.2%}")
        print(f"  Pass@32: {metrics.get('pass_at_32', 0):.2%}")
        print()
        print("TIMING:")
        print(f"  Avg Generation Time: {metrics.get('avg_generation_time', 0):.2f}s")
        print(f"  Avg Lean Check Time: {metrics.get('avg_lean_check_time', 0):.2f}s")
        print(f"  Total Evaluation Time: {metrics.get('total_evaluation_time', 0):.2f}s ({metrics.get('total_evaluation_time', 0)/3600:.2f} hours)")
        print("="*80)
    
    def list_problems(self, filter_passed: Optional[bool] = None, filter_timeouts: bool = False, limit: Optional[int] = None):
        """
        List problems with their status.
        
        Args:
            filter_passed: If True, show only passed problems. If False, show only failed.
                          If None, show all.
            filter_timeouts: If True, show only problems that had at least one timeout
            limit: Maximum number of problems to show
        """
        if not self.problem_summaries:
            print("No problem summaries available. Load metrics first.")
            return
        
        if not self.current_metrics:
            print("No metrics loaded. Cannot filter by timeouts.")
            return
        
        filtered = self.problem_summaries
        if filter_passed is not None:
            filtered = [p for p in filtered if p.passed == filter_passed]
        
        if filter_timeouts:
            # Find problems that had timeouts
            problem_ids_with_timeouts = set()
            for problem_result in self.current_metrics.get("problem_results", []):
                for attempt in problem_result.get("attempts", []):
                    if attempt.get("timeout_occurred", False):
                        problem_ids_with_timeouts.add(problem_result.get("problem_id"))
                        break
            filtered = [p for p in filtered if p.problem_id in problem_ids_with_timeouts]
        
        if limit:
            filtered = filtered[:limit]
        
        print(f"\n{'ID':<30} {'Status':<10} {'Success':<10} {'Avg Gen Time':<15} {'First Success':<15}")
        print("-" * 80)
        
        for summary in filtered:
            status = "PASSED" if summary.passed else "FAILED"
            success_rate = f"{summary.successful_attempts}/{summary.total_attempts}"
            gen_time = f"{summary.avg_generation_time:.2f}s"
            first_success = f"Attempt {summary.first_success_attempt + 1}" if summary.first_success_attempt is not None else "N/A"
            
            print(f"{summary.problem_id:<30} {status:<10} {success_rate:<10} {gen_time:<15} {first_success:<15}")
    
    def inspect_problem(self, problem_id: str, show_all_attempts: bool = False):
        """
        Inspect a specific problem in detail.
        
        Args:
            problem_id: Problem identifier
            show_all_attempts: If True, show all attempts. If False, show only successful ones.
        """
        if not self.current_metrics:
            print("No metrics loaded. Use load_latest_metrics() first.")
            return
        
        # Find problem in metrics
        problem_result = None
        for pr in self.current_metrics.get("problem_results", []):
            if pr.get("problem_id") == problem_id:
                problem_result = pr
                break
        
        if not problem_result:
            print(f"Problem '{problem_id}' not found.")
            return
        
        print("\n" + "="*80)
        print(f"PROBLEM: {problem_id}")
        print("="*80)
        print(f"Path: {problem_result.get('problem_path', 'unknown')}")
        print(f"Status: {'PASSED' if problem_result.get('passed') else 'FAILED'}")
        print(f"First Success: Attempt {problem_result.get('first_success_attempt') + 1}" 
              if problem_result.get('first_success_attempt') is not None else "No successful attempts")
        print(f"Total Attempts: {len(problem_result.get('attempts', []))}")
        print()
        
        attempts = problem_result.get("attempts", [])
        if not show_all_attempts:
            attempts = [a for a in attempts if a.get("success", False)]
            if not attempts:
                print("No successful attempts. Use --show-all to see all attempts.")
                return
        
        for i, attempt in enumerate(attempts):
            print("-" * 80)
            print(f"ATTEMPT {attempt.get('attempt_number', i) + 1}")
            print("-" * 80)
            print(f"Success: {attempt.get('success', False)}")
            print(f"Generation Time: {attempt.get('generation_time', 0):.2f}s")
            print(f"Lean Check Time: {attempt.get('lean_check_time', 0):.2f}s")
            print(f"Total Time: {attempt.get('total_time', 0):.2f}s")
            
            if attempt.get("timeout_occurred"):
                print(f"\n⚠ TIMEOUT: This attempt timed out during Lean verification")
            
            if attempt.get("generation_error"):
                print(f"\nGeneration Error: {attempt['generation_error']}")
            
            if attempt.get("lean_error"):
                print(f"\nLean Error: {attempt['lean_error']}")
            
            if attempt.get("lean_stderr"):
                print(f"\nLean stderr:\n{attempt['lean_stderr'][:500]}")
            
            if attempt.get("extracted_solution"):
                print(f"\nExtracted Solution:")
                print("-" * 40)
                solution = attempt['extracted_solution']
                # Show first 500 chars, or full if short
                if len(solution) > 500:
                    print(solution[:500] + "\n... (truncated)")
                else:
                    print(solution)
            
            if attempt.get("final_lean_code") and show_all_attempts:
                print(f"\nFinal Lean Code:")
                print("-" * 40)
                code = attempt['final_lean_code']
                if len(code) > 1000:
                    print(code[:1000] + "\n... (truncated)")
                else:
                    print(code)
            
            print()
    
    def find_patterns(self):
        """Analyze patterns in failures and successes."""
        if not self.problem_summaries:
            print("No problem summaries available. Load metrics first.")
            return
        
        print("\n" + "="*80)
        print("FAILURE PATTERN ANALYSIS")
        print("="*80)
        
        # Analyze error types
        error_counts = defaultdict(int)
        timeout_count = 0
        for summary in self.problem_summaries:
            for error_type in summary.error_types:
                error_counts[error_type] += 1
                if error_type == "timeout":
                    timeout_count += 1
        
        if error_counts:
            print("\nError Type Distribution:")
            for error_type, count in sorted(error_counts.items(), key=lambda x: -x[1]):
                print(f"  {error_type}: {count} problems")
        
        # Show timeout-specific statistics if available
        if self.current_metrics:
            metrics = self.current_metrics
            total_timeouts = metrics.get("total_timeouts", 0)
            problems_with_timeouts = metrics.get("problems_with_timeouts", 0)
            if total_timeouts > 0:
                total_attempts = sum(len(r.get("attempts", [])) for r in metrics.get("problem_results", []))
                timeout_rate = (total_timeouts / total_attempts * 100) if total_attempts > 0 else 0
                print(f"\nTimeout Statistics:")
                print(f"  Total timeout attempts: {total_timeouts}")
                print(f"  Problems with timeouts: {problems_with_timeouts}/{metrics.get('total_problems', 0)}")
                print(f"  Timeout rate: {timeout_rate:.1f}% of all attempts")
        
        # Analyze timing patterns
        passed_times = [s.avg_generation_time for s in self.problem_summaries if s.passed]
        failed_times = [s.avg_generation_time for s in self.problem_summaries if not s.passed]
        
        if passed_times:
            print(f"\nGeneration Time (Passed Problems):")
            print(f"  Average: {sum(passed_times)/len(passed_times):.2f}s")
            print(f"  Median:  {sorted(passed_times)[len(passed_times)//2]:.2f}s")
        
        if failed_times:
            print(f"\nGeneration Time (Failed Problems):")
            print(f"  Average: {sum(failed_times)/len(failed_times):.2f}s")
            print(f"  Median:  {sorted(failed_times)[len(failed_times)//2]:.2f}s")
        
        # Problems with no successful attempts
        never_passed = [s for s in self.problem_summaries if not s.passed]
        if never_passed:
            print(f"\nProblems that never passed ({len(never_passed)}):")
            for summary in never_passed[:10]:  # Show first 10
                print(f"  - {summary.problem_id}")
            if len(never_passed) > 10:
                print(f"  ... and {len(never_passed) - 10} more")
        
        print("="*80)
    
    def compare_attempts(self, problem_id: str):
        """Compare all attempts for a problem side-by-side."""
        if not self.current_metrics:
            print("No metrics loaded. Use load_latest_metrics() first.")
            return
        
        # Find problem
        problem_result = None
        for pr in self.current_metrics.get("problem_results", []):
            if pr.get("problem_id") == problem_id:
                problem_result = pr
                break
        
        if not problem_result:
            print(f"Problem '{problem_id}' not found.")
            return
        
        attempts = problem_result.get("attempts", [])
        if len(attempts) < 2:
            print("Need at least 2 attempts to compare.")
            return
        
        print(f"\n{'Attempt':<10} {'Success':<10} {'Gen Time':<15} {'Lean Time':<15} {'Total Time':<15}")
        print("-" * 80)
        
        for attempt in attempts:
            print(f"{attempt.get('attempt_number', 0) + 1:<10} "
                  f"{'✓' if attempt.get('success') else '✗':<10} "
                  f"{attempt.get('generation_time', 0):.2f}s{'':<10} "
                  f"{attempt.get('lean_check_time', 0):.2f}s{'':<10} "
                  f"{attempt.get('total_time', 0):.2f}s{'':<10}")


def main():
    """Command-line interface for results inspection."""
    parser = argparse.ArgumentParser(
        description="Inspect evaluation results and generated proofs"
    )
    parser.add_argument(
        "results_dir",
        type=str,
        help="Directory containing evaluation results (should have metrics/ and proofs/ subdirectories)"
    )
    parser.add_argument(
        "--overview",
        action="store_true",
        help="Show overview of evaluation results"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all problems"
    )
    parser.add_argument(
        "--passed-only",
        action="store_true",
        help="Show only passed problems (use with --list)"
    )
    parser.add_argument(
        "--failed-only",
        action="store_true",
        help="Show only failed problems (use with --list)"
    )
    parser.add_argument(
        "--timeouts-only",
        action="store_true",
        help="Show only problems that had timeouts (use with --list)"
    )
    parser.add_argument(
        "--inspect",
        type=str,
        help="Inspect a specific problem by ID"
    )
    parser.add_argument(
        "--show-all",
        action="store_true",
        help="Show all attempts (use with --inspect)"
    )
    parser.add_argument(
        "--patterns",
        action="store_true",
        help="Analyze failure patterns"
    )
    parser.add_argument(
        "--compare",
        type=str,
        help="Compare all attempts for a problem"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of results shown (use with --list)"
    )
    
    args = parser.parse_args()
    
    inspector = ResultsInspector(args.results_dir)
    
    # Load latest metrics
    if not inspector.load_latest_metrics():
        return
    
    # Execute requested actions
    if args.overview:
        inspector.print_overview()
    
    if args.list:
        filter_passed = None
        if args.passed_only:
            filter_passed = True
        elif args.failed_only:
            filter_passed = False
        inspector.list_problems(filter_passed=filter_passed, filter_timeouts=args.timeouts_only, limit=args.limit)
    
    if args.inspect:
        inspector.inspect_problem(args.inspect, show_all_attempts=args.show_all)
    
    if args.patterns:
        inspector.find_patterns()
    
    if args.compare:
        inspector.compare_attempts(args.compare)
    
    # If no specific action, show overview
    if not any([args.overview, args.list, args.inspect, args.patterns, args.compare]):
        inspector.print_overview()
        print("\nUse --help to see available options.")


if __name__ == "__main__":
    main()
