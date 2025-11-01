# Brain CLI - Project Overview

## Vision

A **terminal-based, agent-agnostic research and automation hub** that transforms how you manage knowledge across multiple domains (watches, guitars, sound design, AI tooling, comics, generative art, hackathacks). Think of it as a second brain with conversational AI superpowers, where ANY AI agent can be the orchestrator.

**Core Philosophy:**
- **Interactive > Command-heavy**: Conversational REPL, not endless CLI commands
- **Agent-agnostic > Lock-in**: Switch orchestrators mid-session (Claude → Gemini → Codex)
- **CLI tools > MCPs**: Leverage bash, Make, git hooks, cron for automation
- **Local-first > Cloud-dependent**: Works offline, your data stays yours
- **100% Free**: No subscriptions, no vendor lock-in

## The Problem

Current challenges with AI-assisted research and automation:

1. **Fragmented Tools**: Different AI agents don't work together
2. **Token Limits**: Hit API limits with single agent, can't easily switch
3. **Context Loss**: No persistent memory across sessions or projects
4. **Manual Coordination**: Can't compare agent performance or route tasks intelligently
5. **Scattered Knowledge**: Research lives in Discord, browser tabs, random files
6. **No Automation**: Repetitive workflows done manually (paper monitoring, project tracking)
7. **Platform Lock-in**: Tied to one AI provider's ecosystem

## The Solution

**Brain CLI** = Interactive orchestrator + Multi-agent coordination + Hierarchical memory + Obsidian integration + CLI automation

```
Terminal (Cursor/Claude Code/Standalone)
    ↓
Interactive REPL with natural language + slash commands
    ↓
Agent-Agnostic Orchestrator (swappable primary)
    ↓
Intelligent Routing → Multiple Agents → Result Synthesis
    ↓
Hierarchical Memory (Global/Project/Session) + Obsidian Vault
    ↓
CLI Automation (bash/Make/git hooks/cron)
```

**Key Innovation**: The orchestrator ISN'T tied to Claude Code - it's a standalone CLI that ANY agent can orchestrate. Hit token limits with Claude? Switch to Gemini. Want Codex for code? Make it primary.

## Architecture Decisions

### 1. Agent-Agnostic Orchestrator

**Why**: Avoid lock-in, work around token limits, leverage different agent strengths

**How**:
- Primary agent routes tasks and synthesizes results
- Secondary agents execute specialized tasks
- Switch primary mid-session with `/switch <agent>`
- All agents wrapped with common interface

**Supported Agents**:
- Claude Code (Anthropic)
- Gemini CLI (Google)
- Codex (OpenAI)
- Aider (paul-gauthier/aider)
- OpenCode (OpenCode-ai/opencode)
- Continue (continuedev/continue)
- Open Interpreter (OpenInterpreter/open-interpreter)

### 2. Interactive REPL Model

**Why**: Conversational workflow beats endless CLI commands

**Primary Mode**: Launch `brain` → interactive session with natural language
```bash
$ brain
🧠 Brain CLI v0.1.0 [Claude orchestrating]
> Research high-complication watches under $5k
> /compare claude gemini codex  # Compare agent responses
> /switch gemini  # Switch orchestrator
> /tts on  # Enable voice output
```

**Headless Mode** (future): `brain --prompt "summarize latest AI papers"`

**NOT**: `brain research watches`, `brain analyze --agent claude`, `brain add-shopping milk`

### 3. Directory Structure (Option C - Siblings)

**Why**: Clean separation of tool (public) vs research (private)

```
~/brain/
├── brain-cli/           # Public GitHub repo - the tool
│   ├── src/brain/
│   │   ├── cli.py
│   │   ├── orchestrator.py
│   │   ├── router.py
│   │   ├── agents/
│   │   └── hooks/
│   └── setup.py
│
└── workspace/           # Private repo - your research
    ├── .brain-config.yaml
    ├── workspaces/
    │   ├── watches/
    │   ├── guitars/
    │   └── coding-projects/
    ├── global_memory/
    ├── agent_analytics/
    └── obsidian_vault/
```

**Benefits**:
- Share tool publicly without exposing research
- Two separate Git repos
- No submodule complexity
- Clean, obvious separation

### 4. Obsidian Integration

**Why**: FREE, MCP-ready, local-first, terminal-native

**vs Notion**: $0/mo vs $15/mo, better MCP integration, works offline, Git sync

**Integration**:
- MCP server: `cyanheads/obsidian-mcp-server`
- Essential plugins: Shell Commands, Cron, Dataview, Terminal
- YAML frontmatter for metadata
- Git-based sync (free alternative to Obsidian Sync)
- Vault location: `~/brain/workspace/obsidian_vault/`

### 5. Voice Integration (Phase 2)

**Approach**: Wispr (input) + Swappable TTS (output)

**Why NOT OpenAI Realtime**:
- Too complex (WebSocket management, state sync)
- Locks into OpenAI ecosystem
- User already has Wispr Flow locally
- Simpler = better for MVP → Scale path

**Implementation**:
- Input: Wispr Flow (external, user manages)
- Output: Toggle-able TTS with `/tts on`
- Providers: pyttsx3 (free/local), ElevenLabs, Google TTS, OpenAI TTS, Coqui
- Swap providers: `/tts provider elevenlabs`

## Pattern Adoption

### From Big-3-Super-Agent

**Adopt**:
- Registry-based session management
- Hook system for lifecycle events (pre/post tool use)
- Workspace isolation per project
- CLI modes (interactive vs headless)

**Adapt**:
- Not Claude-specific - agent-agnostic
- Interactive REPL as primary mode
- Multi-agent coordination layer

### From Daniel Miessler

**Adopt**:
- UFC (Unified File Context) directory structure
- Mandatory context loading with observable verification
- Fabric pattern library (300+ community prompts)
- Token budget management

**Adapt**:
- CLI-first automation (not n8n)
- Multi-agent routing (not single LLM)
- Obsidian integration (not custom UI)

## Technology Stack (100% Free)

**Core**:
- Python 3.11+ (orchestrator, REPL, agent wrappers)
- Click/Typer (CLI framework)
- Rich (terminal UI)
- SQLite (performance tracking)

**AI Agents**:
- Claude API (Anthropic SDK)
- Gemini API (google-generativeai)
- OpenAI API (Codex)
- Aider (programmatic usage)
- OpenCode (Go binary)

**CLI Tools**:
- fzf (fuzzy finder)
- ripgrep (fast search)
- bat (syntax highlighting)
- glow (markdown rendering)
- jq/yq (JSON/YAML processing)
- Fabric (AI pattern library)

**Knowledge Management**:
- Obsidian (FREE)
- obsidian-mcp-server
- Git (vault sync)

**Memory & Search**:
- ChromaDB (Phase 2 - semantic memory)
- Neo4j Desktop (Phase 3 - knowledge graph)
- FAISS (optional vector search)

**Voice** (Phase 2):
- Wispr Flow (input - user managed)
- pyttsx3 (free local TTS)
- ElevenLabs/Google/OpenAI/Coqui (optional)

**Automation**:
- Bash scripts
- Git hooks
- Cron/crontab
- Make/Just task runners

## Implementation Phases

### Phase 1: MVP (Weeks 1-2)
- Interactive REPL with natural language
- Agent-agnostic orchestrator (Claude + one other)
- Basic routing (rule-based)
- File-based session memory
- Obsidian MCP integration
- 3 automation workflows

**Deliverable**: Working CLI that routes tasks between 2 agents

### Phase 2: Scale (Weeks 3-6)
- All 7 agents integrated
- Multi-agent comparison mode
- Performance tracking database (SQLite)
- ChromaDB semantic memory
- All 11 automation workflows
- **TTS toggle** (Wispr + swappable TTS output)
- Intelligent routing (LLM-based)
- Fabric pattern integration

**Deliverable**: Production-ready tool with voice output

### Phase 3: Intelligence (Weeks 7-12, Optional)
- Neo4j knowledge graph
- HybridRAG (vector + graph)
- Advanced analytics
- Learning system (agent performance optimization)
- Cursor extension (maybe)

**Deliverable**: AI-powered research assistant with deep memory

### Phase 4: Advanced Voice (Future)
- OpenAI Realtime API exploration
- Full duplex voice interaction
- Agent voice personalities

**Deliverable**: Voice-first interaction mode

## Key Features

### Multi-Agent Coordination
- **Route** tasks to best agent
- **Compare** responses from multiple agents
- **Learn** which agents excel at what
- **Switch** orchestrators mid-session

### Hierarchical Memory
```
Global Memory (cross-project patterns, tools, philosophy)
    ↓
Project Memory (workspace-specific context)
    ↓
Session Memory (current conversation, decisions)
```

### Automation Workflows (11 Total)
1. Coding project tracker with agent validation
2. Watch monitor (Reddit/eBay notifications)
3. Todo integration with research findings
4. Self-updating research projects
5. GitHub project launcher
6. Shopping list integration
7. Paper pipeline (arXiv → summary → queue)
8. Weekly review automation
9. Hackathon ideation workflow
10. AI tool discovery
11. Communication generator

### Performance Tracking
- Track agent performance per task type
- Quality ratings, response time, cost
- Analytics: Which agent for which tasks?
- Learning system improves routing over time

## Integration Points

### Works From:
- Cursor 2.0 terminal
- Claude Code terminal
- Standalone terminal
- Any shell with Python 3.11+

### Integrates With:
- Obsidian vault (MCP)
- Git repositories
- File system (UFC structure)
- Cron (scheduled automation)
- Any agent with API or CLI

### Future Cursor Extension (Phase 3+):
- Native Cursor integration
- Multi-prompt interface
- Embedded REPL
- Slash command registration

## Success Criteria

**Week 2 (MVP)**:
- ✅ Can route tasks between 2 agents
- ✅ Interactive REPL works
- ✅ Session memory persists
- ✅ Obsidian integration active
- ✅ 3 automation workflows running

**Week 6 (Scale)**:
- ✅ All 7 agents working
- ✅ Multi-agent comparison mode
- ✅ TTS toggle functional
- ✅ Performance tracking database
- ✅ All 11 automation workflows
- ✅ Fabric patterns integrated

**Week 12 (Intelligence)**:
- ✅ Knowledge graph operational
- ✅ Learning system improves routing
- ✅ Advanced analytics dashboard
- ✅ HybridRAG semantic search

## Non-Goals (Scope Limits)

**NOT Building**:
- n8n workflows or visual automation
- Custom UI or web interface
- Mobile apps
- Authentication system (enterprise bloat)
- Deployment infrastructure
- Full OpenAI Realtime integration (Phase 1-3)

## Next Steps

1. Read remaining planning docs (01-13)
2. Review implementation examples (11)
3. Validate tech stack decisions (12)
4. Start Phase 1 implementation
5. Create `brain-cli/` skeleton
6. Build agent wrappers
7. Implement interactive REPL
8. Test with 2 agents (Claude + Gemini)

---

**Project Status**: 📋 Planning Complete → Ready for Implementation

**Last Updated**: 2025-11-01
