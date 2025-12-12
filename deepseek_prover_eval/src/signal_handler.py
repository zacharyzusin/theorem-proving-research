"""
Signal handlers for graceful shutdown to prevent orphaned processes.

This module provides signal handling that allows the main evaluation loops
to check for shutdown requests and clean up properly before exiting.
"""
import signal
import sys
import os

# Global flag to track if shutdown has been requested
_shutdown_requested = False


def signal_handler(signum, frame):
    """
    Handle shutdown signals gracefully.
    
    Sets the shutdown flag but does not immediately exit, allowing
    the main evaluation loops to check is_shutdown_requested() and
    clean up properly.
    
    Args:
        signum: Signal number (e.g., SIGINT, SIGTERM)
        frame: Current stack frame
    """
    global _shutdown_requested
    _shutdown_requested = True
    print(f"\n[INFO] Received signal {signum}, shutting down gracefully...", flush=True)
    # Don't call sys.exit() immediately - let the main loop check is_shutdown_requested()
    # and clean up properly. The program will exit naturally when the loop breaks.


def setup_signal_handlers():
    """
    Set up signal handlers for SIGINT and SIGTERM.
    
    Should be called at the start of evaluation scripts to enable
    graceful shutdown on Ctrl+C or SIGTERM.
    """
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def is_shutdown_requested():
    """
    Check if shutdown has been requested.
    
    Returns:
        bool: True if a shutdown signal (SIGINT/SIGTERM) was received
    """
    return _shutdown_requested
