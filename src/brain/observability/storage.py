"""
Event storage using SQLite.

Stores all observability events for analytics and visualization.
"""

import os
import sqlite3
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from contextlib import contextmanager

from .events import BaseEvent, EventType


class EventStore:
    """
    SQLite-based event storage.

    Stores all observability events with efficient querying.
    """

    def __init__(self, db_path: str = None):
        """
        Initialize event store.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path or os.path.expanduser('~/brain/workspace/.observability/events.db')
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_database()

    def _init_database(self):
        """Initialize database schema."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    project TEXT NOT NULL,

                    -- Agent fields
                    agent_id TEXT,
                    agent_name TEXT,
                    task TEXT,
                    workspace_path TEXT,

                    -- Result fields
                    tokens_used INTEGER,
                    cost REAL,
                    time_taken REAL,
                    error_message TEXT,
                    response TEXT,

                    -- Tool fields
                    tool_name TEXT,
                    tool_input TEXT,
                    success BOOLEAN,

                    -- Worktree fields
                    worktree_path TEXT,
                    repo_path TEXT,
                    branch TEXT,

                    -- Session fields
                    session_name TEXT,
                    total_tokens INTEGER,
                    total_cost REAL,
                    conversation_turns INTEGER,

                    -- Metadata
                    metadata TEXT,

                    -- Indexes
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create indexes for common queries
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_event_type
                ON events(event_type)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_project
                ON events(project)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_agent_id
                ON events(agent_id)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp
                ON events(timestamp)
            """)

            conn.commit()

    @contextmanager
    def _get_connection(self):
        """Get database connection context manager."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def store_event(self, event: BaseEvent):
        """
        Store an event in the database.

        Args:
            event: Event to store
        """
        event_dict = event.to_dict()

        with self._get_connection() as conn:
            # Convert metadata to JSON string
            metadata_json = json.dumps(event_dict.pop('metadata', {}))

            # Extract common fields
            event_type = event_dict.pop('event_type')
            timestamp = event_dict.pop('timestamp')
            project = event_dict.pop('project')

            # Build insert statement dynamically based on available fields
            fields = ['event_type', 'timestamp', 'project', 'metadata']
            values = [event_type, timestamp, project, metadata_json]

            for key, value in event_dict.items():
                if value is not None:
                    fields.append(key)
                    # Convert dict/list to JSON
                    if isinstance(value, (dict, list)):
                        values.append(json.dumps(value))
                    else:
                        values.append(value)

            placeholders = ','.join(['?' for _ in values])
            fields_str = ','.join(fields)

            conn.execute(
                f"INSERT INTO events ({fields_str}) VALUES ({placeholders})",
                values
            )
            conn.commit()

    def get_events(
        self,
        event_type: Optional[EventType] = None,
        project: Optional[str] = None,
        agent_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Query events from storage.

        Args:
            event_type: Filter by event type
            project: Filter by project
            agent_id: Filter by agent ID
            limit: Maximum number of events to return
            offset: Offset for pagination

        Returns:
            List of event dictionaries
        """
        with self._get_connection() as conn:
            query = "SELECT * FROM events WHERE 1=1"
            params = []

            if event_type:
                query += " AND event_type = ?"
                params.append(event_type.value)

            if project:
                query += " AND project = ?"
                params.append(project)

            if agent_id:
                query += " AND agent_id = ?"
                params.append(agent_id)

            query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

            events = []
            for row in rows:
                event = dict(row)
                # Parse JSON fields
                if event.get('metadata'):
                    event['metadata'] = json.loads(event['metadata'])
                if event.get('tool_input'):
                    event['tool_input'] = json.loads(event['tool_input'])
                events.append(event)

            return events

    def get_project_stats(self, project: str) -> Dict[str, Any]:
        """
        Get aggregate statistics for a project.

        Args:
            project: Project name

        Returns:
            Dictionary with project statistics
        """
        with self._get_connection() as conn:
            # Total agents
            cursor = conn.execute("""
                SELECT COUNT(DISTINCT agent_id) as total_agents
                FROM events
                WHERE project = ? AND event_type = 'agent_spawned'
            """, (project,))
            total_agents = cursor.fetchone()['total_agents']

            # Completed agents
            cursor = conn.execute("""
                SELECT COUNT(*) as completed
                FROM events
                WHERE project = ? AND event_type = 'agent_completed'
            """, (project,))
            completed = cursor.fetchone()['completed']

            # Failed agents
            cursor = conn.execute("""
                SELECT COUNT(*) as failed
                FROM events
                WHERE project = ? AND event_type = 'agent_failed'
            """, (project,))
            failed = cursor.fetchone()['failed']

            # Total cost and tokens
            cursor = conn.execute("""
                SELECT
                    COALESCE(SUM(cost), 0) as total_cost,
                    COALESCE(SUM(tokens_used), 0) as total_tokens
                FROM events
                WHERE project = ? AND event_type = 'agent_completed'
            """, (project,))
            row = cursor.fetchone()

            # Tool usage
            cursor = conn.execute("""
                SELECT tool_name, COUNT(*) as count
                FROM events
                WHERE project = ? AND event_type = 'tool_used'
                GROUP BY tool_name
                ORDER BY count DESC
                LIMIT 10
            """, (project,))
            tool_usage = [dict(row) for row in cursor.fetchall()]

            return {
                'total_agents': total_agents,
                'completed': completed,
                'failed': failed,
                'total_cost': float(row['total_cost']),
                'total_tokens': int(row['total_tokens']),
                'tool_usage': tool_usage
            }

    def get_agent_timeline(self, agent_id: str) -> List[Dict[str, Any]]:
        """
        Get timeline of events for a specific agent.

        Args:
            agent_id: Agent ID

        Returns:
            List of events in chronological order
        """
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM events
                WHERE agent_id = ?
                ORDER BY timestamp ASC
            """, (agent_id,))

            rows = cursor.fetchall()
            events = []
            for row in rows:
                event = dict(row)
                if event.get('metadata'):
                    event['metadata'] = json.loads(event['metadata'])
                if event.get('tool_input'):
                    event['tool_input'] = json.loads(event['tool_input'])
                events.append(event)

            return events

    def clear_project_events(self, project: str):
        """
        Clear all events for a project.

        Args:
            project: Project name
        """
        with self._get_connection() as conn:
            conn.execute("DELETE FROM events WHERE project = ?", (project,))
            conn.commit()

    def vacuum(self):
        """Optimize database file size."""
        with self._get_connection() as conn:
            conn.execute("VACUUM")


# Global event store instance
_global_store = None


def get_event_store() -> EventStore:
    """Get global event store instance."""
    global _global_store
    if _global_store is None:
        _global_store = EventStore()
    return _global_store
