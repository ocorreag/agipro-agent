"""
Safe print utility for handling None stdout/stderr in Windows GUI mode.
Use this instead of print() to prevent crashes when running as a bundled executable.
"""

import sys
from typing import Any


def safe_print(*args, **kwargs):
    """
    Safe print function that handles None stdout gracefully.
    Use this instead of print() in all modules to prevent crashes in Windows GUI mode.
    """
    try:
        if sys.stdout is not None:
            print(*args, **kwargs)
        # If stdout is None, silently ignore (GUI mode)
    except Exception:
        # If any error occurs, silently ignore
        pass


def safe_error_print(*args, **kwargs):
    """
    Safe error print function that writes to stderr.
    Use this for error messages instead of print() to stderr.
    """
    try:
        if sys.stderr is not None:
            print(*args, file=sys.stderr, **kwargs)
        # If stderr is None, silently ignore (GUI mode)
    except Exception:
        # If any error occurs, silently ignore
        pass
