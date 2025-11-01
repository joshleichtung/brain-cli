"""Simple rule-based router for Brain CLI."""

from typing import Dict
from .agents.base import BaseAgent


class SimpleRouter:
    """Rule-based router for selecting agents based on task keywords."""

    # Simple keyword-based routing rules
    INTENT_RULES = {
        'code': ['code', 'program', 'function', 'debug', 'refactor', 'implement'],
        'research': ['research', 'find', 'search', 'learn', 'discover'],
        'analysis': ['analyze', 'explain', 'why does', 'how does', 'how can', 'understand'],
        'creative': ['create', 'imagine', 'brainstorm', 'design', 'generate'],
        'terminal': ['terminal', 'command', 'shell', 'bash', 'run'],
        'general': []
    }

    # Default agent preferences by intent
    DEFAULT_PREFERENCES = {
        'code': 'claude',
        'research': 'claude',
        'analysis': 'claude',
        'creative': 'gemini',
        'terminal': 'claude',
        'general': 'claude'
    }

    def __init__(self):
        """Initialize the router."""
        pass

    def classify_intent(self, task: str) -> str:
        """
        Classify task intent based on keywords.

        Args:
            task: User's task/question

        Returns:
            Intent category (code, research, analysis, creative, terminal, general)
        """
        task_lower = task.lower()

        # Check in priority order: more specific intents first
        priority_order = ['code', 'terminal', 'research', 'creative', 'analysis']

        for intent in priority_order:
            keywords = self.INTENT_RULES.get(intent, [])
            if any(keyword in task_lower for keyword in keywords):
                return intent

        return 'general'

    def select_agent(self, task: str, agents: Dict[str, BaseAgent],
                    preferred_agent: str = None) -> BaseAgent:
        """
        Select the best agent for a task.

        Args:
            task: User's task/question
            agents: Dict of available agent instances
            preferred_agent: Optional preference override

        Returns:
            Selected agent instance
        """
        # Use preferred agent if specified and available
        if preferred_agent and preferred_agent in agents:
            return agents[preferred_agent]

        # Classify task intent
        intent = self.classify_intent(task)

        # Get default preference for intent
        default_agent = self.DEFAULT_PREFERENCES.get(intent, 'claude')

        # Return agent if available, otherwise first available agent
        if default_agent in agents:
            return agents[default_agent]

        # Fallback to first available agent
        return next(iter(agents.values()))

    def should_use_multiple(self, task: str, complexity: float = 0.5) -> bool:
        """
        Determine if task should use multiple agents.

        For Phase 1, we keep this simple - always single agent.
        This will be enhanced in Phase 2 for comparison mode.

        Args:
            task: User's task/question
            complexity: Task complexity score (0-1)

        Returns:
            True if multiple agents should be used
        """
        # Phase 1: Always single agent
        return False
