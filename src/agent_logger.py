"""
CAUSA Agent Logger - Tracks agent movements and actions.

Provides structured logging for:
- Agent decisions and reasoning
- Tool calls with parameters
- Tool results and errors
- Conversation flow
"""

import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from functools import wraps

from path_manager import path_manager


# ============================================================================
# Logger Setup
# ============================================================================

def setup_agent_logger(
    log_to_file: bool = True,
    log_to_console: bool = True,
    log_level: int = logging.INFO
) -> logging.Logger:
    """
    Setup the agent logger with file and console handlers.

    Args:
        log_to_file: Whether to log to a file
        log_to_console: Whether to log to console
        log_level: Logging level (default INFO)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger("causa_agent")
    logger.setLevel(log_level)

    # Clear existing handlers
    logger.handlers = []

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler
    if log_to_console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # File handler
    if log_to_file:
        try:
            logs_dir = path_manager.get_path('publicaciones') / 'logs'
            logs_dir.mkdir(parents=True, exist_ok=True)

            # Daily log file
            log_file = logs_dir / f"agent_{datetime.now().strftime('%Y-%m-%d')}.log"

            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            if log_to_console:
                logger.warning(f"Could not setup file logging: {e}")

    return logger


# Get or create the logger
_logger: Optional[logging.Logger] = None


def get_logger() -> logging.Logger:
    """Get the agent logger instance."""
    global _logger
    if _logger is None:
        _logger = setup_agent_logger()
    return _logger


# ============================================================================
# Logging Functions
# ============================================================================

def log_agent_start(thread_id: str, model: str = "unknown"):
    """Log when the agent starts a new conversation or continues one."""
    logger = get_logger()
    logger.info(f"{'='*60}")
    logger.info(f"AGENT START | Thread: {thread_id} | Model: {model}")
    logger.info(f"{'='*60}")


def log_user_message(message: str, thread_id: str = ""):
    """Log incoming user message."""
    logger = get_logger()
    # Truncate very long messages for logging
    display_msg = message[:200] + "..." if len(message) > 200 else message
    logger.info(f"USER INPUT  | {display_msg}")


def log_agent_thinking(thought: str):
    """Log agent's reasoning/thinking process."""
    logger = get_logger()
    logger.debug(f"THINKING    | {thought}")


def log_tool_call(tool_name: str, arguments: dict):
    """Log when the agent calls a tool."""
    logger = get_logger()
    # Format arguments nicely, truncating long values
    formatted_args = {}
    for k, v in arguments.items():
        if isinstance(v, str) and len(v) > 100:
            formatted_args[k] = v[:100] + "..."
        else:
            formatted_args[k] = v

    args_str = json.dumps(formatted_args, ensure_ascii=False, indent=None)
    logger.info(f"TOOL CALL   | {tool_name} | Args: {args_str}")


def log_tool_result(tool_name: str, result: Any, success: bool = True):
    """Log the result of a tool call."""
    logger = get_logger()

    # Format result for logging
    if isinstance(result, str):
        display_result = result[:300] + "..." if len(result) > 300 else result
    else:
        display_result = str(result)[:300]

    status = "SUCCESS" if success else "ERROR"
    logger.info(f"TOOL RESULT | {tool_name} | {status} | {display_result}")


def log_agent_response(response: str):
    """Log the agent's response to the user."""
    logger = get_logger()
    # Truncate for logging
    display_response = response[:300] + "..." if len(response) > 300 else response
    logger.info(f"AGENT REPLY | {display_response}")


def log_agent_decision(decision: str, reason: str = ""):
    """Log when the agent makes a decision (continue, end, etc.)."""
    logger = get_logger()
    if reason:
        logger.info(f"DECISION    | {decision} | Reason: {reason}")
    else:
        logger.info(f"DECISION    | {decision}")


def log_error(error: str, context: str = ""):
    """Log an error."""
    logger = get_logger()
    if context:
        logger.error(f"ERROR       | {context} | {error}")
    else:
        logger.error(f"ERROR       | {error}")


def log_warning(warning: str, context: str = ""):
    """Log a warning."""
    logger = get_logger()
    if context:
        logger.warning(f"WARNING     | {context} | {warning}")
    else:
        logger.warning(f"WARNING     | {warning}")


def log_info(info: str):
    """Log general information."""
    logger = get_logger()
    logger.info(f"INFO        | {info}")


def log_conversation_end(thread_id: str):
    """Log when a conversation turn ends."""
    logger = get_logger()
    logger.info(f"TURN END    | Thread: {thread_id}")
    logger.info(f"{'-'*60}")


# ============================================================================
# Tool Logging Decorator
# ============================================================================

def log_tool(func):
    """
    Decorator to automatically log tool calls and results.

    Usage:
        @tool
        @log_tool
        def my_tool(arg1: str) -> str:
            ...
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        tool_name = func.__name__

        # Log the call
        log_tool_call(tool_name, kwargs if kwargs else {"args": args})

        try:
            result = func(*args, **kwargs)
            log_tool_result(tool_name, result, success=True)
            return result
        except Exception as e:
            log_tool_result(tool_name, str(e), success=False)
            raise

    return wrapper


# ============================================================================
# Log File Management
# ============================================================================

def get_recent_logs(lines: int = 100) -> str:
    """
    Get the most recent log entries.

    Args:
        lines: Number of lines to retrieve

    Returns:
        Recent log content as string
    """
    try:
        logs_dir = path_manager.get_path('publicaciones') / 'logs'
        log_file = logs_dir / f"agent_{datetime.now().strftime('%Y-%m-%d')}.log"

        if not log_file.exists():
            return "No logs found for today."

        with open(log_file, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
            recent = all_lines[-lines:] if len(all_lines) > lines else all_lines
            return "".join(recent)
    except Exception as e:
        return f"Error reading logs: {e}"


def get_log_files() -> list:
    """Get list of available log files."""
    try:
        logs_dir = path_manager.get_path('publicaciones') / 'logs'
        if not logs_dir.exists():
            return []

        return sorted([f.name for f in logs_dir.glob("agent_*.log")], reverse=True)
    except Exception:
        return []


def clear_old_logs(days_to_keep: int = 7):
    """
    Clear log files older than specified days.

    Args:
        days_to_keep: Number of days of logs to keep
    """
    try:
        logs_dir = path_manager.get_path('publicaciones') / 'logs'
        if not logs_dir.exists():
            return

        cutoff = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)

        for log_file in logs_dir.glob("agent_*.log"):
            if log_file.stat().st_mtime < cutoff:
                log_file.unlink()
                log_info(f"Deleted old log file: {log_file.name}")
    except Exception as e:
        log_error(f"Error clearing old logs: {e}")
