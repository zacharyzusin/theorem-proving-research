# src/lean_utils.py

import os
import re
import subprocess
import tempfile
import signal

LEAN_TIMEOUT = 20   # seconds – adjust if needed


###########################################################
# Extract Lean code blocks
###########################################################

def extract_lean_blocks(raw: str):
    """
    Extract the LAST ```lean4``` or ```lean``` code block from the LLM output.

    This block should contain the MODEL'S proposed solution (not the problem text).
    Returns (block_text, tail_after_block) or (None, None) on failure.
    """
    patterns = [
        r"```lean4\s*(.*?)```",
        r"```lean\s*(.*?)```",
    ]

    for pat in patterns:
        matches = list(re.finditer(pat, raw, flags=re.DOTALL))
        if matches:
            last = matches[-1]
            block = last.group(1).strip()
            tail = raw[last.end():].strip()
            return block, tail

    return None, None


###########################################################
# Run Lean checker (kill-safe)
###########################################################

def check_lean_file(lean_code: str, project_root: str):
    """
    Run Lean inside the Lean project root with Mathlib, with:
      • hard timeout
      • process-group kill protection
      • safe cleanup

    Returns: (success, stdout, stderr)
    """
    # --- Write temporary Lean file ---
    fd, path = tempfile.mkstemp(suffix=".lean", prefix="/dev/shm/tmp_lean_")
    with os.fdopen(fd, "w") as f:
        f.write(lean_code)

    cmd = ["lake", "env", "lean", path]

    try:
        # Start Lean in its own process group so we can kill the whole group
        proc = subprocess.Popen(
            cmd,
            cwd=project_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            preexec_fn=os.setsid,  # POSIX-only; fine on your machine
        )

        try:
            stdout, stderr = proc.communicate(timeout=LEAN_TIMEOUT)
        except subprocess.TimeoutExpired:
            # Kill the ENTIRE process group, not just the parent
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            except ProcessLookupError:
                pass
            return False, "", f"Lean check TIMEOUT after {LEAN_TIMEOUT} seconds"

        success = (proc.returncode == 0)
        return success, stdout, stderr

    except FileNotFoundError as e:
        # e.g. "lake" not found
        return False, "", f"Failed to run Lean: {e}"

    finally:
        try:
            os.remove(path)
        except FileNotFoundError:
            pass
