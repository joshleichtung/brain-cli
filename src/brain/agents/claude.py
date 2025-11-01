"""Claude agent wrapper for Brain CLI."""

import os
import json
from datetime import datetime
from typing import List
import anthropic

from .base import BaseAgent, AgentResult, RoutingPlan


class ClaudeAgent(BaseAgent):
    """Claude agent implementation using Anthropic API."""

    def __init__(self, config: dict):
        super().__init__(config)

        api_key = config.get('api_key') or os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("Claude API key not found. Set ANTHROPIC_API_KEY environment variable.")

        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = config.get('model', 'claude-sonnet-4-5-20250929')
        self.max_tokens = config.get('max_tokens', 4096)

    def execute(self, task: str, context: dict) -> AgentResult:
        """Execute task with Claude."""
        start_time = datetime.now()

        # Build messages with context
        messages = self._build_messages(task, context)

        try:
            # Call Claude API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=messages
            )

            time_taken = (datetime.now() - start_time).total_seconds()
            tokens_used = response.usage.input_tokens + response.usage.output_tokens

            return AgentResult(
                agent_name=self.name,
                task=task,
                response=response.content[0].text,
                time_taken=time_taken,
                tokens_used=tokens_used,
                cost=self.estimate_cost(tokens_used),
                quality_score=None,
                metadata={
                    'model': self.model,
                    'input_tokens': response.usage.input_tokens,
                    'output_tokens': response.usage.output_tokens,
                    'stop_reason': response.stop_reason
                }
            )

        except Exception as e:
            time_taken = (datetime.now() - start_time).total_seconds()
            raise Exception(f"Claude execution failed: {e}")

    def _build_messages(self, task: str, context: dict) -> list:
        """Build messages array with context."""
        messages = []

        # Add conversation history if available
        conversation = context.get('conversation', [])
        for turn in conversation[-10:]:  # Last 10 turns to manage token usage
            messages.append({
                'role': turn.get('role', 'user'),
                'content': turn.get('content', '')
            })

        # Add current task
        messages.append({
            'role': 'user',
            'content': task
        })

        return messages

    def create_routing_plan(self, task: str, available_agents: dict,
                           context: dict) -> RoutingPlan:
        """Use Claude to analyze task and create routing plan."""

        # Build prompt for routing analysis
        agents_info = self._format_agents(available_agents)

        routing_prompt = f"""Analyze this task and determine the best agent(s) to handle it.

Task: {task}

Available agents:
{agents_info}

Respond ONLY with valid JSON in this exact format:
{{
  "intent": "code|research|analysis|creative|refactor|terminal",
  "complexity": 0.0-1.0,
  "requires_multiple": true or false,
  "recommended_agents": ["agent1", "agent2"],
  "parallel_execution": true or false,
  "estimated_tokens": integer,
  "reasoning": "brief explanation"
}}"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[{'role': 'user', 'content': routing_prompt}]
            )

            # Parse JSON response
            response_text = response.content[0].text.strip()

            # Extract JSON from response (handles markdown code blocks)
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                response_text = response_text.split('```')[1].split('```')[0].strip()

            plan_data = json.loads(response_text)

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

        except Exception as e:
            # Fallback to simple routing if Claude analysis fails
            return RoutingPlan(
                task=task,
                intent='general',
                complexity=0.5,
                requires_multiple=False,
                recommended_agents=[self.name],
                parallel_execution=False,
                context=context,
                estimated_tokens=2000
            )

    def synthesize(self, results: List[AgentResult],
                   original_task: str) -> str:
        """Synthesize multiple agent results."""
        if len(results) == 1:
            return results[0].response

        # Build synthesis prompt
        results_text = self._format_results(results)

        synthesis_prompt = f"""You are synthesizing responses from multiple AI agents for this task:

Task: {original_task}

Agent Responses:
{results_text}

Provide a single, comprehensive response that combines the best insights from all agents. Be concise and clear."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[{'role': 'user', 'content': synthesis_prompt}]
            )

            return response.content[0].text

        except Exception as e:
            # Fallback: return all responses
            return f"Multiple agent responses:\n\n{results_text}"

    def export_context(self) -> dict:
        """Export context for agent switching."""
        return self.context.export()

    def import_context(self, data: dict):
        """Import context from another agent."""
        self.context.import_from(data)

    def ping(self) -> bool:
        """Verify Claude API is accessible."""
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=10,
                messages=[{'role': 'user', 'content': 'ping'}]
            )
            return True
        except Exception:
            return False

    def _format_agents(self, agents: dict) -> str:
        """Format available agents for prompt."""
        formatted = []
        for name, agent in agents.items():
            capabilities = agent.config.get('capabilities', [])
            formatted.append(f"- {name}: {', '.join(capabilities)}")
        return "\n".join(formatted)

    def _format_results(self, results: List[AgentResult]) -> str:
        """Format results for synthesis."""
        formatted = []
        for i, r in enumerate(results, 1):
            formatted.append(f"""
Agent: {r.agent_name}
Time: {r.time_taken:.2f}s | Tokens: {r.tokens_used} | Cost: ${r.cost:.4f}

Response:
{r.response}
""")
        return "\n---\n".join(formatted)
