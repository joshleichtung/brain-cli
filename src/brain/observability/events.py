"""
Event models for observability system.

Based on Big-3 Super Agent observability patterns, tracking:
- Agent lifecycle events
- Tool usage
- Worktree management
- Session updates
- Cost/token tracking
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum


class EventType(Enum):
    """Types of observable events."""
    AGENT_SPAWNED = "agent_spawned"
    AGENT_STARTED = "agent_started"
    AGENT_COMPLETED = "agent_completed"
    AGENT_FAILED = "agent_failed"
    TOOL_USED = "tool_used"
    WORKTREE_CREATED = "worktree_created"
    WORKTREE_REMOVED = "worktree_removed"
    SESSION_UPDATED = "session_updated"


@dataclass
class BaseEvent:
    """Base event class."""
    event_type: EventType
    timestamp: datetime
    project: str
    metadata: Dict[str, Any]

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        data = asdict(self)
        data['event_type'] = self.event_type.value
        data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass
class AgentEvent(BaseEvent):
    """Agent lifecycle event."""
    agent_id: str
    agent_name: str
    task: str
    workspace_path: str

    # Optional fields depending on event type
    error_message: Optional[str] = None
    tokens_used: Optional[int] = None
    cost: Optional[float] = None
    time_taken: Optional[float] = None
    response: Optional[str] = None

    def to_dict(self) -> dict:
        data = super().to_dict()
        # Remove None values for cleaner storage
        return {k: v for k, v in data.items() if v is not None}


@dataclass
class ToolEvent(BaseEvent):
    """Tool usage event."""
    agent_id: str
    tool_name: str
    tool_input: Dict[str, Any]
    success: bool
    error_message: Optional[str] = None

    def to_dict(self) -> dict:
        data = super().to_dict()
        return {k: v for k, v in data.items() if v is not None}


@dataclass
class WorktreeEvent(BaseEvent):
    """Worktree lifecycle event."""
    agent_id: str
    worktree_path: str
    repo_path: str
    branch: str

    def to_dict(self) -> dict:
        return super().to_dict()


@dataclass
class SessionEvent(BaseEvent):
    """Session update event."""
    session_name: str
    total_tokens: int
    total_cost: float
    conversation_turns: int

    def to_dict(self) -> dict:
        return super().to_dict()
