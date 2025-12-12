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
    args = parser.parse_args()
    
    evaluate_minif2f(args.mode)

