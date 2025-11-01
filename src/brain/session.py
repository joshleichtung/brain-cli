"""Session management for Brain CLI."""

import json
import os
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any


@dataclass
class Turn:
    """A single conversation turn."""

    role: str  # 'user' or 'assistant'
    content: str
    agent: str
    timestamp: datetime
    tokens: int
    cost: float

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            'role': self.role,
            'content': self.content,
            'agent': self.agent,
            'timestamp': self.timestamp.isoformat(),
            'tokens': self.tokens,
            'cost': self.cost
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Turn':
        """Create from dictionary."""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


@dataclass
class Session:
    """Session state for a workspace."""

    id: str
    workspace: str
    primary_agent: str
    created_at: datetime
    last_active: datetime
    conversation: List[Turn]
    context: Dict[str, Any]
    total_tokens: int
    total_cost: float

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            'id': self.id,
            'workspace': self.workspace,
            'primary_agent': self.primary_agent,
            'created_at': self.created_at.isoformat(),
            'last_active': self.last_active.isoformat(),
            'conversation': [t.to_dict() for t in self.conversation],
            'context': self.context,
            'total_tokens': self.total_tokens,
            'total_cost': self.total_cost
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Session':
        """Create from dictionary."""
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['last_active'] = datetime.fromisoformat(data['last_active'])
        data['conversation'] = [Turn.from_dict(t) for t in data['conversation']]
        return cls(**data)


class SessionRegistry:
    """Registry for managing workspace sessions."""

    def __init__(self, base_dir: str = '~/brain/workspace/.sessions'):
        """
        Initialize session registry.

        Args:
            base_dir: Base directory for session storage
        """
        self.base_dir = os.path.expanduser(base_dir)
        os.makedirs(self.base_dir, exist_ok=True)

    def create_session(self, workspace: str, primary_agent: str) -> Session:
        """
        Create a new session for a workspace.

        Args:
            workspace: Workspace name
            primary_agent: Primary agent name

        Returns:
            New Session instance
        """
        session_id = f"{workspace}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        session_dir = os.path.join(self.base_dir, workspace)
        os.makedirs(session_dir, exist_ok=True)
        os.makedirs(os.path.join(session_dir, 'history'), exist_ok=True)

        session = Session(
            id=session_id,
            workspace=workspace,
            primary_agent=primary_agent,
            created_at=datetime.now(),
            last_active=datetime.now(),
            conversation=[],
            context={},
            total_tokens=0,
            total_cost=0.0
        )

        self.save_session(session)
        return session

    def save_session(self, session: Session):
        """
        Save session to disk.

        Args:
            session: Session to save
        """
        session_dir = os.path.join(self.base_dir, session.workspace)
        session_file = os.path.join(session_dir, 'session.json')

        # Update last active timestamp
        session.last_active = datetime.now()

        # Save current state
        with open(session_file, 'w') as f:
            json.dump(session.to_dict(), f, indent=2)

        # Archive to history for backup
        history_file = os.path.join(
            session_dir,
            'history',
            f"{datetime.now().strftime('%Y-%m-%d_%H-%M')}.json"
        )
        with open(history_file, 'w') as f:
            json.dump(session.to_dict(), f, indent=2)

    def load_session(self, workspace: str) -> Optional[Session]:
        """
        Load existing session for a workspace.

        Args:
            workspace: Workspace name

        Returns:
            Session if exists, None otherwise
        """
        session_file = os.path.join(self.base_dir, workspace, 'session.json')

        if not os.path.exists(session_file):
            return None

        with open(session_file) as f:
            data = json.load(f)

        return Session.from_dict(data)

    def list_workspaces(self) -> List[str]:
        """
        List all workspaces with sessions.

        Returns:
            List of workspace names
        """
        return [
            d for d in os.listdir(self.base_dir)
            if os.path.isdir(os.path.join(self.base_dir, d))
        ]

    def add_turn(self, session: Session, turn: Turn):
        """
        Add a conversation turn to the session.

        Args:
            session: Session to update
            turn: Turn to add
        """
        session.conversation.append(turn)
        session.total_tokens += turn.tokens
        session.total_cost += turn.cost
        self.save_session(session)

    def switch_primary_agent(self, session: Session, new_agent: str):
        """
        Switch the primary orchestrator for a session.

        Args:
            session: Session to update
            new_agent: New primary agent name
        """
        session.primary_agent = new_agent
        self.save_session(session)
