"""
Observability system for Brain CLI.

Provides event-driven observability with:
- Hook system for lifecycle events
- SQLite event storage
- Analytics and visualization support
"""

from .events import (
    EventType,
    BaseEvent,
    AgentEvent,
    ToolEvent,
    WorktreeEvent,
    SessionEvent
)

from .hooks import HookManager, get_hooks
from .storage import EventStore, get_event_store


__all__ = [
    'EventType',
    'BaseEvent',
    'AgentEvent',
    'ToolEvent',
    'WorktreeEvent',
    'SessionEvent',
    'HookManager',
    'get_hooks',
    'EventStore',
    'get_event_store'
]
