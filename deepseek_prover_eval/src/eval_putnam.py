"""
PutnamBench evaluation script for DeepSeek-Prover-V2-7B.

This module provides the main evaluation loop for the PutnamBench benchmark,
supporting both Chain-of-Thought (CoT) and non-CoT generation modes.

The evaluation process:
1. Loads the DeepSeek-Prover-V2-7B model
2. For each problem, generates multiple proof attempts
3. Extracts and verifies proofs using Lean 4
4. Computes Pass@K metrics (Pass@1, Pass@8, Pass@32)

Usage:
    python src/eval_putnam.py --mode noncot
    python src/eval_putnam.py --mode cot
"""
import argparse
import glob
import re
import threading
import sys
from pathlib import Path

# Add parent directory to path so we can import config
sys.path.insert(0, str(Path(__file__).parent.parent))

from tqdm import tqdm
import torch

from config import (
    PUTNAM_DIR,
    TEMPERATURE,
    TOP_P,
    NUM_SAMPLES,
    MAX_NEW_TOKENS_NONCOT,
    MAX_NEW_TOKENS_COT,
    MODEL_ID,
)

from src.model_loader import load_model_and_tokenizer
from src.lean_utils import check_lean_file, MODEL_GENERATION_TIMEOUT
from src.signal_handler import setup_signal_handlers, is_shutdown_requested


###########################################################
# Safe model generation wrapper with timeout
###########################################################

def safe_generate(model, tokenizer, prompt: str, mode: str):
    """
    Safe wrapper around model.generate() with timeout protection.
    Never throws. Returns either (decoded_text, None) or (None, error_message).
    
    Note: If timeout occurs, the generation thread may continue running in the background
    until it completes. This is a limitation of PyTorch's blocking generate() operation.
    However, we make the thread non-daemon so it can be tracked and cleaned up on program exit.
    """
    result = [None]
    error = [None]
    done = threading.Event()
    cancelled = threading.Event()  # Flag to signal cancellation
    
    # Use mode-specific max tokens
    max_tokens = MAX_NEW_TOKENS_COT if mode == "cot" else MAX_NEW_TOKENS_NONCOT
    
    def generate_worker():
        try:
            # Check if cancelled before starting
            if cancelled.is_set():
                return
            
            inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

            # Check again after tokenization
            if cancelled.is_set():
                return

            with torch.no_grad():
                out = model.generate(
                    **inputs,
                    max_new_tokens=max_tokens,
                    do_sample=True,
                    temperature=TEMPERATURE,
                    top_p=TOP_P,
                )

            # Check if cancelled after generation
            if not cancelled.is_set():
                decoded = tokenizer.decode(out[0], skip_special_tokens=True)
                result[0] = decoded
        except Exception as e:
            if not cancelled.is_set():
                error[0] = str(e)
        finally:
            done.set()
    
    # Make thread non-daemon so we can track it and it doesn't prevent clean shutdown
    thread = threading.Thread(target=generate_worker, daemon=False)
    thread.start()
    
    if not done.wait(timeout=MODEL_GENERATION_TIMEOUT):
        print(f"[WARNING] Model generation timed out after {MODEL_GENERATION_TIMEOUT}s", flush=True)
        # Signal cancellation (though generate() may continue running)
        cancelled.set()
        # Note: The thread will continue until generate() completes, but we return immediately
        # This is a known limitation - PyTorch's generate() cannot be easily interrupted
        return None, f"Model generation TIMEOUT after {MODEL_GENERATION_TIMEOUT} seconds"
    
    if error[0] is not None:
        return None, error[0]
    
    return result[0], None


###########################################################
# Extract solution block (same logic as eval_minif2f)
###########################################################

def extract_solution_block(raw: str, theorem_name: str | None):
    """
    Extract the final Lean theorem (header + proof) from model output.
    For CoT mode, this may include natural language reasoning before the Lean code.
    
    Strategy:
      1. Find ALL code blocks
      2. Look for one that contains the theorem AND a proof (not "sorry")
      3. Extract the solution from that block
    """
    if theorem_name is None:
        return None
    
    key = f"theorem {theorem_name}"
    
    # Find ALL code blocks
    lean_block_patterns = [
        r"```lean4\s*(.*?)```",
        r"```lean\s*(.*?)```",
    ]
    
    lean_blocks = []
    for pattern in lean_block_patterns:
        matches = list(re.finditer(pattern, raw, flags=re.DOTALL))
        for match in matches:
            block = match.group(1).strip()
            lean_blocks.append((match.start(), block))
    
    # Look for a block that contains the theorem AND a proof (not "sorry")
    solution_block = None
    for start_pos, block in reversed(lean_blocks):  # Start from last (most likely solution)
        if key in block:
            # Check if this block has a proof (":= by" or proof tactics) and NOT just "sorry"
            if ":=" in block and (":= by" in block or ("sorry" not in block.split(key)[-1][:200])):
                # This looks like a solution with a proof
                theorem_start = block.rfind(key)
                if theorem_start != -1:
                    solution_candidate = block[theorem_start:].strip()
                    # Make sure it's not just the prompt with "sorry"
                    if "sorry" not in solution_candidate or ":=" in solution_candidate.split("sorry")[0]:
                        solution_block = solution_candidate
                        break
    
    if solution_block:
        solution = solution_block
    else:
        # Fallback: try to find theorem declaration in raw text
        start_idx = raw.rfind(key)
        if start_idx == -1:
            return None
        tail = raw[start_idx:]
        fence_idx = tail.find("```")
        if fence_idx != -1:
            tail = tail[:fence_idx]
        solution = tail.strip()
    
    # Clean up: remove leading imports/open statements
    lines = solution.splitlines()
    cleaned_lines = []
    for ln in lines:
        stripped = ln.lstrip()
        if stripped.startswith("import ") or stripped.startswith("open ") or stripped.startswith("open scoped "):
            continue
        cleaned_lines.append(ln)
    
    # Strip leading blank lines
    while cleaned_lines and cleaned_lines[0].strip() == "":
        cleaned_lines.pop(0)
    
    if not cleaned_lines:
        return None
    
    return "\n".join(cleaned_lines).strip()


###########################################################
# Check if model is available
###########################################################

def check_model_available():
    """Check if model is downloaded before starting."""
    from pathlib import Path
    import os
    
    # Check multiple possible cache locations
    cache_paths = [
        Path.home() / ".cache" / "huggingface" / "hub",
        Path.home() / ".cache" / "huggingface",
        Path(os.environ.get("HF_HOME", "")) / "hub" if os.environ.get("HF_HOME") else None,
    ]
    
    for cache_path in cache_paths:
        if cache_path is None or not cache_path.exists():
            continue
        model_dirs = list(cache_path.glob(f"models--{MODEL_ID.replace('/', '--')}*"))
        if model_dirs:
            # Check if it has files
            model_dir = model_dirs[0]
            files = list(model_dir.rglob("*"))
            if len(files) > 5:  # Has some files
                return True
    
    # Also try to import and check if transformers can find it
    try:
        from transformers import AutoTokenizer
        # Just check if we can access it (won't download if cached)
        tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, local_files_only=True)
        return True
    except:
        pass
    
    return False


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
        # CoT mode: model should output natural language reasoning followed by Lean code
        return (
            "Complete the following Lean 4 code:\n"
            "```lean4\n"
            f"{theorem_src}\n"
            "```\n"
            "First, analyze the problem and explain your reasoning step-by-step in natural language. "
            "Then provide the complete Lean 4 proof code."
        )


###########################################################
# Evaluate Putnam Bench
###########################################################

def evaluate_putnam(mode: str):
    setup_signal_handlers()
    
    # Check if model is downloaded
    if not check_model_available():
        print("="*60)
        print("WARNING: Model not found in cache!")
        print("="*60)
        print("The model needs to be downloaded first (this takes 10-30 minutes).")
        print("You can either:")
        print("  1. Run: python3 download_model.py  (recommended)")
        print("  2. Continue anyway (will download now, but may appear to hang)")
        print("="*60)
        
        # Check if running interactively (has TTY)
        if sys.stdin.isatty():
            response = input("\nContinue with download now? (y/N): ")
            if response.lower() != 'y':
                print("Exiting. Run 'python3 download_model.py' first, then try again.")
                return
        else:
            # Non-interactive mode - just proceed (model will download)
            print("\nRunning non-interactively. Proceeding with download if needed...")
            print("(This may take 10-30 minutes)")
    
    print("="*60)
    print("Loading model from cache...")
    print("If this hangs, press Ctrl+C to cancel")
    print("="*60)
    try:
        model, tokenizer = load_model_and_tokenizer()
        print("✓ Model loaded successfully!")
    except KeyboardInterrupt:
        print("\n[INFO] Model loading interrupted by user")
        return
    except Exception as e:
        print(f"\n[ERROR] Failed to load model: {e}")
        print("If download was interrupted, try running: python3 download_model.py")
        return

    # --- Quick Lean environment sanity check (once) ---
    print("Checking Lean environment...")
    test_ok, _, test_err = check_lean_file(
        "import Mathlib\n#check Nat",
        str(Path(PUTNAM_DIR) / "lean4"),
    )
    if not test_ok:
        print("WARNING: Lean sanity check failed or timed out.")
        print("This might be normal if the project needs to build dependencies.")
        print("Lean error:\n", test_err)
        print("Continuing anyway - individual proof checks will show if there are issues...")
        # Don't return - continue with evaluation

    # All Lean source files in the PutnamBench Lean project
    putnam_src_glob = str(Path(PUTNAM_DIR) / "lean4" / "src" / "putnam_*.lean")
    files = sorted(glob.glob(putnam_src_glob))

    # Optional: Filter to specific problems for testing
    # Uncomment and modify as needed:
    # files = [f for f in files if Path(f).name == "putnam_1962_a1.lean"]  # Test single problem
    # files = files[:10]  # Test first 10 problems

    total = len(files)
    
    # Track results for Pass@K computation
    results = []

    print(f"Evaluating on {total} Putnam problems...")

    for f in tqdm(files):
        if is_shutdown_requested():
            print("\n[INFO] Shutdown requested, stopping evaluation...")
            break
            
        print(f"\n=== Checking: {f} ===", flush=True)

        src = Path(f).read_text()
        prompt = build_prompt(src, mode)

        theorem_name = Path(f).stem
        problem_results = []  # Track successes for this problem

        for attempt in range(NUM_SAMPLES):
            if is_shutdown_requested():
                break
            print(f"--- Sample {attempt + 1}/{NUM_SAMPLES} ---", flush=True)

            decoded, gen_error = safe_generate(model, tokenizer, prompt, mode)

            if gen_error:
                print(f"[GENERATION ERROR] {gen_error}")
                problem_results.append(False)
                continue

            print("=== RAW MODEL OUTPUT ===")
            print(decoded[:500] + "..." if len(decoded) > 500 else decoded)

            # Extract solution using the same logic as eval_minif2f
            solution_block = extract_solution_block(decoded, theorem_name)

            if solution_block is None:
                print("Could not extract a Lean solution block, skipping this sample…")
                problem_results.append(False)
                continue

            print("=== EXTRACTED SOLUTION BLOCK ===")
            print(solution_block)

            # Sanity checks
            if f"theorem {theorem_name}" not in solution_block:
                print(
                    f"Extracted block does NOT contain `theorem {theorem_name}`; "
                    "treating as invalid and skipping this sample…"
                )
                problem_results.append(False)
                continue

            if "sorry" in solution_block and ":=" not in solution_block.split("sorry")[0]:
                print(
                    "Extracted block still contains `sorry` without a proof; "
                    "treating as unsolved and skipping this sample…"
                )
                problem_results.append(False)
                continue
            
            # Use the extracted solution block
            orig = solution_block

            # Assemble the final Lean file
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

            problem_results.append(ok)
            
            if ok:
                print(f"✓ Problem solved on attempt {attempt+1}")

        results.append(problem_results)

    # Compute Pass@K metrics
    if total > 0:
        print("\n" + "="*60)
        print("EVALUATION RESULTS")
        print("="*60)
        
        # Compute Pass@K for various K values
        k_values = [1, 8, 32] if NUM_SAMPLES >= 32 else [1, min(8, NUM_SAMPLES), NUM_SAMPLES]
        
        for k in k_values:
            if k > NUM_SAMPLES:
                continue
            passed = sum(1 for problem_results in results if any(problem_results[:k]))
            pass_at_k = passed / total if total > 0 else 0.0
            print(f"Pass@{k}: {passed}/{total} = {pass_at_k:.2%}")
        
        # Also show overall (Pass@NUM_SAMPLES)
        overall_passed = sum(1 for problem_results in results if any(problem_results))
        print(f"\nOverall (Pass@{NUM_SAMPLES}): {overall_passed}/{total} = {overall_passed/total:.2%}")
    else:
        print("\nNo problems matched the filter; nothing evaluated.")
    
    # Exit if shutdown was requested
    if is_shutdown_requested():
        import sys
        print("\n[INFO] Exiting due to shutdown request.")
        sys.exit(0)


###########################################################
# Main
###########################################################

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["cot", "noncot"], default="noncot")
    args = parser.parse_args()

    evaluate_putnam(args.mode)
