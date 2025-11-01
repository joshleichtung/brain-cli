"""Claude Code agent using the official Claude Agent SDK."""

import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, query
from claude_agent_sdk.types import (
    AssistantMessage,
    SystemMessage,
    ResultMessage,
    ToolUseBlock,
    TextBlock
)

from .base import BaseAgent, AgentResult, RoutingPlan, Context


@dataclass
class ToolUse:
    """Record of a tool being used by the agent."""
    name: str
    input: Dict[str, Any]
    output: Optional[str] = None


class ClaudeCodeAgent(BaseAgent):
    """
    Claude Code agent using the official Agent SDK.

    This agent has full Claude Code capabilities:
    - File operations (Read, Write, Edit, Glob, Grep)
    - Code execution (Bash)
    - MCP server integration
    - Tool use orchestration
    - Context management
    """

    def __init__(self, config: dict):
        """
        Initialize Claude Code agent.

        Args:
            config: Configuration dict with:
                - name: Agent name
                - model: Claude model (default: claude-sonnet-4-5-20250929)
                - workspace_path: Working directory path
                - system_prompt: Optional system prompt
                - permission_mode: 'default', 'acceptEdits', or 'bypassPermissions'
                - cost_per_1k_tokens: Cost in USD per 1K tokens
                - mcp_servers: Optional dict of MCP server configs
        """
        super().__init__(config)

        self.model = config.get('model', 'claude-sonnet-4-5-20250929')
        self.workspace_path = config.get('workspace_path', os.getcwd())
        self.system_prompt = config.get('system_prompt')
        self.permission_mode = config.get('permission_mode', 'acceptEdits')
        self.cost_per_1k_tokens = config.get('cost_per_1k_tokens', 0.003)
        self.mcp_servers = config.get('mcp_servers', {})

        # Build Claude Agent SDK options
        self.options = ClaudeAgentOptions(
            system_prompt=self.system_prompt,
            permission_mode=self.permission_mode,
            cwd=self.workspace_path,
            mcp_servers=self.mcp_servers
        )

    async def execute(self, task: str, context: dict) -> AgentResult:
        """
        Execute a task using Claude Code.

        Args:
            task: Task description from user
            context: Context dict with conversation history

        Returns:
            AgentResult with response, tool usage, costs, etc.
        """
        start_time = datetime.now()

        full_response = []
        tool_uses: List[ToolUse] = []
        session_id = None
        total_cost = 0.0
        tokens_used = 0
        metadata = {}

        try:
            # Use query() for simple one-shot interaction
            # For interactive multi-turn, we'd use ClaudeSDKClient context manager
            async for message in query(prompt=task, options=self.options):
                msg_type = type(message).__name__

                if msg_type == 'SystemMessage':
                    # Extract session info
                    session_id = message.data.get('session_id')
                    metadata['session_id'] = session_id
                    metadata['tools'] = message.data.get('tools', [])
                    metadata['model'] = message.data.get('model')

                elif msg_type == 'AssistantMessage':
                    # Extract text and tool usage from content blocks
                    for content in message.content:
                        if isinstance(content, TextBlock):
                            full_response.append(content.text)
                        elif isinstance(content, ToolUseBlock):
                            tool_uses.append(ToolUse(
                                name=content.name,
                                input=content.input,
                                output=None  # Output comes in separate message
                            ))

                elif msg_type == 'ResultMessage':
                    # Extract final stats
                    total_cost = message.total_cost_usd
                    usage = message.usage
                    tokens_used = usage['input_tokens'] + usage['output_tokens']

                    metadata.update({
                        'duration_ms': message.duration_ms,
                        'duration_api_ms': message.duration_api_ms,
                        'num_turns': message.num_turns,
                        'usage': usage,
                        'is_error': message.is_error
                    })

            time_taken = (datetime.now() - start_time).total_seconds()

            return AgentResult(
                agent_name=self.name,
                task=task,
                response=''.join(full_response),
                time_taken=time_taken,
                tokens_used=tokens_used,
                cost=total_cost,
                quality_score=None,
                metadata={
                    **metadata,
                    'tool_uses': [
                        {'name': t.name, 'input': t.input}
                        for t in tool_uses
                    ],
                    'num_tools_used': len(tool_uses)
                }
            )

        except Exception as e:
            time_taken = (datetime.now() - start_time).total_seconds()

            return AgentResult(
                agent_name=self.name,
                task=task,
                response=f"Error executing task: {str(e)}",
                time_taken=time_taken,
                tokens_used=0,
                cost=0.0,
                quality_score=None,
                metadata={
                    'error': str(e),
                    'error_type': type(e).__name__
                }
            )

    async def create_routing_plan(self, task: str, available_agents: dict,
                                 context: dict) -> RoutingPlan:
        """
        Use Claude Code to analyze task and create routing plan.

        Since this agent has full tool use capabilities, it can analyze
        the task and recommend which agents should work on it.
        """
        prompt = f"""Analyze this task and determine the best agent(s) to handle it.

Task: {task}

Available agents: {', '.join(available_agents.keys())}

Analyze:
1. What type of task is this? (code, research, analysis, creative, etc.)
2. How complex is it? (0-1 scale)
3. Does it require multiple agents working together?
4. Which agents are best suited?
5. Should agents work in parallel or sequence?

Respond in JSON format:
{{
  "intent": "code|research|analysis|creative|other",
  "complexity": 0.0-1.0,
  "requires_multiple": true/false,
  "recommended_agents": ["agent1", "agent2"],
  "parallel_execution": true/false,
  "estimated_tokens": 1000,
  "reasoning": "brief explanation"
}}
"""

        # Use Claude Code to analyze
        result = await self.execute(prompt, context)

        # Parse JSON response
        import json
        import re

        # Try to extract JSON from response (may be in markdown code block)
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', result.response, re.DOTALL)
        if json_match:
            plan_data = json.loads(json_match.group(1))
        else:
            # Try parsing entire response as JSON
            try:
                plan_data = json.loads(result.response)
            except json.JSONDecodeError:
                # Fallback to simple plan
                plan_data = {
                    'intent': 'general',
                    'complexity': 0.5,
                    'requires_multiple': False,
                    'recommended_agents': [self.name],
                    'parallel_execution': False,
                    'estimated_tokens': 1000,
                    'reasoning': 'Using default routing due to parse error'
                }

        return RoutingPlan(
            task=task,
            intent=plan_data['intent'],
            complexity=plan_data['complexity'],
            requires_multiple=plan_data['requires_multiple'],
            recommended_agents=plan_data['recommended_agents'],
            parallel_execution=plan_data['parallel_execution'],
            context=context,
            estimated_tokens=plan_data['estimated_tokens']
        )

    async def synthesize(self, results: List[AgentResult],
                        original_task: str) -> str:
        """
        Synthesize multiple agent results into unified response.

        This is useful when multiple agents worked on the same task
        and we need to combine their outputs.
        """
        if len(results) == 1:
            return results[0].response

        # Build synthesis prompt
        results_text = []
        for i, result in enumerate(results, 1):
            results_text.append(f"""
Agent {i}: {result.agent_name}
Time: {result.time_taken:.2f}s | Tokens: {result.tokens_used} | Cost: ${result.cost:.4f}
Tools used: {result.metadata.get('num_tools_used', 0)}
Response:
{result.response}
""")

        prompt = f"""Original task: {original_task}

Multiple agents provided responses. Synthesize the best final answer.

{chr(10).join(results_text)}

Provide a single, comprehensive response that:
1. Combines the best insights from all agents
2. Resolves any contradictions
3. Provides clear, actionable information
4. Acknowledges different perspectives if relevant
"""

        synthesis_result = await self.execute(prompt, {})
        return synthesis_result.response

    def export_context(self) -> dict:
        """Export current context for agent switching."""
        return self.context.export()

    def import_context(self, data: dict):
        """Import context from another agent."""
        self.context.import_from(data)

    async def ping(self) -> bool:
        """Health check - verify Claude Code is responsive."""
        try:
            result = await self.execute("Respond with 'pong'", {})
            return 'pong' in result.response.lower()
        except Exception:
            return False
