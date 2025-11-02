"""Agent Fleet Manager for orchestrating multiple agents."""

import asyncio
import sqlite3
import os
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum

from .agents.base import BaseAgent, AgentResult
from .observability import get_hooks


class AgentStatus(Enum):
    """Agent status states."""
    SPAWNING = "spawning"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SHUTDOWN = "shutdown"


@dataclass
class AgentInstance:
    """Represents a running agent instance."""
    agent_id: str
    agent_name: str  # Type of agent (claude-code, gemini, etc.)
    project: str     # Which workspace/project
    task: str
    status: AgentStatus
    worktree_path: Optional[str]
    spawn_time: datetime
    completion_time: Optional[datetime] = None
    result: Optional[AgentResult] = None
    error: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            'agent_id': self.agent_id,
            'agent_name': self.agent_name,
            'project': self.project,
            'task': self.task,
            'status': self.status.value,
            'worktree_path': self.worktree_path,
            'spawn_time': self.spawn_time.isoformat(),
            'completion_time': self.completion_time.isoformat() if self.completion_time else None,
            'error': self.error
        }


class AgentFleetManager:
    """
    Manages a fleet of agent instances.

    Responsibilities:
    - Spawn agents on-demand
    - Track active agents (max concurrency)
    - Queue tasks if over limit
    - Monitor agent status
    - Cleanup completed agents
    - Persist agent registry to SQLite
    """

    def __init__(self, db_path: str = None, max_concurrent: int = 10):
        """
        Initialize fleet manager.

        Args:
            db_path: Path to SQLite database for agent registry
            max_concurrent: Maximum concurrent agents (default: 10)
        """
        self.max_concurrent = max_concurrent
        self.active_agents: Dict[str, AgentInstance] = {}
        self.task_queue: List[tuple] = []  # (agent_class, task, project, config)

        # Setup database
        if db_path is None:
            db_path = os.path.expanduser('~/brain/workspace/.fleet/agents.db')

        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Initialize SQLite database for agent registry."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS agents (
                agent_id TEXT PRIMARY KEY,
                agent_name TEXT NOT NULL,
                project TEXT NOT NULL,
                task TEXT NOT NULL,
                status TEXT NOT NULL,
                worktree_path TEXT,
                spawn_time TEXT NOT NULL,
                completion_time TEXT,
                error TEXT,
                tokens_used INTEGER,
                cost_usd REAL,
                time_taken_seconds REAL
            )
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_project
            ON agents(project)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_status
            ON agents(status)
        ''')

        conn.commit()
        conn.close()

    async def spawn_agent(
        self,
        agent_class: type,
        task: str,
        project: str,
        config: dict,
        worktree_path: Optional[str] = None
    ) -> str:
        """
        Spawn a new agent instance.

        Args:
            agent_class: Agent class to instantiate (ClaudeCodeAgent, etc.)
            task: Task for agent to execute
            project: Which workspace/project this belongs to
            config: Configuration dict for agent
            worktree_path: Optional worktree path (managed by WorktreeManager)

        Returns:
            agent_id: Unique identifier for this agent instance
        """
        # Check concurrency limit
        if len(self.active_agents) >= self.max_concurrent:
            # Queue the task
            self.task_queue.append((agent_class, task, project, config, worktree_path))
            print(f"⏸️  Max concurrency reached ({self.max_concurrent}). Queued task.")
            return None

        # Generate unique agent ID
        import uuid
        agent_id = f"{config['name']}-{uuid.uuid4().hex[:8]}"

        # Create agent instance record
        instance = AgentInstance(
            agent_id=agent_id,
            agent_name=config['name'],
            project=project,
            task=task,
            status=AgentStatus.SPAWNING,
            worktree_path=worktree_path,
            spawn_time=datetime.now()
        )

        # Add to active agents
        self.active_agents[agent_id] = instance

        # Save to database
        self._save_instance(instance)

        # Spawn agent asynchronously
        asyncio.create_task(self._run_agent(agent_id, agent_class, config, task))

        print(f"🚀 Spawned agent: {agent_id} (project: {project})")

        # Emit hook event
        hooks = get_hooks()
        asyncio.create_task(hooks.agent_spawned(
            agent_id=agent_id,
            agent_name=config['name'],
            task=task,
            workspace_path=config.get('workspace_path', ''),
            project=project,
            metadata={'worktree_path': worktree_path}
        ))

        return agent_id

    async def _run_agent(
        self,
        agent_id: str,
        agent_class: type,
        config: dict,
        task: str
    ):
        """
        Run an agent asynchronously.

        This is the actual agent execution that happens in background.
        """
        instance = self.active_agents[agent_id]

        try:
            # Update status to running
            instance.status = AgentStatus.RUNNING
            self._save_instance(instance)

            # Emit hook event
            hooks = get_hooks()
            await hooks.agent_started(
                agent_id=agent_id,
                agent_name=instance.agent_name,
                task=task,
                workspace_path=config.get('workspace_path', ''),
                project=instance.project
            )

            # Create agent
            agent: BaseAgent = agent_class(config)

            # Execute task
            result = await agent.execute(task, context={})

            # Update instance with result
            instance.result = result
            instance.status = AgentStatus.COMPLETED
            instance.completion_time = datetime.now()

            self._save_instance(instance)

            print(f"✅ Agent completed: {agent_id}")
            print(f"   Response: {result.response[:100]}...")
            print(f"   Tokens: {result.tokens_used} | Cost: ${result.cost:.4f}")

            # Emit hook event
            time_taken = (instance.completion_time - instance.spawn_time).total_seconds()
            await hooks.agent_completed(
                agent_id=agent_id,
                agent_name=instance.agent_name,
                task=task,
                workspace_path=config.get('workspace_path', ''),
                project=instance.project,
                tokens_used=result.tokens_used,
                cost=result.cost,
                time_taken=time_taken,
                response=result.response
            )

        except Exception as e:
            # Handle failure
            instance.status = AgentStatus.FAILED
            instance.error = str(e)
            instance.completion_time = datetime.now()

            self._save_instance(instance)

            print(f"❌ Agent failed: {agent_id}")
            print(f"   Error: {e}")

            # Emit hook event
            await hooks.agent_failed(
                agent_id=agent_id,
                agent_name=instance.agent_name,
                task=task,
                workspace_path=config.get('workspace_path', ''),
                project=instance.project,
                error_message=str(e)
            )

        finally:
            # Process queue if any tasks waiting
            await self._process_queue()

    async def _process_queue(self):
        """Process queued tasks if concurrency allows."""
        while self.task_queue and len(self.active_agents) < self.max_concurrent:
            agent_class, task, project, config, worktree_path = self.task_queue.pop(0)
            await self.spawn_agent(agent_class, task, project, config, worktree_path)

    def get_agent_status(self, agent_id: str) -> Optional[AgentInstance]:
        """Get status of a specific agent."""
        return self.active_agents.get(agent_id)

    def list_active_agents(self) -> List[AgentInstance]:
        """List all active agents."""
        return list(self.active_agents.values())

    def list_agents_by_project(self, project: str) -> List[AgentInstance]:
        """List all agents working on a specific project."""
        return [
            agent for agent in self.active_agents.values()
            if agent.project == project
        ]

    def get_running_count(self) -> int:
        """Get count of currently running agents."""
        return len([
            agent for agent in self.active_agents.values()
            if agent.status == AgentStatus.RUNNING
        ])

    def get_queue_size(self) -> int:
        """Get number of queued tasks."""
        return len(self.task_queue)

    async def wait_for_agent(self, agent_id: str, timeout: Optional[float] = None) -> AgentResult:
        """
        Wait for an agent to complete.

        Args:
            agent_id: Agent to wait for
            timeout: Optional timeout in seconds

        Returns:
            AgentResult when agent completes
        """
        start_time = datetime.now()

        while True:
            instance = self.active_agents.get(agent_id)

            if not instance:
                raise ValueError(f"Agent {agent_id} not found")

            if instance.status in (AgentStatus.COMPLETED, AgentStatus.FAILED):
                if instance.status == AgentStatus.FAILED:
                    raise RuntimeError(f"Agent failed: {instance.error}")
                return instance.result

            # Check timeout
            if timeout:
                elapsed = (datetime.now() - start_time).total_seconds()
                if elapsed > timeout:
                    raise TimeoutError(f"Agent {agent_id} did not complete within {timeout}s")

            # Wait a bit before checking again
            await asyncio.sleep(0.5)

    async def wait_for_all(self, timeout: Optional[float] = None) -> Dict[str, AgentResult]:
        """
        Wait for all active agents to complete.

        Args:
            timeout: Optional timeout in seconds

        Returns:
            Dict mapping agent_id to AgentResult
        """
        results = {}

        for agent_id in list(self.active_agents.keys()):
            try:
                result = await self.wait_for_agent(agent_id, timeout=timeout)
                results[agent_id] = result
            except Exception as e:
                print(f"⚠️  Error waiting for {agent_id}: {e}")

        return results

    def cleanup_completed(self):
        """Remove completed/failed agents from active list."""
        to_remove = [
            agent_id
            for agent_id, instance in self.active_agents.items()
            if instance.status in (AgentStatus.COMPLETED, AgentStatus.FAILED, AgentStatus.SHUTDOWN)
        ]

        for agent_id in to_remove:
            del self.active_agents[agent_id]

        if to_remove:
            print(f"🧹 Cleaned up {len(to_remove)} completed agents")

    def shutdown_agent(self, agent_id: str):
        """Shutdown a specific agent."""
        if agent_id in self.active_agents:
            self.active_agents[agent_id].status = AgentStatus.SHUTDOWN
            self._save_instance(self.active_agents[agent_id])
            print(f"🛑 Shutdown agent: {agent_id}")

    def shutdown_all(self):
        """Shutdown all agents."""
        for agent_id in list(self.active_agents.keys()):
            self.shutdown_agent(agent_id)

    def _save_instance(self, instance: AgentInstance):
        """Save agent instance to database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Extract result data if available
        tokens_used = instance.result.tokens_used if instance.result else None
        cost_usd = instance.result.cost if instance.result else None
        time_taken_seconds = instance.result.time_taken if instance.result else None

        cursor.execute('''
            INSERT OR REPLACE INTO agents
            (agent_id, agent_name, project, task, status, worktree_path,
             spawn_time, completion_time, error, tokens_used, cost_usd, time_taken_seconds)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            instance.agent_id,
            instance.agent_name,
            instance.project,
            instance.task,
            instance.status.value,
            instance.worktree_path,
            instance.spawn_time.isoformat(),
            instance.completion_time.isoformat() if instance.completion_time else None,
            instance.error,
            tokens_used,
            cost_usd,
            time_taken_seconds
        ))

        conn.commit()
        conn.close()

    def get_project_stats(self, project: str) -> dict:
        """Get aggregate stats for a project."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT
                COUNT(*) as total_agents,
                SUM(tokens_used) as total_tokens,
                SUM(cost_usd) as total_cost,
                AVG(time_taken_seconds) as avg_time,
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
                COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed
            FROM agents
            WHERE project = ?
        ''', (project,))

        row = cursor.fetchone()
        conn.close()

        return {
            'total_agents': row[0] or 0,
            'total_tokens': row[1] or 0,
            'total_cost': row[2] or 0.0,
            'avg_time': row[3] or 0.0,
            'completed': row[4] or 0,
            'failed': row[5] or 0
        }
