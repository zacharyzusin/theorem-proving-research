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

PROMPT_NONCOT = Path("prompts/noncot.txt")
PROMPT_COT = Path("prompts/cot.txt")


#############################################
# Model generation parameters
#############################################

MAX_NEW_TOKENS = 512
TEMPERATURE = 0.8
TOP_P = 0.95
NUM_SAMPLES = 32


#############################################
# Model loading configuration
#############################################

MODEL_ID = "deepseek-ai/DeepSeek-Prover-V2-7B"

# Use 4-bit quantization to fit on TITAN RTX 24GB
LOAD_IN_4BIT = True

# Let transformers/accelerate handle device placement
DEVICE_MAP = "auto"
