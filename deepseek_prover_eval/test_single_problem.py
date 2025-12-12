#!/usr/bin/env python3
"""
Quick test script to verify the pipeline works on a single problem.
Tests problem_0073.lean (54 % 6 = 0) which should be simple.
"""
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import the evaluation module
import src.eval_minif2f as eval_minif2f
from config import MINIF2F_PROJECT_ROOT

def test_single_problem():
    """Test a single simple problem."""
    print("="*60)
    print("Testing DeepSeek-Prover-V2-7B on a single problem")
    print("="*60)
    
    # Use problem_0073 (54 % 6 = 0) - should be simple
    problem_file = Path("minif2f_extracted/problem_0073.lean")
    
    if not problem_file.exists():
        print(f"ERROR: Problem file not found: {problem_file}")
        print(f"Current directory: {Path.cwd()}")
        return False
    
    print(f"\nProblem file: {problem_file}")
    problem_src = problem_file.read_text()
    print("\nProblem:")
    print(problem_src)
    
    # Load model
    print("\n" + "="*60)
    print("Loading model...")
    print("="*60)
    from src.model_loader import load_model_and_tokenizer
    model, tokenizer = load_model_and_tokenizer()
    print("Model loaded successfully!")
    
    # Test non-CoT mode first (faster)
    mode = "noncot"
    print(f"\n" + "="*60)
    print(f"Testing in {mode} mode")
    print("="*60)
    
    prompt = eval_minif2f.build_prompt(problem_src, mode)
    print("\nPrompt:")
    print(prompt)
    print("\n" + "-"*60)
    
    theorem_name = eval_minif2f.extract_theorem_name(problem_src)
    print(f"Theorem name: {theorem_name}")
    
    # Generate just 2 samples for quick testing
    print("\nGenerating 2 samples...")
    for attempt in range(2):
        print(f"\n--- Sample {attempt+1}/2 ---")
        
        decoded, gen_error = eval_minif2f.safe_generate(model, tokenizer, prompt, mode)
        if gen_error is not None:
            print(f"[GENERATION ERROR] {gen_error}")
            continue
        
        print("\n=== RAW MODEL OUTPUT (first 500 chars) ===")
        print(decoded[:500] + "..." if len(decoded) > 500 else decoded)
        
        solution_block = eval_minif2f.extract_solution_block(decoded, theorem_name)
        if solution_block is None:
            print("Could not extract a Lean solution block, skipping...")
            continue
        
        print("\n=== EXTRACTED SOLUTION BLOCK ===")
        print(solution_block)
        
        final_lean = eval_minif2f.merge_problem_and_solution(problem_src, solution_block)
        
        print("\n=== FINAL LEAN FILE TO CHECK ===")
        print(final_lean)
        
        from src.lean_utils import check_lean_file
        ok, out, err = check_lean_file(final_lean, str(MINIF2F_PROJECT_ROOT))
        
        print(f"\nLEAN CHECK RESULT = {ok}")
        if err:
            print("[lean stderr]")
            print(err[:500] if len(err) > 500 else err)
        if out:
            print("[lean stdout]")
            print(out[:500] if len(out) > 500 else out)
        
        if ok:
            print(f"\n✓✓✓ SUCCESS! Problem solved on attempt {attempt+1} ✓✓✓")
            return True
        else:
            print(f"\n✗ Attempt {attempt+1} failed")
    
    print("\n" + "="*60)
    print("Test completed - no successful proof found in 2 attempts")
    print("="*60)
    return False

if __name__ == "__main__":
    success = test_single_problem()
    sys.exit(0 if success else 1)
