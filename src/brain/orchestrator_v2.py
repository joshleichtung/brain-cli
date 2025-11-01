"""
Refactored agent-agnostic orchestrator with fleet and worktree management.

This is the v2 orchestrator that integrates:
- AgentFleetManager: On-demand agent spawning
- WorktreeManager: Git worktree isolation
- Async/await: Non-blocking execution
- Multi-agent coordination: Parallel execution with result comparison
"""

import asyncio
import os
from typing import Dict, Optional, List, Tuple
from datetime import datetime

from .agents.base import BaseAgent, AgentResult, RoutingPlan
from .agents.claude_code import ClaudeCodeAgent
from .router import SimpleRouter
from .fleet import AgentFleetManager
from .worktree import WorktreeManager


class AgnosticOrchestrator:
    """
    Agent-agnostic orchestrator with fleet management.

    Responsibilities:
    - Route tasks to appropriate agents
    - Spawn agents on-demand via fleet manager
    - Create isolated worktrees for parallel work
    - Suggest multi-agent execution (user confirms)
    - Display results side-by-side
    - Synthesize multi-agent results
    """

    def __init__(
        self,
        primary_agent_name: str,
        agent_configs: Dict[str, dict],
        workspace_path: str = None,
        session=None,
        max_concurrent_agents: int = 10
    ):
        """
        Initialize the orchestrator.

        Args:
            primary_agent_name: Name of primary orchestrating agent
            agent_configs: Dict mapping agent names to their configs
            workspace_path: Base workspace path for this session
            session: Optional session object for context
            max_concurrent_agents: Maximum concurrent agents in fleet
        """
        self.primary_name = primary_agent_name
        self.agent_configs = agent_configs
        self.workspace_path = workspace_path or os.getcwd()
        self.session = session

        # Initialize managers
        self.fleet = AgentFleetManager(max_concurrent=max_concurrent_agents)
        self.worktree_manager = WorktreeManager()
        self.router = SimpleRouter()

        # Create primary agent instance (for routing decisions)
        if primary_agent_name not in agent_configs:
            raise ValueError(f"Primary agent '{primary_agent_name}' not in configs")

        primary_config = agent_configs[primary_agent_name].copy()
        primary_config['name'] = primary_agent_name
        primary_config['workspace_path'] = workspace_path

        # For now, we'll use ClaudeCodeAgent as primary for routing
        # TODO: Support multiple agent types
        self.primary_agent = ClaudeCodeAgent(primary_config)

    async def execute(
        self,
        user_input: str,
        mode: str = "auto",
        num_agents: Optional[int] = None
    ) -> str:
        """
        Execute a user task with agent coordination.

        Args:
            user_input: User's task/question
            mode: Execution mode
                - "auto": Orchestrator suggests, user confirms (default)
                - "single": Force single agent
                - "multi": Force multiple agents (requires num_agents)
            num_agents: Number of agents for multi mode

        Returns:
            Final response string (or formatted multi-agent results)
        """
        context = self._build_context()

        if mode == "single":
            return await self._execute_single(user_input, context)

        elif mode == "multi":
            if num_agents is None:
                raise ValueError("num_agents required for multi mode")
            return await self._execute_multi(user_input, context, num_agents)

        elif mode == "auto":
            # Ask primary agent for routing suggestion
            suggestion = await self._get_routing_suggestion(user_input, context)

            # For now, default to single agent
            # TODO: Implement user confirmation UI
            if suggestion.requires_multiple:
                print(f"\n💡 Suggestion: Use {len(suggestion.recommended_agents)} agents")
                print(f"   Reasoning: {suggestion.intent} task, complexity {suggestion.complexity}")
                # For now, default to single
                return await self._execute_single(user_input, context)
            else:
                return await self._execute_single(user_input, context)

        else:
            raise ValueError(f"Unknown execution mode: {mode}")

    async def _execute_single(self, user_input: str, context: dict) -> str:
        """
        Execute with single agent using fleet manager.

        Args:
            user_input: User's task/question
            context: Context dict with conversation history

        Returns:
            Agent response
        """
        # Use router to select best agent
        agent_name = self.router.classify_intent(user_input)
        agent_config = self.agent_configs.get(
            self.router.DEFAULT_PREFERENCES.get(agent_name, 'claude-code')
        )

        if agent_config is None:
            agent_config = self.agent_configs[self.primary_name]

        # Prepare config
        config = agent_config.copy()
        config['name'] = agent_config.get('name', self.primary_name)
        config['workspace_path'] = self.workspace_path

        # Spawn agent via fleet
        agent_id = await self.fleet.spawn_agent(
            agent_class=ClaudeCodeAgent,  # TODO: Support multiple agent types
            task=user_input,
            project=self.session.workspace if self.session else 'default',
            config=config,
            worktree_path=None  # No worktree needed for single agent
        )

        if agent_id is None:
            return "⚠️ Task queued - too many concurrent agents"

        # Wait for completion
        try:
            result = await self.fleet.wait_for_agent(agent_id, timeout=300.0)

            # Update session
            self._update_session(result)

            return result.response

        except Exception as e:
            return f"❌ Error executing task: {e}"

        finally:
            # Cleanup
            self.fleet.cleanup_completed()

    async def _execute_multi(
        self,
        user_input: str,
        context: dict,
        num_agents: int
    ) -> str:
        """
        Execute with multiple agents in parallel.

        Args:
            user_input: User's task/question
            context: Context dict
            num_agents: Number of agents to spawn

        Returns:
            Formatted results from all agents
        """
        print(f"\n🚀 Spawning {num_agents} agents...")

        # Get project name for worktree management
        project = self.session.workspace if self.session else 'default'

        # Spawn multiple agents
        agent_ids = []
        for i in range(num_agents):
            # Create worktree for each agent (if git repo)
            agent_id_temp = f"agent-{i+1}-{os.urandom(4).hex()}"

            worktree_path = self.worktree_manager.get_or_create_worktree(
                repo_path=self.workspace_path,
                agent_id=agent_id_temp
            )

            # Prepare config
            config = self.agent_configs[self.primary_name].copy()
            config['name'] = self.primary_name
            config['workspace_path'] = worktree_path

            # Spawn agent
            agent_id = await self.fleet.spawn_agent(
                agent_class=ClaudeCodeAgent,
                task=user_input,
                project=project,
                config=config,
                worktree_path=worktree_path if worktree_path != self.workspace_path else None
            )

            if agent_id:
                agent_ids.append((agent_id, worktree_path))
                print(f"   ✅ Agent {i+1}: {agent_id}")

        print(f"\n⏳ Waiting for {len(agent_ids)} agents to complete...")

        # Wait for all agents
        results = []
        for agent_id, worktree_path in agent_ids:
            try:
                result = await self.fleet.wait_for_agent(agent_id, timeout=600.0)
                results.append(result)
                print(f"   ✅ {agent_id} completed")

                # Unlock worktree
                if worktree_path != self.workspace_path:
                    self.worktree_manager.unlock_worktree(agent_id)

            except Exception as e:
                print(f"   ❌ {agent_id} failed: {e}")

        # Cleanup
        self.fleet.cleanup_completed()

        # Format results side-by-side
        return self._format_multi_results(results, user_input)

    def _format_multi_results(
        self,
        results: List[AgentResult],
        original_task: str
    ) -> str:
        """
        Format multiple agent results for side-by-side display.

        Args:
            results: List of AgentResult objects
            original_task: Original user task

        Returns:
            Formatted string with all results
        """
        if not results:
            return "❌ No results from agents"

        if len(results) == 1:
            return results[0].response

        # Build formatted output
        output = [
            f"\n{'=' * 70}",
            f"📊 Results from {len(results)} agents",
            f"Task: {original_task}",
            f"{'=' * 70}\n"
        ]

        for i, result in enumerate(results, 1):
            output.extend([
                f"\n┌─ Agent {i}: {result.agent_name} {'─' * (50 - len(result.agent_name))}┐",
                f"│ Time: {result.time_taken:.2f}s | Tokens: {result.tokens_used} | Cost: ${result.cost:.4f}",
                f"│ Tools used: {result.metadata.get('num_tools_used', 0)}",
                f"├{'─' * 68}┤",
            ])

            # Split response into lines
            for line in result.response.split('\n'):
                # Wrap long lines
                if len(line) <= 66:
                    output.append(f"│ {line:<66} │")
                else:
                    # Simple wrapping
                    words = line.split()
                    current_line = "│ "
                    for word in words:
                        if len(current_line) + len(word) + 1 <= 68:
                            current_line += word + " "
                        else:
                            output.append(f"{current_line:<68} │")
                            current_line = "│ " + word + " "
                    if current_line.strip() != "│":
                        output.append(f"{current_line:<68} │")

            output.append(f"└{'─' * 68}┘")

        # Add summary
        total_cost = sum(r.cost for r in results)
        total_tokens = sum(r.tokens_used for r in results)
        avg_time = sum(r.time_taken for r in results) / len(results)

        output.extend([
            f"\n{'=' * 70}",
            f"💰 Total Cost: ${total_cost:.4f} | Total Tokens: {total_tokens}",
            f"⏱️  Average Time: {avg_time:.2f}s",
            f"{'=' * 70}\n"
        ])

        return '\n'.join(output)

    async def _get_routing_suggestion(
        self,
        task: str,
        context: dict
    ) -> RoutingPlan:
        """
        Get routing suggestion from primary agent.

        Args:
            task: User's task
            context: Context dict

        Returns:
            RoutingPlan with recommendations
        """
        # Use primary agent to analyze task
        return await self.primary_agent.create_routing_plan(
            task,
            self.agent_configs,
            context
        )

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

    def _update_session(self, result: AgentResult):
        """Update session with agent result."""
        if not self.session:
            return

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

    async def switch_orchestrator(self, new_agent_name: str):
        """
        Switch to a different primary agent mid-session.

        Args:
            new_agent_name: Name of new primary agent
        """
        if new_agent_name not in self.agent_configs:
            available = ', '.join(self.agent_configs.keys())
            raise ValueError(
                f"Agent '{new_agent_name}' not found. "
                f"Available: {available}"
            )

        # Export context from current agent
        old_context = self.primary_agent.export_context()

        # Create new primary agent
        config = self.agent_configs[new_agent_name].copy()
        config['name'] = new_agent_name
        config['workspace_path'] = self.workspace_path

        self.primary_agent = ClaudeCodeAgent(config)
        self.primary_name = new_agent_name

        # Import context to new agent
        self.primary_agent.import_context(old_context)

        # Update session
        if self.session:
            self.session.primary_agent = new_agent_name

    async def get_agent_status(self) -> Dict[str, bool]:
        """
        Get health status of primary agent.

        Returns:
            Dict with agent health status
        """
        is_healthy = await self.primary_agent.ping()
        return {self.primary_name: is_healthy}

    def get_fleet_status(self) -> dict:
        """
        Get fleet manager status.

        Returns:
            Dict with fleet stats
        """
        return {
            'active_agents': len(self.fleet.list_active_agents()),
            'running': self.fleet.get_running_count(),
            'queued': self.fleet.get_queue_size(),
            'max_concurrent': self.fleet.max_concurrent
        }

    def get_project_stats(self) -> dict:
        """
        Get aggregate stats for current project.

        Returns:
            Dict with project stats
        """
        project = self.session.workspace if self.session else 'default'
        return self.fleet.get_project_stats(project)
