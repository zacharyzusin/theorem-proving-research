import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from config import MODEL_ID, LOAD_IN_4BIT, DEVICE_MAP

def load_model_and_tokenizer():
    print(f"Loading model: {MODEL_ID}")
    print("Note: First-time download can take 10+ minutes. Press Ctrl+C to cancel.")
    print("Loading tokenizer...", flush=True)

    quant_config = None
    if LOAD_IN_4BIT:
        quant_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
        )

    try:
        tokenizer = AutoTokenizer.from_pretrained(
            MODEL_ID, 
            use_fast=False,
            resume_download=True,  # Resume if interrupted
        )
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        print("✓ Tokenizer loaded", flush=True)
    except KeyboardInterrupt:
        print("\n[INFO] Tokenizer loading interrupted")
        raise
    except Exception as e:
        print(f"\n[ERROR] Failed to load tokenizer: {e}")
        raise

    print("Loading model (this may take several minutes)...", flush=True)
    try:
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_ID,
            device_map=DEVICE_MAP,
            dtype=torch.bfloat16,
            quantization_config=quant_config,
            resume_download=True,  # Resume if interrupted
            low_cpu_mem_usage=True,  # More efficient loading
        )
        print("✓ Model loaded", flush=True)
    except KeyboardInterrupt:
        print("\n[INFO] Model loading interrupted")
        raise
    except Exception as e:
        print(f"\n[ERROR] Failed to load model: {e}")
        raise

    return model, tokenizer
