"""
Agent Logger - Tracks all agent activities for debugging and transparency.
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("agent_logger")


class ActionType(str, Enum):
    """Types of agent actions."""
    INIT = "init"
    LOAD_MEMORY = "load_memory"
    SEARCH_NEWS = "search_news"
    SEARCH_EPHEMERIDES = "search_ephemerides"
    GENERATE_CONTENT = "generate_content"
    REVIEW_CONTENT = "review_content"
    GENERATE_IMAGE = "generate_image"
    SAVE_FILE = "save_file"
    API_CALL = "api_call"
    ERROR = "error"
    BRIDGE_CALL = "bridge_call"


@dataclass
class AgentAction:
    """Represents a single agent action."""
    timestamp: str
    action_type: str
    description: str
    details: Dict[str, Any] = field(default_factory=dict)
    duration_ms: Optional[float] = None
    success: bool = True
    error: Optional[str] = None


class AgentLogger:
    """Logs and stores agent activities for transparency."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self.actions: List[AgentAction] = []
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._start_time = datetime.now()
        self._current_action_start = None

        # Log file path
        self.log_dir = Path(os.getenv("AGENT_LOG_DIR", "/tmp/causa_agent_logs"))
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / f"agent_{self.session_id}.json"

        self.log(ActionType.INIT, "Agent logger initialized", {
            "session_id": self.session_id,
            "log_file": str(self.log_file)
        })

    def log(self, action_type: ActionType, description: str,
            details: Dict[str, Any] = None, success: bool = True,
            error: str = None) -> AgentAction:
        """Log an agent action."""

        action = AgentAction(
            timestamp=datetime.now().isoformat(),
            action_type=action_type.value,
            description=description,
            details=details or {},
            success=success,
            error=error
        )

        self.actions.append(action)

        # Log to console
        status = "✓" if success else "✗"
        logger.info(f"[{action_type.value}] {status} {description}")
        if details:
            for key, value in details.items():
                if isinstance(value, str) and len(value) > 100:
                    value = value[:100] + "..."
                logger.info(f"  {key}: {value}")
        if error:
            logger.error(f"  Error: {error}")

        # Persist to file
        self._save()

        return action

    def start_action(self, action_type: ActionType, description: str):
        """Start timing an action."""
        self._current_action_start = datetime.now()
        logger.info(f"[{action_type.value}] ▶ Starting: {description}")

    def end_action(self, action_type: ActionType, description: str,
                   details: Dict[str, Any] = None, success: bool = True,
                   error: str = None) -> AgentAction:
        """End timing an action and log it."""
        duration_ms = None
        if self._current_action_start:
            delta = datetime.now() - self._current_action_start
            duration_ms = delta.total_seconds() * 1000
            self._current_action_start = None

        action = self.log(action_type, description, details, success, error)
        action.duration_ms = duration_ms

        if duration_ms:
            logger.info(f"  Duration: {duration_ms:.0f}ms")

        return action

    def get_recent_actions(self, limit: int = 20) -> List[Dict]:
        """Get recent actions for display."""
        recent = self.actions[-limit:] if len(self.actions) > limit else self.actions
        return [asdict(a) for a in recent]

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of agent activity."""
        total_actions = len(self.actions)
        success_count = sum(1 for a in self.actions if a.success)
        error_count = total_actions - success_count

        action_counts = {}
        for action in self.actions:
            action_type = action.action_type
            action_counts[action_type] = action_counts.get(action_type, 0) + 1

        return {
            "session_id": self.session_id,
            "total_actions": total_actions,
            "success_count": success_count,
            "error_count": error_count,
            "action_breakdown": action_counts,
            "duration_seconds": (datetime.now() - self._start_time).total_seconds()
        }

    def _save(self):
        """Save actions to log file."""
        try:
            data = {
                "session_id": self.session_id,
                "actions": [asdict(a) for a in self.actions],
                "summary": self.get_summary()
            }
            self.log_file.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        except Exception as e:
            logger.error(f"Failed to save log: {e}")

    def clear(self):
        """Clear all actions (new session)."""
        self.actions = []
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._start_time = datetime.now()
        self.log_file = self.log_dir / f"agent_{self.session_id}.json"


# Singleton instance
_agent_logger: Optional[AgentLogger] = None


def get_agent_logger() -> AgentLogger:
    """Get the singleton agent logger instance."""
    global _agent_logger
    if _agent_logger is None:
        _agent_logger = AgentLogger()
    return _agent_logger
