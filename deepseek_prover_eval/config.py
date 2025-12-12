from pathlib import Path

#############################################
# MiniF2F Lean4 Dataset Paths
#############################################

# Root of the Lean4 MiniF2F project
MINIF2F_ROOT = Path("/local/rcs/zwz2000/ProofResearch/miniF2F")

# Lake project root (contains lakefile.lean)
MINIF2F_PROJECT_ROOT = MINIF2F_ROOT

# Lean4 formal problem sources
MINIF2F_FORMAL_TEST = MINIF2F_ROOT / "formal" / "test.lean"
MINIF2F_FORMAL_VALID = MINIF2F_ROOT / "formal" / "valid.lean"

# Directory for extracted per-problem Lean files
MINIF2F_EXTRACTED_DIR = Path("minif2f_extracted")
MINIF2F_EXTRACTED_GLOB = str(MINIF2F_EXTRACTED_DIR / "*.lean")

###############################################
# Putnam benchmark configuration
###############################################

PUTNAM_DIR = "/local/rcs/zwz2000/ProofResearch/PutnamBench"
PUTNAM_PROJECT_ROOT = "/local/rcs/zwz2000/ProofResearch/PutnamBench/lean4"
PUTNAM_SRC_GLOB = "/local/rcs/zwz2000/ProofResearch/PutnamBench/lean4/src/*.lean"

#############################################
# Prompt files
#############################################


#############################################
# Model generation parameters
#############################################

# Different max tokens for CoT vs non-CoT (CoT needs more for reasoning)
MAX_NEW_TOKENS_NONCOT = 2048  # Reasonable for non-CoT proofs
MAX_NEW_TOKENS_COT = 32768    # Paper specifies 32k for CoT mode

TEMPERATURE = 0.7  # Typical range 0.6-0.8
TOP_P = 0.95       # Typical range 0.9-1.0
NUM_SAMPLES = 32   # For Pass@32 evaluation


#############################################
# Model loading configuration
#############################################

MODEL_ID = "deepseek-ai/DeepSeek-Prover-V2-7B"

# Use 4-bit quantization to fit on TITAN RTX 24GB
LOAD_IN_4BIT = True

# Let transformers/accelerate handle device placement
DEVICE_MAP = "auto"
