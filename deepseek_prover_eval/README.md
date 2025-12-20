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
git clone --recursive https://github.com/zacharyzusin/theorem-proving-research.git
cd theorem-proving-research
cd miniF2F
lake build  # Build Lean project with Mathlib

# Build PutnamBench
cd ../PutnamBench/lean4
lake build
```

### 2. Setup Python Environment

```bash
cd ../deepseek_prover_eval
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Download Model

The model will be downloaded automatically on first run, or you can download it separately:

```bash
# In an interactive GPU session (recommended)
srun --pty -t 0-01:00 --partition=short --gres=gpu:A6000:1 -A edu /bin/bash
source venv/bin/activate
python scripts/download_model.py
```

**Note**: Model download is ~14GB and takes 10-30 minutes depending on connection speed.

### 4. Extract MiniF2F Problems (if needed)

```bash
python src/extract_minif2f.py
```

This extracts individual problem files from the MiniF2F dataset into `data/minif2f_extracted/`.

### 5. Verify Setup

```bash
python scripts/verify_setup.py
```

This checks that all dependencies (Lean, Mathlib, model) are properly configured.

## Quick Start (Slurm Cluster)

For a complete evaluation run on a Slurm cluster:

```bash
# 1. Submit 16-shard parallel evaluation
sbatch eval_minif2f_array_16shards.sh

# 2. Monitor progress
squeue -u $USER
tail -f logs/eval_<JOB_ID>_*.out

# 3. After completion, merge results
python scripts/merge_shards.py data/results/minif2f_sharded_16 data/results/minif2f_merged --mode noncot

# 4. Examine results
python scripts/inspect_results.py data/results/minif2f_merged --overview
```

## Usage

### Basic Evaluation (Single GPU)

**MiniF2F (non-CoT mode):**
```bash
python src/eval_minif2f.py --mode noncot --output-dir data/results/minif2f
```

**MiniF2F (CoT mode):**
```bash
python src/eval_minif2f.py --mode cot --output-dir data/results/minif2f_cot
```

**PutnamBench (non-CoT mode):**
```bash
python src/eval_putnam.py --mode noncot --output-dir data/results/putnam
```

**PutnamBench (CoT mode):**
```bash
python src/eval_putnam.py --mode cot --output-dir data/results/putnam_cot
```

### Parallel Evaluation (Slurm Cluster)

For faster evaluation on a cluster, use the sharded evaluation scripts:

**16-shard MiniF2F evaluation:**
```bash
sbatch eval_minif2f_array_16shards.sh
```

**8-shard MiniF2F evaluation:**
```bash
sbatch eval_minif2f_array.sh
```

**Single GPU evaluation:**
```bash
sbatch eval_minif2f.sh
```

The sharded scripts automatically distribute problems across multiple GPUs and merge results.

### Merging Sharded Results

After running a sharded evaluation, merge all shards into a single directory:

```bash
python scripts/merge_shards.py data/results/minif2f_sharded_16 data/results/minif2f_merged --mode noncot
```

This creates a unified results directory with:
- All problem results in `proofs/`
- Aggregated metrics in `metrics/`

### Examining Results

Use the inspection tool to analyze results:

```bash
# Overview statistics
python scripts/inspect_results.py data/results/minif2f_merged --overview

# List all problems
python scripts/inspect_results.py data/results/minif2f_merged --list

# Show only passed problems
python scripts/inspect_results.py data/results/minif2f_merged --list --passed-only

# Show only failed problems
python scripts/inspect_results.py data/results/minif2f_merged --list --failed-only

# Inspect a specific problem
python scripts/inspect_results.py data/results/minif2f_merged --inspect problem_0001 --show-all

# Analyze failure patterns
python scripts/inspect_results.py data/results/minif2f_merged --patterns
```

### Configuration

Edit `config.py` to adjust:
- Model generation parameters (temperature, top_p, max tokens)
- Number of samples per problem (`NUM_SAMPLES`, default: 8)
- Lean verification timeout (`LEAN_TIMEOUT`, default: 600s / 10 minutes)
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
│   ├── metrics.py         # Metrics tracking and reporting
│   ├── inspect_results.py # Results inspection tool
│   └── signal_handler.py  # Graceful shutdown handling
├── scripts/               # Utility scripts
│   ├── download_model.py  # Model download script
│   ├── aggregate_shards.py # Aggregate metrics from shards
│   ├── merge_shards.py     # Merge sharded results into one directory
│   ├── inspect_results.py # Results inspection (wrapper)
│   ├── kill_stuck.sh      # Kill stuck processes
│   ├── monitor_download.sh # Monitor download progress
│   └── check_download_status.sh # Check download status
├── eval_minif2f.sh        # Single-GPU Slurm script
├── eval_minif2f_array.sh  # 8-shard Slurm script
├── eval_minif2f_array_16shards.sh # 16-shard Slurm script
├── tests/                 # Test scripts
│   ├── test_pipeline.py   # Pipeline tests
│   └── test_single_problem.py # Single problem test
├── data/                  # Data directory
│   ├── minif2f_extracted/ # Extracted MiniF2F problems
│   └── results/           # Evaluation results (ignored by git)
│       ├── minif2f_sharded_16/ # Sharded results (16 shards)
│       └── minif2f_merged/     # Merged results
├── logs/                  # Slurm job logs (ignored by git)
├── config.py              # Configuration file
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Evaluation Metrics

The pipeline computes **Pass@K** metrics, which measure the fraction of problems solved with at least one correct proof out of K attempts:

- **Pass@1**: Solved on first attempt
- **Pass@8**: Solved within 8 attempts
- **Pass@N**: Solved within N attempts (where N = `NUM_SAMPLES` from config, default: 8)

Results are saved to JSON files in the `metrics/` subdirectory and printed at the end of evaluation. Each problem's detailed results (all attempts, errors, timing) are saved to individual JSON files in the `proofs/` subdirectory.

## Safety Features

### Process Management
- **Timeouts**: All operations (model generation, Lean verification) have hard timeouts
- **Process Tree Killing**: Uses `psutil` to kill entire process trees, not just parent processes
- **Signal Handling**: Graceful shutdown on SIGINT/SIGTERM
- **Resource Cleanup**: Temporary files and processes are cleaned up properly

### Preventing Hanging Processes
- Lean verification timeout: 600 seconds (10 minutes, configurable via `LEAN_TIMEOUT`)
- Model generation timeout: 300 seconds (5 minutes)
- Process group isolation for safe killing
- Non-daemon threads that don't prevent program exit
- Temporary Lean files created within project root to ensure Mathlib resolution

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
2. Increase `LEAN_TIMEOUT` in `config.py` (default: 600s / 10 minutes)
3. Check system resources (CPU, memory)

### Mathlib Resolution Issues
If you see "unknown package 'Mathlib'" errors:
1. Ensure temporary Lean files are created within the project root (this is handled automatically)
2. Run `lake build` in the miniF2F directory before evaluation
3. For Slurm jobs, ensure `lake build` runs in the job script (already included in provided scripts)

### GPU Memory Issues
If you run out of GPU memory:
- The code uses 4-bit quantization by default (see `config.py`)
- Reduce `MAX_NEW_TOKENS_COT` if needed
- Close other GPU processes

### Slurm Job Management

**Check job status:**
```bash
squeue -u $USER
```

**Monitor job output:**
```bash
tail -f logs/eval_<JOB_ID>.out
```

**Cancel a job:**
```bash
scancel <JOB_ID>
```

**Cancel all your jobs:**
```bash
scancel -u $USER
```

**Check job details:**
```bash
scontrol show job <JOB_ID>
```

### Performance Optimization

For faster evaluation:
- Use parallel sharding (16 shards recommended for MiniF2F)
- Reduce `NUM_SAMPLES` if needed (default: 8)
- Ensure adequate walltime allocation (12 hours max on most clusters)
- Monitor GPU utilization: `nvidia-smi` in an interactive session