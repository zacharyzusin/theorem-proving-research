"""
Configuration file for DeepSeek-Prover-V2-7B evaluation pipeline.

This module contains all configuration parameters including:
- Dataset paths (MiniF2F, PutnamBench)
- Model generation parameters (temperature, top_p, max tokens)
- Model loading configuration
"""
from pathlib import Path
import os

# Get the project root directory (where this config.py file is located)
PROJECT_ROOT = Path(__file__).parent.resolve()

#############################################
# MiniF2F Lean4 Dataset Paths
#############################################

# Root of the Lean4 MiniF2F project
# Default: assumes miniF2F is in parent directory
# Can be overridden with MINIF2F_ROOT environment variable
MINIF2F_ROOT = Path(
    os.environ.get("MINIF2F_ROOT", PROJECT_ROOT.parent / "miniF2F")
).resolve()

# Lake project root (contains lakefile.lean)
MINIF2F_PROJECT_ROOT = MINIF2F_ROOT

# Lean4 formal problem sources
MINIF2F_FORMAL_TEST = MINIF2F_ROOT / "formal" / "test.lean"
MINIF2F_FORMAL_VALID = MINIF2F_ROOT / "formal" / "valid.lean"

# Directory for extracted per-problem Lean files (relative to project root)
MINIF2F_EXTRACTED_DIR = PROJECT_ROOT / "data" / "minif2f_extracted"
MINIF2F_EXTRACTED_GLOB = str(MINIF2F_EXTRACTED_DIR / "*.lean")

###############################################
# Putnam benchmark configuration
###############################################

# Default: assumes PutnamBench is in parent directory
# Can be overridden with PUTNAM_DIR environment variable
PUTNAM_DIR = Path(
    os.environ.get("PUTNAM_DIR", PROJECT_ROOT.parent / "PutnamBench")
).resolve()
PUTNAM_PROJECT_ROOT = PUTNAM_DIR / "lean4"
PUTNAM_SRC_GLOB = str(PUTNAM_PROJECT_ROOT / "src" / "putnam_*.lean")

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
