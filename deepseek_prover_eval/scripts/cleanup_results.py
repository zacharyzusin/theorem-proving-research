#!/usr/bin/env python3
"""
Prune empty directories under data/results to keep the repo clean.

This will ONLY remove directories that are empty (no files inside).
Safe to run multiple times.
"""
from __future__ import annotations

import os
from pathlib import Path


def remove_empty_dirs(root: Path) -> int:
    removed = 0
    # Walk bottom-up so we can remove parents after children
    for dirpath, dirnames, filenames in os.walk(root, topdown=False):
        p = Path(dirpath)
        # Consider a directory empty if no files and (after pruning) no subdirs
        if not any(Path(dirpath).iterdir()):
            try:
                p.rmdir()
                removed += 1
                print(f"Removed empty directory: {p}")
            except OSError:
                pass
    return removed


def main():
    project_root = Path(__file__).resolve().parent.parent
    results_root = project_root / "data" / "results"
    if not results_root.exists():
        print(f"No results directory found at: {results_root}")
        return 0
    removed = remove_empty_dirs(results_root)
    print(f"Done. Removed {removed} empty director{'y' if removed == 1 else 'ies'}.")
    return removed


if __name__ == "__main__":
    main()

