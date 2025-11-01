# Implementation Examples

Quick reference code templates for common Brain CLI patterns.

## Project Structure Template

```
~/brain/
├── brain-cli/                  # Public tool repo
│   ├── README.md
│   ├── setup.py
│   ├── requirements.txt
│   ├── .gitignore
│   ├── src/brain/
│   │   ├── __init__.py
│   │   ├── cli.py             # REPL entry point
│   │   ├── orchestrator.py    # Agent coordination
│   │   ├── router.py          # Task routing
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── claude.py
│   │   │   ├── gemini.py
│   │   │   └── codex.py
│   │   ├── session.py         # Session management
│   │   ├── hooks.py           # Hook system
│   │   ├── memory.py          # ChromaDB integration
│   │   ├── knowledge_graph.py # Neo4j integration
│   │   ├── obsidian.py        # Obsidian MCP
│   │   ├── fabric.py          # Fabric patterns
│   │   ├── tts.py             # Voice output
│   │   ├── analytics.py       # Performance tracking
│   │   └── utils.py
│   └── tests/
│
└── workspace/                  # Private content repo
    ├── .brain-config.yaml
    ├── workspaces/
    ├── global_memory/
    ├── obsidian_vault/
    ├── scripts/
    └── .sessions/
```

## Agent Wrapper Template

```python
# src/brain/agents/example.py
from .base import BaseAgent, AgentResult
from datetime import datetime

class ExampleAgent(BaseAgent):
    def __init__(self, config: dict):
        super().__init__(config)
        # Initialize API client
        self.client = initialize_client(config)

    def execute(self, task: str, context: dict) -> AgentResult:
        """Execute task with context"""
        start_time = datetime.now()

        # Build prompt with context
        messages = self._build_messages(task, context)

        # Call API
        response = self.client.generate(messages)

        time_taken = (datetime.now() - start_time).total_seconds()

        return AgentResult(
            agent_name=self.name,
            task=task,
            response=response.text,
            time_taken=time_taken,
            tokens_used=response.tokens,
            cost=self.estimate_cost(response.tokens),
            quality_score=None,
            metadata={}
        )

    def _build_messages(self, task: str, context: dict) -> list:
        """Build messages with context"""
        messages = []

        # Add global context
        if context.get('global_context'):
            messages.append({
                'role': 'system',
                'content': context['global_context']
            })

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
        """Analyze task and create routing plan"""
        # Use agent to analyze
        analysis = self.execute(
            f"Analyze this task for routing: {task}",
            context
        )

        return RoutingPlan(
            task=task,
            intent='general',
            complexity=0.5,
            requires_multiple=False,
            recommended_agents=[self.name],
            parallel_execution=False,
            context=context,
            estimated_tokens=1000
        )

    def synthesize(self, results: List[AgentResult],
                   original_task: str) -> str:
        """Synthesize multiple results"""
        if len(results) == 1:
            return results[0].response

        # Combine results
        combined = "\n\n".join([r.response for r in results])
        return self.execute(
            f"Synthesize these responses to: {original_task}\n\n{combined}",
            {}
        ).response

    def export_context(self) -> dict:
        return self.context.export()

    def import_context(self, data: dict):
        self.context.import_from(data)

    def ping(self) -> bool:
        """Health check"""
        try:
            self.client.ping()
            return True
        except:
            return False
```

## Hook Template

```python
# Custom hook example
from brain.hooks import HookType, HookContext

def custom_logging_hook(context: HookContext):
    """Log specific events to custom location"""
    if context.hook_type == HookType.POST_EXECUTE:
        log_file = f"~/brain/workspace/.logs/{context.session.workspace}.log"

        with open(os.path.expanduser(log_file), 'a') as f:
            f.write(f"[{context.timestamp}] {context.agent_name}: {context.task}\n")
            f.write(f"  Result: {context.result.response[:100]}...\n")
            f.write(f"  Tokens: {context.result.tokens_used}, Cost: ${context.result.cost:.4f}\n\n")

# Register
hook_manager.register(HookType.POST_EXECUTE, custom_logging_hook)
```

## Automation Script Template

```bash
#!/bin/bash
# Template for automation workflows

WORKSPACE="your-workspace"
LOG_FILE="$HOME/brain/workspace/.logs/workflow-$(date +%Y%m%d).log"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Main workflow
main() {
    log "Starting workflow: $(basename $0)"

    # Use Brain CLI for task
    brain --workspace "$WORKSPACE" --prompt "Your task here" | tee -a "$LOG_FILE"

    if [ $? -eq 0 ]; then
        log "✅ Workflow completed successfully"
    else
        log "❌ Workflow failed"
        # Send notification
        osascript -e 'display notification "Workflow failed" with title "Brain CLI"'
    fi
}

# Run
main "$@"
```

## Obsidian Integration Template

```python
# Create and log to Obsidian
from brain.obsidian import ObsidianMCP

def log_research_finding(workspace: str, finding: dict):
    """Create research note in Obsidian"""
    obsidian = ObsidianMCP(vault_path='~/brain/workspace/obsidian_vault')

    note_content = f"""---
type: research
workspace: {workspace}
created: {datetime.now().isoformat()}
tags: {finding.get('tags', [])}
---

# {finding['title']}

## Summary
{finding['summary']}

## Key Points
{chr(10).join([f'- {point}' for point in finding['points']])}

## Sources
{chr(10).join([f'- [{s["title"]}]({s["url"]})' for s in finding['sources']])}

## Next Steps
{chr(10).join([f'- [ ] {step}' for step in finding.get('next_steps', [])])}
"""

    note_path = f"Research/{workspace}/{finding['title']}.md"
    obsidian.create_note(note_path, note_content, tags=finding.get('tags', []))

    return note_path
```

## Slash Command Template

```python
# Add custom slash command
def handle_custom_command(args: List[str], orchestrator, session, console):
    """Template for custom slash command"""

    if not args:
        console.print("[red]Usage: /custom <arg1> <arg2>[/red]")
        return

    arg1 = args[0]
    arg2 = args[1] if len(args) > 1 else None

    # Your command logic
    try:
        result = do_something(arg1, arg2)
        console.print(f"✅ {result}")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")

# Register in handle_slash_command()
elif command == 'custom':
    handle_custom_command(args, orchestrator, session, console)
```

## Test Template

```python
# tests/test_custom_feature.py
import pytest
from brain.agents import ClaudeAgent
from brain.orchestrator import AgnosticOrchestrator

def test_agent_initialization():
    """Test agent initializes correctly"""
    config = {
        'name': 'claude',
        'model': 'claude-sonnet-4-5-20250929',
        'cost_per_1k_tokens': 0.003
    }
    agent = ClaudeAgent(config)
    assert agent.name == 'claude'
    assert agent.ping()

def test_task_execution():
    """Test task execution"""
    config = {
        'name': 'claude',
        'model': 'claude-sonnet-4-5-20250929',
        'cost_per_1k_tokens': 0.003
    }
    agent = ClaudeAgent(config)

    result = agent.execute("What is 2+2?", {})

    assert result.response
    assert "4" in result.response
    assert result.tokens_used > 0
    assert result.cost > 0

def test_orchestrator_routing():
    """Test orchestrator routes correctly"""
    agents = {
        'claude': ClaudeAgent({'name': 'claude'}),
        'gemini': GeminiAgent({'name': 'gemini'})
    }

    orchestrator = AgnosticOrchestrator('claude', agents)

    # Test routing
    result = orchestrator.execute("Explain quantum computing")

    assert result
    assert len(result) > 0

if __name__ == '__main__':
    pytest.main([__file__])
```

## Configuration Template

```yaml
# ~/.brain-config.yaml
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

default_orchestrator: claude

routing:
  strategy: llm  # 'rule', 'llm', or 'hybrid'
  use_performance_history: true
  confidence_threshold: 0.7

memory:
  semantic_search: true
  knowledge_graph: true
  context_max_tokens: 3000

obsidian:
  vault_path: ~/brain/workspace/obsidian_vault
  auto_log_sessions: true
  note_templates: ~/brain/workspace/obsidian_vault/Templates

automation:
  workflows_dir: ~/brain/workspace/scripts
  cron_enabled: true

tts:
  enabled: false
  provider: pyttsx3  # 'pyttsx3', 'elevenlabs', 'google', 'openai'
  rate: 150
  volume: 0.9
```

## Workspace Configuration Template

```yaml
# ~/brain/workspace/workspaces/example/.workspace.yaml
name: example
description: Example workspace configuration
primary_agent: claude
preferred_agents:
  research: claude
  code: codex
  creative: gemini

context_files:
  - context/domain_knowledge.md
  - context/project_goals.md
  - context/technical_stack.md

automations:
  - daily_update
  - weekly_review

tags:
  - research
  - project

created: 2025-11-01
last_active: 2025-11-01

settings:
  auto_load_context: true
  log_to_obsidian: true
  semantic_memory: true
```

## CLI Usage Examples

```bash
# Interactive mode
brain --workspace coding-projects

# Headless mode
brain --prompt "Analyze this code: $(cat file.py)"

# Specific agent
brain --agent codex --prompt "Refactor this function"

# Multi-agent comparison
brain --workspace research
> /compare Explain quantum entanglement

# Agent switching
brain
> Working on research...
> /switch gemini
> Continue with creative brainstorming...

# Fabric patterns
brain
> /fabric extract_wisdom < article.md
> /fabric research_synthesis < multiple_sources.txt

# Analytics
brain
> /stats claude
> /report
> /dashboard 30

# TTS control
brain
> /tts on
> Explain this concept (will speak response)
> /tts off
```

## Git Hook Template

```bash
#!/bin/bash
# .git/hooks/post-commit
# Auto-create project notes on commit

PROJECT_DIR=$(pwd)
PROJECT_NAME=$(basename "$PROJECT_DIR")
COMMIT_MSG=$(git log -1 --pretty=%B)

# Log to Brain CLI
brain --workspace coding-projects --prompt \
  "New commit in $PROJECT_NAME: $COMMIT_MSG. Update project note if significant."
```

## Crontab Template

```bash
# Edit with: crontab -e

# Brain CLI Automation Workflows

# Hourly: Watch monitor
0 * * * * bash ~/brain/workspace/scripts/watch_monitor.sh

# Daily 9 AM: Research updates
0 9 * * * bash ~/brain/workspace/scripts/research_update.sh watches
0 9 * * * bash ~/brain/workspace/scripts/research_update.sh guitars

# Daily 10 AM: Paper pipeline
0 10 * * * bash ~/brain/workspace/scripts/paper_pipeline.sh

# Twice weekly: AI tool discovery
0 11 * * 1,4 bash ~/brain/workspace/scripts/ai_tool_discovery.sh

# Daily 5 PM: Project check
0 17 * * * bash ~/brain/workspace/scripts/project_check.sh

# Friday 5 PM: Weekly review
0 17 * * 5 bash ~/brain/workspace/scripts/weekly_review.sh

# Every 2 hours: Obsidian sync
0 */2 * * * bash ~/brain/workspace/scripts/obsidian_sync.sh
```

## Environment Variables Template

```bash
# ~/.bashrc or ~/.zshrc

# Brain CLI
export BRAIN_HOME="$HOME/brain"
export BRAIN_WORKSPACE_DEFAULT="default"

# API Keys
export ANTHROPIC_API_KEY="your-claude-key"
export GOOGLE_API_KEY="your-gemini-key"
export OPENAI_API_KEY="your-openai-key"

# Aliases
alias b='brain'
alias bw='brain --workspace'
alias bp='brain --prompt'

# Quick workspace access
alias b-code='brain --workspace coding-projects'
alias b-watches='brain --workspace watches'
alias b-guitars='brain --workspace guitars'
alias b-ai='brain --workspace ai-tooling'

# Obsidian integration
alias brain-note='cursor ~/brain/workspace/obsidian_vault'

# Automation
alias brain-setup='bash ~/brain/workspace/scripts/setup_cron.sh'
```

## Quick Start Script

```bash
#!/bin/bash
# setup_brain_cli.sh - Quick setup script

echo "🧠 Setting up Brain CLI..."

# Create directories
mkdir -p ~/brain/brain-cli
mkdir -p ~/brain/workspace/{workspaces,global_memory,obsidian_vault,scripts,.sessions}

# Clone or init repos
cd ~/brain/brain-cli
git init

# Install dependencies
python3 -m venv venv
source venv/bin/activate
pip install anthropic google-generativeai click rich pyyaml python-dotenv chromadb

# Install Obsidian MCP server
npm install -g @cyanheads/obsidian-mcp-server

# Install Fabric
pipx install fabric
fabric --setup

# Create config template
cat > ~/brain/workspace/.brain-config.yaml << 'EOF'
agents:
  claude:
    enabled: true
    api_key: ${ANTHROPIC_API_KEY}
    model: claude-sonnet-4-5-20250929
    cost_per_1k_tokens: 0.003

  gemini:
    enabled: true
    api_key: ${GOOGLE_API_KEY}
    model: gemini-1.5-pro
    cost_per_1k_tokens: 0.00125
EOF

echo "✅ Brain CLI setup complete!"
echo "Next steps:"
echo "1. Set API keys in environment variables"
echo "2. Run: cd ~/brain/brain-cli && pip install -e ."
echo "3. Run: brain --workspace default"
```

## Debug Template

```python
# Enable debug logging
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('~/brain/workspace/.logs/debug.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('brain')

# In code
logger.debug(f"Task: {task}")
logger.info(f"Routing to {agent_name}")
logger.warning(f"Low confidence: {confidence}")
logger.error(f"Agent failed: {error}")
```

These templates provide starting points for implementing Brain CLI features. Adapt as needed for your specific use case.
