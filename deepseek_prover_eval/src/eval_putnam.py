# src/eval_putnam.py

import argparse
import glob
from pathlib import Path

from tqdm import tqdm
import torch

from config import (
    PUTNAM_DIR,
    PROMPT_NONCOT,
    PROMPT_COT,
    MAX_NEW_TOKENS,
    TEMPERATURE,
    TOP_P,
    NUM_SAMPLES,
)

from src.model_loader import load_model_and_tokenizer
from src.lean_utils import check_lean_file, extract_lean_blocks


###########################################################
# Safe model generation wrapper
###########################################################

def safe_generate(model, tokenizer, prompt: str):
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
# Build prompt
###########################################################

def build_prompt(theorem_src: str, mode: str) -> str:
    if mode == "noncot":
        return (
            "Complete the following Lean 4 code:\n"
            "```lean4\n"
            f"{theorem_src}\n"
            "```"
        )
    else:
        # CoT / proof-plan style
        return (
            "You are completing a Lean 4 theorem. Write only Lean 4 code. "
            "No natural language.\n\n"
            "Here is the code:\n"
            "```lean4\n"
            f"{theorem_src}\n"
            "```\n"
            "Before writing the final Lean 4 code, think step-by-step in a "
            "proof plan, but keep that reasoning hidden and output only the "
            "final Lean 4 code."
        )


###########################################################
# Evaluate Putnam Bench
###########################################################

def evaluate_putnam(mode: str):
    model, tokenizer = load_model_and_tokenizer()

    # --- Quick Lean environment sanity check (once) ---
    test_ok, _, test_err = check_lean_file(
        "import Mathlib\n#check Nat",
        str(Path(PUTNAM_DIR) / "lean4"),
    )
    if not test_ok:
        print("FATAL: Lean / Mathlib environment seems misconfigured.")
        print("Lean error:\n", test_err)
        return

    # All Lean source files in the PutnamBench Lean project
    putnam_src_glob = str(Path(PUTNAM_DIR) / "lean4" / "src" / "putnam_*.lean")
    files = sorted(glob.glob(putnam_src_glob))

    # TEMP: for debugging/testing, restrict to a single problem
    files = [
        f
        for f in files
        if Path(f).name in {
            "putnam_1962_a1.lean",
            # "putnam_2004_a1.lean",
            # "putnam_2002_a1.lean",
        }
    ]

    total = len(files)
    solved = 0

    print(f"Evaluating on {total} Putnam problems...")

    for f in tqdm(files):
        print(f"\n=== Checking: {f} ===", flush=True)

        src = Path(f).read_text()
        prompt = build_prompt(src, mode)

        # Derive the expected theorem name from the filename.
        # Example: "putnam_2000_a1.lean" -> "putnam_2000_a1"
        theorem_name = Path(f).stem

        success = False

        for attempt in range(NUM_SAMPLES):
            print(f"--- Sample {attempt + 1}/{NUM_SAMPLES} ---", flush=True)

            decoded, gen_error = safe_generate(model, tokenizer, prompt)

            if gen_error:
                print(f"[GENERATION ERROR] {gen_error}")
                continue

            print("=== RAW MODEL OUTPUT ===")
            print(decoded)

            ##################################################################
            # Extract solution block from the model output
            ##################################################################
            orig, tail = extract_lean_blocks(decoded)

            if orig is None:
                print("No Lean block found, skipping…")
                continue

            # Strip ANY `import` lines the model may have inserted
            orig = "\n".join(
                line for line in orig.splitlines()
                if not line.strip().startswith("import ")
            )

            print("=== EXTRACTED LEAN BLOCK ===")
            print(orig)

            # ---------- Sanity checks on the extracted block ----------

            # 1. Must contain the theorem we're trying to prove
            if f"theorem {theorem_name}" not in orig:
                print(
                    f"Extracted block does NOT contain `theorem {theorem_name}`; "
                    "treating as invalid and skipping this sample…"
                )
                continue

            # 2. Do not allow `sorry` in the theorem block
            if "sorry" in orig:
                print(
                    "Extracted block still contains `sorry`; "
                    "treating as unsolved and skipping this sample…"
                )
                continue

            ##################################################################
            # Assemble the final Lean file
            ##################################################################
            final_lean = (
                "import Mathlib\n\n"
                "open Real Nat Topology MeasureTheory\n"
                "open scoped BigOperators\n\n"
                + orig
            )

            print("=== FINAL LEAN FILE TO CHECK ===")
            print(final_lean)

            ok, out_str, err_str = check_lean_file(
                final_lean,
                str(Path(PUTNAM_DIR) / "lean4"),
            )

            print(f"LEAN CHECK RESULT = {ok}")
            if out_str:
                print("[lean stdout]")
                print(out_str)
            if err_str:
                print("[lean stderr]")
                print(err_str)

            # If Lean failed because the environment broke mid-run (rare),
            # you *could* add an extra guard here, e.g.:
            #
            # if (not ok) and ("unknown module prefix 'Mathlib'" in err_str
            #                  or "No directory 'Mathlib'" in err_str):
            #     print("\nFATAL: Lean environment broke during evaluation.")
            #     return
            #
            # but normally we just treat this as "attempt failed".

            if ok:
                success = True
                break

        solved += int(success)

    print(
        f"\nFinal Result ({mode}): {solved}/{total} = "
        f"{(solved / total if total > 0 else 0.0):.2%}"
    )


###########################################################
# Main
###########################################################

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["cot", "noncot"], default="noncot")
    args = parser.parse_args()

    evaluate_putnam(args.mode)
