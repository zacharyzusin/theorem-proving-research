# DeepSeek-Prover-V2-7B Evaluation (MiniF2F & PutnamBench)

This project is a minimal harness to evaluate **DeepSeek-Prover-V2-7B** on
**MiniF2F** and **PutnamBench** in both non-CoT and CoT modes.

> For official scripts and exact reproduction of results, see:
> https://github.com/deepseek-ai/DeepSeek-Prover-V2

## 1. Setup

```bash
git clone https://github.com/openai/miniF2F
git clone https://github.com/trishullab/PutnamBench

cd deepseek_prover_eval
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
