# Agent Wrappers - Implementation Details

## Overview

Each AI agent requires a wrapper that implements the `BaseAgent` interface, translating between the orchestrator's common protocol and the agent's specific API or CLI.

**Supported Agents**:
1. Claude Code (Anthropic API)
2. Gemini CLI (Google GenerativeAI)
3. Codex (OpenAI API)
4. Aider (paul-gauthier/aider CLI)
5. OpenCode (OpenCode-ai/opencode Go binary)
6. Continue (continuedev/continue)
7. Open Interpreter (OpenInterpreter/open-interpreter)

## Base Agent Interface

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

@dataclass
class AgentResult:
    agent_name: str
    task: str
    response: str
    time_taken: float
    tokens_used: int
    cost: float
    quality_score: Optional[float]
    metadata: Dict[str, Any]

class BaseAgent(ABC):
    def __init__(self, config: dict):
        self.name = config['name']
        self.config = config
        self.context = Context()

    @abstractmethod
    def execute(self, task: str, context: dict) -> AgentResult:
        """Execute a task with context"""
        pass

    @abstractmethod
    def create_routing_plan(self, task: str, available_agents: dict,
                           context: dict) -> RoutingPlan:
        """Analyze task and create routing plan (for primary agent only)"""
        pass

    @abstractmethod
    def synthesize(self, results: List[AgentResult],
                   original_task: str) -> str:
        """Synthesize results into final response (for primary agent only)"""
        pass

    @abstractmethod
    def export_context(self) -> dict:
        """Export current context for switching"""
        pass

    @abstractmethod
    def import_context(self, data: dict):
        """Import context from another agent"""
        pass

    @abstractmethod
    def ping(self) -> bool:
        """Health check"""
        pass

    def estimate_cost(self, tokens: int) -> float:
        """Calculate cost based on token usage"""
        return tokens * self.config['cost_per_1k_tokens'] / 1000
```

## 1. Claude Wrapper

**Type**: API-based
**SDK**: Anthropic Python SDK
**Best For**: Analysis, research, complex reasoning, conversation

```python
import anthropic
from datetime import datetime

class ClaudeAgent(BaseAgent):
    def __init__(self, config: dict):
        super().__init__(config)
        self.client = anthropic.Anthropic(
            api_key=config.get('api_key') or os.getenv('ANTHROPIC_API_KEY')
        )
        self.model = config.get('model', 'claude-sonnet-4-5-20250929')
        self.max_tokens = config.get('max_tokens', 4096)

    def execute(self, task: str, context: dict) -> AgentResult:
        start_time = datetime.now()

        # Build messages with context
        messages = self._build_messages(task, context)

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
            quality_score=None,  # Set by user or evaluation
            metadata={
                'model': self.model,
                'input_tokens': response.usage.input_tokens,
                'output_tokens': response.usage.output_tokens,
                'stop_reason': response.stop_reason
            }
        )

    def _build_messages(self, task: str, context: dict) -> list:
        messages = []

        # Add conversation history
        for turn in context.get('conversation', []):
            messages.append({
                'role': turn['role'],
                'content': turn['content']
            })

        # Add current task
        messages.append({
            'role': 'user',
            'content': task
        })

        return messages

    def create_routing_plan(self, task: str, available_agents: dict,
                           context: dict) -> RoutingPlan:
        """Use Claude to analyze task and create routing plan"""
        prompt = f"""
Analyze this task and determine the best agent(s) to handle it.

Task: {task}

Available agents: {self._format_agents(available_agents)}

Return JSON:
{{
  "intent": "code|research|analysis|creative|refactor|terminal",
  "complexity": 0.0-1.0,
  "requires_multiple": true/false,
  "recommended_agents": ["agent1", "agent2"],
  "parallel_execution": true/false,
  "estimated_tokens": int,
  "reasoning": "why these agents"
}}
"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[{'role': 'user', 'content': prompt}]
        )

        plan_data = json.loads(response.content[0].text)

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

    def synthesize(self, results: List[AgentResult],
                   original_task: str) -> str:
        """Synthesize multiple agent results"""
        if len(results) == 1:
            return results[0].response

        prompt = f"""
Original task: {original_task}

Multiple agents provided responses. Synthesize the best final answer.

{self._format_results(results)}

Provide a single, comprehensive response that combines the best insights.
"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=[{'role': 'user', 'content': prompt}]
        )

        return response.content[0].text

    def export_context(self) -> dict:
        return self.context.export()

    def import_context(self, data: dict):
        self.context.import_from(data)

    def ping(self) -> bool:
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
        return "\n".join([
            f"- {name}: {agent.config['capabilities']}"
            for name, agent in agents.items()
        ])

    def _format_results(self, results: List[AgentResult]) -> str:
        formatted = []
        for r in results:
            formatted.append(f"""
Agent: {r.agent_name}
Time: {r.time_taken:.2f}s
Tokens: {r.tokens_used}
Response: {r.response}
""")
        return "\n---\n".join(formatted)
```

## 2. Gemini Wrapper

**Type**: API-based
**SDK**: google-generativeai
**Best For**: Research, creative tasks, multimodal

```python
import google.generativeai as genai

class GeminiAgent(BaseAgent):
    def __init__(self, config: dict):
        super().__init__(config)
        genai.configure(
            api_key=config.get('api_key') or os.getenv('GOOGLE_API_KEY')
        )
        self.model = genai.GenerativeModel(
            config.get('model', 'gemini-1.5-pro')
        )
        self.chat = None

    def execute(self, task: str, context: dict) -> AgentResult:
        start_time = datetime.now()

        # Initialize or continue chat
        if not self.chat:
            self.chat = self.model.start_chat(
                history=self._build_history(context)
            )

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
                'model': 'gemini-1.5-pro',
                'estimated_tokens': True
            }
        )

    def _build_history(self, context: dict) -> list:
        history = []
        for turn in context.get('conversation', []):
            history.append({
                'role': 'user' if turn['role'] == 'user' else 'model',
                'parts': [turn['content']]
            })
        return history

    def _estimate_tokens(self, input_text: str, output_text: str) -> int:
        # Rough estimate: 1 token ≈ 4 characters
        return (len(input_text) + len(output_text)) // 4

    def create_routing_plan(self, task: str, available_agents: dict,
                           context: dict) -> RoutingPlan:
        # Similar to Claude implementation
        # Use Gemini to analyze and create plan
        pass

    def synthesize(self, results: List[AgentResult],
                   original_task: str) -> str:
        # Similar to Claude implementation
        pass

    def export_context(self) -> dict:
        return self.context.export()

    def import_context(self, data: dict):
        self.context.import_from(data)
        self.chat = None  # Reset chat session

    def ping(self) -> bool:
        try:
            response = self.model.generate_content("ping")
            return True
        except Exception:
            return False
```

## 3. Codex Wrapper

**Type**: API-based
**SDK**: OpenAI Python SDK
**Best For**: Code generation, refactoring, debugging

```python
from openai import OpenAI

class CodexAgent(BaseAgent):
    def __init__(self, config: dict):
        super().__init__(config)
        self.client = OpenAI(
            api_key=config.get('api_key') or os.getenv('OPENAI_API_KEY')
        )
        self.model = config.get('model', 'gpt-4-turbo')

    def execute(self, task: str, context: dict) -> AgentResult:
        start_time = datetime.now()

        messages = self._build_messages(task, context)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages
        )

        time_taken = (datetime.now() - start_time).total_seconds()
        tokens_used = response.usage.total_tokens

        return AgentResult(
            agent_name=self.name,
            task=task,
            response=response.choices[0].message.content,
            time_taken=time_taken,
            tokens_used=tokens_used,
            cost=self.estimate_cost(tokens_used),
            quality_score=None,
            metadata={
                'model': self.model,
                'input_tokens': response.usage.prompt_tokens,
                'output_tokens': response.usage.completion_tokens,
                'finish_reason': response.choices[0].finish_reason
            }
        )

    def _build_messages(self, task: str, context: dict) -> list:
        messages = [
            {'role': 'system', 'content': 'You are an expert programmer.'}
        ]

        for turn in context.get('conversation', []):
            messages.append({
                'role': turn['role'],
                'content': turn['content']
            })

        messages.append({'role': 'user', 'content': task})

        return messages

    # create_routing_plan, synthesize similar to Claude
    # export_context, import_context, ping similar to Claude
```

## 4. Aider Wrapper

**Type**: CLI-based
**Tool**: paul-gauthier/aider
**Best For**: Code editing, refactoring, git integration

```python
import subprocess
import tempfile
import os

class AiderAgent(BaseAgent):
    def __init__(self, config: dict):
        super().__init__(config)
        self.aider_path = config.get('aider_path', 'aider')
        self.model = config.get('model', 'gpt-4-turbo')

    def execute(self, task: str, context: dict) -> AgentResult:
        start_time = datetime.now()

        # Write task to temp file
        with tempfile.NamedTemporaryFile(mode='w', delete=False,
                                        suffix='.txt') as f:
            f.write(task)
            task_file = f.name

        # Get files to edit from context
        files = context.get('files', [])

        # Run aider
        cmd = [
            self.aider_path,
            '--model', self.model,
            '--message-file', task_file,
            '--yes',  # Auto-confirm
            '--no-auto-commits',  # Don't auto-commit
        ] + files

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )

        os.unlink(task_file)

        time_taken = (datetime.now() - start_time).total_seconds()

        # Parse output for token usage (aider shows this)
        tokens_used = self._parse_tokens(result.stdout)

        return AgentResult(
            agent_name=self.name,
            task=task,
            response=result.stdout,
            time_taken=time_taken,
            tokens_used=tokens_used,
            cost=self.estimate_cost(tokens_used),
            quality_score=None,
            metadata={
                'model': self.model,
                'files_modified': files,
                'stderr': result.stderr
            }
        )

    def _parse_tokens(self, output: str) -> int:
        # Aider shows token usage in output
        # Example: "Tokens: 1,234 sent, 567 received"
        import re
        match = re.search(r'Tokens: ([\d,]+) sent, ([\d,]+) received', output)
        if match:
            sent = int(match.group(1).replace(',', ''))
            received = int(match.group(2).replace(',', ''))
            return sent + received
        return 0

    def create_routing_plan(self, task: str, available_agents: dict,
                           context: dict) -> RoutingPlan:
        # Aider typically isn't primary orchestrator
        # Simple rule-based plan
        return RoutingPlan(
            task=task,
            intent='code',
            complexity=0.5,
            requires_multiple=False,
            recommended_agents=[self.name],
            parallel_execution=False,
            context=context,
            estimated_tokens=2000
        )

    def synthesize(self, results: List[AgentResult],
                   original_task: str) -> str:
        # Aider typically isn't synthesizer
        return results[0].response if results else ""

    def export_context(self) -> dict:
        return self.context.export()

    def import_context(self, data: dict):
        self.context.import_from(data)

    def ping(self) -> bool:
        try:
            result = subprocess.run(
                [self.aider_path, '--version'],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False
```

## 5. OpenCode Wrapper

**Type**: CLI-based
**Tool**: OpenCode-ai/opencode Go binary
**Best For**: Terminal operations, system tasks

```python
class OpenCodeAgent(BaseAgent):
    def __init__(self, config: dict):
        super().__init__(config)
        self.opencode_path = config.get('opencode_path', 'opencode')

    def execute(self, task: str, context: dict) -> AgentResult:
        start_time = datetime.now()

        # OpenCode uses stdin for prompts
        result = subprocess.run(
            [self.opencode_path],
            input=task,
            capture_output=True,
            text=True,
            timeout=180
        )

        time_taken = (datetime.now() - start_time).total_seconds()

        # OpenCode doesn't expose token usage
        tokens_used = self._estimate_tokens(task, result.stdout)

        return AgentResult(
            agent_name=self.name,
            task=task,
            response=result.stdout,
            time_taken=time_taken,
            tokens_used=tokens_used,
            cost=0.0,  # Free/local
            quality_score=None,
            metadata={
                'stderr': result.stderr,
                'return_code': result.returncode
            }
        )

    def _estimate_tokens(self, input_text: str, output_text: str) -> int:
        return (len(input_text) + len(output_text)) // 4

    def ping(self) -> bool:
        try:
            result = subprocess.run(
                [self.opencode_path, '--version'],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False

    # Simple implementations for create_routing_plan, synthesize
    # export_context, import_context
```

## 6. Continue Wrapper

**Type**: CLI/API hybrid
**Tool**: continuedev/continue
**Best For**: IDE-integrated tasks, context-aware coding

```python
class ContinueAgent(BaseAgent):
    def __init__(self, config: dict):
        super().__init__(config)
        # Continue can be accessed via its Python API
        # or by invoking VS Code extension programmatically
        self.config_path = config.get('config_path',
                                     '~/.continue/config.json')

    def execute(self, task: str, context: dict) -> AgentResult:
        # Implementation depends on Continue's programmatic access
        # May require VS Code extension bridge or API server
        pass

    # Similar structure to other agents
```

## 7. Open Interpreter Wrapper

**Type**: Python library
**Tool**: OpenInterpreter/open-interpreter
**Best For**: Code execution, system operations, data analysis

```python
from interpreter import interpreter

class OpenInterpreterAgent(BaseAgent):
    def __init__(self, config: dict):
        super().__init__(config)
        interpreter.auto_run = True
        interpreter.model = config.get('model', 'gpt-4-turbo')

    def execute(self, task: str, context: dict) -> AgentResult:
        start_time = datetime.now()

        # Open Interpreter returns a generator
        output_chunks = []
        for chunk in interpreter.chat(task, stream=True):
            if 'content' in chunk:
                output_chunks.append(chunk['content'])

        response = ''.join(output_chunks)
        time_taken = (datetime.now() - start_time).total_seconds()

        # Estimate tokens
        tokens_used = self._estimate_tokens(task, response)

        return AgentResult(
            agent_name=self.name,
            task=task,
            response=response,
            time_taken=time_taken,
            tokens_used=tokens_used,
            cost=self.estimate_cost(tokens_used),
            quality_score=None,
            metadata={
                'model': interpreter.model,
                'executed_code': True
            }
        )

    def _estimate_tokens(self, input_text: str, output_text: str) -> int:
        return (len(input_text) + len(output_text)) // 4

    def ping(self) -> bool:
        try:
            # Test with simple command
            list(interpreter.chat("print('ping')", stream=True))
            return True
        except Exception:
            return False

    # Implementations for other methods
```

## Agent Configuration

**Config File**: `~/brain/workspace/.brain-config.yaml`

```yaml
agents:
  claude:
    enabled: true
    api_key: ${ANTHROPIC_API_KEY}
    model: claude-sonnet-4-5-20250929
    max_tokens: 4096
    cost_per_1k_tokens: 0.003
    capabilities:
      - analysis
      - research
      - conversation
      - reasoning

  gemini:
    enabled: true
    api_key: ${GOOGLE_API_KEY}
    model: gemini-1.5-pro
    cost_per_1k_tokens: 0.00125
    capabilities:
      - research
      - creative
      - multimodal

  codex:
    enabled: true
    api_key: ${OPENAI_API_KEY}
    model: gpt-4-turbo
    cost_per_1k_tokens: 0.01
    capabilities:
      - code
      - refactor
      - debugging

  aider:
    enabled: true
    aider_path: /usr/local/bin/aider
    model: gpt-4-turbo
    cost_per_1k_tokens: 0.01
    capabilities:
      - code
      - refactor
      - git

  opencode:
    enabled: true
    opencode_path: /usr/local/bin/opencode
    cost_per_1k_tokens: 0.0
    capabilities:
      - terminal
      - system

  continue:
    enabled: false  # Phase 2
    config_path: ~/.continue/config.json

  open_interpreter:
    enabled: false  # Phase 2
    model: gpt-4-turbo

default_orchestrator: claude
```

## Agent Factory

```python
class AgentFactory:
    AGENT_CLASSES = {
        'claude': ClaudeAgent,
        'gemini': GeminiAgent,
        'codex': CodexAgent,
        'aider': AiderAgent,
        'opencode': OpenCodeAgent,
        'continue': ContinueAgent,
        'open_interpreter': OpenInterpreterAgent
    }

    @classmethod
    def create_agent(cls, name: str, config: dict) -> BaseAgent:
        agent_class = cls.AGENT_CLASSES.get(name)
        if not agent_class:
            raise ValueError(f"Unknown agent: {name}")

        return agent_class(config)

    @classmethod
    def create_all_agents(cls, config_file: str) -> dict:
        with open(config_file) as f:
            config = yaml.safe_load(f)

        agents = {}
        for name, agent_config in config['agents'].items():
            if agent_config.get('enabled', True):
                agent_config['name'] = name
                agents[name] = cls.create_agent(name, agent_config)

        return agents
```

## Testing Agent Wrappers

```python
# test_agents.py
def test_agent(agent: BaseAgent):
    print(f"\nTesting {agent.name}...")

    # Ping test
    if not agent.ping():
        print(f"❌ {agent.name} not responding")
        return

    print(f"✅ {agent.name} health check passed")

    # Simple execution test
    result = agent.execute(
        "What is 2+2?",
        context={'conversation': []}
    )

    print(f"Response: {result.response[:100]}...")
    print(f"Time: {result.time_taken:.2f}s")
    print(f"Tokens: {result.tokens_used}")
    print(f"Cost: ${result.cost:.4f}")

if __name__ == '__main__':
    config_file = '~/brain/workspace/.brain-config.yaml'
    agents = AgentFactory.create_all_agents(config_file)

    for agent in agents.values():
        test_agent(agent)
```

## Error Handling

All wrappers should handle common errors:

```python
class AgentError(Exception):
    pass

class TokenLimitError(AgentError):
    pass

class APIError(AgentError):
    pass

class TimeoutError(AgentError):
    pass

# In agent execute methods:
def execute(self, task: str, context: dict) -> AgentResult:
    try:
        # ... execution logic
    except anthropic.RateLimitError:
        raise TokenLimitError(f"{self.name} rate limit exceeded")
    except anthropic.APIError as e:
        raise APIError(f"{self.name} API error: {e}")
    except subprocess.TimeoutExpired:
        raise TimeoutError(f"{self.name} execution timeout")
    except Exception as e:
        raise AgentError(f"{self.name} unexpected error: {e}")
```

## Next Document

See `03-BIG3-PATTERNS.md` for registry, hooks, and session management patterns.
