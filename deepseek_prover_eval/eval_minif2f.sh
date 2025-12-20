#!/bin/bash
#SBATCH --account=edu
#SBATCH --partition=short
#SBATCH --job-name=deepseek_eval
#SBATCH --gres=gpu:A6000:1          # Request A6000 GPU
#SBATCH -c 8                        # 8 CPU cores
#SBATCH --time=12:00:00             # 12 hours
#SBATCH --mem-per-cpu=8gb           # 64GB total RAM
#SBATCH --output=logs/eval_%j.out
#SBATCH --error=logs/eval_%j.err

# Create logs directory
mkdir -p logs

echo "=== Job Info ==="
echo "Job started at: $(date)"
echo "Job ID: $SLURM_JOB_ID"
echo "Partition: $SLURM_JOB_PARTITION"
echo "Running on node: $(hostname)"
echo "================"

# Activate virtual environment
source /insomnia001/depts/edu/COMS-E6998-012/zwz2000/theorem-proving-research/deepseek_prover_eval/venv/bin/activate

# Increase Lean verification timeout (seconds)
export LEAN_TIMEOUT=600

# Set working directory
cd /insomnia001/depts/edu/COMS-E6998-012/zwz2000/theorem-proving-research/deepseek_prover_eval

# Ensure MiniF2F/Mathlib is built (one-time, but harmless to re-run).
# Without this, Lean checks fail with "unknown package 'Mathlib'" and you waste GPU hours.
echo ""
echo "=== Building Lean dependencies (miniF2F/Mathlib) ==="
cd /insomnia001/depts/edu/COMS-E6998-012/zwz2000/theorem-proving-research/miniF2F
lake exe cache get || true
lake build
echo "==================================================="
echo ""

# Print GPU info
echo ""
echo "=== GPU Info ==="
nvidia-smi
echo "================"
echo ""

# Run evaluation
cd /insomnia001/depts/edu/COMS-E6998-012/zwz2000/theorem-proving-research/deepseek_prover_eval
python src/eval_minif2f.py --mode noncot --output-dir data/results/minif2f

echo ""
echo "=== Job Complete ==="
echo "Job finished at: $(date)"
echo "===================="

deactivate