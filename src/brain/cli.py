"""Interactive REPL for Brain CLI."""

import os
import re
import yaml
import click
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from typing import Optional

from .orchestrator import AgnosticOrchestrator
from .session import SessionRegistry
from .agents import ClaudeAgent, GeminiAgent
from .agents.base import Turn
from datetime import datetime


def load_agent_configs() -> dict:
    """Load agent configurations from config file."""
    config_file = os.path.expanduser('~/brain/workspace/.brain-config.yaml')

    if not os.path.exists(config_file):
        raise FileNotFoundError(
            f"Configuration file not found: {config_file}\n"
            f"Please create this file with your agent configurations."
        )

    with open(config_file) as f:
        config_text = f.read()

    # Expand environment variables (${VAR_NAME} or $VAR_NAME)
    def expand_env_vars(text):
        def replace_var(match):
            var_name = match.group(1) or match.group(2)
            return os.getenv(var_name, '')
        # Match ${VAR} or $VAR
        return re.sub(r'\$\{([^}]+)\}|\$([A-Za-z_][A-Za-z0-9_]*)', replace_var, text)

    config_text = expand_env_vars(config_text)

    config = yaml.safe_load(config_text)

    return config


def create_agents(config: dict) -> dict:
    """Create agent instances from configuration."""
    agents = {}

    agent_configs = config.get('agents', {})

    # Claude agent
    if agent_configs.get('claude', {}).get('enabled', False):
        try:
            claude_config = agent_configs['claude'].copy()
            claude_config['name'] = 'claude'
            agents['claude'] = ClaudeAgent(claude_config)
        except Exception as e:
            print(f"Warning: Could not create Claude agent: {e}")

    # Gemini agent
    if agent_configs.get('gemini', {}).get('enabled', False):
        try:
            gemini_config = agent_configs['gemini'].copy()
            gemini_config['name'] = 'gemini'
            agents['gemini'] = GeminiAgent(gemini_config)
        except Exception as e:
            print(f"Warning: Could not create Gemini agent: {e}")

    if not agents:
        raise RuntimeError(
            "No agents could be created. Please check your configuration "
            "and ensure API keys are set."
        )

    return agents


@click.command()
@click.option('--workspace', default='default', help='Workspace to activate')
@click.option('--agent', default=None, help='Primary agent (defaults to config)')
@click.option('--prompt', default=None, help='Headless mode: execute single prompt')
def main(workspace: str, agent: Optional[str], prompt: Optional[str]):
    """Brain CLI - Agent-agnostic research and automation hub."""
    console = Console()

    try:
        # Load configuration
        config = load_agent_configs()
    except FileNotFoundError as e:
        console.print(f"[red]{e}[/red]")
        console.print("\nExample configuration:")
        console.print(Panel("""
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

default_orchestrator: claude
        """.strip(), title="~/.brain-config.yaml"))
        return

    try:
        # Create agents
        agents = create_agents(config)
    except RuntimeError as e:
        console.print(f"[red]{e}[/red]")
        return

    # Determine primary agent
    primary = agent or config.get('default_orchestrator', 'claude')
    if primary not in agents:
        console.print(f"[red]Primary agent '{primary}' not available[/red]")
        console.print(f"Available agents: {', '.join(agents.keys())}")
        primary = next(iter(agents.keys()))
        console.print(f"Using {primary} instead")

    if prompt:
        # Headless mode
        run_headless(workspace, primary, agents, prompt, console)
    else:
        # Interactive mode
        run_interactive(workspace, primary, agents, console)


def run_headless(workspace: str, primary: str, agents: dict,
                prompt: str, console: Console):
    """Run single command in headless mode."""
    orchestrator = AgnosticOrchestrator(primary, agents)

    try:
        response = orchestrator.execute(prompt)
        console.print(Markdown(response))
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


def run_interactive(workspace: str, primary: str, agents: dict,
                   console: Console):
    """Run interactive REPL mode."""
    # Initialize orchestrator
    orchestrator = AgnosticOrchestrator(primary, agents)

    # Load or create session
    registry = SessionRegistry()
    session = registry.load_session(workspace)

    if session:
        # Resume existing session
        orchestrator.session = session
        console.print(f"\n🔄 Resumed session: {workspace}")
        console.print(f"💬 {len(session.conversation)} previous turns loaded")
    else:
        # Create new session
        session = registry.create_session(workspace, primary)
        orchestrator.session = session
        console.print(f"\n✨ Created new session: {workspace}")

    # Welcome message
    console.print(Panel(
        f"[bold]Brain CLI v0.1.0[/bold]\n\n"
        f"🤖 Primary: [cyan]{primary}[/cyan]\n"
        f"📁 Workspace: [cyan]{workspace}[/cyan]\n"
        f"💰 Total cost: [green]${session.total_cost:.4f}[/green]\n\n"
        f"Type [yellow]/help[/yellow] for commands or [yellow]/exit[/yellow] to quit",
        title="🧠 Welcome to Brain CLI"
    ))

    # REPL loop
    while True:
        try:
            user_input = console.input("\n[bold blue]>[/bold blue] ")

            if not user_input.strip():
                continue

            # Handle slash commands
            if user_input.startswith('/'):
                handle_slash_command(
                    user_input, orchestrator, session, registry, console
                )
                continue

            # Add user turn to session
            user_turn = Turn(
                role='user',
                content=user_input,
                agent=orchestrator.primary_name,
                timestamp=datetime.now(),
                tokens=0,  # Will be updated by agent
                cost=0.0
            )
            session.conversation.append(user_turn)

            # Execute task
            try:
                response = orchestrator.execute(user_input)

                # Display response
                console.print()
                console.print(Markdown(response))

                # Save session after each exchange
                registry.save_session(session)

            except Exception as e:
                console.print(f"\n[red]Error: {e}[/red]")
                # Remove the user turn if execution failed
                session.conversation.pop()

        except KeyboardInterrupt:
            console.print("\n\n👋 Goodbye!")
            registry.save_session(session)
            break
        except EOFError:
            registry.save_session(session)
            break


def handle_slash_command(command: str, orchestrator: AgnosticOrchestrator,
                        session, registry: SessionRegistry, console: Console):
    """Handle slash commands."""
    parts = command[1:].split(maxsplit=1)
    cmd = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""

    if cmd == 'switch':
        if not args:
            console.print("[red]Usage: /switch <agent>[/red]")
            return

        agent_name = args.strip()
        try:
            orchestrator.switch_orchestrator(agent_name)
            registry.switch_primary_agent(session, agent_name)
            console.print(f"✅ Switched to [cyan]{agent_name}[/cyan]")
        except ValueError as e:
            console.print(f"[red]{e}[/red]")

    elif cmd == 'agents':
        console.print("\n📋 [bold]Available Agents[/bold]\n")
        status = orchestrator.get_agent_status()
        for name, healthy in status.items():
            status_str = "✅" if healthy else "❌"
            primary_str = "⭐" if name == orchestrator.primary_name else "  "
            console.print(f"{primary_str} {status_str} {name}")

    elif cmd == 'context':
        console.print("\n💾 [bold]Session Context[/bold]\n")
        console.print(f"  Workspace: [cyan]{session.workspace}[/cyan]")
        console.print(f"  Primary: [cyan]{session.primary_agent}[/cyan]")
        console.print(f"  Turns: {len(session.conversation)}")
        console.print(f"  Tokens: {session.total_tokens:,}")
        console.print(f"  Cost: [green]${session.total_cost:.4f}[/green]")

    elif cmd == 'save':
        registry.save_session(session)
        console.print("✅ Session saved")

    elif cmd == 'clear':
        session.conversation = []
        session.total_tokens = 0
        session.total_cost = 0.0
        registry.save_session(session)
        console.print("✅ Conversation cleared")

    elif cmd == 'help':
        show_help(console)

    elif cmd == 'exit' or cmd == 'quit':
        raise KeyboardInterrupt

    else:
        console.print(f"[red]Unknown command: /{cmd}[/red]")
        console.print("Type [yellow]/help[/yellow] for available commands")


def show_help(console: Console):
    """Display help message."""
    help_text = """
# Brain CLI Commands

## Agent Management
- `/switch <agent>` - Switch primary orchestrator
- `/agents` - List available agents and status

## Session Management
- `/context` - Show session statistics
- `/save` - Save current session
- `/clear` - Clear conversation history

## System
- `/help` - Show this help
- `/exit` or `/quit` - Exit (or press Ctrl+C)

## Phase 2 Features (Coming Soon)
- `/compare <prompt>` - Compare responses from multiple agents
- `/workspace <name>` - Switch workspace
    """
    console.print(Markdown(help_text))


if __name__ == '__main__':
    main()
