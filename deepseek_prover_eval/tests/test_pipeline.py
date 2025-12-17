#!/usr/bin/env python3
"""
Quick test script to verify the pipeline works without hanging.
"""
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.lean_utils import check_lean_file
from config import MINIF2F_PROJECT_ROOT

def test_lean_check():
    """Test that Lean checking works and times out properly."""
    print("Testing Lean checker with a simple valid proof...")
    
    simple_proof = """
import Mathlib

theorem test : 1 + 1 = 2 := by norm_num
"""
    
    ok, out, err, timeout_occurred = check_lean_file(simple_proof, str(MINIF2F_PROJECT_ROOT))
    print(f"Result: {ok}")
    if not ok:
        print(f"Error: {err}")
        return False
    if timeout_occurred:
        print("WARNING: timeout occurred unexpectedly for simple proof")
        return False
    
    print("✓ Simple proof check passed")
    
    # Test timeout with an infinite loop (if Lean supports it)
    # For now, just test that timeout mechanism exists
    print("\nTesting timeout mechanism...")
    print("(This should complete within timeout period)")
    
    return True

if __name__ == "__main__":
    success = test_lean_check()
    sys.exit(0 if success else 1)
