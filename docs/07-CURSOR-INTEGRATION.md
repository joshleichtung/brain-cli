# Cursor Integration

## Overview

Cursor 2.0 introduces a multi-prompt interface and enhanced terminal integration, making it an excellent environment for Brain CLI. We'll support Brain CLI usage from Cursor's terminal, with a future path toward a native Cursor extension.

**Philosophy**: Terminal-first, extension-optional

## Current State: Cursor 2.0 Features

### Multi-Prompt Interface

Cursor 2.0 allows:
- Multiple chat threads in sidebar
- Context-aware prompts across files
- Terminal command suggestions
- Agent integration

**How Brain CLI Benefits**:
- Run `brain` from Cursor terminal
- Agent responses appear in terminal
- Copy responses to Cursor chat for refinement
- Seamless workflow between CLI and IDE

### Terminal Integration

Cursor's terminal:
- Runs alongside editor
- Supports all CLI tools
- Can be split and organized
- Command history and autocomplete

**Brain CLI Integration**:
- Launch: `brain` in Cursor terminal
- Interactive REPL mode within IDE
- Agent coordination without leaving Cursor
- Results immediately available for code editing

## Phase 1: Terminal Usage (Weeks 1-2)

### Setup

No special setup needed - Brain CLI works in any terminal:

```bash
# In Cursor terminal
cd ~/Projects/my-project
brain --workspace coding-projects
```

### Workflow

**Scenario 1: Code Review**
```
1. Open project in Cursor
2. In terminal: brain
3. > Analyze the authentication system architecture
4. Read agent response
5. Use insights to refactor in Cursor editor
```

**Scenario 2: Multi-Agent Comparison**
```
1. In terminal: brain
2. > /compare Explain this API design pattern
3. Review responses from Claude, Gemini, Codex
4. Copy best explanation to Cursor chat
5. Ask Cursor AI to implement based on that explanation
```

**Scenario 3: Research While Coding**
```
1. Coding in Cursor editor
2. Split terminal alongside
3. brain --workspace watches
4. Research watches while coding
5. No context switching between apps
```

### Optimizations

**Terminal Configuration** (`.zshrc` / `.bashrc`):
```bash
# Brain CLI aliases for Cursor workflow
alias b='brain'
alias bw='brain --workspace'
alias bp='brain --prompt'

# Quick workspace switching
alias b-code='brain --workspace coding-projects'
alias b-watches='brain --workspace watches'
alias b-guitars='brain --workspace guitars'

# Integration with Cursor
export CURSOR_BRAIN_INTEGRATION=1

# Function to open Obsidian note in Cursor
cursor-note() {
  note_path="$HOME/brain/workspace/obsidian_vault/$1"
  cursor "$note_path"
}
```

**Keybindings** (Cursor terminal):
- `Cmd+T`: New terminal → auto-launch brain
- `Cmd+Shift+T`: Split terminal → brain in split
- Custom terminal profiles for different workspaces

## Phase 2: Enhanced Integration (Weeks 3-6)

### Shell Integration

**Shell Commands Plugin** (Cursor):

Create custom commands that invoke Brain CLI:

```json
// Cursor settings.json
{
  "terminal.integrated.shellIntegration.enabled": true,
  "brain.commands": {
    "analyze": {
      "command": "brain --prompt 'Analyze: ${selectedText}'",
      "description": "Analyze selected code with Brain CLI"
    },
    "refactor": {
      "command": "brain --prompt 'Suggest refactoring: ${filePath}'",
      "description": "Get refactoring suggestions"
    },
    "explain": {
      "command": "brain --prompt 'Explain: ${selectedText}'",
      "description": "Explain code with multiple agents"
    }
  }
}
```

### Context Sharing

**Bidirectional Context**:

Cursor → Brain CLI:
```bash
# Pass current file to Brain
brain --prompt "Review this file" --context "$(cursor --get-active-file)"
```

Brain CLI → Cursor:
```bash
# Send Brain response to Cursor chat
brain --prompt "Analyze auth system" | cursor --append-to-chat
```

### Workflow Scripts

**Script**: Auto-launch Brain in Project
```bash
#!/bin/bash
# .cursor/brain-auto-launch.sh

# Detect project workspace
if [[ -f ".brain-workspace" ]]; then
  WORKSPACE=$(cat ".brain-workspace")
  brain --workspace "$WORKSPACE"
else
  # Ask user to set workspace
  echo "No .brain-workspace file found. Set workspace:"
  read -p "Workspace name: " WORKSPACE
  echo "$WORKSPACE" > ".brain-workspace"
  brain --workspace "$WORKSPACE"
fi
```

**Trigger**: Add to Cursor workspace settings
```json
{
  "terminal.integrated.cwd": "${workspaceFolder}",
  "terminal.integrated.shellArgs.osx": ["-c", "bash .cursor/brain-auto-launch.sh"]
}
```

## Phase 3: Native Extension (Weeks 7-12, Optional)

### Extension Architecture

**Cursor Extension** (VS Code-compatible):

```
brain-cursor-extension/
├── package.json
├── src/
│   ├── extension.ts          # Main extension entry
│   ├── brainClient.ts        # Brain CLI communication
│   ├── chatProvider.ts       # Cursor chat integration
│   ├── terminalProvider.ts   # Terminal management
│   └── statusBar.ts          # Status bar indicator
└── README.md
```

### Features

**1. Sidebar Panel**
- Brain CLI chat interface
- Workspace selector
- Agent switcher
- Session history

**2. Status Bar**
- Active agent indicator
- Token usage
- Quick actions (compare, switch)

**3. Context Menu**
- Right-click: "Ask Brain CLI"
- Right-click: "Compare Agents on Selection"
- Right-click: "Add to Research Notes"

**4. Commands**
- `Brain: Launch Interactive Session`
- `Brain: Compare Agents`
- `Brain: Switch Workspace`
- `Brain: Open Obsidian Note`

### Implementation Example

**Extension Entry Point** (`extension.ts`):
```typescript
import * as vscode from 'vscode';
import { BrainClient } from './brainClient';
import { ChatProvider } from './chatProvider';

export function activate(context: vscode.ExtensionContext) {
  const brainClient = new BrainClient();
  const chatProvider = new ChatProvider(brainClient);

  // Register chat provider
  context.subscriptions.push(
    vscode.window.registerWebviewViewProvider(
      'brain-chat',
      chatProvider
    )
  );

  // Register commands
  context.subscriptions.push(
    vscode.commands.registerCommand('brain.launch', () => {
      brainClient.launchInteractive();
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('brain.compare', async () => {
      const editor = vscode.window.activeTextEditor;
      if (!editor) return;

      const selection = editor.document.getText(editor.selection);
      const result = await brainClient.compare(selection);

      chatProvider.showComparison(result);
    })
  );

  // Status bar
  const statusBar = vscode.window.createStatusBarItem(
    vscode.StatusBarAlignment.Right,
    100
  );
  statusBar.text = '$(brain) Brain CLI';
  statusBar.command = 'brain.launch';
  statusBar.show();
  context.subscriptions.push(statusBar);
}
```

**Brain Client** (`brainClient.ts`):
```typescript
import { spawn } from 'child_process';

export class BrainClient {
  private process: any;
  private workspace: string;

  async launchInteractive(): Promise<void> {
    // Launch brain CLI as subprocess
    this.process = spawn('brain', ['--workspace', this.workspace], {
      cwd: vscode.workspace.rootPath
    });

    // Create terminal
    const terminal = vscode.window.createTerminal('Brain CLI');
    terminal.show();

    // Pipe to terminal
    this.process.stdout.on('data', (data: Buffer) => {
      terminal.sendText(data.toString(), false);
    });
  }

  async compare(text: string): Promise<any> {
    // Call brain CLI in headless mode
    return new Promise((resolve, reject) => {
      const proc = spawn('brain', [
        '--prompt',
        `/compare Explain: ${text}`
      ]);

      let output = '';
      proc.stdout.on('data', (data: Buffer) => {
        output += data.toString();
      });

      proc.on('close', (code: number) => {
        if (code === 0) {
          resolve(JSON.parse(output));
        } else {
          reject(new Error('Brain CLI failed'));
        }
      });
    });
  }

  async switchWorkspace(workspace: string): Promise<void> {
    this.workspace = workspace;
    // Send /workspace command to running process
    if (this.process) {
      this.process.stdin.write(`/workspace ${workspace}\n`);
    }
  }
}
```

### UI Mockup

**Sidebar Panel**:
```
┌─────────────────────────────┐
│ 🧠 Brain CLI                │
├─────────────────────────────┤
│ Workspace: coding-projects  │
│ Agent: Claude ▼             │
├─────────────────────────────┤
│ > Analyze auth system       │
│                             │
│ [Agent Response...]         │
│                             │
│ > /compare Explain JWT      │
│                             │
│ 📊 Comparison:              │
│ ├─ Claude: [...]            │
│ ├─ Gemini: [...]            │
│ └─ Codex: [...]             │
├─────────────────────────────┤
│ [Quick Actions]             │
│ [Compare] [Switch] [Save]   │
└─────────────────────────────┘
```

**Status Bar**:
```
🧠 Brain CLI | Claude | Tokens: 12.5K | $0.0375 | ⭐
```

## Integration Challenges

### 1. Terminal vs GUI

**Challenge**: Brain CLI is terminal-based, Cursor is GUI

**Solutions**:
- **Phase 1**: Keep terminal-based (works perfectly)
- **Phase 2**: Add shell integration for context sharing
- **Phase 3**: Native extension wraps CLI in GUI panel

**Recommendation**: Start with terminal (Phase 1), only build extension if strong user demand.

### 2. Context Synchronization

**Challenge**: Keep Cursor and Brain CLI context in sync

**Solutions**:
- Share workspace directory
- Use Obsidian as common knowledge base
- Brain CLI exports context API for extension

### 3. Multi-Agent UI

**Challenge**: Displaying multiple agent responses in GUI

**Solutions**:
- Tabs for each agent
- Side-by-side comparison view
- Collapsible sections with ratings

## Comparison: Terminal vs Extension

| Feature | Terminal (Phase 1) | Extension (Phase 3) |
|---------|-------------------|---------------------|
| Complexity | Low | High |
| Setup | None | Install extension |
| Integration | Shell commands | Deep VS Code integration |
| Context Sharing | Manual | Automatic |
| UI | Text-based | GUI panels |
| Maintenance | Low | High |
| Flexibility | High | Medium |
| Learning Curve | Low (CLI users) | Low (GUI users) |

**Recommendation**: Start with terminal-based (Phase 1). Build extension only if:
- User demand is strong
- Terminal workflow proves limiting
- Complex UI features are needed (e.g., multi-agent visualization)

## Current Best Practice (Phase 1-2)

**Optimal Cursor Workflow**:

1. **Split Terminal Layout**
   ```
   ┌────────────────┬────────────┐
   │                │            │
   │  Editor        │  Files     │
   │                │            │
   ├────────────────┴────────────┤
   │  Terminal: Brain CLI        │
   └─────────────────────────────┘
   ```

2. **Workspace Configuration** (`.cursor/settings.json`)
   ```json
   {
     "brain.autoLaunch": true,
     "brain.defaultWorkspace": "coding-projects",
     "terminal.integrated.defaultProfile.osx": "brain-shell"
   }
   ```

3. **Keyboard Shortcuts**
   - `Cmd+B`: Launch Brain CLI
   - `Cmd+Shift+B`: Compare agents on selection
   - `Cmd+Alt+B`: Switch workspace

4. **Shell Functions** (`.zshrc`)
   ```bash
   # Quick Brain commands from Cursor terminal
   ba() { brain --prompt "Analyze: $(cat $1)" }
   br() { brain --prompt "Refactor: $(cat $1)" }
   be() { brain --prompt "Explain: $*" }
   ```

## Future Possibilities

**Cursor AI + Brain CLI Coordination**:
- Use Cursor AI for quick edits
- Use Brain CLI for complex analysis
- Compare Cursor AI vs Brain CLI agents
- Best-of-both: Cursor for code gen, Brain for architecture

**Multi-Agent Workflow**:
```
1. Cursor AI: Generate initial code
2. Brain CLI: Review with Claude
3. Brain CLI: Get Gemini alternative
4. Brain CLI: Codex optimization
5. Cursor AI: Implement chosen approach
```

## Summary

**Phase 1 (Weeks 1-2)**: ✅ Use Brain CLI in Cursor terminal
- No changes needed
- Works immediately
- Full functionality

**Phase 2 (Weeks 3-6)**: ⚡ Enhanced shell integration
- Custom commands
- Context sharing
- Workflow scripts

**Phase 3 (Weeks 7-12, Optional)**: 🚀 Native extension
- GUI panels
- Deep integration
- Multi-agent visualization
- **Only if user demand justifies complexity**

**Recommendation**: Start with Phase 1 terminal usage. It's simple, powerful, and may be sufficient for most users.

## Next Document

See `08-PHASE-1-MVP.md` for detailed implementation plan (weeks 1-2).
