#!/usr/bin/env python3
"""
Download the DeepSeek-Prover-V2-7B model with progress indication.
This can be run separately before evaluation to avoid long waits.
"""
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config import MODEL_ID, LOAD_IN_4BIT, DEVICE_MAP
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from tqdm import tqdm
import torch

def check_model_downloaded():
    """Check if model is already downloaded."""
    try:
        # Try to find the model in cache
        cache_path = Path.home() / ".cache" / "huggingface" / "hub"
        model_dirs = list(cache_path.glob(f"models--{MODEL_ID.replace('/', '--')}*"))
        if model_dirs:
            # Check if it has actual files (not just empty directory)
            model_dir = model_dirs[0]
            files = list(model_dir.rglob("*"))
            if len(files) > 10:  # Should have many files if fully downloaded
                size = sum(f.stat().st_size for f in files if f.is_file())
                size_gb = size / (1024**3)
                print(f"✓ Model appears to be in cache: {model_dir}")
                print(f"  Cache size: {size_gb:.2f} GB")
                return True
    except Exception as e:
        pass
    return False

def download_model():
    """Download the model with progress indication."""
    print("="*60)
    print(f"Downloading model: {MODEL_ID}")
    print("="*60)
    print("This may take 10-30 minutes depending on your connection.")
    print("Model size: ~14GB")
    print("Press Ctrl+C to cancel (download will resume on next run)")
    print("="*60)
    
    if check_model_downloaded():
        response = input("\nModel appears to be downloaded. Re-download? (y/N): ")
        if response.lower() != 'y':
            print("Skipping download.")
            return
    
    quant_config = None
    if LOAD_IN_4BIT:
        quant_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
        )
    
    print("\n[1/2] Downloading tokenizer...")
    try:
        tokenizer = AutoTokenizer.from_pretrained(
            MODEL_ID,
            use_fast=False,
            resume_download=True,
        )
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        print("✓ Tokenizer downloaded")
    except KeyboardInterrupt:
        print("\n[INFO] Download interrupted. Run again to resume.")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Failed to download tokenizer: {e}")
        sys.exit(1)
    
    print("\n[2/2] Downloading model (this is the large file, ~14GB)...")
    print("Progress will be shown by HuggingFace transformers library")
    try:
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_ID,
            device_map=DEVICE_MAP,
            dtype=torch.bfloat16,
            quantization_config=quant_config,
            resume_download=True,
            low_cpu_mem_usage=True,
        )
        print("\n✓ Model downloaded successfully!")
        print(f"Model is ready to use. You can now run evaluation scripts.")
    except KeyboardInterrupt:
        print("\n[INFO] Download interrupted. Run this script again to resume.")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Failed to download model: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        download_model()
    except KeyboardInterrupt:
        print("\n\n[INFO] Download cancelled by user.")
        print("You can run this script again later to resume the download.")
        sys.exit(0)

