#!/bin/bash
#SBATCH --account=edu
#SBATCH --partition=short           # Use short partition (has GPU nodes)
#SBATCH --job-name=test_gpu
#SBATCH --gres=gpu:1                # Request any GPU
#SBATCH -c 4
#SBATCH --time=0:30:00
#SBATCH --mem-per-cpu=4gb
#SBATCH --output=test_gpu_%j.out
#SBATCH --error=test_gpu_%j.err

echo "Job started at: $(date)"
echo "Partition: $SLURM_JOB_PARTITION"
echo "Running on node: $(hostname)"
echo "GPU info:"
nvidia-smi

source /insomnia001/depts/edu/COMS-E6998-012/zwz2000/theorem-proving-research/deepseek_prover_eval/venv/bin/activate
cd /insomnia001/depts/edu/COMS-E6998-012/zwz2000/theorem-proving-research/deepseek_prover_eval

echo "Testing PyTorch CUDA..."
python -c "import torch; print(f'PyTorch version: {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}'); print(f'GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"None\"}')"

echo "Job finished at: $(date)"