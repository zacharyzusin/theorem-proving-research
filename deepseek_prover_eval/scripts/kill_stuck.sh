#!/bin/bash
# Helper script to kill stuck Python/Lean processes

echo "Killing stuck processes..."

# Kill Python processes running eval scripts
pkill -9 -f "eval_minif2f"
pkill -9 -f "eval_putnam"
pkill -9 -f "test_single_problem"

# Kill any Lean/lake processes
pkill -9 -f "lake env lean"
pkill -9 lean
pkill -9 lake

# Kill any Python processes that might be stuck
ps aux | grep python | grep -E "(eval|test)" | grep -v grep | awk '{print $2}' | xargs -r kill -9

echo "Done. Checking for remaining processes..."
ps aux | grep -E "(python.*eval|lean|lake)" | grep -v grep || echo "No stuck processes found."

