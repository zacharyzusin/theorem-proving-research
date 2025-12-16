# Automated Theorem Proving with Lean + DeepSeek Prover

This repository contains a complete evaluation framework for running **DeepSeek-Prover-V2** models on formal mathematics benchmarks, including:

- **PutnamBench** (Lean 4 formalizations of Putnam problems)
- **MiniF2F** (competition math problems in Lean)

The framework loads the model, generates Lean proofs, extracts Lean code blocks, checks them inside real Lean projects, and computes the benchmark score.

---

## Features

- Clean evaluation pipeline for Lean 4 theorem-proving LLMs  
- Safe Lean execution with:
  - **Process-group isolation**
  - **Hard timeouts**
  - **Automatic SIGKILL cleanup**
- Robust Lean block extraction
- Compatibility with arbitrary model prompts (CoT and non-CoT)
- Easy extensibility to new Lean benchmarks

---

## 1. Installation

Clone your repository:

```bash
git clone https://github.com/zacharyzusin/theorem-proving-research.git
cd theorem-proving-research
```

Create a Python environment:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Make sure you have PyTorch with CUDA installed if you want GPU inference.

---

## 2. Model Setup (DeepSeek-Prover-V2)

Models are pulled from HuggingFace:

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

tok = AutoTokenizer.from_pretrained("deepseek-ai/DeepSeek-Prover-V2-7B")
model = AutoModelForCausalLM.from_pretrained(
    "deepseek-ai/DeepSeek-Prover-V2-7B",
    torch_dtype="auto",
    device_map="auto"
)
```

The repository already includes this logic in:

```bash
src/model_loader.py
```

---

## 3. Benchmarks

This repo expects two external benchmark directories:

### ✔ MiniF2F
https://github.com/openai/miniF2F

### ✔ PutnamBench
https://github.com/trishullab/PutnamBench

Clone them next to your evaluation repo, like:

```
project_root/
    theorem-proving-research/
    miniF2F/
    PutnamBench/
```

Your `config.py` must point to them:

```python
MINIF2F_DIR = "/path/to/miniF2F"
PUTNAM_DIR  = "/path/to/PutnamBench"
```

---

## 4. Safe Lean Execution

The file `src/lean_utils.py` includes:

- Timeouts
- Process group kill (`os.killpg`)
- Temporary file cleanup
- Isolation in the appropriate Lean project root

Lean is executed via:

```bash
lake env lean file.lean
```

This ensures Mathlib is available, and avoids the "unknown module Mathlib" error.

---

## 5. Running PutnamBench

Run:

```bash
python3 -m src.eval_putnam --mode cot
```

or without chain-of-thought:

```bash
python3 -m src.eval_putnam --mode noncot
```

This will:

1. Load the model
2. Load PutnamBench Lean files
3. Prompt model for Lean solutions
4. Extract the final `lean4` block
5. Check the Lean code in the PutnamBench Lean project
6. Report a score

---

## 6. Running MiniF2F

```bash
python3 -m src.eval_minif2f --mode cot
```

MiniF2F works similarly by extracting Lean code and checking inside the MiniF2F Lean project.

---

## 7. Timeout Configuration

The Lean verification timeout is configurable to handle proofs of varying complexity:

- **Default timeout**: 120 seconds (2 minutes) - increased from 60s to handle more complex proofs
- **Configurable via**: `LEAN_TIMEOUT` in `config.py` or `LEAN_TIMEOUT` environment variable

### Adjusting Timeouts

If you notice many proofs timing out:

1. **Increase the timeout in config.py:**
   ```python
   LEAN_TIMEOUT = 180  # 3 minutes
   ```

2. **Or set via environment variable:**
   ```bash
   export LEAN_TIMEOUT=180
   python3 -m src.eval_minif2f --mode noncot
   ```

### Understanding Timeouts

Complex proofs may require more time for:
- First-time Mathlib dependency compilation
- Complex proof tactics that take time to verify  
- Large proof terms
- Type checking complex expressions

The metrics system tracks timeouts separately from other failures, so you can:
- Identify which problems are timing out
- Analyze whether timeouts are due to valid but slow proofs vs. infinite loops
- Adjust timeout settings based on actual timeout patterns

Use the inspection tool to analyze timeout patterns:
```bash
python3 -m src.inspect_results data/results/minif2f --patterns
python3 -m src.inspect_results data/results/minif2f --list --timeouts-only
```

---

## 8. Metrics and Performance Tracking

The evaluation framework now includes comprehensive metrics tracking:

### Metrics Collected

- **Timing Metrics:**
  - Proof generation time per attempt
  - Lean verification time per attempt
  - Total time per problem
  - Average and median times across all attempts

- **Accuracy Metrics:**
  - Pass@1, Pass@8, Pass@32 scores
  - Success rate per problem
  - First successful attempt number

- **Detailed Results:**
  - Raw model outputs
  - Extracted solution blocks
  - Final Lean code checked
  - Error messages (generation errors, Lean errors)

### Running Evaluations with Metrics

Results are automatically saved to `data/results/{dataset}/`:

```bash
# Run evaluation (results saved automatically)
python3 -m src.eval_minif2f --mode noncot --output-dir data/results/minif2f
python3 -m src.eval_putnam --mode cot --output-dir data/results/putnam
```

Results are organized as:
```
data/results/{dataset}/
├── metrics/
│   └── {dataset}_{mode}_{timestamp}.json  # Complete metrics summary
└── proofs/
    └── {problem_id}.json  # Individual problem results
```

### Inspecting Results

Use the inspection tool to review generated proofs and analyze performance:

```bash
# Show overview of latest evaluation
python3 -m src.inspect_results data/results/minif2f --overview

# List all problems
python3 -m src.inspect_results data/results/minif2f --list

# Show only passed problems
python3 -m src.inspect_results data/results/minif2f --list --passed-only

# Show only failed problems
python3 -m src.inspect_results data/results/minif2f --list --failed-only

# Inspect a specific problem
python3 -m src.inspect_results data/results/minif2f --inspect problem_0073

# Show all attempts (including failures) for a problem
python3 -m src.inspect_results data/results/minif2f --inspect problem_0073 --show-all

# Analyze failure patterns
python3 -m src.inspect_results data/results/minif2f --patterns

# Compare all attempts for a problem
python3 -m src.inspect_results data/results/minif2f --compare problem_0073
```

The inspection tool provides:
- Overview statistics (accuracy, timing)
- Problem listings with filtering
- Detailed problem inspection (all attempts, errors, generated code)
- Pattern analysis (common error types, timing differences)
- Side-by-side attempt comparison

---

## 9. Submodules (Optional)

If you want your repository to include the benchmark repos as submodules:

```bash
git submodule add https://github.com/openai/miniF2F miniF2F
git submodule add https://github.com/trishullab/PutnamBench PutnamBench
```

To clone with submodules:

```bash
git clone --recursive https://github.com/zacharyzusin/theorem-proving-research.git
```

---

## 10. Folder Structure

```
theorem-proving-research/
│
├── src/
│   ├── eval_putnam.py
│   ├── eval_minif2f.py
│   ├── lean_utils.py
│   ├── model_loader.py
│   ├── metrics.py          # Metrics tracking and reporting
│   ├── inspect_results.py  # Qualitative inspection tool
│   └── ...
├── data/
│   └── results/
│       ├── minif2f/        # MiniF2F evaluation results
│       │   ├── metrics/    # Summary metrics JSON files
│       │   └── proofs/     # Individual problem results
│       └── putnam/         # PutnamBench evaluation results
│           ├── metrics/
│           └── proofs/
│
├── config.py
├── requirements.txt
├── README.md
│
├── miniF2F/          ← external repo or submodule
└── PutnamBench/      ← external repo or submodule
```
