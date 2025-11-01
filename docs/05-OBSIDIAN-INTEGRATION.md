# Obsidian Integration

## Why Obsidian

**Decision**: Obsidian over Notion

**Reasons**:
- **FREE** vs $15/month (Notion Plus)
- **Local-first**: Your data, your control
- **MCP Server**: `cyanheads/obsidian-mcp-server` for AI integration
- **Terminal-native**: Works with CLI workflow
- **Git sync**: Free alternative to Obsidian Sync
- **Plugin ecosystem**: Shell Commands, Cron, Dataview, Terminal
- **Markdown**: Plain text, portable, grep-able

## Architecture

```
~/brain/workspace/obsidian_vault/
├── .obsidian/                  # Obsidian config
│   ├── plugins/
│   │   ├── shell-commands/
│   │   ├── obsidian-cron/
│   │   ├── dataview/
│   │   └── terminal/
│   └── config
├── Daily Notes/               # Daily logs
├── Research/                  # Domain research
│   ├── Watches/
│   ├── Guitars/
│   └── AI Tools/
├── Projects/                  # Active projects
├── Templates/                 # Note templates
└── _brain_metadata/           # Brain CLI metadata
    ├── session_logs/
    └── agent_analytics/
```

## MCP Server Integration

### Setup

```bash
# Install obsidian-mcp-server
npm install -g @cyanheads/obsidian-mcp-server

# Configure in Claude Code MCP settings
# Add to .claude/mcp.json or equivalent
```

### MCP Configuration

```json
{
  "mcpServers": {
    "obsidian": {
      "command": "npx",
      "args": [
        "@cyanheads/obsidian-mcp-server",
        "--vault-path",
        "/Users/josh/brain/workspace/obsidian_vault"
      ]
    }
  }
}
```

### MCP Tools Available

**obsidian-mcp-server** provides:
- `search_vault`: Search across all notes
- `get_note`: Read specific note
- `create_note`: Create new note
- `update_note`: Modify existing note
- `append_to_note`: Add to note
- `list_notes`: List all notes
- `get_tags`: Get all tags
- `search_by_tag`: Find notes by tag

### Python Wrapper

```python
import subprocess
import json

class ObsidianMCP:
    def __init__(self, vault_path: str):
        self.vault_path = vault_path

    def _call_mcp(self, tool: str, params: dict) -> dict:
        """Call MCP server tool"""
        # MCP servers expose tools via JSON-RPC
        # This is a simplified wrapper
        payload = {
            'jsonrpc': '2.0',
            'method': tool,
            'params': params,
            'id': 1
        }

        result = subprocess.run(
            ['npx', '@cyanheads/obsidian-mcp-server',
             '--vault-path', self.vault_path],
            input=json.dumps(payload),
            capture_output=True,
            text=True
        )

        return json.loads(result.stdout)

    def search_vault(self, query: str) -> List[dict]:
        """Search for notes containing query"""
        return self._call_mcp('search_vault', {'query': query})

    def get_note(self, path: str) -> str:
        """Get note content"""
        result = self._call_mcp('get_note', {'path': path})
        return result.get('content', '')

    def create_note(self, path: str, content: str, tags: List[str] = None):
        """Create new note"""
        params = {'path': path, 'content': content}
        if tags:
            params['tags'] = tags

        return self._call_mcp('create_note', params)

    def append_to_note(self, path: str, content: str):
        """Append content to existing note"""
        return self._call_mcp('append_to_note', {
            'path': path,
            'content': content
        })

    def search_by_tag(self, tag: str) -> List[dict]:
        """Find notes with specific tag"""
        return self._call_mcp('search_by_tag', {'tag': tag})
```

## Essential Plugins

### 1. Shell Commands Plugin

Execute shell commands from Obsidian.

**Use Cases**:
- Launch Brain CLI from note
- Run automation scripts
- Trigger agent tasks

**Configuration**:
```yaml
# Shell Commands config
commands:
  - name: "Launch Brain CLI"
    command: "cd ~/brain/brain-cli && brain --workspace {{workspace}}"
    icon: "🧠"

  - name: "Run Research Script"
    command: "bash ~/brain/workspace/scripts/research.sh {{note_title}}"
    icon: "🔍"

  - name: "Ask Claude"
    command: "brain --prompt 'Summarize: {{note_content}}'"
    icon: "🤖"
```

### 2. Obsidian Cron Plugin

Schedule automated tasks.

**Use Cases**:
- Daily research updates
- Weekly review generation
- Auto-sync to git

**Configuration**:
```yaml
# Cron jobs
jobs:
  - name: "Daily Research Update"
    schedule: "0 9 * * *"  # 9 AM daily
    command: "bash ~/brain/workspace/scripts/daily_research_update.sh"

  - name: "Weekly Review"
    schedule: "0 17 * * 5"  # 5 PM Friday
    command: "brain --prompt 'Generate weekly review'"

  - name: "Git Sync"
    schedule: "0 */2 * * *"  # Every 2 hours
    command: "cd ~/brain/workspace/obsidian_vault && git add . && git commit -m 'Auto-sync' && git push"
```

### 3. Dataview Plugin

Query notes like a database.

**Use Cases**:
- Track research papers
- Monitor project status
- Analyze note metadata

**Example Queries**:

List all research papers:
```dataview
TABLE file.cday as "Added", tags as "Tags"
FROM "Research"
WHERE contains(tags, "paper")
SORT file.cday DESC
```

Show pending projects:
```dataview
TASK
FROM "Projects"
WHERE !completed
```

Agent performance summary:
```dataview
TABLE
  agent,
  count(rows) as "Tasks",
  sum(tokens) as "Total Tokens",
  sum(cost) as "Total Cost"
FROM "_brain_metadata/session_logs"
GROUP BY agent
```

### 4. Terminal Plugin

Embed terminal in Obsidian.

**Use Cases**:
- Run Brain CLI without leaving Obsidian
- Execute scripts inline
- Monitor long-running tasks

## Note Templates

### Research Note Template

```markdown
---
type: research
domain: {{domain}}
created: {{date}}
tags: [research, {{domain}}]
status: active
---

# {{title}}

## Context
What prompted this research?

## Questions
- [ ] Main question 1
- [ ] Main question 2

## Findings
### Source 1
**Source**: [Link]
**Key Points**:
-

### Source 2
**Source**: [Link]
**Key Points**:
-

## Synthesis
Key insights from all sources:

## Next Steps
- [ ] Action 1
- [ ] Action 2

## Brain CLI Commands Used
```bash
brain --workspace {{domain}}
/compare claude gemini "{{question}}"
```

## Related Notes
- [[Note 1]]
- [[Note 2]]
```

### Project Note Template

```markdown
---
type: project
status: active
started: {{date}}
tags: [project]
agent: claude
---

# {{title}}

## Goal
What we're building and why

## Requirements
- Requirement 1
- Requirement 2

## Architecture
High-level design

## Progress
- [x] Done task
- [ ] Todo task

## Decisions
### Decision 1
**Date**: {{date}}
**Choice**: What we chose
**Rationale**: Why
**Agents Consulted**: claude, gemini

## Issues
### Issue 1
**Description**:
**Solution**:

## Related
- [[Design Doc]]
- [[Research]]
```

### Daily Note Template

```markdown
---
type: daily
date: {{date:YYYY-MM-DD}}
tags: [daily]
---

# {{date:dddd, MMMM DD, YYYY}}

## 🎯 Focus
Today's main objectives

## 🧠 Brain CLI Sessions
### Session 1: {{workspace}}
**Agent**: claude
**Task**:
**Outcome**:
**Cost**: $X.XX

## 📝 Notes
-

## ✅ Completed
- [x] Task 1

## 📚 Learned
-

## 🔗 Links
- [[Related Note]]
```

## Integration with Brain CLI

### Session Logging

Automatically log Brain CLI sessions to Obsidian:

```python
class ObsidianLogger:
    def __init__(self, vault_path: str):
        self.obsidian = ObsidianMCP(vault_path)

    def log_session(self, session: Session):
        """Log session to daily note"""
        today = datetime.now().strftime('%Y-%m-%d')
        daily_note_path = f"Daily Notes/{today}.md"

        # Create daily note if doesn't exist
        if not self.obsidian.note_exists(daily_note_path):
            template = self._load_template('daily_note')
            self.obsidian.create_note(daily_note_path, template)

        # Append session
        session_log = f"""
## 🧠 Brain CLI Session - {datetime.now().strftime('%H:%M')}
**Workspace**: {session.workspace}
**Agent**: {session.primary_agent}
**Turns**: {len(session.conversation)}
**Tokens**: {session.total_tokens}
**Cost**: ${session.total_cost:.4f}

### Key Points
{self._extract_key_points(session)}
"""

        self.obsidian.append_to_note(daily_note_path, session_log)

    def log_research_finding(self, workspace: str, finding: dict):
        """Create research note from finding"""
        note_path = f"Research/{workspace}/{finding['title']}.md"

        template = self._load_template('research_note')
        content = template.format(**finding)

        self.obsidian.create_note(note_path, content, tags=finding.get('tags', []))

    def _extract_key_points(self, session: Session) -> str:
        # Use agent to summarize session
        summary_prompt = f"Summarize key points from this session:\n{session.conversation}"
        # Call agent...
        return "- Point 1\n- Point 2"

    def _load_template(self, template_name: str) -> str:
        template_path = f"~/brain/workspace/obsidian_vault/Templates/{template_name}.md"
        with open(os.path.expanduser(template_path)) as f:
            return f.read()
```

### Hook Integration

Log to Obsidian via hooks:

```python
def obsidian_logging_hook(context: HookContext):
    """Log session to Obsidian"""
    if context.hook_type == HookType.SESSION_END:
        vault_path = '~/brain/workspace/obsidian_vault'
        logger = ObsidianLogger(vault_path)
        logger.log_session(context.session)

hook_manager.register(HookType.SESSION_END, obsidian_logging_hook)
```

## Git Sync (Free Obsidian Sync Alternative)

### Setup

```bash
cd ~/brain/workspace/obsidian_vault
git init
git remote add origin <your-repo>

# Create .gitignore
cat > .gitignore << EOF
.obsidian/workspace*
.obsidian/cache
.trash/
EOF

# Initial commit
git add .
git commit -m "Initial vault"
git push -u origin main
```

### Auto-sync Script

```bash
#!/bin/bash
# ~/brain/workspace/scripts/obsidian_sync.sh

VAULT_DIR="$HOME/brain/workspace/obsidian_vault"
cd "$VAULT_DIR" || exit 1

# Check for changes
if [[ -z $(git status -s) ]]; then
  echo "No changes to sync"
  exit 0
fi

# Commit and push
git add .
git commit -m "Auto-sync: $(date '+%Y-%m-%d %H:%M')"
git push origin main

echo "✅ Synced to remote"
```

### Cron Job

```bash
# Run every 2 hours
0 */2 * * * bash ~/brain/workspace/scripts/obsidian_sync.sh >> ~/brain/workspace/.logs/obsidian_sync.log 2>&1
```

## Slash Command Integration

Add Obsidian commands to Brain CLI:

```python
def handle_obsidian_command(cmd: str, args: List[str], console: Console):
    """Handle /obsidian commands"""
    vault_path = '~/brain/workspace/obsidian_vault'
    obsidian = ObsidianMCP(vault_path)

    if cmd == 'search':
        query = ' '.join(args)
        results = obsidian.search_vault(query)
        console.print(f"\n📝 Found {len(results)} notes:")
        for r in results:
            console.print(f"  - {r['path']}")

    elif cmd == 'note':
        if not args:
            console.print("[red]Usage: /obsidian note <path>[/red]")
            return
        path = args[0]
        content = obsidian.get_note(path)
        console.print(Markdown(content))

    elif cmd == 'create':
        if len(args) < 2:
            console.print("[red]Usage: /obsidian create <path> <content>[/red]")
            return
        path = args[0]
        content = ' '.join(args[1:])
        obsidian.create_note(path, content)
        console.print(f"✅ Created {path}")

# In REPL:
# > /obsidian search "quantum computing"
# > /obsidian note "Research/Watches/Rolex.md"
# > /obsidian create "Research/New Topic.md" "# New Topic\n\nContent..."
```

## Dataview Queries for Agent Analytics

Track agent performance in Obsidian:

```dataview
TABLE
  agent as "Agent",
  count(rows) as "Sessions",
  sum(tokens) as "Tokens",
  sum(cost) as "Cost ($)",
  round(avg(quality_rating), 2) as "Avg Quality"
FROM "_brain_metadata/session_logs"
WHERE date >= date(today) - dur(7 days)
GROUP BY agent
SORT cost DESC
```

Research progress tracking:

```dataview
TABLE
  status,
  length(findings) as "Findings",
  file.cday as "Started"
FROM "Research"
WHERE type = "research"
SORT file.cday DESC
LIMIT 10
```

## Advantages

**vs Notion**:
- ✅ FREE (Notion = $15/month)
- ✅ Local-first (your data)
- ✅ Git versioning
- ✅ Plain markdown (portable)
- ✅ Faster (no cloud latency)
- ✅ Grep-able (terminal-native)
- ✅ Plugin ecosystem
- ✅ MCP server integration

**vs Plain Markdown**:
- ✅ Graph view (connection visualization)
- ✅ Backlinks (automatic connections)
- ✅ Tags and metadata
- ✅ Dataview queries
- ✅ Plugin ecosystem
- ✅ Beautiful UI (when you want it)

## Summary

**Obsidian as Second Brain**:
- ✅ MCP server for AI integration
- ✅ Shell Commands for CLI integration
- ✅ Cron for automation
- ✅ Dataview for analytics
- ✅ Git for free sync
- ✅ Terminal plugin for inline CLI

**Next**: See `06-AUTOMATION-WORKFLOWS.md` for the 11 automation workflows.
