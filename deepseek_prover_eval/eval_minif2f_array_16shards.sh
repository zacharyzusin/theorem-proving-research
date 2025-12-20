#!/bin/bash
#SBATCH --account=edu
#SBATCH --partition=short
#SBATCH --job-name=deepseek_miniF2F
#SBATCH --gres=gpu:A6000:1
#SBATCH -c 8
#SBATCH --time=12:00:00  # Maximum allowed on short/edu1 partitions
#SBATCH --mem-per-cpu=8gb
#SBATCH --array=0-15
#SBATCH --output=logs/eval_%A_%a.out
#SBATCH --error=logs/eval_%A_%a.err

mkdir -p logs

echo "=== Job Info ==="
echo "Job started at: $(date)"
echo "Job ID: $SLURM_JOB_ID"
echo "Array Job: $SLURM_ARRAY_JOB_ID"
echo "Array Task ID: $SLURM_ARRAY_TASK_ID"
echo "Partition: $SLURM_JOB_PARTITION"
echo "Node: $(hostname)"
echo "================"

# Activate virtual environment
source /insomnia001/depts/edu/COMS-E6998-012/zwz2000/theorem-proving-research/deepseek_prover_eval/venv/bin/activate

# Increase Lean verification timeout (seconds)
# Default in config.py is 120s; for long proofs you can raise this.
export LEAN_TIMEOUT=600

# Ensure MiniF2F/Mathlib is built (safe to re-run)
echo ""
echo "=== Building Lean dependencies (miniF2F/Mathlib) ==="
cd /insomnia001/depts/edu/COMS-E6998-012/zwz2000/theorem-proving-research/miniF2F
lake exe cache get || true
lake build
printf "import Mathlib\n#check Nat\n" > Sanity.lean
lake env lean Sanity.lean
rm -f Sanity.lean
echo "==================================================="
echo ""

echo "=== GPU Info ==="
nvidia-smi
echo "================"
echo ""

NUM_SHARDS=16
SHARD_ID=${SLURM_ARRAY_TASK_ID}

cd /insomnia001/depts/edu/COMS-E6998-012/zwz2000/theorem-proving-research/deepseek_prover_eval

OUT_DIR="data/results/minif2f_sharded_16/shard_${SHARD_ID}"

python src/eval_minif2f.py \
  --mode noncot \
  --output-dir "${OUT_DIR}" \
  --num-shards ${NUM_SHARDS} \
  --shard-id ${SHARD_ID}

echo ""
echo "=== Job Complete ==="
echo "Job finished at: $(date)"
echo "===================="

deactivate
