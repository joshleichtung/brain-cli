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

### Completed (Week 1-5)

✅ **Week 1**: Infrastructure
- Agent fleet management with on-demand spawning
- Git worktree isolation for parallel agent work
- Orchestrator v2 with async execution
- All tests passing (19/19)

✅ **Week 2**: Enhanced REPL
- Rich terminal UI with interactive prompts
- User confirmation flow for multi-agent operations
- Agent selection interface

✅ **Week 3**: Observability
- Event hook system (8 lifecycle event types)
- SQLite event storage
- FastAPI observability service with WebSocket
- Real-time event broadcasting

✅ **Week 4**: Dashboard
- React + TypeScript + Tailwind v3 dashboard
- WebSocket-based live event monitoring
- Agent lifecycle visualization

✅ **Week 5**: Analytics
- Jira/GitHub CSV parsers with flexible column matching
- Pattern detection: K-means clustering, LDA topic modeling
- NLP analysis: Named entity recognition, sentiment analysis
- Analytics API endpoints integrated with FastAPI
- Dashboard analytics UI with upload and visualization
- Test suite: 6/6 passing

### Tags
- `v0.1.0-foundation` - Week 1: Infrastructure
- `v0.2.0-repl` - Week 2: Enhanced REPL
- `v0.3.0-observability` - Week 3: Observability system
- `v0.4.0-dashboard` - Week 4: React dashboard
- `v0.5.0-analytics-core` - Week 5 M1: Analytics module
- `v0.5.1-analytics-tested` - Week 5 M2: Analytics tests
- `v0.5.2-analytics-ui` - Week 5 M3: Analytics dashboard UI

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
