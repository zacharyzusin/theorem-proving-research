import argparse
import glob
import re
from pathlib import Path

from tqdm import tqdm
import torch

from config import (
    MINIF2F_EXTRACTED_GLOB,
    PROMPT_NONCOT,
    MINIF2F_PROJECT_ROOT,
    PROMPT_COT,
    MAX_NEW_TOKENS,
    TEMPERATURE,
    TOP_P,
    NUM_SAMPLES,
)

from src.model_loader import load_model_and_tokenizer
from src.lean_utils import check_lean_file


###########################################################
# Safe model generation wrapper
###########################################################


def safe_generate(model, tokenizer, prompt: str):
    """
    Safe wrapper around model.generate().
    Never throws. Returns either (decoded_text, None) or (None, error_message).
    """
    try:
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

        with torch.no_grad():
            out = model.generate(
                **inputs,
                max_new_tokens=MAX_NEW_TOKENS,
                do_sample=True,
                temperature=TEMPERATURE,
                top_p=TOP_P,
            )

        decoded = tokenizer.decode(out[0], skip_special_tokens=True)
        return decoded, None

    except Exception as e:
        return None, str(e)


###########################################################
# Prompt construction
###########################################################


def build_prompt(theorem_src: str, mode: str) -> str:
    """
    Build the prompt for CoT / non-CoT modes.

    theorem_src is the *full* MiniF2F .lean file (problem_XXXX.lean).
    """
    if mode == "noncot":
        return (
            "Complete the following Lean 4 code:\n"
            "```lean4\n"
            f"{theorem_src}\n"
            "```"
        )
    else:
        # CoT mode: ask for a proof plan before the Lean code
        return (
            "Complete the following Lean 4 code:\n"
            "```lean4\n"
            f"{theorem_src}\n"
            "```\n"
            "Before producing the Lean 4 code, write a detailed proof plan.\n"
        )


###########################################################
# Helper: extract theorem name from the MiniF2F problem file
###########################################################


def extract_theorem_name(problem_src: str):
    """
    Try to extract the first theorem/lemma/example name from the MiniF2F problem.
    We assume lines like:

      theorem foo : ...
      lemma bar : ...
      example baz : ...

    Returns the name as a string, or None if not found.
    """
    for keyword in ("theorem", "lemma", "example"):
        m = re.search(rf"\b{keyword}\s+([^\s:]+)", problem_src)
        if m:
            return m.group(1)
    return None


###########################################################
# Helper: extract solution theorem block from model output
###########################################################


def extract_solution_block(raw: str, theorem_name: str | None):
    """
    Heuristic extraction of the final Lean theorem (header + proof)
    for the given theorem name from the raw model output.

    Strategy:
      1. If we know the theorem name, take the *last* occurrence of
         "theorem <name>" in the raw output.
      2. From there, keep everything up to the next ``` fence (if present),
         otherwise up to end-of-string.
      3. Strip any leading ```lean4/```lean lines if the model wrapped it
         in a code fence.
      4. Strip leading imports / open lines from the block (we'll reuse the
         imports from the MiniF2F file itself).
    """
    # 1. Find last theorem occurrence if we know the name
    start_idx = -1
    if theorem_name is not None:
        key = f"theorem {theorem_name}"
        start_idx = raw.rfind(key)

    # If we couldn't find it, just bail
    if start_idx == -1:
        return None

    tail = raw[start_idx:]

    # 2. Cut off at the next closing fence ``` if present
    fence_idx = tail.find("```")
    if fence_idx != -1:
        tail = tail[:fence_idx]

    tail = tail.strip()

    # 3. If it *starts* with ```lean4 / ```lean, drop that first line
    if tail.startswith("```lean4") or tail.startswith("```lean"):
        lines = tail.splitlines()
        # drop the first line (the ```lean4 fence)
        tail = "\n".join(lines[1:]).strip()

    # 4. Drop any leading imports / open lines from the solution block
    lines = tail.splitlines()
    cleaned_lines = []
    for ln in lines:
        stripped = ln.lstrip()
        if stripped.startswith("import ") or stripped.startswith("open ") or stripped.startswith(
            "open scoped "
        ):
            # skip imports/open from the model; we'll use the original file's
            continue
        cleaned_lines.append(ln)

    # Strip leading blank lines
    while cleaned_lines and cleaned_lines[0].strip() == "":
        cleaned_lines.pop(0)

    # If nothing remains, this extraction failed
    if not cleaned_lines:
        return None

    return "\n".join(cleaned_lines).strip()


###########################################################
# Helper: merge original preamble with solution theorem
###########################################################


def merge_problem_and_solution(problem_src: str, solution_block: str) -> str:
    """
    Combine the original MiniF2F problem file with the model's solution
    theorem block.

    - Keep the imports / `open` / `open scoped` etc. from the problem.
    - Replace the original theorem (with `:= sorry` or whatever) by just
      placing the model's theorem after the preamble.

    For most MiniF2F problems, there's exactly one theorem per file,
    so this is fine.
    """
    lines = problem_src.splitlines()
    idx_first_decl = None

    # Find first 'theorem'/'lemma'/'example' line
    for i, ln in enumerate(lines):
        stripped = ln.lstrip()
        if (
            stripped.startswith("theorem ")
            or stripped.startswith("lemma ")
            or stripped.startswith("example ")
        ):
            idx_first_decl = i
            break

    if idx_first_decl is None:
        # Fallback: keep the whole original file, then append the solution
        return problem_src.rstrip() + "\n\n" + solution_block.strip() + "\n"

    preamble = "\n".join(lines[:idx_first_decl]).rstrip()
    if preamble:
        preamble = preamble + "\n\n"

    final_lean = preamble + solution_block.strip() + "\n"
    return final_lean


###########################################################
# Main evaluation loop
###########################################################


def evaluate_minif2f(mode: str):
    model, tokenizer = load_model_and_tokenizer()

    files = sorted(glob.glob(MINIF2F_EXTRACTED_GLOB))

    files = files[:2]
    """files = [
        f for f in files
        if "mathd_numbertheory_299" in Path(f).read_text()
    ]"""

    total = len(files)
    solved = 0

    print(f"Evaluating on {total} MiniF2F problems...")

    for fpath in tqdm(files):
        print(f"\n=== Checking: {fpath} ===", flush=True)

        problem_src = Path(fpath).read_text()
        prompt = build_prompt(problem_src, mode)
        theorem_name = extract_theorem_name(problem_src)
        if theorem_name is None:
            print("[WARN] Could not find theorem name in problem file, skipping.")
            continue

        success = False

        for attempt in range(NUM_SAMPLES):
            print(f"--- Sample {attempt+1}/{NUM_SAMPLES} ---")

            decoded, gen_error = safe_generate(model, tokenizer, prompt)
            if gen_error is not None:
                print(f"[GENERATION ERROR] {gen_error}")
                continue

            print("=== RAW MODEL OUTPUT ===")
            print(decoded)

            # Extract the theorem+proof block for this theorem name
            solution_block = extract_solution_block(decoded, theorem_name)
            if solution_block is None:
                print("Could not extract a Lean solution block, skipping this sample…")
                continue

            print("=== EXTRACTED SOLUTION BLOCK ===")
            print(solution_block)

            # Assemble final Lean file
            final_lean = merge_problem_and_solution(problem_src, solution_block)

            print("=== FINAL LEAN FILE TO CHECK ===")
            print(final_lean)

            ok, out, err = check_lean_file(final_lean, MINIF2F_PROJECT_ROOT)

            print(f"LEAN CHECK RESULT = {ok}")
            if err:
                print("[lean stderr]")
                print(err)
            if out:
                print("[lean stdout]")
                print(out)

            if ok:
                success = True
                break

        solved += int(success)

    if total > 0:
        print(f"\nFinal Result ({mode}): {solved}/{total} = {solved/total:.2%}")
    else:
        print("\nNo problems matched the filter; nothing evaluated.")


###########################################################
# Entry point
###########################################################


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["cot", "noncot"], default="noncot")
    args = parser.parse_args()

    evaluate_minif2f(args.mode)
