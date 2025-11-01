# Automation Workflows

## Overview

11 automation workflows for CLI-first research and project management. All implemented using bash scripts, git hooks, cron jobs, and Make/Just task runners - **NOT n8n** (scope creep).

**Key Principle**: Terminal-native automation that integrates with Brain CLI and agents.

## 1. Coding Project Tracker with Agent Validation

### Purpose
Track active coding projects, validate with agents, sync to Obsidian.

### Workflow
1. Git hook detects new project (new repo cloned or created)
2. Brain CLI analyzes project structure and tech stack
3. Agent generates project summary and recommendations
4. Creates Obsidian note with project metadata
5. Daily checks for uncommitted changes and suggests commits

### Implementation

**Git Hook** (`~/.git/hooks/post-checkout`):
```bash
#!/bin/bash
# Trigger after git clone or checkout

PROJECT_DIR=$(pwd)
PROJECT_NAME=$(basename "$PROJECT_DIR")

# Check if tracked
if [[ ! -f "$HOME/brain/workspace/.tracked_projects/$PROJECT_NAME" ]]; then
  echo "🧠 New project detected: $PROJECT_NAME"
  echo "Analyzing with Brain CLI..."

  # Call Brain CLI
  brain --prompt "Analyze this new project at $PROJECT_DIR and create an Obsidian note"

  # Mark as tracked
  mkdir -p "$HOME/brain/workspace/.tracked_projects"
  echo "$PROJECT_DIR" > "$HOME/brain/workspace/.tracked_projects/$PROJECT_NAME"
fi
```

**Daily Check Script** (`scripts/project_check.sh`):
```bash
#!/bin/bash
# Check all tracked projects for uncommitted changes

TRACKED_DIR="$HOME/brain/workspace/.tracked_projects"

for project_file in "$TRACKED_DIR"/*; do
  PROJECT_NAME=$(basename "$project_file")
  PROJECT_DIR=$(cat "$project_file")

  cd "$PROJECT_DIR" || continue

  # Check for uncommitted changes
  if [[ -n $(git status -s) ]]; then
    echo "⚠️ $PROJECT_NAME has uncommitted changes"

    # Ask agent for commit message suggestion
    brain --workspace coding-projects --prompt \
      "Generate a commit message for these changes in $PROJECT_NAME: $(git status -s | head -10)"
  fi
done
```

**Cron Job**:
```bash
# Run daily at 5 PM
0 17 * * * bash ~/brain/workspace/scripts/project_check.sh
```

## 2. Watch Monitor (Reddit/eBay Notifications)

### Purpose
Monitor Reddit and eBay for watch deals, notify when matches found.

### Workflow
1. Hourly scrape: r/Watchexchange, eBay listings
2. Filter by criteria (brands, price range, condition)
3. Agent analyzes if deal is legit
4. Creates Obsidian note + sends notification
5. Tracks price history

### Implementation

**Monitor Script** (`scripts/watch_monitor.sh`):
```bash
#!/bin/bash

WORKSPACE="watches"
BRANDS=("Rolex" "Omega" "Seiko" "Grand Seiko")
MAX_PRICE=10000

echo "🔍 Monitoring watch listings..."

# Reddit
for brand in "${BRANDS[@]}"; do
  echo "Checking r/Watchexchange for $brand..."

  # Use brain CLI with agent to scrape and analyze
  brain --workspace "$WORKSPACE" --prompt \
    "Search r/Watchexchange for $brand watches under \$$MAX_PRICE. \
     Analyze if any are good deals. Create Obsidian notes for matches."
done

# eBay (using eBay API or scraping)
for brand in "${BRANDS[@]}"; do
  echo "Checking eBay for $brand..."

  # Call eBay API or use agent with browser automation
  brain --workspace "$WORKSPACE" --prompt \
    "Search eBay for $brand watches under \$$MAX_PRICE listed in last 24h. \
     Filter for good deals and create Obsidian notes."
done

echo "✅ Watch monitoring complete"
```

**Notification** (via macOS notification or Slack):
```bash
# In script:
if [[ $matches_found -gt 0 ]]; then
  osascript -e "display notification \"Found $matches_found watch deals\" with title \"Watch Monitor\""

  # Or Slack
  # curl -X POST -H 'Content-type: application/json' \
  #   --data "{\"text\":\"Found $matches_found watch deals\"}" \
  #   "$SLACK_WEBHOOK_URL"
fi
```

**Cron Job**:
```bash
# Run every hour
0 * * * * bash ~/brain/workspace/scripts/watch_monitor.sh
```

## 3. Todo Integration with Research Findings

### Purpose
Automatically create todos from research findings and agent suggestions.

### Workflow
1. Agent identifies action items during research session
2. Extracts todo items from conversation
3. Creates tasks in Obsidian (or todo.txt, Todoist, etc.)
4. Links back to research note

### Implementation

**Hook** (after session ends):
```python
def todo_extraction_hook(context: HookContext):
    """Extract todos from session"""
    if context.hook_type != HookType.SESSION_END:
        return

    session = context.session

    # Use agent to extract action items
    todos_prompt = f"""
    Analyze this session and extract actionable todos:
    {session.conversation}

    Format:
    - [ ] Todo 1
    - [ ] Todo 2
    """

    todos = extract_todos_with_agent(todos_prompt)

    if todos:
        # Write to Obsidian
        obsidian = ObsidianMCP(vault_path)
        obsidian.append_to_note(
            f"Projects/{session.workspace}/Todos.md",
            f"\n## From Session {session.id}\n{todos}"
        )

hook_manager.register(HookType.SESSION_END, todo_extraction_hook)
```

**Integration with todo.txt**:
```bash
# Alternatively, use todo.txt format
TODO_FILE="$HOME/brain/workspace/todo.txt"

brain --workspace watches --prompt "Extract todos from today's research" \
  | grep "^- \[ \]" \
  | sed 's/^- \[ \] //' \
  >> "$TODO_FILE"
```

## 4. Self-Updating Research Projects

### Purpose
Daily monitoring and updating of ongoing research topics.

### Workflow
1. Each research project has monitoring config
2. Daily: agents fetch new information
3. Summarize changes and updates
4. Append to research note
5. Notify if significant developments

### Implementation

**Research Config** (`workspaces/watches/.research_config.yaml`):
```yaml
research_topics:
  - name: "Rolex Market Trends"
    sources:
      - "r/rolex"
      - "chrono24.com/rolex"
      - "hodinkee.com"
    keywords: ["market", "price", "trend", "analysis"]
    update_frequency: "daily"

  - name: "Grand Seiko Releases"
    sources:
      - "r/GrandSeiko"
      - "grand-seiko.com/us-en/news"
    keywords: ["release", "new model", "announcement"]
    update_frequency: "weekly"
```

**Update Script** (`scripts/research_update.sh`):
```bash
#!/bin/bash

WORKSPACE="$1"
CONFIG_FILE="$HOME/brain/workspace/workspaces/$WORKSPACE/.research_config.yaml"

if [[ ! -f "$CONFIG_FILE" ]]; then
  echo "No research config for $WORKSPACE"
  exit 0
fi

echo "🔄 Updating research for $WORKSPACE..."

# Use agent to fetch updates
brain --workspace "$WORKSPACE" --prompt \
  "Check for updates on all research topics in config. \
   Summarize any significant changes and append to respective Obsidian notes."

echo "✅ Research updated"
```

**Cron Job**:
```bash
# Run daily at 9 AM
0 9 * * * bash ~/brain/workspace/scripts/research_update.sh watches
0 9 * * * bash ~/brain/workspace/scripts/research_update.sh guitars
```

## 5. GitHub Project Launcher

### Purpose
Quick project initialization with agent-generated structure.

### Workflow
1. Command: `brain-new-project <name> <type>`
2. Agent generates appropriate project structure
3. Creates GitHub repo
4. Initializes with README, .gitignore, etc.
5. Creates Obsidian project note
6. Opens in editor (Cursor/VS Code)

### Implementation

**Script** (`scripts/new_project.sh`):
```bash
#!/bin/bash

PROJECT_NAME="$1"
PROJECT_TYPE="$2"  # python, node, rust, etc.

if [[ -z "$PROJECT_NAME" || -z "$PROJECT_TYPE" ]]; then
  echo "Usage: brain-new-project <name> <type>"
  exit 1
fi

echo "🚀 Creating $PROJECT_TYPE project: $PROJECT_NAME"

# Create directory
PROJECT_DIR="$HOME/Projects/$PROJECT_NAME"
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR" || exit 1

# Use agent to generate structure
brain --workspace coding-projects --prompt \
  "Generate a complete $PROJECT_TYPE project structure for '$PROJECT_NAME'. \
   Include: README.md, .gitignore, basic files, and setup instructions."

# Initialize git
git init
git add .
git commit -m "Initial commit"

# Create GitHub repo
gh repo create "$PROJECT_NAME" --public --source=. --push

# Create Obsidian note
brain --workspace coding-projects --prompt \
  "Create an Obsidian project note for $PROJECT_NAME at $PROJECT_DIR"

# Open in editor
cursor "$PROJECT_DIR"  # or code "$PROJECT_DIR"

echo "✅ Project created and opened"
```

**Alias**:
```bash
# Add to .bashrc / .zshrc
alias brain-new-project='bash ~/brain/workspace/scripts/new_project.sh'
```

## 6. Shopping List Integration

### Purpose
Manage shopping lists with agent assistance (price comparison, alternatives).

### Workflow
1. Add items via Brain CLI
2. Agent finds best prices across sites
3. Suggests alternatives and reviews
4. Generates purchase recommendations
5. Tracks when items go on sale

### Implementation

**Add Item**:
```bash
brain --workspace shopping --prompt "Add to shopping list: Shure SM7B microphone"
```

**Agent processes**:
```python
def handle_shopping_add(item: str):
    # Search for item
    results = {
        'amazon': search_amazon(item),
        'sweetwater': search_sweetwater(item),
        'ebay': search_ebay(item)
    }

    # Compare prices
    best_price = min(results, key=lambda x: x['price'])

    # Create shopping note
    note_content = f"""
# {item}

## Best Price
{best_price['source']}: ${best_price['price']}
Link: {best_price['url']}

## Alternatives
{generate_alternatives(item)}

## Reviews Summary
{summarize_reviews(item)}

## Price Alert
Set alert for: ${best_price['price'] * 0.9}
"""

    obsidian.create_note(f"Shopping/{item}.md", note_content)

    # Set price monitoring
    add_to_price_monitor(item, best_price['price'] * 0.9)
```

**Price Monitor** (daily):
```bash
# Check if tracked items dropped in price
brain --workspace shopping --prompt "Check all shopping list items for price drops"
```

## 7. Paper Pipeline (arXiv → Summary → Reading Queue)

### Purpose
Monitor arXiv for relevant papers, summarize, add to reading queue.

### Workflow
1. Daily check arXiv for keywords
2. Agent summarizes abstract and key findings
3. Rates relevance (1-10)
4. High-rated papers added to reading queue
5. Creates Obsidian note with summary

### Implementation

**Monitor Script** (`scripts/paper_pipeline.sh`):
```bash
#!/bin/bash

KEYWORDS=("reinforcement learning" "large language models" "agent architectures")

echo "📚 Checking arXiv for new papers..."

for keyword in "${KEYWORDS[@]}"; do
  echo "Searching for: $keyword"

  brain --workspace ai-research --prompt \
    "Search arXiv for papers about '$keyword' published in last 7 days. \
     For each relevant paper:
     1. Summarize abstract
     2. Extract key findings
     3. Rate relevance (1-10)
     4. If rating >= 7, create Obsidian note in Research/Papers/
     5. Add to reading queue if rating >= 8"
done

echo "✅ Paper pipeline complete"
```

**Cron Job**:
```bash
# Run daily at 10 AM
0 10 * * * bash ~/brain/workspace/scripts/paper_pipeline.sh
```

**Reading Queue** (`workspaces/ai-research/Reading_Queue.md`):
```markdown
---
type: reading_queue
updated: {{date}}
---

# Reading Queue

## High Priority (Rating >= 8)
- [ ] [Paper 1] - Rating: 9
- [ ] [Paper 2] - Rating: 8

## Medium Priority (Rating 7)
- [ ] [Paper 3] - Rating: 7

## Completed
- [x] [Previous Paper] - Read: 2025-10-28
```

## 8. Weekly Review Automation

### Purpose
Generate weekly summary of all activities, decisions, and learnings.

### Workflow
1. Friday 5 PM: Collect week's data
2. Agent analyzes:
   - All Brain CLI sessions
   - Obsidian notes created/updated
   - Git commits
   - Research findings
3. Generates weekly review report
4. Creates Obsidian note

### Implementation

**Script** (`scripts/weekly_review.sh`):
```bash
#!/bin/bash

WEEK_START=$(date -v-7d '+%Y-%m-%d')
WEEK_END=$(date '+%Y-%m-%d')

echo "📊 Generating weekly review: $WEEK_START to $WEEK_END"

brain --prompt \
  "Generate a comprehensive weekly review covering:
   1. All Brain CLI sessions this week
   2. Obsidian notes created/updated
   3. Git commits across all projects
   4. Research findings and insights
   5. Key decisions made
   6. Learnings and next steps

   Create detailed Obsidian note: 'Weekly Reviews/$WEEK_END.md'"

echo "✅ Weekly review generated"

# Open in Obsidian
open "obsidian://open?vault=brain&file=Weekly%20Reviews/$WEEK_END.md"
```

**Cron Job**:
```bash
# Friday 5 PM
0 17 * * 5 bash ~/brain/workspace/scripts/weekly_review.sh
```

## 9. Hackathon Ideation Workflow

### Purpose
Generate and evaluate hackathon project ideas with agents.

### Workflow
1. Command: `brain-hackathon <theme>`
2. Agents brainstorm ideas (compare multiple agents)
3. Evaluate feasibility, originality, impact
4. Generate implementation plan
5. Create project structure if approved

### Implementation

**Script** (`scripts/hackathon_ideation.sh`):
```bash
#!/bin/bash

THEME="$1"

if [[ -z "$THEME" ]]; then
  echo "Usage: brain-hackathon <theme>"
  exit 1
fi

echo "💡 Brainstorming hackathon ideas for: $THEME"

# Use compare mode to get ideas from multiple agents
brain --workspace hackathons --prompt \
  "/compare Brainstorm 5 hackathon project ideas for theme: $THEME. \
   For each idea provide:
   1. Name and tagline
   2. Core concept
   3. Technical approach
   4. Feasibility (1-10)
   5. Originality (1-10)
   6. Impact (1-10)"

echo ""
echo "Review the ideas above. To implement one:"
echo "  brain-implement-idea <idea_name>"
```

**Alias**:
```bash
alias brain-hackathon='bash ~/brain/workspace/scripts/hackathon_ideation.sh'
```

## 10. AI Tool Discovery and Documentation

### Purpose
Monitor new AI tools, agents, libraries; document and categorize.

### Workflow
1. Monitor sources: GitHub trending, Hacker News, Reddit
2. Agent evaluates new tools
3. Creates documentation note with:
   - Overview and use cases
   - Installation and setup
   - Integration potential with Brain CLI
4. Categorizes and tags

### Implementation

**Monitor Script** (`scripts/ai_tool_discovery.sh`):
```bash
#!/bin/bash

echo "🔍 Discovering new AI tools..."

brain --workspace ai-tooling --prompt \
  "Monitor these sources for new AI tools, agents, and libraries:
   - GitHub Trending (AI/ML section)
   - Hacker News front page
   - r/MachineLearning, r/LocalLLaMA

   For each interesting tool found:
   1. Evaluate potential and use cases
   2. Check integration possibility with Brain CLI
   3. Create Obsidian note: Research/AI Tools/{tool_name}.md
   4. Tag appropriately (agent, cli, integration, etc.)"

echo "✅ AI tool discovery complete"
```

**Cron Job**:
```bash
# Run twice weekly: Monday and Thursday at 11 AM
0 11 * * 1,4 bash ~/brain/workspace/scripts/ai_tool_discovery.sh
```

## 11. Communication Generator (Slack/Email/SMS)

### Purpose
Generate various communication types with agent assistance.

### Workflow
1. Command: `brain-comm <type> <context>`
2. Agent generates draft (formal email, casual Slack, concise SMS)
3. User reviews and edits
4. Optional: Send directly or copy to clipboard

### Implementation

**Script** (`scripts/communication_generator.sh`):
```bash
#!/bin/bash

TYPE="$1"  # email, slack, sms
CONTEXT="$2"

if [[ -z "$TYPE" || -z "$CONTEXT" ]]; then
  echo "Usage: brain-comm <type> <context>"
  echo "Types: email, slack, sms"
  exit 1
fi

echo "✍️ Generating $TYPE message..."

brain --prompt \
  "Generate a $TYPE message for this context: $CONTEXT

   Format appropriately for the medium:
   - Email: formal structure with subject, greeting, body, signature
   - Slack: casual, concise, emoji-friendly
   - SMS: ultra-concise, under 160 characters

   After generating, ask if I want to:
   1. Copy to clipboard
   2. Edit further
   3. Send directly (if integration available)"

# Copy to clipboard
# pbcopy on macOS, xclip on Linux
```

**Alias**:
```bash
alias brain-comm='bash ~/brain/workspace/scripts/communication_generator.sh'
```

**Usage**:
```bash
brain-comm email "Following up on the project proposal from last week"
brain-comm slack "Announcing the new feature launch to the team"
brain-comm sms "Meeting reminder for tomorrow at 2pm"
```

## Automation Architecture

**Key Technologies**:
- **Bash**: All workflow scripts
- **Git Hooks**: Project detection and tracking
- **Cron**: Scheduled automation
- **Make/Just**: Task runner for complex workflows
- **Brain CLI**: Agent coordination
- **Obsidian**: Knowledge capture

**Workflow Pattern**:
```
Trigger (cron/hook/command)
    ↓
Bash Script
    ↓
Brain CLI (agent coordination)
    ↓
Agent(s) Execute
    ↓
Output to Obsidian
    ↓
Notification (optional)
```

## Summary

**11 Workflows Implemented**:
1. ✅ Coding project tracker with agent validation
2. ✅ Watch monitor (Reddit/eBay notifications)
3. ✅ Todo integration with research findings
4. ✅ Self-updating research projects
5. ✅ GitHub project launcher
6. ✅ Shopping list integration
7. ✅ Paper pipeline (arXiv → summary → queue)
8. ✅ Weekly review automation
9. ✅ Hackathon ideation workflow
10. ✅ AI tool discovery and documentation
11. ✅ Communication generator

**Phase 1**: Workflows 1, 3, 8 (core productivity)
**Phase 2**: Workflows 2, 4, 5, 6, 7, 9, 10, 11 (comprehensive automation)

## Next Document

See `07-CURSOR-INTEGRATION.md` for terminal usage and future extension plans.
