"""
Metrics tracking and reporting for proof generation evaluation.

This module provides functionality to:
- Track timing metrics (generation time, lean check time)
- Record accuracy metrics (pass/fail, Pass@K)
- Save detailed results for qualitative inspection
- Generate summary reports
"""
import json
import time
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Any
from datetime import datetime


@dataclass
class ProofAttempt:
    """Single proof generation attempt with all relevant metrics."""
    attempt_number: int
    success: bool
    generation_time: float  # seconds
    lean_check_time: float  # seconds
    total_time: float  # seconds
    timeout_occurred: bool = False  # True if Lean check timed out
    generation_error: Optional[str] = None
    lean_error: Optional[str] = None
    raw_output: Optional[str] = None
    extracted_solution: Optional[str] = None
    final_lean_code: Optional[str] = None
    lean_stdout: Optional[str] = None
    lean_stderr: Optional[str] = None


@dataclass
class ProblemResult:
    """Results for a single problem across all attempts."""
    problem_id: str
    problem_path: str
    mode: str  # "cot" or "noncot"
    dataset: str  # "minif2f" or "putnam"
    attempts: List[ProofAttempt]
    passed: bool  # True if any attempt succeeded
    first_success_attempt: Optional[int] = None  # 0-indexed attempt number
    total_generation_time: float = 0.0
    total_lean_check_time: float = 0.0
    total_time: float = 0.0


@dataclass
class EvaluationMetrics:
    """Complete evaluation metrics for a dataset."""
    dataset: str
    mode: str
    total_problems: int
    problems_passed: int
    problems_failed: int
    pass_at_1: float
    pass_at_8: float
    pass_at_32: float
    total_timeouts: int  # Number of attempts that timed out
    problems_with_timeouts: int  # Number of problems that had at least one timeout
    avg_generation_time: float
    avg_lean_check_time: float
    avg_total_time: float
    median_generation_time: float
    median_lean_check_time: float
    median_total_time: float
    total_generation_time: float
    total_lean_check_time: float
    total_evaluation_time: float
    timestamp: str
    problem_results: List[ProblemResult]


class MetricsTracker:
    """Tracks metrics during evaluation and saves results."""
    
    def __init__(self, output_dir: Path, dataset: str, mode: str):
        """
        Initialize metrics tracker.
        
        Args:
            output_dir: Directory to save results
            dataset: Dataset name ("minif2f" or "putnam")
            mode: Generation mode ("cot" or "noncot")
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.dataset = dataset
        self.mode = mode
        self.problem_results: List[ProblemResult] = []
        self.evaluation_start_time = time.time()
        
        # Create subdirectories
        self.proofs_dir = self.output_dir / "proofs"
        self.proofs_dir.mkdir(exist_ok=True)
        self.metrics_dir = self.output_dir / "metrics"
        self.metrics_dir.mkdir(exist_ok=True)
    
    def start_problem(self, problem_id: str, problem_path: str) -> str:
        """
        Start tracking a new problem.
        
        Returns:
            problem_key: Unique identifier for this problem
        """
        return f"{self.dataset}_{self.mode}_{problem_id}"
    
    def record_attempt(
        self,
        problem_id: str,
        problem_path: str,
        attempt_number: int,
        success: bool,
        generation_time: float,
        lean_check_time: float,
        timeout_occurred: bool = False,
        generation_error: Optional[str] = None,
        lean_error: Optional[str] = None,
        raw_output: Optional[str] = None,
        extracted_solution: Optional[str] = None,
        final_lean_code: Optional[str] = None,
        lean_stdout: Optional[str] = None,
        lean_stderr: Optional[str] = None,
    ) -> ProofAttempt:
        """
        Record a single proof attempt.
        
        Returns:
            ProofAttempt object
        """
        total_time = generation_time + lean_check_time
        
        attempt = ProofAttempt(
            attempt_number=attempt_number,
            success=success,
            generation_time=generation_time,
            lean_check_time=lean_check_time,
            total_time=total_time,
            timeout_occurred=timeout_occurred,
            generation_error=generation_error,
            lean_error=lean_error,
            raw_output=raw_output,
            extracted_solution=extracted_solution,
            final_lean_code=final_lean_code,
            lean_stdout=lean_stdout,
            lean_stderr=lean_stderr,
        )
        
        return attempt
    
    def finish_problem(
        self,
        problem_id: str,
        problem_path: str,
        attempts: List[ProofAttempt],
    ):
        """
        Finish tracking a problem and save results.
        
        Args:
            problem_id: Problem identifier
            problem_path: Path to problem file
            attempts: List of all proof attempts for this problem
        """
        passed = any(attempt.success for attempt in attempts)
        first_success = None
        for i, attempt in enumerate(attempts):
            if attempt.success:
                first_success = i
                break
        
        total_gen_time = sum(a.generation_time for a in attempts)
        total_lean_time = sum(a.lean_check_time for a in attempts)
        total_time = sum(a.total_time for a in attempts)
        
        problem_result = ProblemResult(
            problem_id=problem_id,
            problem_path=str(problem_path),
            mode=self.mode,
            dataset=self.dataset,
            attempts=attempts,
            passed=passed,
            first_success_attempt=first_success,
            total_generation_time=total_gen_time,
            total_lean_check_time=total_lean_time,
            total_time=total_time,
        )
        
        self.problem_results.append(problem_result)
        
        # Save individual problem result
        self._save_problem_result(problem_result)
    
    def _save_problem_result(self, problem_result: ProblemResult):
        """Save individual problem result to JSON file."""
        # Create safe filename
        safe_id = problem_result.problem_id.replace("/", "_").replace("\\", "_")
        filename = f"{safe_id}.json"
        filepath = self.proofs_dir / filename
        
        # Convert to dict, handling None values
        result_dict = asdict(problem_result)
        
        # Save to file
        with open(filepath, 'w') as f:
            json.dump(result_dict, f, indent=2, default=str)
    
    def compute_metrics(self) -> EvaluationMetrics:
        """Compute final evaluation metrics."""
        total_problems = len(self.problem_results)
        problems_passed = sum(1 for r in self.problem_results if r.passed)
        problems_failed = total_problems - problems_passed
        
        # Compute Pass@K
        pass_at_1 = sum(1 for r in self.problem_results if r.attempts and r.attempts[0].success) / total_problems if total_problems > 0 else 0.0
        
        # Pass@8: check if any of first 8 attempts succeeded
        pass_at_8_count = 0
        for r in self.problem_results:
            if r.attempts:
                if any(r.attempts[i].success for i in range(min(8, len(r.attempts)))):
                    pass_at_8_count += 1
        pass_at_8 = pass_at_8_count / total_problems if total_problems > 0 else 0.0
        
        pass_at_32 = problems_passed / total_problems if total_problems > 0 else 0.0
        
        # Compute timeout statistics
        total_timeouts = sum(1 for r in self.problem_results for a in r.attempts if a.timeout_occurred)
        problems_with_timeouts = sum(1 for r in self.problem_results 
                                     if any(a.timeout_occurred for a in r.attempts))
        
        # Compute timing statistics
        all_gen_times = [a.generation_time for r in self.problem_results for a in r.attempts]
        all_lean_times = [a.lean_check_time for r in self.problem_results for a in r.attempts]
        all_total_times = [a.total_time for r in self.problem_results for a in r.attempts]
        
        avg_gen_time = sum(all_gen_times) / len(all_gen_times) if all_gen_times else 0.0
        avg_lean_time = sum(all_lean_times) / len(all_lean_times) if all_lean_times else 0.0
        avg_total_time = sum(all_total_times) / len(all_total_times) if all_total_times else 0.0
        
        median_gen_time = sorted(all_gen_times)[len(all_gen_times) // 2] if all_gen_times else 0.0
        median_lean_time = sorted(all_lean_times)[len(all_lean_times) // 2] if all_lean_times else 0.0
        median_total_time = sorted(all_total_times)[len(all_total_times) // 2] if all_total_times else 0.0
        
        total_gen_time = sum(all_gen_times)
        total_lean_time = sum(all_lean_times)
        total_eval_time = time.time() - self.evaluation_start_time
        
        metrics = EvaluationMetrics(
            dataset=self.dataset,
            mode=self.mode,
            total_problems=total_problems,
            problems_passed=problems_passed,
            problems_failed=problems_failed,
            pass_at_1=pass_at_1,
            pass_at_8=pass_at_8,
            pass_at_32=pass_at_32,
            total_timeouts=total_timeouts,
            problems_with_timeouts=problems_with_timeouts,
            avg_generation_time=avg_gen_time,
            avg_lean_check_time=avg_lean_time,
            avg_total_time=avg_total_time,
            median_generation_time=median_gen_time,
            median_lean_check_time=median_lean_time,
            median_total_time=median_total_time,
            total_generation_time=total_gen_time,
            total_lean_check_time=total_lean_time,
            total_evaluation_time=total_eval_time,
            timestamp=datetime.now().isoformat(),
            problem_results=self.problem_results,
        )
        
        return metrics
    
    def save_metrics(self, metrics: Optional[EvaluationMetrics] = None):
        """Save final metrics to JSON file."""
        if metrics is None:
            metrics = self.compute_metrics()
        
        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.dataset}_{self.mode}_{timestamp}.json"
        filepath = self.metrics_dir / filename
        
        # Convert to dict
        metrics_dict = asdict(metrics)
        
        # Save to file
        with open(filepath, 'w') as f:
            json.dump(metrics_dict, f, indent=2, default=str)
        
        return filepath
    
    def print_summary(self, metrics: Optional[EvaluationMetrics] = None):
        """Print summary statistics to console."""
        if metrics is None:
            metrics = self.compute_metrics()
        
        print("\n" + "="*80)
        print("EVALUATION SUMMARY")
        print("="*80)
        print(f"Dataset: {metrics.dataset.upper()}")
        print(f"Mode: {metrics.mode.upper()}")
        print(f"Timestamp: {metrics.timestamp}")
        print()
        print("ACCURACY METRICS:")
        print(f"  Total Problems: {metrics.total_problems}")
        print(f"  Problems Passed: {metrics.problems_passed}")
        print(f"  Problems Failed: {metrics.problems_failed}")
        # Calculate Pass@K counts
        pass_at_1_count = sum(1 for r in metrics.problem_results if r.attempts and r.attempts[0].success)
        pass_at_8_count = sum(1 for r in metrics.problem_results 
                              if r.attempts and any(r.attempts[i].success for i in range(min(8, len(r.attempts)))))
        
        print(f"  Pass@1:  {metrics.pass_at_1:.2%} ({pass_at_1_count}/{metrics.total_problems})")
        print(f"  Pass@8:  {metrics.pass_at_8:.2%} ({pass_at_8_count}/{metrics.total_problems})")
        print(f"  Pass@32: {metrics.pass_at_32:.2%} ({metrics.problems_passed}/{metrics.total_problems})")
        print()
        print("TIMEOUT STATISTICS:")
        print(f"  Total Timeouts: {metrics.total_timeouts} attempts")
        print(f"  Problems with Timeouts: {metrics.problems_with_timeouts}/{metrics.total_problems}")
        if metrics.total_timeouts > 0:
            timeout_rate = metrics.total_timeouts / sum(len(r.attempts) for r in metrics.problem_results) * 100
            print(f"  Timeout Rate: {timeout_rate:.1f}% of attempts")
        print()
        print("TIMING METRICS:")
        print(f"  Average Generation Time: {metrics.avg_generation_time:.2f}s")
        print(f"  Median Generation Time:  {metrics.median_generation_time:.2f}s")
        print(f"  Average Lean Check Time: {metrics.avg_lean_check_time:.2f}s")
        print(f"  Median Lean Check Time:  {metrics.median_lean_check_time:.2f}s")
        print(f"  Average Total Time:      {metrics.avg_total_time:.2f}s")
        print(f"  Median Total Time:       {metrics.median_total_time:.2f}s")
        print()
        print("TOTAL TIME:")
        print(f"  Total Generation Time:   {metrics.total_generation_time:.2f}s ({metrics.total_generation_time/3600:.2f} hours)")
        print(f"  Total Lean Check Time:   {metrics.total_lean_check_time:.2f}s ({metrics.total_lean_check_time/3600:.2f} hours)")
        print(f"  Total Evaluation Time:   {metrics.total_evaluation_time:.2f}s ({metrics.total_evaluation_time/3600:.2f} hours)")
        print("="*80)
