# DeepSeek-Prover-V2-7B Evaluation Pipeline

A production-ready evaluation pipeline for **DeepSeek-Prover-V2-7B** on formal theorem proving benchmarks (MiniF2F and PutnamBench) in both Chain-of-Thought (CoT) and non-CoT modes.

## Overview

This repository provides a complete evaluation framework that:
- Loads and runs the DeepSeek-Prover-V2-7B model
- Generates proofs for MiniF2F and PutnamBench problems
- Verifies proofs using Lean 4
- Computes Pass@K evaluation metrics
- Handles timeouts and process management safely

## Features

- ✅ **Safe Process Management**: Timeouts, signal handling, and process cleanup to prevent hanging
- ✅ **Dual Mode Support**: Both CoT (Chain-of-Thought) and non-CoT generation modes
- ✅ **Pass@K Metrics**: Standard evaluation metrics (Pass@1, Pass@8, Pass@32)
- ✅ **Robust Error Handling**: Graceful shutdown, timeout protection, resource cleanup
- ✅ **Production Ready**: Clean code structure, comprehensive documentation, proper organization

## Requirements

- Python 3.10+
- CUDA-capable GPU (24GB+ VRAM recommended, uses 4-bit quantization)
- Lean 4 with Mathlib
- Access to HuggingFace (for model download)

## Installation

### 1. Clone Dependencies

```bash
# Clone MiniF2F dataset
git clone https://github.com/openai/miniF2F
cd miniF2F
# Follow MiniF2F setup instructions to build Lean project

# Clone PutnamBench dataset
cd ..
git clone https://github.com/trishullab/PutnamBench
cd PutnamBench/lean4
# Follow PutnamBench setup instructions to build Lean project
```

### 2. Setup Python Environment

```bash
cd deepseek_prover_eval
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Download Model

The model will be downloaded automatically on first run, or you can download it separately:

```bash
python scripts/download_model.py
```

**Note**: Model download is ~14GB and takes 10-30 minutes depending on connection speed.

### 4. Extract MiniF2F Problems (if needed)

```bash
python src/extract_minif2f.py
```

This extracts individual problem files from the MiniF2F dataset into `data/minif2f_extracted/`.

## Usage

### Basic Evaluation

**MiniF2F (non-CoT mode):**
```bash
python src/eval_minif2f.py --mode noncot
```

**MiniF2F (CoT mode):**
```bash
python src/eval_minif2f.py --mode cot
```

**PutnamBench (non-CoT mode):**
```bash
python src/eval_putnam.py --mode noncot
```

**PutnamBench (CoT mode):**
```bash
python src/eval_putnam.py --mode cot
```

### Configuration

Edit `config.py` to adjust:
- Model generation parameters (temperature, top_p, max tokens)
- Number of samples per problem (NUM_SAMPLES)
- Dataset paths (via environment variables or direct editing)

### Environment Variables

You can override dataset paths using environment variables:

```bash
export MINIF2F_ROOT=/path/to/miniF2F
export PUTNAM_DIR=/path/to/PutnamBench
python src/eval_minif2f.py --mode noncot
```

## Project Structure

```
deepseek_prover_eval/
├── src/                    # Core evaluation code
│   ├── eval_minif2f.py    # MiniF2F evaluation script
│   ├── eval_putnam.py     # PutnamBench evaluation script
│   ├── extract_minif2f.py # MiniF2F problem extraction
│   ├── model_loader.py    # Model loading utilities
│   ├── lean_utils.py      # Lean verification utilities
│   └── signal_handler.py  # Graceful shutdown handling
├── scripts/               # Utility scripts
│   ├── download_model.py  # Model download script
│   ├── kill_stuck.sh      # Kill stuck processes
│   ├── monitor_download.sh # Monitor download progress
│   └── check_download_status.sh # Check download status
├── tests/                 # Test scripts
│   ├── test_pipeline.py   # Pipeline tests
│   └── test_single_problem.py # Single problem test
├── data/                  # Data directory
│   └── minif2f_extracted/ # Extracted MiniF2F problems
├── config.py              # Configuration file
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Evaluation Metrics

The pipeline computes **Pass@K** metrics, which measure the fraction of problems solved with at least one correct proof out of K attempts:

- **Pass@1**: Solved on first attempt
- **Pass@8**: Solved within 8 attempts
- **Pass@32**: Solved within 32 attempts

Results are printed at the end of evaluation.

## Safety Features

### Process Management
- **Timeouts**: All operations (model generation, Lean verification) have hard timeouts
- **Process Tree Killing**: Uses `psutil` to kill entire process trees, not just parent processes
- **Signal Handling**: Graceful shutdown on SIGINT/SIGTERM
- **Resource Cleanup**: Temporary files and processes are cleaned up properly

### Preventing Hanging Processes
- Lean verification timeout: 60 seconds (configurable)
- Model generation timeout: 300 seconds (5 minutes)
- Process group isolation for safe killing
- Non-daemon threads that don't prevent program exit

## Troubleshooting

### Model Download Issues
```bash
# Check download status
./scripts/check_download_status.sh

# Monitor download progress
./scripts/monitor_download.sh

# Kill stuck processes
./scripts/kill_stuck.sh
```

### Lean Verification Timeouts
If Lean checks timeout frequently:
1. Ensure Mathlib is built: `cd miniF2F && lake build`
2. Increase `LEAN_TIMEOUT` in `src/lean_utils.py` (default: 60s)
3. Check system resources (CPU, memory)

### GPU Memory Issues
If you run out of GPU memory:
- The code uses 4-bit quantization by default (see `config.py`)
- Reduce `MAX_NEW_TOKENS_COT` if needed
- Close other GPU processes