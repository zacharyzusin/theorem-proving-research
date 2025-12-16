#!/usr/bin/env python3
"""
Convenience script for inspecting evaluation results.
"""
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.inspect_results import main

if __name__ == "__main__":
    main()
