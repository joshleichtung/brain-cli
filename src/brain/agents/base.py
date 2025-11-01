"""Base agent interface for Brain CLI."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Optional, Dict, Any


@dataclass
class AgentResult:
    """Result from agent execution."""

    agent_name: str
    task: str
    response: str
    time_taken: float  # seconds
    tokens_used: int
    cost: float
    quality_score: Optional[float] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class RoutingPlan:
    """Plan for routing a task to agents."""

    task: str
    intent: str  # 'code', 'research', 'analysis', 'creative', etc.
    complexity: float  # 0-1
    requires_multiple: bool
    recommended_agents: List[str]
    parallel_execution: bool
    context: dict
    estimated_tokens: int

    def to_dict(self) -> dict:
        return asdict(self)


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
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


class Context:
    """Conversation context."""

    def __init__(self):
        self.conversation: List[Turn] = []
        self.session_memory: Dict[str, Any] = {}
        self.task_context: Dict[str, Any] = {}
        self.user_prefs: Dict[str, Any] = {}

    def export(self) -> dict:
        return {
            'conversation': [t.to_dict() for t in self.conversation],
            'memory': self.session_memory,
            'task': self.task_context,
            'prefs': self.user_prefs
        }

    def import_from(self, data: dict):
        self.conversation = [Turn.from_dict(t) for t in data.get('conversation', [])]
        self.session_memory = data.get('memory', {})
        self.task_context = data.get('task', {})
        self.user_prefs = data.get('prefs', {})


class BaseAgent(ABC):
    """Abstract base class for all AI agents."""

    def __init__(self, config: dict):
        self.name = config['name']
        self.config = config
        self.context = Context()

    @abstractmethod
    def execute(self, task: str, context: dict) -> AgentResult:
        """
        Execute a task with given context.

        Args:
            task: User's task/question
            context: Dict containing conversation history, memory, etc.

        Returns:
            AgentResult with response and metadata
        """
        pass

    @abstractmethod
    def create_routing_plan(self, task: str, available_agents: dict,
                           context: dict) -> RoutingPlan:
        """
        Analyze task and create routing plan.
        Only called when this agent is primary orchestrator.

        Args:
            task: User's task/question
            available_agents: Dict of available agent instances
            context: Current context

        Returns:
            RoutingPlan with recommendations
        """
        pass

    @abstractmethod
    def synthesize(self, results: List[AgentResult],
                   original_task: str) -> str:
        """
        Synthesize multiple agent results into final response.
        Only called when this agent is primary orchestrator.

        Args:
            results: List of results from different agents
            original_task: The original user task

        Returns:
            Synthesized response string
        """
        pass

    @abstractmethod
    def export_context(self) -> dict:
        """Export current context for agent switching."""
        pass

    @abstractmethod
    def import_context(self, data: dict):
        """Import context from another agent."""
        pass

    @abstractmethod
    def ping(self) -> bool:
        """Health check - verify agent is responsive."""
        pass

    def estimate_cost(self, tokens: int) -> float:
        """Calculate cost based on token usage."""
        cost_per_1k = self.config.get('cost_per_1k_tokens', 0.0)
        return tokens * cost_per_1k / 1000
