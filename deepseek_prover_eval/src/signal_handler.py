"""
Signal handlers for graceful shutdown to prevent orphaned processes.
"""
import signal
import sys
import os

_shutdown_requested = False

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global _shutdown_requested
    _shutdown_requested = True
    print(f"\n[INFO] Received signal {signum}, shutting down gracefully...", flush=True)
    sys.exit(1)

def setup_signal_handlers():
    """Set up signal handlers for SIGINT and SIGTERM."""
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

def is_shutdown_requested():
    """Check if shutdown has been requested."""
    return _shutdown_requested
