## MiniF2F Evaluation Reports

Start here:
- Read `OVERVIEW.md` for an at-a-glance summary: total solved/failed, Pass@K, timing stats, failure breakdown, and slowest problems.
- Browse `successes/` for solved problems (final Lean code + timing per first-success attempt).
- Browse `failures/` for unsolved problems (timeouts, Lean/generation errors, and truncated code snippets for context).
- Use `summary.csv` for quick filtering/sorting across all problems.

Files
- `OVERVIEW.md`: High-level accuracy and performance metrics.
- `summary.csv` (columns):
  - `problem_id`: MiniF2F problem identifier
  - `passed`: true/false
  - `first_success_attempt`: 0-based index of first success, or -1 if no success
  - `num_attempts`: number of attempts (N = `NUM_SAMPLES`)
  - `num_successful_attempts`: how many of the N attempts succeeded
  - `num_timeouts`: count of timed-out attempts
  - `avg_generation_time_s`, `avg_lean_check_time_s`: per-attempt averages
- `successes/PROBLEM_ID.txt`: First successful attempt metadata and final Lean code.
- `failures/PROBLEM_ID.txt`: Per-attempt diagnostics for unsolved problems (timeouts, Lean/generation errors, truncated code).

Common tasks (examples)
- Count passes/fails quickly:
  - Open `summary.csv` in a spreadsheet, or run:
    - Passes: lines with `,true,`
    - Fails: lines with `,false,`
- Find problems that timed out:
  - Filter `summary.csv` where `num_timeouts > 0`
- Inspect a specific problem:
  - If passed: open `successes/PROBLEM_ID.txt`
  - If failed: open `failures/PROBLEM_ID.txt`

Notes
- Pass@K in `OVERVIEW.md` reflects the actual number of attempts (`NUM_SAMPLES`), here Pass@8.
- Timing stats in `OVERVIEW.md` are per attempt (generation, Lean check, and total).

