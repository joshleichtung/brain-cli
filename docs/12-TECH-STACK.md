# Technology Stack

Complete technology list for Brain CLI - **100% FREE** (no subscriptions).

## Core Technologies

### Programming Language
- **Python 3.11+**: Main implementation language
  - Modern features (type hints, async)
  - Rich ecosystem
  - Cross-platform

### CLI Framework
- **Click** or **Typer**: Command-line interface
  - Argument parsing
  - Command grouping
  - Auto-generated help

### Terminal UI
- **Rich**: Beautiful terminal output
  - Markdown rendering
  - Tables and formatting
  - Progress indicators
  - Syntax highlighting

## AI Agent APIs

### Primary Agents
- **Anthropic API**: Claude models
  - Claude Sonnet 4.5 (primary)
  - Python SDK: `anthropic`
  - Cost: ~$0.003 per 1K tokens

- **Google Generative AI**: Gemini models
  - Gemini 1.5 Pro
  - Python SDK: `google-generativeai`
  - Cost: ~$0.00125 per 1K tokens

- **OpenAI API**: GPT models (Codex)
  - GPT-4 Turbo
  - Python SDK: `openai`
  - Cost: ~$0.01 per 1K tokens

### CLI-Based Agents
- **Aider**: paul-gauthier/aider
  - Install: `pipx install aider-chat`
  - Git-integrated code editing
  - Free + API costs

- **OpenCode**: OpenCode-ai/opencode
  - Install: Download Go binary
  - Terminal operations
  - Free

- **Continue**: continuedev/continue
  - IDE-integrated (optional Phase 2)
  - Free + API costs

- **Open Interpreter**: OpenInterpreter/open-interpreter
  - Install: `pip install open-interpreter`
  - Code execution
  - Free + API costs

## Database & Storage

### SQL Database
- **SQLite**: Performance tracking
  - Built into Python
  - Zero-config
  - File-based
  - **FREE**

### Vector Database
- **ChromaDB**: Semantic memory (Phase 2)
  - Install: `pip install chromadb`
  - Embeddings: OpenAI or sentence-transformers
  - Local-first
  - **FREE**

- **Alternative**: FAISS (Facebook)
  - Install: `pip install faiss-cpu`
  - Pure vector search
  - **FREE**

### Graph Database
- **Neo4j Desktop**: Knowledge graph (Phase 3)
  - Download: neo4j.com/download
  - FREE for local use
  - Or Docker: `docker run neo4j:latest`
  - **FREE**

## Knowledge Management

### Primary Tool
- **Obsidian**: Note-taking and knowledge base
  - Download: obsidian.md
  - Local markdown files
  - Plugin ecosystem
  - **FREE** (Sync is $8/mo but use Git instead)

### Obsidian Plugins
- **Shell Commands**: Run terminal commands
- **Obsidian Cron**: Scheduled tasks
- **Dataview**: Query notes as database
- **Terminal**: Embedded terminal
- All plugins: **FREE**

### MCP Integration
- **obsidian-mcp-server**: cyanheads/obsidian-mcp-server
  - Install: `npm install -g @cyanheads/obsidian-mcp-server`
  - AI-Obsidian integration
  - **FREE**

## CLI Tools

### Essential Tools
- **fzf**: Fuzzy finder
  - Install: `brew install fzf` (macOS) or `apt install fzf` (Linux)
  - Interactive selection
  - **FREE**

- **ripgrep (rg)**: Fast search
  - Install: `brew install ripgrep`
  - Faster than grep
  - **FREE**

- **bat**: Syntax highlighting for cat
  - Install: `brew install bat`
  - Prettier file viewing
  - **FREE**

- **glow**: Markdown renderer
  - Install: `brew install glow`
  - Terminal markdown
  - **FREE**

- **jq**: JSON processor
  - Install: `brew install jq`
  - JSON parsing
  - **FREE**

- **yq**: YAML processor
  - Install: `brew install yq`
  - YAML parsing
  - **FREE**

### Task Runners
- **Make**: Traditional task runner
  - Built into Unix systems
  - **FREE**

- **Just**: Modern command runner
  - Install: `brew install just`
  - Simpler than Make
  - **FREE**

## AI Pattern Library

### Fabric
- **Fabric**: danielmiessler/fabric
  - Install: `pipx install fabric`
  - 300+ community AI patterns
  - **FREE**

## Voice Integration

### Text-to-Speech (Phase 2)

**Primary (Free)**:
- **pyttsx3**: Local TTS
  - Install: `pip install pyttsx3`
  - Offline, fast
  - **FREE**

**Alternatives (Optional)**:
- **Google TTS**: gTTS
  - Install: `pip install gTTS`
  - Cloud-based, good quality
  - **FREE**

- **Coqui TTS**: Local neural TTS
  - Install: `pip install TTS`
  - High quality, slower
  - **FREE**

- **ElevenLabs**: Premium TTS
  - API: elevenlabs.io
  - Best quality
  - **PAID** (~$5-$22/month)

- **OpenAI TTS**: Premium TTS
  - API via openai package
  - Good quality
  - **PAID** (~$0.015 per 1K chars)

### Speech-to-Text (User Managed)
- **Wispr Flow**: User's existing tool
  - External to Brain CLI
  - User manages
  - **PAID** (User's subscription)

## Automation

### Scheduling
- **cron / crontab**: Unix scheduler
  - Built into Unix/Linux/macOS
  - **FREE**

- **launchd**: macOS scheduler (alternative)
  - Built into macOS
  - **FREE**

### Git Integration
- **Git**: Version control
  - Built into most systems
  - **FREE**

- **GitHub CLI (gh)**: GitHub operations
  - Install: `brew install gh`
  - PR creation, issues
  - **FREE**

### Shell
- **Bash**: Scripting language
  - Built into Unix systems
  - **FREE**

- **Zsh**: Modern shell (macOS default)
  - Built into macOS
  - **FREE**

## Development Tools

### Version Control
- **Git**: Source control
  - **FREE**

- **GitHub**: Remote hosting
  - **FREE** (public repos)

### Python Package Management
- **pip**: Package installer
  - Built into Python
  - **FREE**

- **venv**: Virtual environments
  - Built into Python
  - **FREE**

- **pipx**: Isolated CLI tools
  - Install: `pip install pipx`
  - **FREE**

### Testing
- **pytest**: Testing framework
  - Install: `pip install pytest`
  - **FREE**

- **pytest-cov**: Coverage reporting
  - Install: `pip install pytest-cov`
  - **FREE**

### Code Quality
- **black**: Code formatter
  - Install: `pip install black`
  - **FREE**

- **flake8**: Linting
  - Install: `pip install flake8`
  - **FREE**

- **mypy**: Type checking
  - Install: `pip install mypy`
  - **FREE**

## IDE / Editors

### Primary Options
- **Cursor**: AI-powered editor
  - Download: cursor.sh
  - **FREE** (with usage limits)

- **VS Code**: Free editor
  - Download: code.visualstudio.com
  - **FREE**

- **Claude Code**: AI-powered CLI
  - Via Anthropic
  - **FREE** (with API usage)

### Terminal
- **iTerm2**: macOS terminal
  - Download: iterm2.com
  - **FREE**

- **Alacritty**: GPU-accelerated terminal
  - Download: github.com/alacritty/alacritty
  - **FREE**

## Phase-Specific Technologies

### Phase 1 (MVP)
- ✅ Python 3.11+
- ✅ Click/Typer
- ✅ Rich
- ✅ Anthropic SDK (Claude)
- ✅ Google GenAI SDK (Gemini)
- ✅ SQLite
- ✅ obsidian-mcp-server
- ✅ Bash scripting
- ✅ cron

**Total Cost**: $0/month (API usage only)

### Phase 2 (Scale)
- ✅ Phase 1 stack
- ✅ OpenAI SDK (Codex)
- ✅ Aider
- ✅ OpenCode
- ✅ ChromaDB
- ✅ Fabric
- ✅ pyttsx3 (TTS)
- ✅ fzf, ripgrep, bat

**Total Cost**: $0/month (API usage only)

### Phase 3 (Intelligence)
- ✅ Phase 1-2 stack
- ✅ Neo4j Desktop
- ✅ scikit-learn (ML)
- ✅ spaCy (NLP - optional)
- ✅ networkx (graph algorithms)

**Total Cost**: $0/month (API usage only)

## Optional Paid Services

### Voice (Phase 2+)
- ElevenLabs TTS: $5-$22/month
- OpenAI TTS: ~$0.015 per 1K chars
- User's Wispr Flow: ~$10/month

### Cloud Sync (Optional)
- Obsidian Sync: $8/month (or use Git for free)
- GitHub private repos: $4/month (or use free public)

### Premium AI Models (Optional)
- OpenAI o1: ~$15 per 1M tokens
- Anthropic Opus: ~$15 per 1M tokens
- Google Gemini Ultra: TBD

## Installation Summary

```bash
# Python packages
pip install anthropic google-generativeai openai
pip install click rich pyyaml python-dotenv
pip install chromadb  # Phase 2
pip install pytest pytest-cov  # Testing
pip install pyttsx3  # TTS Phase 2
pip install scikit-learn spacy  # Phase 3

# CLI tools
brew install fzf ripgrep bat glow jq yq just gh

# Python CLI tools
pipx install aider-chat
pipx install fabric
pipx install open-interpreter

# Node.js tools
npm install -g @cyanheads/obsidian-mcp-server

# Download/Install
# - Obsidian: obsidian.md
# - Neo4j Desktop: neo4j.com/download (Phase 3)
# - Cursor: cursor.sh (optional)
# - OpenCode: github.com/OpenCode-ai/opencode (optional)
```

## Cost Breakdown

### One-Time Costs
- $0 - Everything is open source or free to download

### Monthly Costs (Optional)
- $0 - All core features work without subscriptions
- API Usage - Pay only for what you use:
  - Claude: ~$0.003 per 1K tokens
  - Gemini: ~$0.00125 per 1K tokens
  - Codex: ~$0.01 per 1K tokens

### Example Monthly API Usage
**Light Use** (100 tasks/month, 2K tokens avg):
- Total tokens: 200K
- Claude (70%): ~$0.42
- Gemini (20%): ~$0.05
- Codex (10%): ~$0.20
- **Total: ~$0.67/month**

**Heavy Use** (1000 tasks/month, 3K tokens avg):
- Total tokens: 3M
- Claude (60%): ~$5.40
- Gemini (20%): ~$0.75
- Codex (20%): ~$6.00
- **Total: ~$12.15/month**

**Enterprise Use** (5000 tasks/month):
- Est. **$50-100/month** (still cheaper than most SaaS)

## System Requirements

### Minimum
- **OS**: macOS, Linux, or Windows (WSL2)
- **RAM**: 4GB
- **Storage**: 1GB (10GB with Neo4j)
- **Python**: 3.11+
- **Node.js**: 16+ (for MCP server)
- **Internet**: Required for API calls

### Recommended
- **OS**: macOS or Linux
- **RAM**: 8GB+
- **Storage**: 20GB (for logs, Obsidian vault, databases)
- **Python**: 3.11+
- **Terminal**: iTerm2 or Alacritty
- **Shell**: Zsh or Bash

## Dependencies Summary

### Python Core
```
anthropic>=0.34.0
google-generativeai>=0.3.0
openai>=1.0.0
click>=8.1.0
rich>=13.0.0
pyyaml>=6.0
python-dotenv>=1.0.0
```

### Python Phase 2
```
chromadb>=0.4.0
pyttsx3>=2.90
fabric-ai>=1.0.0
```

### Python Phase 3
```
neo4j>=5.0.0
scikit-learn>=1.3.0
networkx>=3.0
spacy>=3.6.0  # optional
```

## Architecture Advantages

**100% Free Core**:
- No vendor lock-in
- No subscription fatigue
- Pay only for AI API usage
- Self-hosted data

**Open Source**:
- Full transparency
- Community support
- Extensible
- Forkable

**Local-First**:
- Data privacy
- Works offline (except AI calls)
- Fast
- No cloud dependencies

**Terminal-Native**:
- Fast workflow
- Scriptable
- Automatable
- Universal (works everywhere)

## Next Steps

With this stack:
1. **Phase 1**: Implement with 0 monthly cost
2. **Phase 2**: Add features with 0 additional cost
3. **Phase 3**: Scale with optional Neo4j (still free)
4. **Production**: Pay only for API usage

**Total Infrastructure Cost**: **$0/month**

**Only Variable Cost**: AI API usage (pay-as-you-go)
