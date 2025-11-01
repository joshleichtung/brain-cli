"""Agent-agnostic orchestrator for Brain CLI."""

from typing import Dict, Optional, List
from datetime import datetime

from .agents.base import BaseAgent, AgentResult, RoutingPlan
from .router import SimpleRouter


class AgnosticOrchestrator:
    """
    Agent-agnostic orchestrator that coordinates multiple AI agents.

    Responsibilities:
    - Route tasks to appropriate agents
    - Manage agent switching
    - Preserve context across agents
    - Synthesize multi-agent results
    """

    def __init__(self, primary_agent_name: str, agents: Dict[str, BaseAgent],
                 session=None):
        """
        Initialize the orchestrator.

        Args:
            primary_agent_name: Name of the primary orchestrating agent
            agents: Dict mapping agent names to agent instances
            session: Optional session object for context
        """
        self.primary_name = primary_agent_name
        self.agents = agents
        self.router = SimpleRouter()
        self.session = session

        if primary_agent_name not in agents:
            raise ValueError(f"Primary agent '{primary_agent_name}' not found in agents")

        self.primary_agent = agents[primary_agent_name]

    def execute(self, user_input: str, mode: str = "single") -> str:
        """
        Execute a user task with agent coordination.

        Args:
            user_input: User's task/question
            mode: Execution mode ('single', 'compare', 'parallel')

        Returns:
            Final response string
        """
        # Build context from session
        context = self._build_context()

        if mode == "single":
            return self._execute_single(user_input, context)
        elif mode == "compare":
            return self._execute_compare(user_input, context)
        elif mode == "parallel":
            return self._execute_parallel(user_input, context)
        else:
            raise ValueError(f"Unknown execution mode: {mode}")

    def _execute_single(self, user_input: str, context: dict) -> str:
        """
        Execute with single agent (primary or routed).

        Args:
            user_input: User's task/question
            context: Context dict with conversation history

        Returns:
            Agent response
        """
        # For Phase 1, we use simple routing
        # In Phase 2, we'll ask the primary agent to create a routing plan
        selected_agent = self.router.select_agent(
            user_input,
            self.agents,
            preferred_agent=self.primary_name
        )

        # Execute with selected agent
        result = selected_agent.execute(user_input, context)

        # Update session if available
        if self.session:
            from .agents.base import Turn
            turn = Turn(
                role='assistant',
                content=result.response,
                agent=result.agent_name,
                timestamp=datetime.now(),
                tokens=result.tokens_used,
                cost=result.cost
            )
            self.session.conversation.append(turn)
            self.session.total_tokens += result.tokens_used
            self.session.total_cost += result.cost

        return result.response

    def _execute_compare(self, user_input: str, context: dict) -> str:
        """
        Execute with multiple agents for comparison (Phase 2 feature).

        Args:
            user_input: User's task/question
            context: Context dict

        Returns:
            Synthesized response
        """
        # Phase 1: Not implemented yet
        # Phase 2: Execute with all available agents and compare
        return "Compare mode will be available in Phase 2"

    def _execute_parallel(self, user_input: str, context: dict) -> str:
        """
        Execute with multiple agents in parallel (Phase 2 feature).

        Args:
            user_input: User's task/question
            context: Context dict

        Returns:
            Synthesized response
        """
        # Phase 1: Not implemented yet
        # Phase 2: Execute with multiple agents and synthesize
        return "Parallel mode will be available in Phase 2"

    def _build_context(self) -> dict:
        """
        Build context dict from session.

        Returns:
            Context dict with conversation history
        """
        if not self.session:
            return {'conversation': []}

        # Convert Turn objects to dict format
        conversation = []
        for turn in self.session.conversation[-10:]:  # Last 10 turns
            conversation.append({
                'role': turn.role,
                'content': turn.content,
                'agent': turn.agent
            })

        context = {
            'conversation': conversation,
            'workspace': getattr(self.session, 'workspace', 'default'),
            'session_context': getattr(self.session, 'context', {})
        }

        return context

    def switch_orchestrator(self, new_agent_name: str):
        """
        Switch to a different primary agent mid-session.

        Args:
            new_agent_name: Name of new primary agent

        Raises:
            ValueError: If agent not found
        """
        if new_agent_name not in self.agents:
            available = ', '.join(self.agents.keys())
            raise ValueError(
                f"Agent '{new_agent_name}' not found. "
                f"Available: {available}"
            )

        # Export context from current agent
        old_context = self.primary_agent.export_context()

        # Switch to new agent
        self.primary_name = new_agent_name
        self.primary_agent = self.agents[new_agent_name]

        # Import context to new agent
        self.primary_agent.import_context(old_context)

        # Update session
        if self.session:
            self.session.primary_agent = new_agent_name

    def get_agent_status(self) -> Dict[str, bool]:
        """
        Get health status of all agents.

        Returns:
            Dict mapping agent names to health status
        """
        status = {}
        for name, agent in self.agents.items():
            status[name] = agent.ping()
        return status

    def get_routing_plan(self, task: str) -> RoutingPlan:
        """
        Get routing plan from primary agent.

        Args:
            task: User's task/question

        Returns:
            RoutingPlan with recommendations
        """
        context = self._build_context()
        return self.primary_agent.create_routing_plan(
            task,
            self.agents,
            context
        )

    def synthesize_results(self, results: List[AgentResult],
                          original_task: str) -> str:
        """
        Synthesize multiple agent results.

        Args:
            results: List of AgentResult objects
            original_task: Original user task

        Returns:
            Synthesized response
        """
        return self.primary_agent.synthesize(results, original_task)
