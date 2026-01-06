## Evaluation Reports

This folder contains human-friendly reports generated from the final merged metrics of each evaluation run.

Start with the dataset-specific folders:

- MiniF2F: `minif2f_run/`
- PutnamBench: `putnam_run/`

Each dataset folder includes:
- `OVERVIEW.md` — high-level summary (accuracy, timing stats, failure breakdown, slowest problems, etc.)
- `summary.csv` — one row per problem with pass/fail, first-success attempt, timeouts, and timings
- `successes/PROBLEM_ID.txt` — first successful attempt’s final Lean code + timing metadata
- `failures/PROBLEM_ID.txt` — diagnostics for unsolved problems (timeouts, Lean/generation errors, truncated code)

Tip: If browsing on GitHub, open `OVERVIEW.md` first, then use the links and folder structure to drill down into successes and failures of interest. If working locally on a cluster, use tools like `head`, `grep`, or spreadsheet software to slice `summary.csv`.

