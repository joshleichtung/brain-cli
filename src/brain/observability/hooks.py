"""
Hook system for observability.

Implements observer pattern for event-driven observability.
Components can subscribe to events and react accordingly.
"""

import asyncio
from typing import Callable, List, Dict, Any
from datetime import datetime

from .events import BaseEvent, EventType, AgentEvent, ToolEvent, WorktreeEvent, SessionEvent


class HookManager:
    """
    Manages event hooks for observability.

    Components can subscribe to specific event types and receive
    notifications when those events occur.
    """

    def __init__(self):
        """Initialize hook manager."""
        self.subscribers: Dict[EventType, List[Callable]] = {
            event_type: [] for event_type in EventType
        }

    def subscribe(self, event_type: EventType, callback: Callable):
        """
        Subscribe to an event type.

        Args:
            event_type: Type of event to subscribe to
            callback: Function to call when event occurs
                     Should accept BaseEvent as parameter
        """
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []

        self.subscribers[event_type].append(callback)

    def unsubscribe(self, event_type: EventType, callback: Callable):
        """
        Unsubscribe from an event type.

        Args:
            event_type: Type of event to unsubscribe from
            callback: Previously subscribed callback
        """
        if event_type in self.subscribers:
            try:
                self.subscribers[event_type].remove(callback)
            except ValueError:
                pass  # Callback not in list

    async def emit(self, event: BaseEvent):
        """
        Emit an event to all subscribers.

        Args:
            event: Event to emit
        """
        event_type = event.event_type

        if event_type not in self.subscribers:
            return

        # Call all subscribers
        tasks = []
        for callback in self.subscribers[event_type]:
            try:
                # Support both sync and async callbacks
                if asyncio.iscoroutinefunction(callback):
                    tasks.append(callback(event))
                else:
                    callback(event)
            except Exception as e:
                # Don't let subscriber errors crash the system
                print(f"⚠️  Hook error for {event_type.value}: {e}")

        # Wait for async callbacks
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    def emit_sync(self, event: BaseEvent):
        """
        Emit an event synchronously.

        Args:
            event: Event to emit
        """
        event_type = event.event_type

        if event_type not in self.subscribers:
            return

        for callback in self.subscribers[event_type]:
            try:
                # Only call sync callbacks
                if not asyncio.iscoroutinefunction(callback):
                    callback(event)
            except Exception as e:
                print(f"⚠️  Hook error for {event_type.value}: {e}")

    # Convenience methods for creating and emitting common events

    async def agent_spawned(
        self,
        agent_id: str,
        agent_name: str,
        task: str,
        workspace_path: str,
        project: str,
        metadata: Dict[str, Any] = None
    ):
        """Emit agent spawned event."""
        event = AgentEvent(
            event_type=EventType.AGENT_SPAWNED,
            timestamp=datetime.now(),
            project=project,
            metadata=metadata or {},
            agent_id=agent_id,
            agent_name=agent_name,
            task=task,
            workspace_path=workspace_path
        )
        await self.emit(event)

    async def agent_started(
        self,
        agent_id: str,
        agent_name: str,
        task: str,
        workspace_path: str,
        project: str,
        metadata: Dict[str, Any] = None
    ):
        """Emit agent started event."""
        event = AgentEvent(
            event_type=EventType.AGENT_STARTED,
            timestamp=datetime.now(),
            project=project,
            metadata=metadata or {},
            agent_id=agent_id,
            agent_name=agent_name,
            task=task,
            workspace_path=workspace_path
        )
        await self.emit(event)

    async def agent_completed(
        self,
        agent_id: str,
        agent_name: str,
        task: str,
        workspace_path: str,
        project: str,
        tokens_used: int,
        cost: float,
        time_taken: float,
        response: str,
        metadata: Dict[str, Any] = None
    ):
        """Emit agent completed event."""
        event = AgentEvent(
            event_type=EventType.AGENT_COMPLETED,
            timestamp=datetime.now(),
            project=project,
            metadata=metadata or {},
            agent_id=agent_id,
            agent_name=agent_name,
            task=task,
            workspace_path=workspace_path,
            tokens_used=tokens_used,
            cost=cost,
            time_taken=time_taken,
            response=response
        )
        await self.emit(event)

    async def agent_failed(
        self,
        agent_id: str,
        agent_name: str,
        task: str,
        workspace_path: str,
        project: str,
        error_message: str,
        metadata: Dict[str, Any] = None
    ):
        """Emit agent failed event."""
        event = AgentEvent(
            event_type=EventType.AGENT_FAILED,
            timestamp=datetime.now(),
            project=project,
            metadata=metadata or {},
            agent_id=agent_id,
            agent_name=agent_name,
            task=task,
            workspace_path=workspace_path,
            error_message=error_message
        )
        await self.emit(event)

    async def tool_used(
        self,
        agent_id: str,
        tool_name: str,
        tool_input: Dict[str, Any],
        success: bool,
        project: str,
        error_message: str = None,
        metadata: Dict[str, Any] = None
    ):
        """Emit tool used event."""
        event = ToolEvent(
            event_type=EventType.TOOL_USED,
            timestamp=datetime.now(),
            project=project,
            metadata=metadata or {},
            agent_id=agent_id,
            tool_name=tool_name,
            tool_input=tool_input,
            success=success,
            error_message=error_message
        )
        await self.emit(event)

    async def worktree_created(
        self,
        agent_id: str,
        worktree_path: str,
        repo_path: str,
        branch: str,
        project: str,
        metadata: Dict[str, Any] = None
    ):
        """Emit worktree created event."""
        event = WorktreeEvent(
            event_type=EventType.WORKTREE_CREATED,
            timestamp=datetime.now(),
            project=project,
            metadata=metadata or {},
            agent_id=agent_id,
            worktree_path=worktree_path,
            repo_path=repo_path,
            branch=branch
        )
        await self.emit(event)

    async def worktree_removed(
        self,
        agent_id: str,
        worktree_path: str,
        repo_path: str,
        branch: str,
        project: str,
        metadata: Dict[str, Any] = None
    ):
        """Emit worktree removed event."""
        event = WorktreeEvent(
            event_type=EventType.WORKTREE_REMOVED,
            timestamp=datetime.now(),
            project=project,
            metadata=metadata or {},
            agent_id=agent_id,
            worktree_path=worktree_path,
            repo_path=repo_path,
            branch=branch
        )
        await self.emit(event)

    async def session_updated(
        self,
        session_name: str,
        total_tokens: int,
        total_cost: float,
        conversation_turns: int,
        project: str,
        metadata: Dict[str, Any] = None
    ):
        """Emit session updated event."""
        event = SessionEvent(
            event_type=EventType.SESSION_UPDATED,
            timestamp=datetime.now(),
            project=project,
            metadata=metadata or {},
            session_name=session_name,
            total_tokens=total_tokens,
            total_cost=total_cost,
            conversation_turns=conversation_turns
        )
        await self.emit(event)


# Global hook manager instance
_global_hooks = None


def get_hooks() -> HookManager:
    """Get global hook manager instance."""
    global _global_hooks
    if _global_hooks is None:
        _global_hooks = HookManager()
    return _global_hooks
