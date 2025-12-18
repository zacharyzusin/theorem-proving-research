"""
Lean 4 verification utilities.

Provides safe Lean file checking with timeouts, process tree killing,
and proper resource cleanup to prevent hanging processes.
"""
import os
import re
import subprocess
import tempfile
import signal
import time
import psutil
import sys
from pathlib import Path

# Add parent directory to path so we can import config
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import timeout from config (with fallback for backward compatibility)
try:
    from config import LEAN_TIMEOUT
except ImportError:
    # Fallback if config not available
    LEAN_TIMEOUT = int(os.environ.get("LEAN_TIMEOUT", 120))  # Default: 2 minutes

# Model generation timeout (seconds). This is used by safe_generate() in eval scripts.
# Override via env var to tune for different hardware/queues.
MODEL_GENERATION_TIMEOUT = int(os.environ.get("MODEL_GENERATION_TIMEOUT", 300))  # default: 5 minutes


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
            tail = raw[last.end():].strip()  # FIX: Define tail variable
            return block, tail

    return None, None


###########################################################
# Kill process tree safely
###########################################################

def kill_process_tree(pid, timeout=5):
    """
    Kill a process and all its children recursively.
    Returns True if all processes were killed, False otherwise.
    """
    try:
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)
        
        # First try graceful termination
        for child in children:
            try:
                child.terminate()
            except psutil.NoSuchProcess:
                pass
        
        try:
            parent.terminate()
        except psutil.NoSuchProcess:
            pass
        
        # Wait for processes to terminate
        gone, alive = psutil.wait_procs(children + [parent], timeout=timeout)
        
        # Force kill any remaining processes
        for proc in alive:
            try:
                proc.kill()
            except psutil.NoSuchProcess:
                pass
        
        return True
    except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
        # Process already gone or we don't have permission
        return False
    except Exception as e:
        # Fallback to basic kill
        try:
            os.kill(pid, signal.SIGKILL)
            if hasattr(os, 'killpg'):
                try:
                    os.killpg(os.getpgid(pid), signal.SIGKILL)
                except (ProcessLookupError, OSError):
                    pass
        except (ProcessLookupError, OSError):
            pass
        return False


###########################################################
# Run Lean checker (kill-safe with enhanced protection)
###########################################################

def check_lean_file(lean_code: str, project_root: str, timeout: int = None):
    """
    Run Lean inside the Lean project root with Mathlib, with:
      • hard timeout
      • process-tree kill protection
      • safe cleanup
      • resource limits

    Args:
        lean_code: Lean code to check
        project_root: Root directory of the Lean project
        timeout: Timeout in seconds (defaults to LEAN_TIMEOUT from config)

    Returns: (success, stdout, stderr, timeout_occurred)
             where timeout_occurred is True if the check timed out
    """
    if timeout is None:
        timeout = LEAN_TIMEOUT
    # --- Write temporary Lean file ---
    # Use system temp directory instead of /dev/shm (more portable)
    try:
        fd, path = tempfile.mkstemp(suffix=".lean", prefix="tmp_lean_")
    except (OSError, PermissionError):
        # Fallback to current directory if temp fails
        import uuid
        path = f"/tmp/tmp_lean_{uuid.uuid4().hex}.lean"
        fd = os.open(path, os.O_CREAT | os.O_WRONLY | os.O_TRUNC, 0o644)
    
    try:
        with os.fdopen(fd, "w") as f:
            f.write(lean_code)
    except Exception as e:
        try:
            os.close(fd)
        except:
            pass
        return False, "", f"Failed to write temp file: {e}"

    cmd = ["lake", "env", "lean", path]
    proc = None

    try:
        # Start Lean in its own process group so we can kill the whole group
        # Use start_new_session=True (modern approach) instead of preexec_fn
        # which can fail in threading contexts
        proc = subprocess.Popen(
            cmd,
            cwd=project_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,  # Creates new process group for safe killing
        )

        timeout_occurred = False
        try:
            stdout, stderr = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            timeout_occurred = True
            # Kill the ENTIRE process tree
            print(f"[WARNING] Lean process timed out after {timeout}s, killing process tree...", flush=True)
            
            # With start_new_session=True, the PID is the process group leader
            # So we can kill the process group directly
            try:
                # Try to get the process group ID (should be same as PID with start_new_session)
                pgid = os.getpgid(proc.pid)
                os.killpg(pgid, signal.SIGKILL)
            except (ProcessLookupError, OSError, ProcessLookupError):
                # Process might have already finished, or we don't have permission
                pass
            
            # Use psutil to kill process tree (more thorough)
            try:
                kill_process_tree(proc.pid)
            except Exception:
                pass
            
            # Ensure process is dead
            try:
                proc.kill()
            except (ProcessLookupError, ValueError):
                pass
            
            # Wait a bit to ensure cleanup
            try:
                proc.wait(timeout=2)
            except (subprocess.TimeoutExpired, ProcessLookupError):
                pass
            
            return False, "", f"Lean check TIMEOUT after {timeout} seconds", True

        success = (proc.returncode == 0)
        return success, stdout, stderr, timeout_occurred

    except FileNotFoundError as e:
        # e.g. "lake" not found
        return False, "", f"Failed to run Lean: {e}", False
    except Exception as e:
        # Catch any other unexpected errors
        if proc is not None:
            try:
                kill_process_tree(proc.pid)
            except:
                pass
        return False, "", f"Unexpected error running Lean: {e}", False

    finally:
        # Always clean up temp file
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass
