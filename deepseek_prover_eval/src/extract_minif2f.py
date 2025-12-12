"""
Extract individual problem files from MiniF2F dataset.

This script reads the consolidated MiniF2F Lean files (test.lean and valid.lean)
and extracts each theorem/lemma into a separate file for easier evaluation.
"""
import sys
from pathlib import Path
from tqdm import tqdm

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import MINIF2F_FORMAL_TEST, MINIF2F_FORMAL_VALID, MINIF2F_EXTRACTED_DIR

# Ensure output directory exists
MINIF2F_EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)

LEAN4_HEADER = """\
import Mathlib

open Real Nat Topology
open scoped BigOperators

"""

STARTERS = ("theorem ", "lemma ")


def split_header_body(path: Path):
    text = path.read_text()
    lines = text.splitlines()
    in_body = False
    body_lines = []

    for line in lines:
        if not in_body and line.lstrip().startswith(STARTERS):
            in_body = True
        if in_body:
            body_lines.append(line)

    return "\n".join(body_lines)


def extract_blocks(body: str):
    lines = body.splitlines()
    blocks = []
    current = []
    capturing = False

    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith(STARTERS):
            if capturing and current:
                blocks.append("\n".join(current))
                current = []
            capturing = True
        if capturing:
            current.append(line)

    if capturing and current:
        blocks.append("\n".join(current))

    return blocks


def extract_minif2f():
    print("Extractor running...\n")

    problem_id = 1
    src_files = [MINIF2F_FORMAL_TEST, MINIF2F_FORMAL_VALID]

    for f in src_files:
        print(f"Extracting from {f} ...")
        body = split_header_body(f)
        blocks = extract_blocks(body)

        for block in tqdm(blocks, desc=f.name):
            out = LEAN4_HEADER + block
            (MINIF2F_EXTRACTED_DIR / f"problem_{problem_id:04d}.lean").write_text(out)
            problem_id += 1

    print(f"\nExtraction complete: {problem_id - 1} problems written.\n")


if __name__ == "__main__":
    extract_minif2f()
