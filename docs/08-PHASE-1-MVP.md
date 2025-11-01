# Phase 1: MVP (Weeks 1-2)

## Goal

Working Brain CLI that routes tasks between 2 agents (Claude + Gemini), with interactive REPL, session memory, Obsidian integration, and 3 automation workflows.

**Success Criteria**:
- ✅ Interactive REPL accepts natural language
- ✅ Routes tasks between Claude and Gemini
- ✅ Session memory persists across restarts
- ✅ Obsidian integration active (create/read notes)
- ✅ 3 automation workflows running
- ✅ Works from Cursor/Claude Code/standalone terminal

## Week 1: Core Infrastructure

### Day 1-2: Project Setup

**Tasks**:
1. Create `brain-cli/` repository structure
2. Setup Python environment and dependencies
3. Implement base agent interface
4. Create Claude and Gemini wrappers

**Deliverables**:

**Directory Structure**:
```
~/brain/brain-cli/
├── README.md
├── setup.py
├── requirements.txt
├── .gitignore
├── src/
│   └── brain/
│       ├── __init__.py
│       ├── cli.py
│       ├── orchestrator.py
│       ├── router.py
│       ├── agents/
│       │   ├── __init__.py
│       │   ├── base.py
│       │   ├── claude.py
│       │   └── gemini.py
│       ├── session.py
│       ├── hooks.py
│       └── utils.py
└── tests/
    ├── test_agents.py
    └── test_orchestrator.py
```

**`requirements.txt`**:
```
anthropic>=0.34.0
google-generativeai>=0.3.0
click>=8.1.0
rich>=13.0.0
pyyaml>=6.0
python-dotenv>=1.0.0
```

**`setup.py`**:
```python
from setuptools import setup, find_packages

setup(
    name='brain-cli',
    version='0.1.0',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=[
        'anthropic>=0.34.0',
        'google-generativeai>=0.3.0',
        'click>=8.1.0',
        'rich>=13.0.0',
        'pyyaml>=6.0',
        'python-dotenv>=1.0.0',
    ],
    entry_points={
        'console_scripts': [
            'brain=brain.cli:main',
        ],
    },
)
```

**Installation**:
```bash
cd ~/brain/brain-cli
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

### Day 3-4: Agent Wrappers

**Tasks**:
1. Implement `BaseAgent` interface
2. Create Claude wrapper (full implementation)
3. Create Gemini wrapper (full implementation)
4. Test both agents with simple prompts

**Implementation**: See `02-AGENT-WRAPPERS.md` for complete code.

**Test Script**:
```python
# tests/test_agents.py
from brain.agents import ClaudeAgent, GeminiAgent

def test_claude():
    config = {
        'name': 'claude',
        'model': 'claude-sonnet-4-5-20250929',
        'cost_per_1k_tokens': 0.003
    }
    agent = ClaudeAgent(config)

    assert agent.ping(), "Claude not responding"

    result = agent.execute("What is 2+2?", {})
    assert "4" in result.response
    print(f"✅ Claude test passed: {result.tokens_used} tokens, ${result.cost:.4f}")

def test_gemini():
    config = {
        'name': 'gemini',
        'model': 'gemini-1.5-pro',
        'cost_per_1k_tokens': 0.00125
    }
    agent = GeminiAgent(config)

    assert agent.ping(), "Gemini not responding"

    result = agent.execute("What is 2+2?", {})
    assert "4" in result.response
    print(f"✅ Gemini test passed: {result.tokens_used} tokens, ${result.cost:.4f}")

if __name__ == '__main__':
    test_claude()
    test_gemini()
```

### Day 5: Orchestrator Core

**Tasks**:
1. Implement `AgnosticOrchestrator`
2. Simple rule-based router
3. Basic agent switching
4. Test routing between Claude and Gemini

**Key Files**:
- `orchestrator.py`: Main coordination logic
- `router.py`: Rule-based routing

**Minimal Router** (Phase 1):
```python
# src/brain/router.py
class SimpleRouter:
    RULES = {
        'code': 'claude',
        'research': 'claude',
        'analysis': 'claude',
        'creative': 'gemini',
        'general': 'claude'
    }

    def select_agent(self, task: str, agents: dict) -> BaseAgent:
        # Simple keyword matching
        task_lower = task.lower()

        if any(kw in task_lower for kw in ['code', 'program', 'function']):
            return agents.get('claude')
        elif any(kw in task_lower for kw in ['creative', 'imagine', 'brainstorm']):
            return agents.get('gemini')
        else:
            return agents.get('claude')  # Default
```

### Day 6-7: Session Management & REPL

**Tasks**:
1. Implement session registry
2. Build interactive REPL
3. Add slash commands (/switch, /agents, /help)
4. Test full conversation flow

**Session Implementation**: See `03-BIG3-PATTERNS.md` for complete code.

**REPL** (`cli.py`):
```python
# src/brain/cli.py
import click
from rich.console import Console
from rich.markdown import Markdown
from .orchestrator import AgnosticOrchestrator
from .session import SessionRegistry
import os

@click.command()
@click.option('--workspace', default='default', help='Workspace to activate')
@click.option('--agent', default='claude', help='Primary agent')
@click.option('--prompt', default=None, help='Headless mode: single prompt')
def main(workspace: str, agent: str, prompt: str):
    """Brain CLI - Agent-agnostic research hub"""
    console = Console()

    # Load config
    config_file = os.path.expanduser('~/brain/workspace/.brain-config.yaml')
    with open(config_file) as f:
        config = yaml.safe_load(f)

    # Initialize orchestrator
    orchestrator = AgnosticOrchestrator(agent, config['agents'])

    if prompt:
        # Headless mode
        result = orchestrator.execute(prompt)
        console.print(Markdown(result))
        return

    # Interactive mode
    registry = SessionRegistry()
    session = registry.load_session(workspace) or \
              registry.create_session(workspace, agent)

    orchestrator.session = session

    console.print(f"\n🧠 Brain CLI v0.1.0 [{agent} orchestrating]")
    console.print(f"📁 Workspace: {workspace}\n")

    while True:
        try:
            user_input = console.input("[bold blue]>[/bold blue] ")

            if not user_input.strip():
                continue

            # Slash commands
            if user_input.startswith('/'):
                handle_slash_command(user_input, orchestrator, session,
                                   registry, console)
                continue

            # Execute task
            response = orchestrator.execute(user_input)
            console.print(Markdown(response))
            console.print()

        except KeyboardInterrupt:
            console.print("\n\n👋 Goodbye!")
            registry.save_session(session)
            break
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

def handle_slash_command(cmd: str, orchestrator, session, registry, console):
    parts = cmd[1:].split()
    command = parts[0].lower()
    args = parts[1:]

    if command == 'switch':
        if not args:
            console.print("[red]Usage: /switch <agent>[/red]")
            return
        orchestrator.switch_orchestrator(args[0])
        console.print(f"🔄 Switched to {args[0]}")

    elif command == 'agents':
        console.print("\n📋 Available agents:")
        for name, agent in orchestrator.agents.items():
            status = "✅" if agent.ping() else "❌"
            primary = "⭐" if name == orchestrator.primary_name else "  "
            console.print(f"{primary} {status} {name}")

    elif command == 'help':
        show_help(console)

    elif command == 'exit':
        raise KeyboardInterrupt

    else:
        console.print(f"[red]Unknown command: /{command}[/red]")
        console.print("Type /help for available commands")

def show_help(console):
    help_text = """
# Brain CLI Commands

**Agent Management**:
- `/switch <agent>` - Switch primary orchestrator
- `/agents` - List available agents

**Session**:
- `/help` - Show this help
- `/exit` or Ctrl+C - Exit

More commands coming in Phase 2!
"""
    console.print(Markdown(help_text))

if __name__ == '__main__':
    main()
```

## Week 2: Integration & Automation

### Day 8-9: Obsidian Integration

**Tasks**:
1. Install obsidian-mcp-server
2. Create Python wrapper for MCP tools
3. Implement session logging to Obsidian
4. Test note creation and reading

**Setup**:
```bash
# Install MCP server
npm install -g @cyanheads/obsidian-mcp-server

# Create vault
mkdir -p ~/brain/workspace/obsidian_vault
```

**Integration**: See `05-OBSIDIAN-INTEGRATION.md` for complete implementation.

**Test**:
```python
# Test Obsidian integration
from brain.obsidian import ObsidianLogger

vault_path = '~/brain/workspace/obsidian_vault'
logger = ObsidianLogger(vault_path)

# Log test session
logger.log_session(session)

# Create test note
logger.log_research_finding('test', {
    'title': 'Test Finding',
    'content': 'This is a test',
    'tags': ['test']
})
```

### Day 10-11: Automation Workflows

**Phase 1 Workflows** (3 core productivity workflows):
1. Coding project tracker
2. Todo integration
3. Weekly review automation

**Setup**:
```bash
mkdir -p ~/brain/workspace/scripts
mkdir -p ~/brain/workspace/.tracked_projects
```

**Workflow 1: Project Tracker**
```bash
# Create git hook template
cat > ~/brain/workspace/scripts/git-post-checkout.sh << 'EOF'
#!/bin/bash
# Place in .git/hooks/post-checkout for each tracked project

PROJECT_DIR=$(pwd)
PROJECT_NAME=$(basename "$PROJECT_DIR")

if [[ ! -f "$HOME/brain/workspace/.tracked_projects/$PROJECT_NAME" ]]; then
  echo "🧠 New project detected: $PROJECT_NAME"
  brain --workspace coding-projects --prompt \
    "Analyze project at $PROJECT_DIR and create Obsidian note"

  mkdir -p "$HOME/brain/workspace/.tracked_projects"
  echo "$PROJECT_DIR" > "$HOME/brain/workspace/.tracked_projects/$PROJECT_NAME"
fi
EOF

chmod +x ~/brain/workspace/scripts/git-post-checkout.sh
```

**Workflow 2: Todo Integration** - See `06-AUTOMATION-WORKFLOWS.md` for implementation.

**Workflow 3: Weekly Review**
```bash
# Weekly review script
cat > ~/brain/workspace/scripts/weekly_review.sh << 'EOF'
#!/bin/bash

WEEK_END=$(date '+%Y-%m-%d')

echo "📊 Generating weekly review: $WEEK_END"

brain --prompt "Generate weekly review and create Obsidian note: Weekly Reviews/$WEEK_END.md"
EOF

chmod +x ~/brain/workspace/scripts/weekly_review.sh

# Setup cron (Friday 5 PM)
(crontab -l 2>/dev/null; echo "0 17 * * 5 bash ~/brain/workspace/scripts/weekly_review.sh") | crontab -
```

### Day 12: Testing & Validation

**Test Checklist**:

1. **Agent Communication**:
   - [ ] Claude responds correctly
   - [ ] Gemini responds correctly
   - [ ] Agents handle errors gracefully
   - [ ] Token usage tracked accurately

2. **Orchestrator**:
   - [ ] Routes tasks appropriately
   - [ ] Switches agents mid-session
   - [ ] Context preserved after switch
   - [ ] Handles agent failures

3. **Session Management**:
   - [ ] Session saves to disk
   - [ ] Session loads on restart
   - [ ] Conversation history preserved
   - [ ] Token/cost tracking accurate

4. **REPL**:
   - [ ] Accepts natural language input
   - [ ] Slash commands work
   - [ ] Markdown rendering correct
   - [ ] Error messages clear

5. **Obsidian Integration**:
   - [ ] Notes created successfully
   - [ ] Session logs appear in daily notes
   - [ ] MCP server responsive

6. **Automation**:
   - [ ] Project tracker detects new repos
   - [ ] Todo extraction works
   - [ ] Weekly review generates correctly

**Test Script**:
```bash
# Full integration test
cd ~/brain/brain-cli

# Test 1: Basic agent test
brain --prompt "Test: What is 2+2?"

# Test 2: Agent switching
brain --workspace test << EOF
Hello
/switch gemini
What's your name?
/switch claude
/agents
/exit
EOF

# Test 3: Session persistence
brain --workspace test << EOF
Remember: my favorite color is blue
/exit
EOF

brain --workspace test << EOF
What's my favorite color?
/exit
EOF

# Test 4: Obsidian integration
brain --workspace test --prompt "Create an Obsidian note titled 'Test Note' with content 'Hello World'"

# Verify note created
ls ~/brain/workspace/obsidian_vault/Test\ Note.md

# Test 5: Automation workflow
bash ~/brain/workspace/scripts/weekly_review.sh
```

### Day 13-14: Documentation & Polish

**Tasks**:
1. Write README.md with setup instructions
2. Create user guide
3. Document slash commands
4. Add example workflows
5. Create demo video/GIF

**README.md**:
```markdown
# Brain CLI

Agent-agnostic research and automation hub for terminal-based workflows.

## Features

- 🤖 Multi-agent coordination (Claude, Gemini)
- 💬 Interactive REPL with natural language
- 🔄 Switch agents mid-session
- 💾 Session persistence
- 📝 Obsidian integration
- ⚙️ CLI-first automation

## Installation

```bash
cd ~/brain/brain-cli
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

## Configuration

Create `~brain/workspace/.brain-config.yaml`:

```yaml
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
```

Set environment variables:
```bash
export ANTHROPIC_API_KEY="your-key"
export GOOGLE_API_KEY="your-key"
```

## Usage

### Interactive Mode

```bash
brain --workspace coding-projects
```

### Headless Mode

```bash
brain --prompt "Analyze this project structure"
```

### Slash Commands

- `/switch <agent>` - Switch orchestrator
- `/agents` - List available agents
- `/help` - Show help
- `/exit` - Exit

## Next Steps

See `planning/09-PHASE-2-SCALE.md` for Phase 2 features.
```

## Phase 1 Completion Checklist

### Core Functionality
- [ ] Agent wrappers (Claude, Gemini) working
- [ ] Orchestrator routes between agents
- [ ] Agent switching preserves context
- [ ] Interactive REPL accepts natural language
- [ ] Slash commands functional

### Session Management
- [ ] Sessions persist to disk
- [ ] Sessions load on restart
- [ ] Conversation history preserved
- [ ] Token/cost tracking accurate

### Integration
- [ ] Obsidian MCP server installed
- [ ] Notes can be created/read
- [ ] Session logging to daily notes works

### Automation
- [ ] Project tracker script created
- [ ] Todo extraction hook implemented
- [ ] Weekly review script with cron job

### Testing
- [ ] All agent tests pass
- [ ] Integration tests pass
- [ ] Manual workflow tests successful
- [ ] Error handling verified

### Documentation
- [ ] README with setup instructions
- [ ] User guide complete
- [ ] Example workflows documented
- [ ] Code comments added

## Success Metrics

**Functionality**:
- ✅ Can complete 10 consecutive tasks without errors
- ✅ Agent switching works seamlessly
- ✅ Session resumes correctly after restart

**Performance**:
- ⚡ Response time < 10 seconds for simple tasks
- 💰 Cost tracking accurate to 4 decimal places
- 💾 Session size < 1MB for 100 turns

**Integration**:
- 📝 Obsidian notes created successfully
- ⚙️ All 3 automation workflows functional
- 🔄 Workflows run without manual intervention

## Deliverables

1. **Working CLI**: `brain` command available globally
2. **2 Agent Wrappers**: Claude and Gemini functional
3. **Interactive REPL**: Natural language + slash commands
4. **Session Persistence**: Context preserved across restarts
5. **Obsidian Integration**: Notes can be created/read
6. **3 Automation Workflows**: Project tracker, todo extraction, weekly review
7. **Documentation**: README, user guide, examples
8. **Tests**: Integration test suite passing

## Next Phase

See `09-PHASE-2-SCALE.md` for:
- All 7 agents integrated
- Multi-agent comparison mode
- TTS voice output
- All 11 automation workflows
- ChromaDB semantic memory
- Fabric pattern integration
