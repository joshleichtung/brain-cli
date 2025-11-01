"""
Enhanced REPL with orchestrator v2 integration.

Features:
- Rich terminal UI with colors and formatting
- Integration with AgnosticOrchestrator
- Interactive multi-agent confirmation
- Fleet status display
- Cost tracking
- Session management
"""

import asyncio
import os
import sys
from typing import Optional
from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.live import Live
from rich.layout import Layout
from rich.text import Text

from .orchestrator_v2 import AgnosticOrchestrator
from .session import SessionRegistry
from .agents.base import RoutingPlan


class BrainREPL:
    """
    Enhanced REPL for Brain CLI with orchestrator integration.
    """

    def __init__(
        self,
        workspace_path: str = None,
        session_name: str = None,
        primary_agent: str = 'claude-code'
    ):
        """
        Initialize REPL.

        Args:
            workspace_path: Path to workspace directory
            session_name: Optional session name to resume
            primary_agent: Primary orchestrating agent
        """
        self.console = Console()
        self.workspace_path = workspace_path or os.getcwd()
        self.primary_agent = primary_agent

        # Agent configurations
        self.agent_configs = {
            'claude-code': {
                'model': 'claude-sonnet-4-5-20250929',
                'permission_mode': 'acceptEdits',
                'cost_per_1k_tokens': 0.003
            }
        }

        # Session management
        self.session_registry = SessionRegistry(
            base_dir=os.path.expanduser('~/brain/workspace/.sessions')
        )

        if session_name:
            try:
                self.session = self.session_registry.load_session(session_name)
                if self.session is None:
                    # Session doesn't exist, create new one
                    self.console.print(f"[yellow]📝 Creating new session: {session_name}[/yellow]")
                    self.session = self.session_registry.create_session(
                        workspace=session_name,
                        primary_agent=primary_agent
                    )
                else:
                    self.console.print(f"[green]✅ Loaded session: {session_name}[/green]")
            except Exception as e:
                self.console.print(f"[yellow]⚠️  Could not load session: {e}[/yellow]")
                self.session = self.session_registry.create_session(
                    workspace=session_name or 'default',
                    primary_agent=primary_agent
                )
        else:
            self.session = self.session_registry.create_session(
                workspace='default',
                primary_agent=primary_agent
            )

        # Initialize orchestrator
        self.orchestrator = AgnosticOrchestrator(
            primary_agent_name=primary_agent,
            agent_configs=self.agent_configs,
            workspace_path=self.workspace_path,
            session=self.session,
            max_concurrent_agents=5
        )

        self.running = False

    def display_banner(self):
        """Display welcome banner."""
        banner = Panel.fit(
            "[bold cyan]🧠 Brain CLI[/bold cyan]\n"
            "[dim]Agent-agnostic multi-agent orchestration[/dim]\n\n"
            f"[yellow]Workspace:[/yellow] {self.workspace_path}\n"
            f"[yellow]Session:[/yellow] {self.session.workspace}\n"
            f"[yellow]Primary Agent:[/yellow] {self.primary_agent}",
            border_style="cyan"
        )
        self.console.print(banner)

    def display_help(self):
        """Display help message."""
        table = Table(title="Available Commands", border_style="cyan")
        table.add_column("Command", style="yellow")
        table.add_column("Description")

        table.add_row("/help", "Show this help message")
        table.add_row("/status", "Show fleet and session status")
        table.add_row("/multi <n> <task>", "Force multi-agent execution with N agents")
        table.add_row("/single <task>", "Force single agent execution")
        table.add_row("/save", "Save current session")
        table.add_row("/clear", "Clear conversation history")
        table.add_row("/exit, /quit", "Exit REPL")

        self.console.print(table)

    def display_status(self):
        """Display fleet and session status."""
        # Fleet status
        fleet_status = self.orchestrator.get_fleet_status()
        fleet_table = Table(title="Fleet Status", border_style="blue")
        fleet_table.add_column("Metric", style="yellow")
        fleet_table.add_column("Value")

        fleet_table.add_row("Active Agents", str(fleet_status['active_agents']))
        fleet_table.add_row("Running", str(fleet_status['running']))
        fleet_table.add_row("Queued", str(fleet_status['queued']))
        fleet_table.add_row("Max Concurrent", str(fleet_status['max_concurrent']))

        # Session status
        session_table = Table(title="Session Status", border_style="green")
        session_table.add_column("Metric", style="yellow")
        session_table.add_column("Value")

        session_table.add_row("Conversation Turns", str(len(self.session.conversation)))
        session_table.add_row("Total Tokens", str(self.session.total_tokens))
        session_table.add_row("Total Cost", f"${self.session.total_cost:.4f}")

        self.console.print(fleet_table)
        self.console.print()
        self.console.print(session_table)

    async def handle_routing_suggestion(
        self,
        task: str,
        suggestion: RoutingPlan
    ) -> tuple[str, Optional[int]]:
        """
        Handle routing suggestion from orchestrator.

        Shows suggestion to user and asks for confirmation.

        Args:
            task: User's task
            suggestion: RoutingPlan from orchestrator

        Returns:
            Tuple of (mode, num_agents)
        """
        if not suggestion.requires_multiple:
            return ("single", None)

        # Display suggestion
        panel = Panel(
            f"[bold]Task Analysis[/bold]\n\n"
            f"[yellow]Intent:[/yellow] {suggestion.intent}\n"
            f"[yellow]Complexity:[/yellow] {suggestion.complexity:.2f}\n"
            f"[yellow]Estimated Tokens:[/yellow] {suggestion.estimated_tokens}\n\n"
            f"[cyan]💡 Suggestion:[/cyan] Use {len(suggestion.recommended_agents)} agents\n"
            f"[cyan]Parallel:[/cyan] {suggestion.parallel_execution}",
            title="🤖 Orchestrator Suggestion",
            border_style="magenta"
        )
        self.console.print(panel)

        # Ask user
        use_multi = Confirm.ask(
            "\n[bold]Use multiple agents?[/bold]",
            default=True
        )

        if not use_multi:
            return ("single", None)

        # Ask for number of agents
        num_agents = Prompt.ask(
            "[bold]How many agents?[/bold]",
            default=str(len(suggestion.recommended_agents))
        )

        try:
            num_agents = int(num_agents)
            return ("multi", num_agents)
        except ValueError:
            self.console.print("[red]Invalid number, using single agent[/red]")
            return ("single", None)

    async def execute_task(self, task: str, mode: str = "auto", num_agents: Optional[int] = None):
        """
        Execute a task through the orchestrator.

        Args:
            task: User's task
            mode: Execution mode (auto, single, multi)
            num_agents: Number of agents for multi mode
        """
        try:
            if mode == "auto":
                # Get suggestion from orchestrator
                context = self.orchestrator._build_context()
                suggestion = await self.orchestrator._get_routing_suggestion(task, context)

                # Ask user for confirmation
                mode, num_agents = await self.handle_routing_suggestion(task, suggestion)

            # Show progress
            with self.console.status(
                f"[bold cyan]Executing with {mode} mode...[/bold cyan]",
                spinner="dots"
            ):
                if mode == "multi":
                    response = await self.orchestrator.execute(task, mode="multi", num_agents=num_agents)
                else:
                    response = await self.orchestrator.execute(task, mode="single")

            # Display response
            response_panel = Panel(
                response,
                title="[bold green]Response[/bold green]",
                border_style="green"
            )
            self.console.print()
            self.console.print(response_panel)

            # Save session
            self.session_registry.save_session(self.session)

        except Exception as e:
            self.console.print(f"[bold red]Error:[/bold red] {e}")
            import traceback
            traceback.print_exc()

    async def run(self):
        """Run the REPL loop."""
        self.running = True
        self.display_banner()
        self.console.print("\n[dim]Type /help for commands, /exit to quit[/dim]\n")

        while self.running:
            try:
                # Get user input
                user_input = Prompt.ask("\n[bold cyan]brain>[/bold cyan]")

                if not user_input.strip():
                    continue

                # Handle commands
                if user_input.startswith('/'):
                    await self.handle_command(user_input)
                else:
                    # Execute task
                    await self.execute_task(user_input, mode="auto")

            except KeyboardInterrupt:
                self.console.print("\n[yellow]Use /exit to quit[/yellow]")
            except EOFError:
                break
            except Exception as e:
                self.console.print(f"[bold red]Error:[/bold red] {e}")

        # Cleanup
        self.console.print("\n[cyan]Goodbye! 👋[/cyan]\n")

    async def handle_command(self, command: str):
        """Handle REPL commands."""
        parts = command.split(maxsplit=1)
        cmd = parts[0].lower()

        if cmd in ['/exit', '/quit']:
            self.running = False

        elif cmd == '/help':
            self.display_help()

        elif cmd == '/status':
            self.display_status()

        elif cmd == '/save':
            self.session_registry.save_session(self.session)
            self.console.print("[green]✅ Session saved[/green]")

        elif cmd == '/clear':
            self.session.conversation.clear()
            self.console.print("[green]✅ Conversation cleared[/green]")

        elif cmd == '/multi':
            # /multi 3 What is the meaning of life?
            if len(parts) < 2:
                self.console.print("[red]Usage: /multi <num_agents> <task>[/red]")
                return

            args = parts[1].split(maxsplit=1)
            if len(args) < 2:
                self.console.print("[red]Usage: /multi <num_agents> <task>[/red]")
                return

            try:
                num_agents = int(args[0])
                task = args[1]
                await self.execute_task(task, mode="multi", num_agents=num_agents)
            except ValueError:
                self.console.print("[red]Invalid number of agents[/red]")

        elif cmd == '/single':
            # /single What is 2+2?
            if len(parts) < 2:
                self.console.print("[red]Usage: /single <task>[/red]")
                return

            task = parts[1]
            await self.execute_task(task, mode="single")

        else:
            self.console.print(f"[red]Unknown command: {cmd}[/red]")
            self.console.print("[dim]Type /help for available commands[/dim]")


async def main():
    """Main entry point for REPL."""
    import argparse

    parser = argparse.ArgumentParser(description='Brain CLI - Multi-agent orchestration')
    parser.add_argument('--workspace', '-w', help='Workspace directory path')
    parser.add_argument('--session', '-s', help='Session name to resume')
    parser.add_argument('--agent', '-a', default='claude-code', help='Primary agent')

    args = parser.parse_args()

    repl = BrainREPL(
        workspace_path=args.workspace,
        session_name=args.session,
        primary_agent=args.agent
    )

    await repl.run()


if __name__ == '__main__':
    asyncio.run(main())
