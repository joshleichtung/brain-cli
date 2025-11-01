# Brain CLI

**Agent-agnostic research and automation hub for terminal-based workflows.**

## Overview

Brain CLI is a terminal-based orchestrator that coordinates multiple AI agents (Claude, Gemini, Codex, Aider, OpenCode, etc.) to help you manage research, automate workflows, and build a second brain - all from the command line.

**Key Features**:
- 🤖 Multi-agent coordination with intelligent routing
- 💬 Interactive REPL with natural language
- 🔄 Switch agents mid-session without losing context
- 💾 Session persistence across restarts
- 📝 Obsidian integration for knowledge management
- ⚙️ CLI-first automation (bash, Make, cron)
- 🔊 Optional TTS voice output
- 100% FREE infrastructure (pay only for AI API usage)

## Project Status

🚧 **Phase 1: MVP** - In Development

See `docs/` for complete planning documentation.

## Quick Start

Coming soon! Phase 1 implementation in progress.

## Documentation

- **[00-OVERVIEW.md](docs/00-OVERVIEW.md)** - Project vision and architecture
- **[08-PHASE-1-MVP.md](docs/08-PHASE-1-MVP.md)** - Current implementation phase
- **[12-TECH-STACK.md](docs/12-TECH-STACK.md)** - Complete technology list

Full documentation in `docs/` directory.

## Architecture

**Agent-Agnostic Orchestrator**:
```
Interactive REPL
    ↓
Orchestrator (swappable primary agent)
    ↓
Router → Multiple Agents → Result Synthesis
    ↓
Hierarchical Memory + Obsidian
    ↓
CLI Automation
```

**Supported Agents**:
- Claude Code (Anthropic)
- Gemini (Google)
- Codex (OpenAI)
- Aider (CLI-based)
- OpenCode (Go binary)
- Continue (IDE integration)
- Open Interpreter (code execution)

## Design Principles

- **Interactive > Command-heavy**: Conversational REPL, not endless CLI commands
- **Agent-agnostic > Lock-in**: Switch orchestrators anytime
- **CLI tools > MCPs**: Bash, Make, git hooks for automation
- **Local-first > Cloud-dependent**: Your data, your control
- **100% Free**: No subscriptions, only API usage costs

## Phases

- **Phase 1 (Weeks 1-2)**: MVP with 2 agents, REPL, session persistence
- **Phase 2 (Weeks 3-6)**: All 7 agents, TTS, 11 automation workflows
- **Phase 3 (Weeks 7-12)**: Knowledge graph, ML routing (optional)

## Tech Stack

- Python 3.11+
- Anthropic, Google GenAI, OpenAI SDKs
- SQLite, ChromaDB, Neo4j
- Obsidian + MCP server
- Click, Rich (CLI/TUI)
- Fabric (AI patterns)

**Cost**: $0/month infrastructure, pay-as-you-go API usage

## License

TBD

## Contributing

Coming soon!

## Author

Built by Josh for terminal-native AI workflows.

---

🧠 **Brain CLI** - Think faster, automate smarter, remember everything.
