#!/usr/bin/env python3
"""
Entry point for MiniF2F evaluation.

This is a convenience script that calls the main evaluation function.
Can be run directly: python scripts/eval_minif2f.py --mode noncot
"""
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.eval_minif2f import evaluate_minif2f

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Evaluate DeepSeek-Prover-V2-7B on MiniF2F")
    parser.add_argument("--mode", choices=["cot", "noncot"], default="noncot",
                       help="Generation mode: 'cot' for Chain-of-Thought, 'noncot' for direct proof")
    parser.add_argument("--output-dir", type=str, default=None,
                       help="Directory to save metrics and results (default: data/results/minif2f)")
    verbosity_group = parser.add_mutually_exclusive_group()
    verbosity_group.add_argument(
        "--quiet",
        action="store_true",
        help="Reduce logging; show only high-level progress and summary",
    )
    verbosity_group.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging (default behavior)",
    )
    args = parser.parse_args()
    
    evaluate_minif2f(args.mode, args.output_dir, quiet=args.quiet, verbose=args.verbose)

