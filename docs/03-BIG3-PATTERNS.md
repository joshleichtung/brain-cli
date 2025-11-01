# Big-3-Super-Agent Patterns

## Overview

The [big-3-super-agent](https://github.com/coleam00/big-3-super-agent) project provides proven patterns for building sophisticated AI agent systems. We'll adapt these patterns for our agent-agnostic, multi-agent orchestrator.

**Key Patterns to Adopt**:
1. Registry-based session management
2. Hook system for lifecycle events
3. Workspace isolation per project
4. CLI modes (interactive vs headless)

**Adaptations**:
- Make agent-agnostic (not Claude-specific)
- Support multi-agent coordination
- Interactive REPL as primary mode

## 1. Registry-Based Session Management

### Concept

Sessions persist state across interactions, enabling context continuity and allowing resume after interruption.

### Big-3 Implementation

Big-3 uses a file-based registry:
```
~/.big3/sessions/
├── session_123.json
├── session_456.json
└── active_session
```

### Our Adaptation

**Directory Structure**:
```
~/brain/workspace/.sessions/
├── default/
│   ├── session.json
│   ├── context.json
│   └── history/
│       ├── 2025-11-01_10-30.json
│       └── 2025-11-01_14-15.json
├── watches-research/
│   ├── session.json
│   ├── context.json
│   └── history/
└── guitar-project/
    ├── session.json
    ├── context.json
    └── history/
```

### Session Schema

```python
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Dict, Optional
import json
import os

@dataclass
class Turn:
    role: str  # 'user' or 'assistant'
    content: str
    agent: str  # Which agent responded
    timestamp: datetime
    tokens: int
    cost: float

    def to_dict(self):
        return {
            'role': self.role,
            'content': self.content,
            'agent': self.agent,
            'timestamp': self.timestamp.isoformat(),
            'tokens': self.tokens,
            'cost': self.cost
        }

    @classmethod
    def from_dict(cls, data: dict):
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)

@dataclass
class Session:
    id: str
    workspace: str
    primary_agent: str
    created_at: datetime
    last_active: datetime
    conversation: List[Turn]
    context: Dict
    total_tokens: int
    total_cost: float

    def to_dict(self):
        return {
            'id': self.id,
            'workspace': self.workspace,
            'primary_agent': self.primary_agent,
            'created_at': self.created_at.isoformat(),
            'last_active': self.last_active.isoformat(),
            'conversation': [t.to_dict() for t in self.conversation],
            'context': self.context,
            'total_tokens': self.total_tokens,
            'total_cost': self.total_cost
        }

    @classmethod
    def from_dict(cls, data: dict):
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['last_active'] = datetime.fromisoformat(data['last_active'])
        data['conversation'] = [Turn.from_dict(t) for t in data['conversation']]
        return cls(**data)

class SessionRegistry:
    def __init__(self, base_dir: str = '~/brain/workspace/.sessions'):
        self.base_dir = os.path.expanduser(base_dir)
        os.makedirs(self.base_dir, exist_ok=True)

    def create_session(self, workspace: str, primary_agent: str) -> Session:
        """Create a new session"""
        session_id = f"{workspace}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        session_dir = os.path.join(self.base_dir, workspace)
        os.makedirs(session_dir, exist_ok=True)
        os.makedirs(os.path.join(session_dir, 'history'), exist_ok=True)

        session = Session(
            id=session_id,
            workspace=workspace,
            primary_agent=primary_agent,
            created_at=datetime.now(),
            last_active=datetime.now(),
            conversation=[],
            context={},
            total_tokens=0,
            total_cost=0.0
        )

        self.save_session(session)
        return session

    def save_session(self, session: Session):
        """Save session to disk"""
        session_dir = os.path.join(self.base_dir, session.workspace)
        session_file = os.path.join(session_dir, 'session.json')

        # Update last active
        session.last_active = datetime.now()

        # Save current state
        with open(session_file, 'w') as f:
            json.dump(session.to_dict(), f, indent=2)

        # Archive to history (for backup)
        history_file = os.path.join(
            session_dir,
            'history',
            f"{datetime.now().strftime('%Y-%m-%d_%H-%M')}.json"
        )
        with open(history_file, 'w') as f:
            json.dump(session.to_dict(), f, indent=2)

    def load_session(self, workspace: str) -> Optional[Session]:
        """Load existing session"""
        session_file = os.path.join(self.base_dir, workspace, 'session.json')

        if not os.path.exists(session_file):
            return None

        with open(session_file) as f:
            data = json.load(f)

        return Session.from_dict(data)

    def list_workspaces(self) -> List[str]:
        """List all available workspaces with sessions"""
        return [d for d in os.listdir(self.base_dir)
                if os.path.isdir(os.path.join(self.base_dir, d))]

    def add_turn(self, session: Session, turn: Turn):
        """Add a conversation turn"""
        session.conversation.append(turn)
        session.total_tokens += turn.tokens
        session.total_cost += turn.cost
        self.save_session(session)

    def switch_primary_agent(self, session: Session, new_agent: str):
        """Switch the primary orchestrator"""
        session.primary_agent = new_agent
        self.save_session(session)
```

### Usage

```python
# Start new session
registry = SessionRegistry()
session = registry.create_session('watches-research', 'claude')

# Add conversation
turn = Turn(
    role='user',
    content='Find Rolex Submariner under $10k',
    agent='claude',
    timestamp=datetime.now(),
    tokens=250,
    cost=0.00075
)
registry.add_turn(session, turn)

# Resume later
session = registry.load_session('watches-research')
print(f"Resuming with {len(session.conversation)} turns")
```

## 2. Hook System for Lifecycle Events

### Concept

Hooks allow custom code execution at key points in the agent lifecycle, enabling logging, validation, monitoring, and custom behaviors.

### Big-3 Hook Points

- `pre_tool_use`: Before agent uses a tool
- `post_tool_use`: After agent uses a tool
- `pre_response`: Before agent responds
- `post_response`: After agent responds

### Our Hook System

**Hook Types**:

```python
from enum import Enum
from typing import Callable, Any, Dict
import logging

class HookType(Enum):
    PRE_EXECUTE = 'pre_execute'
    POST_EXECUTE = 'post_execute'
    PRE_ROUTE = 'pre_route'
    POST_ROUTE = 'post_route'
    PRE_SYNTHESIZE = 'pre_synthesize'
    POST_SYNTHESIZE = 'post_synthesize'
    PRE_SWITCH = 'pre_switch'
    POST_SWITCH = 'post_switch'
    SESSION_START = 'session_start'
    SESSION_END = 'session_end'

@dataclass
class HookContext:
    hook_type: HookType
    agent_name: str
    task: Optional[str]
    result: Optional[Any]
    session: Session
    timestamp: datetime
    metadata: Dict[str, Any]

class HookManager:
    def __init__(self):
        self.hooks: Dict[HookType, List[Callable]] = {
            hook_type: [] for hook_type in HookType
        }
        self.logger = logging.getLogger('brain.hooks')

    def register(self, hook_type: HookType, func: Callable):
        """Register a hook function"""
        self.hooks[hook_type].append(func)
        self.logger.info(f"Registered hook: {func.__name__} for {hook_type.value}")

    def trigger(self, context: HookContext):
        """Trigger all hooks for a given type"""
        for hook_func in self.hooks[context.hook_type]:
            try:
                hook_func(context)
            except Exception as e:
                self.logger.error(f"Hook {hook_func.__name__} failed: {e}")
```

### Built-in Hooks

**Logging Hook**:
```python
def logging_hook(context: HookContext):
    """Log all agent actions"""
    log_file = f"~/brain/workspace/.logs/{context.session.workspace}.log"
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    with open(os.path.expanduser(log_file), 'a') as f:
        f.write(f"[{context.timestamp}] {context.hook_type.value} - "
                f"{context.agent_name}: {context.task}\n")

# Register
hook_manager.register(HookType.PRE_EXECUTE, logging_hook)
hook_manager.register(HookType.POST_EXECUTE, logging_hook)
```

**Performance Monitoring Hook**:
```python
def performance_hook(context: HookContext):
    """Track agent performance metrics"""
    if context.hook_type == HookType.POST_EXECUTE:
        result = context.result
        db = PerformanceDatabase()
        db.log_execution(
            agent=context.agent_name,
            task_type=context.metadata.get('intent', 'unknown'),
            result=result,
            user_rating=None
        )

hook_manager.register(HookType.POST_EXECUTE, performance_hook)
```

**Cost Tracking Hook**:
```python
def cost_tracking_hook(context: HookContext):
    """Track cumulative costs"""
    if context.hook_type == HookType.POST_EXECUTE:
        result = context.result
        cost_file = '~/brain/workspace/.costs/cumulative.json'
        os.makedirs(os.path.dirname(cost_file), exist_ok=True)

        # Load existing
        if os.path.exists(cost_file):
            with open(cost_file) as f:
                costs = json.load(f)
        else:
            costs = {}

        # Update
        agent = context.agent_name
        costs[agent] = costs.get(agent, 0.0) + result.cost

        # Save
        with open(cost_file, 'w') as f:
            json.dump(costs, f, indent=2)

hook_manager.register(HookType.POST_EXECUTE, cost_tracking_hook)
```

**Validation Hook**:
```python
def validation_hook(context: HookContext):
    """Validate task safety before execution"""
    if context.hook_type == HookType.PRE_EXECUTE:
        task = context.task.lower()

        # Check for dangerous operations
        dangerous_keywords = ['rm -rf', 'delete', 'drop table']
        if any(keyword in task for keyword in dangerous_keywords):
            raise ValueError(f"Potentially dangerous task blocked: {task}")

hook_manager.register(HookType.PRE_EXECUTE, validation_hook)
```

### Integration with Orchestrator

```python
class AgnosticOrchestrator:
    def __init__(self, primary: str, agent_configs: dict):
        # ... existing init
        self.hooks = HookManager()
        self._register_default_hooks()

    def _register_default_hooks(self):
        self.hooks.register(HookType.PRE_EXECUTE, logging_hook)
        self.hooks.register(HookType.POST_EXECUTE, performance_hook)
        self.hooks.register(HookType.POST_EXECUTE, cost_tracking_hook)
        self.hooks.register(HookType.PRE_EXECUTE, validation_hook)

    def execute(self, user_input: str, mode: str = "single"):
        # Pre-execute hook
        self.hooks.trigger(HookContext(
            hook_type=HookType.PRE_EXECUTE,
            agent_name=self.primary_name,
            task=user_input,
            result=None,
            session=self.session,
            timestamp=datetime.now(),
            metadata={}
        ))

        # ... existing execute logic

        # Post-execute hook
        self.hooks.trigger(HookContext(
            hook_type=HookType.POST_EXECUTE,
            agent_name=self.primary_name,
            task=user_input,
            result=final_response,
            session=self.session,
            timestamp=datetime.now(),
            metadata={'intent': routing_plan.intent}
        ))

        return final_response
```

## 3. Workspace Isolation

### Concept

Each project/domain gets its own workspace with isolated configuration, memory, and sessions.

### Big-3 Approach

Workspaces are directories with:
- Configuration
- Session state
- Project-specific context
- History

### Our Implementation

**Workspace Structure**:
```
~/brain/workspace/workspaces/
├── watches/
│   ├── .workspace.yaml
│   ├── context/
│   │   ├── market_analysis.md
│   │   └── dealers.md
│   ├── notes/
│   └── data/
├── guitars/
│   ├── .workspace.yaml
│   ├── context/
│   ├── notes/
│   └── data/
└── coding-projects/
    ├── .workspace.yaml
    ├── context/
    ├── notes/
    └── data/
```

**Workspace Config** (`.workspace.yaml`):
```yaml
name: watches
description: Watch collecting research and monitoring
primary_agent: claude
preferred_agents:
  research: claude
  data_analysis: gemini
  automation: opencode

context_files:
  - context/market_analysis.md
  - context/dealers.md

automations:
  - reddit_monitor
  - ebay_scraper

tags:
  - hobbies
  - research
  - collectibles

created: 2025-11-01
last_active: 2025-11-01
```

**Workspace Manager**:
```python
class WorkspaceManager:
    def __init__(self, base_dir: str = '~/brain/workspace/workspaces'):
        self.base_dir = os.path.expanduser(base_dir)
        os.makedirs(self.base_dir, exist_ok=True)

    def create_workspace(self, name: str, description: str,
                        primary_agent: str) -> dict:
        """Create a new workspace"""
        workspace_dir = os.path.join(self.base_dir, name)
        os.makedirs(workspace_dir, exist_ok=True)
        os.makedirs(os.path.join(workspace_dir, 'context'), exist_ok=True)
        os.makedirs(os.path.join(workspace_dir, 'notes'), exist_ok=True)
        os.makedirs(os.path.join(workspace_dir, 'data'), exist_ok=True)

        config = {
            'name': name,
            'description': description,
            'primary_agent': primary_agent,
            'preferred_agents': {},
            'context_files': [],
            'automations': [],
            'tags': [],
            'created': datetime.now().isoformat(),
            'last_active': datetime.now().isoformat()
        }

        config_file = os.path.join(workspace_dir, '.workspace.yaml')
        with open(config_file, 'w') as f:
            yaml.dump(config, f)

        return config

    def load_workspace(self, name: str) -> dict:
        """Load workspace configuration"""
        config_file = os.path.join(self.base_dir, name, '.workspace.yaml')

        if not os.path.exists(config_file):
            raise ValueError(f"Workspace {name} not found")

        with open(config_file) as f:
            return yaml.safe_load(f)

    def list_workspaces(self) -> List[dict]:
        """List all workspaces"""
        workspaces = []
        for name in os.listdir(self.base_dir):
            workspace_dir = os.path.join(self.base_dir, name)
            if os.path.isdir(workspace_dir):
                try:
                    config = self.load_workspace(name)
                    workspaces.append(config)
                except Exception:
                    continue
        return workspaces

    def load_context_files(self, workspace: str) -> str:
        """Load all context files for a workspace"""
        config = self.load_workspace(workspace)
        workspace_dir = os.path.join(self.base_dir, workspace)

        context = []
        for file_path in config.get('context_files', []):
            full_path = os.path.join(workspace_dir, file_path)
            if os.path.exists(full_path):
                with open(full_path) as f:
                    context.append(f"# {file_path}\n{f.read()}")

        return "\n\n".join(context)
```

## 4. CLI Modes

### Concept

Support both interactive (REPL) and headless (single command) modes.

### Big-3 Modes

- Interactive: `big3` launches REPL
- Headless: `big3 --prompt "task"` runs single task

### Our Implementation

**Interactive Mode** (Primary):
```python
# cli.py
import click
from rich.console import Console
from rich.markdown import Markdown

@click.command()
@click.option('--workspace', default='default', help='Workspace to activate')
@click.option('--agent', default=None, help='Primary agent (defaults to workspace config)')
@click.option('--prompt', default=None, help='Headless mode: execute single prompt')
def main(workspace: str, agent: Optional[str], prompt: Optional[str]):
    """Brain CLI - Agent-agnostic research and automation hub"""

    console = Console()

    if prompt:
        # Headless mode
        result = run_headless(workspace, agent, prompt)
        console.print(Markdown(result))
        return

    # Interactive mode
    run_interactive(workspace, agent, console)

def run_interactive(workspace: str, agent: Optional[str], console: Console):
    """Interactive REPL mode"""
    # Load workspace
    ws_manager = WorkspaceManager()
    ws_config = ws_manager.load_workspace(workspace)

    # Determine primary agent
    primary = agent or ws_config['primary_agent']

    # Initialize orchestrator
    orchestrator = AgnosticOrchestrator(primary, load_agent_configs())

    # Load or create session
    registry = SessionRegistry()
    session = registry.load_session(workspace) or \
              registry.create_session(workspace, primary)

    orchestrator.session = session

    # Load context
    context_text = ws_manager.load_context_files(workspace)
    if context_text:
        session.context['workspace_context'] = context_text

    # Welcome message
    console.print(f"\n🧠 Brain CLI v0.1.0 [{primary} orchestrating]")
    console.print(f"📁 Workspace: {workspace}")
    console.print(f"💬 {len(session.conversation)} previous turns loaded\n")

    # REPL loop
    while True:
        try:
            user_input = console.input("[bold blue]>[/bold blue] ")

            if not user_input.strip():
                continue

            # Handle slash commands
            if user_input.startswith('/'):
                handle_slash_command(user_input, orchestrator, session,
                                   registry, console)
                continue

            # Execute task
            response = orchestrator.execute(user_input)

            # Display response
            console.print(Markdown(response))
            console.print()

        except KeyboardInterrupt:
            console.print("\n\n👋 Goodbye!")
            break
        except EOFError:
            break
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

def run_headless(workspace: str, agent: Optional[str], prompt: str) -> str:
    """Headless single-command mode"""
    ws_manager = WorkspaceManager()
    ws_config = ws_manager.load_workspace(workspace)

    primary = agent or ws_config['primary_agent']

    orchestrator = AgnosticOrchestrator(primary, load_agent_configs())

    # Load context
    context = {
        'workspace_context': ws_manager.load_context_files(workspace),
        'conversation': []
    }

    # Execute
    result = orchestrator.execute(prompt)

    return result
```

**Slash Commands**:
```python
def handle_slash_command(command: str, orchestrator: AgnosticOrchestrator,
                        session: Session, registry: SessionRegistry,
                        console: Console):
    """Handle slash commands"""

    parts = command[1:].split()
    cmd = parts[0].lower()
    args = parts[1:]

    if cmd == 'switch':
        if not args:
            console.print("[red]Usage: /switch <agent>[/red]")
            return
        orchestrator.switch_orchestrator(args[0])
        console.print(f"🔄 Switched to {args[0]}")

    elif cmd == 'compare':
        if not args:
            console.print("[red]Usage: /compare <prompt>[/red]")
            return
        task = ' '.join(args)
        result = orchestrator.execute(task, mode='compare')
        console.print(Markdown(result))

    elif cmd == 'agents':
        console.print("\n📋 Available agents:")
        for name, agent in orchestrator.agents.items():
            status = "✅" if agent.ping() else "❌"
            primary = "⭐" if name == orchestrator.primary_name else "  "
            console.print(f"{primary} {status} {name}")

    elif cmd == 'context':
        console.print(f"\n💾 Session context:")
        console.print(f"  Turns: {len(session.conversation)}")
        console.print(f"  Tokens: {session.total_tokens}")
        console.print(f"  Cost: ${session.total_cost:.4f}")

    elif cmd == 'save':
        registry.save_session(session)
        console.print("💾 Session saved")

    elif cmd == 'help':
        show_help(console)

    else:
        console.print(f"[red]Unknown command: /{cmd}[/red]")
        console.print("Type /help for available commands")

def show_help(console: Console):
    help_text = """
# Brain CLI Commands

**Agent Management**:
- `/switch <agent>` - Switch primary orchestrator
- `/agents` - List available agents and status
- `/compare <prompt>` - Compare responses from multiple agents

**Session Management**:
- `/context` - Show session statistics
- `/save` - Save current session
- `/workspace <name>` - Switch workspace

**System**:
- `/help` - Show this help
- `/exit` or Ctrl+C - Exit
"""
    console.print(Markdown(help_text))
```

## Summary

**Adopted from Big-3**:
- ✅ Registry-based session management
- ✅ Hook system for lifecycle events
- ✅ Workspace isolation
- ✅ CLI modes (interactive + headless)

**Our Enhancements**:
- ✅ Agent-agnostic (not Claude-specific)
- ✅ Multi-agent coordination
- ✅ Performance tracking hooks
- ✅ Cost monitoring hooks
- ✅ Workspace-specific configurations

## Next Document

See `04-MIESSLER-PATTERNS.md` for UFC, context loading, and Fabric integration.
