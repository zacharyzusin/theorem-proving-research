#!/usr/bin/env python3
"""
Verify that the setup is correct by checking:
1. Config paths are valid
2. miniF2F files exist
3. PutnamBench files exist
4. Lean projects can be accessed
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import (
    MINIF2F_ROOT,
    MINIF2F_PROJECT_ROOT,
    MINIF2F_FORMAL_TEST,
    MINIF2F_FORMAL_VALID,
    PUTNAM_DIR,
    PUTNAM_PROJECT_ROOT,
    PUTNAM_SRC_GLOB,
)

def check_path(path, name, required=True):
    """Check if a path exists."""
    exists = path.exists()
    status = "✓" if exists else "✗"
    print(f"{status} {name}: {path}")
    if not exists and required:
        print(f"   ERROR: Required path does not exist!")
        return False
    elif not exists:
        print(f"   WARNING: Optional path does not exist")
    return exists

def main():
    print("="*60)
    print("Verifying Setup")
    print("="*60)
    print()
    
    all_ok = True
    
    # Check miniF2F
    print("MiniF2F Configuration:")
    print(f"  MINIF2F_ROOT: {MINIF2F_ROOT}")
    print(f"  MINIF2F_PROJECT_ROOT: {MINIF2F_PROJECT_ROOT}")
    print()
    
    if not check_path(MINIF2F_ROOT, "MINIF2F_ROOT directory"):
        all_ok = False
    if not check_path(MINIF2F_PROJECT_ROOT, "MINIF2F_PROJECT_ROOT (Lean project root)"):
        all_ok = False
    if not check_path(MINIF2F_FORMAL_TEST, "MINIF2F_FORMAL_TEST (test.lean)"):
        all_ok = False
    if not check_path(MINIF2F_FORMAL_VALID, "MINIF2F_FORMAL_VALID (valid.lean)"):
        all_ok = False
    
    # Check for lakefile.lean
    lakefile_candidates = [
        MINIF2F_PROJECT_ROOT / "lakefile.lean",
        MINIF2F_ROOT / "lakefile.lean",
        MINIF2F_ROOT / "lean" / "lakefile.lean",
    ]
    lakefile_found = False
    for candidate in lakefile_candidates:
        if candidate.exists():
            print(f"✓ Found lakefile.lean: {candidate}")
            lakefile_found = True
            break
    if not lakefile_found:
        print("✗ WARNING: Could not find lakefile.lean in expected locations")
        print("  Searched:")
        for candidate in lakefile_candidates:
            print(f"    - {candidate}")
    
    print()
    
    # Check PutnamBench
    print("PutnamBench Configuration:")
    print(f"  PUTNAM_DIR: {PUTNAM_DIR}")
    print(f"  PUTNAM_PROJECT_ROOT: {PUTNAM_PROJECT_ROOT}")
    print()
    
    if not check_path(PUTNAM_DIR, "PUTNAM_DIR directory"):
        all_ok = False
    if not check_path(PUTNAM_PROJECT_ROOT, "PUTNAM_PROJECT_ROOT (Lean project root)"):
        all_ok = False
    
    # Check for Putnam source files
    import glob
    putnam_files = glob.glob(PUTNAM_SRC_GLOB)
    print(f"✓ Found {len(putnam_files)} PutnamBench source files")
    if len(putnam_files) == 0:
        print(f"  WARNING: No files found matching: {PUTNAM_SRC_GLOB}")
        all_ok = False
    else:
        print(f"  Example: {Path(putnam_files[0]).name}")
    
    print()
    
    # Check Lean toolchain files
    print("Lean Toolchain Files:")
    lean_toolchain_candidates = [
        MINIF2F_PROJECT_ROOT / "lean-toolchain",
        MINIF2F_ROOT / "lean-toolchain",
        MINIF2F_ROOT / "lean" / "lean-toolchain",
    ]
    toolchain_found = False
    for candidate in lean_toolchain_candidates:
        if candidate.exists():
            print(f"✓ Found lean-toolchain: {candidate}")
            try:
                content = candidate.read_text().strip()
                print(f"  Version: {content}")
            except:
                pass
            toolchain_found = True
            break
    if not toolchain_found:
        print("✗ WARNING: Could not find lean-toolchain file")
    
    putnam_toolchain = PUTNAM_PROJECT_ROOT / "lean-toolchain"
    if putnam_toolchain.exists():
        print(f"✓ Found PutnamBench lean-toolchain: {putnam_toolchain}")
        try:
            content = putnam_toolchain.read_text().strip()
            print(f"  Version: {content}")
        except:
            pass
    else:
        print(f"✗ WARNING: Could not find PutnamBench lean-toolchain: {putnam_toolchain}")
    
    print()
    print("="*60)
    if all_ok:
        print("✓ Setup verification complete - all required paths exist!")
        print()
        print("Next steps:")
        print("1. Build Lean projects: cd miniF2F && lake build")
        print("2. Build PutnamBench: cd PutnamBench/lean4 && lake build")
        print("3. Extract MiniF2F problems: python src/extract_minif2f.py")
        print("4. Download model: python scripts/download_model.py")
    else:
        print("✗ Setup verification found issues - please fix the errors above")
    print("="*60)

if __name__ == "__main__":
    main()
