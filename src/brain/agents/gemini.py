"""Gemini agent wrapper for Brain CLI."""

import os
from datetime import datetime
from typing import List
import google.generativeai as genai

from .base import BaseAgent, AgentResult, RoutingPlan


class GeminiAgent(BaseAgent):
    """Gemini agent implementation using Google GenerativeAI API."""

    def __init__(self, config: dict):
        super().__init__(config)

        api_key = config.get('api_key') or os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError("Gemini API key not found. Set GOOGLE_API_KEY environment variable.")

        genai.configure(api_key=api_key)
        self.model_name = config.get('model', 'gemini-1.5-pro')
        self.model = genai.GenerativeModel(self.model_name)
        self.chat = None

    def execute(self, task: str, context: dict) -> AgentResult:
        """Execute task with Gemini."""
        start_time = datetime.now()

        try:
            # Initialize or continue chat
            if not self.chat:
                history = self._build_history(context)
                self.chat = self.model.start_chat(history=history)

            # Send message
            response = self.chat.send_message(task)

            time_taken = (datetime.now() - start_time).total_seconds()

            # Estimate tokens (Gemini doesn't expose usage directly)
            tokens_used = self._estimate_tokens(task, response.text)

            return AgentResult(
                agent_name=self.name,
                task=task,
                response=response.text,
                time_taken=time_taken,
                tokens_used=tokens_used,
                cost=self.estimate_cost(tokens_used),
                quality_score=None,
                metadata={
                    'model': self.model_name,
                    'estimated_tokens': True
                }
            )

        except Exception as e:
            time_taken = (datetime.now() - start_time).total_seconds()
            raise Exception(f"Gemini execution failed: {e}")

    def _build_history(self, context: dict) -> list:
        """Build chat history for Gemini."""
        history = []
        conversation = context.get('conversation', [])

        for turn in conversation[-10:]:  # Last 10 turns
            role = 'user' if turn.get('role') == 'user' else 'model'
            history.append({
                'role': role,
                'parts': [turn.get('content', '')]
            })

        return history

    def _estimate_tokens(self, input_text: str, output_text: str) -> int:
        """Rough estimate: 1 token ≈ 4 characters."""
        return (len(input_text) + len(output_text)) // 4

    def create_routing_plan(self, task: str, available_agents: dict,
                           context: dict) -> RoutingPlan:
        """Create routing plan (simple version for Gemini)."""
        # Gemini typically won't be primary orchestrator in Phase 1
        # but we need to implement the interface
        return RoutingPlan(
            task=task,
            intent=self._classify_intent(task),
            complexity=0.5,
            requires_multiple=False,
            recommended_agents=[self.name],
            parallel_execution=False,
            context=context,
            estimated_tokens=2000
        )

    def _classify_intent(self, task: str) -> str:
        """Simple intent classification."""
        task_lower = task.lower()

        if any(kw in task_lower for kw in ['code', 'program', 'function', 'debug']):
            return 'code'
        elif any(kw in task_lower for kw in ['research', 'find', 'search', 'learn']):
            return 'research'
        elif any(kw in task_lower for kw in ['analyze', 'explain', 'why', 'how']):
            return 'analysis'
        elif any(kw in task_lower for kw in ['create', 'imagine', 'brainstorm', 'design']):
            return 'creative'
        else:
            return 'general'

    def synthesize(self, results: List[AgentResult],
                   original_task: str) -> str:
        """Synthesize multiple results."""
        if len(results) == 1:
            return results[0].response

        # Simple synthesis: concatenate with headers
        synthesis = [f"Response from {r.agent_name}:\n{r.response}"
                    for r in results]
        return "\n\n---\n\n".join(synthesis)

    def export_context(self) -> dict:
        """Export context for agent switching."""
        return self.context.export()

    def import_context(self, data: dict):
        """Import context from another agent."""
        self.context.import_from(data)
        # Reset chat session when context changes
        self.chat = None

    def ping(self) -> bool:
        """Verify Gemini API is accessible."""
        try:
            response = self.model.generate_content("ping")
            return True
        except Exception:
            return False
