# Architecture Pivot: Claude Agent SDK Integration

## Executive Summary

After research and consideration, we're pivoting from reimplementing Claude Code features to **orchestrating Claude Code instances** using the official Claude Agent SDK. This gives us full Claude Code capabilities immediately while maintaining our agent-agnostic orchestration vision.

## Key Decision

**Before:** Build our own REPL with direct API calls (text-only LLM)
**After:** Orchestrate Claude Code instances via Agent SDK (full tool use, file ops, MCP)

## Why This Makes Sense

### 1. **Avoid Reimplementation**
Don't rebuild what Claude Code already provides:
- ✅ File operations (Read, Write, Edit, Glob, Grep)
- ✅ Code execution (Bash)
- ✅ MCP server integration
- ✅ Tool use orchestration
- ✅ Context management
- ✅ Error handling

### 2. **Analytics Requirements Drive This**
You mentioned wanting:
> "analytics tools that help us find patterns in data like exports from jira or github"

**Python ecosystem is dominant** for this:
- pandas (data frames, CSV/JSON)
- scikit-learn (clustering, pattern detection)
- spaCy (NLP, text analysis)
- matplotlib/seaborn (visualization)

**Having Python orchestrator + analytics in one backend** is cleaner than TypeScript orchestrator + Python analytics service.

### 3. **Dashboard Pattern from Big-3**
The Big-3 observability system shows the pattern:
- **Agents** (Claude Code instances) run independently
- **Hook scripts** report events via HTTP to central service
- **Dashboard** (Vue app) visualizes all agent activity
- **SQLite** stores event history
- **WebSocket** streams real-time updates

This is a **proven pattern** we can adopt.

## New Architecture

```
┌─────────────────────────────────────────────────────────┐
│ Python Backend (Single Process - FastAPI)               │
│                                                          │
│ ┌──────────────────────────────────────────────────────┐│
│ │ Brain Orchestrator                                   ││
│ │ • Router: Task → agent selection                     ││
│ │ • Fleet Manager: Spawn/command multiple agents       ││
│ │ • Session Manager: Conversation & cost tracking      ││
│ └──────────────────────────────────────────────────────┘│
│                                                          │
│ ┌──────────────────────────────────────────────────────┐│
│ │ Agent Pool (via Claude Agent SDK)                    ││
│ │                                                       ││
│ │  ClaudeCodeAgent(workspace="watches")                ││
│ │  ├─> Full Claude Code: file ops, bash, MCP           ││
│ │  └─> Session ID: abc123                              ││
│ │                                                       ││
│ │  ClaudeCodeAgent(workspace="guitars")                ││
│ │  ├─> Independent Claude Code instance                ││
│ │  └─> Session ID: def456                              ││
│ │                                                       ││
│ │  GeminiAgent (comparison/research)                   ││
│ │  └─> Google API for alternative perspective          ││
│ └──────────────────────────────────────────────────────┘│
│                                                          │
│ ┌──────────────────────────────────────────────────────┐│
│ │ Analytics Engine (Direct Import - Same Process)      ││
│ │ • pandas: Jira/GitHub data analysis                  ││
│ │ • scikit-learn: Pattern detection, clustering        ││
│ │ • spaCy: NLP, entity extraction                      ││
│ │ • Functions called directly (no HTTP overhead)       ││
│ └──────────────────────────────────────────────────────┘│
│                                                          │
│ ┌──────────────────────────────────────────────────────┐│
│ │ Observability Service (HTTP + WebSocket)             ││
│ │ • Hook event collector (POST /events)                ││
│ │ • SQLite event store                                 ││
│ │ • WebSocket broadcaster (ws://dashboard)             ││
│ │ • Cost/token aggregation across agents               ││
│ └──────────────────────────────────────────────────────┘│
└──────────────┬───────────────────────────────────────────┘
               │ HTTP/WebSocket
               ▼
    ┌──────────────────────────┐
    │ Vue Dashboard (Browser)  │
    │ • Live agent status      │
    │ • Multi-project view     │
    │ • Cost tracking          │
    │ • Tool use visualization │
    │ • Chat transcripts       │
    │ • Analytics results      │
    └──────────────────────────┘
```

## What We Keep From Current Work

Our Phase 1 work wasn't wasted! We keep:

✅ **Orchestrator Pattern** - Multi-agent coordination
✅ **Router** - Intent classification, agent selection
✅ **Session Management** - Conversation history, cost tracking
✅ **Agent Interface** - BaseAgent abstraction
✅ **REPL Shell** - Terminal interface (now delegates to Agent SDK)
✅ **Project Structure** - Python package, tests, documentation

## What Changes

### ClaudeAgent → ClaudeCodeAgent

**Before (Direct API):**
```python
class ClaudeAgent(BaseAgent):
    def __init__(self, config):
        self.client = anthropic.Anthropic(api_key=api_key)

    def execute(self, task, context):
        response = self.client.messages.create(...)
        return AgentResult(...)  # Text only, no tools
```

**After (Agent SDK):**
```python
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions

class ClaudeCodeAgent(BaseAgent):
    def __init__(self, config):
        self.options = ClaudeAgentOptions(
            system_prompt=config.get('system_prompt'),
            permission_mode='bypassPermissions',  # Or 'acceptEdits'
            cwd=config.get('workspace_path')
        )

    async def execute(self, task, context):
        async with ClaudeSDKClient(options=self.options) as client:
            await client.query(task)

            # Collect all responses
            full_response = []
            tool_uses = []

            async for message in client.receive_response():
                if isinstance(message, AssistantMessage):
                    for content in message.content:
                        if hasattr(content, 'text'):
                            full_response.append(content.text)
                        elif hasattr(content, 'name'):  # Tool use
                            tool_uses.append({
                                'name': content.name,
                                'input': content.input
                            })

            return AgentResult(
                agent_name=self.name,
                response=''.join(full_response),
                tokens_used=...,  # From ResultMessage
                tool_uses=tool_uses  # NEW: Track what tools were used
            )
```

**Key Benefits:**
- File operations work
- Bash commands work
- MCP servers work
- Context management automatic
- Tool use tracked

## Implementation Phases

### Phase 1: Core SDK Integration (Week 1)
- [x] Research Claude Agent SDK
- [x] Install and test SDK
- [x] Validate basic query functionality
- [ ] Refactor ClaudeAgent to ClaudeCodeAgent (using SDK)
- [ ] Update orchestrator to handle async/await
- [ ] Test file operations and tool use
- [ ] Commit and validate

### Phase 2: Fleet Management (Week 2)
- [ ] Agent fleet manager (spawn multiple Claude Code instances)
- [ ] Workspace-specific agents (one per project)
- [ ] Agent registry (track all running agents)
- [ ] Inter-agent communication (if needed)
- [ ] Cost aggregation across fleet

### Phase 3: Hooks & Observability (Week 3)
- [ ] Hook event server (FastAPI endpoint)
- [ ] SQLite event storage
- [ ] WebSocket broadcaster
- [ ] Agent hook integration (report to central service)
- [ ] Event types: PreToolUse, PostToolUse, SessionStart, etc.

### Phase 4: Dashboard (Week 4)
- [ ] Vue 3 app setup
- [ ] WebSocket client connection
- [ ] Real-time agent status display
- [ ] Cost tracking visualization
- [ ] Tool use timeline
- [ ] Multi-project filtering

### Phase 5: Analytics Integration (Week 5)
- [ ] pandas module for data analysis
- [ ] Jira export parser
- [ ] GitHub export parser
- [ ] Pattern detection (scikit-learn clustering)
- [ ] NLP analysis (spaCy)
- [ ] Analytics results in dashboard

## Claude Agent SDK Test Results

✅ Successfully installed: `claude-agent-sdk==0.1.6`
✅ Claude Code version: `2.0.31`
✅ Simple query test: **PASSED**
✅ Options test (custom system prompt): **PASSED**
✅ Streaming response handling: **WORKING**
✅ Cost/token tracking: **WORKING**

**Test Output:**
```
🧪 Testing Claude Agent SDK...
💬 4
📊 Complete!
   Duration: 1426ms
   Tokens: 8 (in: 3, out: 5)
   Cost: $0.000075
✅ Agent SDK test successful!
```

## Benefits of This Architecture

### 1. **Immediate Full Functionality**
- Don't wait months to build file ops, bash, MCP
- Claude Code's entire feature set available day 1
- Proven, battle-tested tools

### 2. **True Multi-Agent Orchestration**
- Multiple Claude Code instances (one per project)
- Each with own workspace, session, context
- Orchestrator routes tasks to appropriate agent
- Can still compare with Gemini, Aider, etc.

### 3. **Analytics Integration is Clean**
```python
# Orchestrator can call analytics directly
from brain.analytics import analyze_jira_patterns

df = analyze_jira_patterns('workspace/jira_export.json')
insights = await claude_agent.query(
    f"Analyze these patterns: {df.describe()}"
)
```

No HTTP calls, no separate service, just imports.

### 4. **Observability Built-In**
- Hook system tracks ALL agent activity
- Dashboard shows real-time status
- Cost tracking across entire fleet
- Historical analysis via SQLite

### 5. **Agent-Agnostic Remains True**
- Can still add Gemini, Aider, OpenInterpreter
- Orchestrator routes to best agent
- Each agent implements same BaseAgent interface
- Claude Code just happens to be the most capable

## Migration Path

We have TWO options:

### Option A: Gradual Migration
1. Keep current ClaudeAgent (API-based) working
2. Add ClaudeCodeAgent alongside it
3. Add routing logic to choose between them
4. Gradually prefer ClaudeCodeAgent
5. Eventually deprecate ClaudeAgent

### Option B: Clean Break
1. Rename current ClaudeAgent to ClaudeLegacyAgent
2. Implement ClaudeCodeAgent as new default
3. Update all references
4. Keep legacy for comparison

**Recommendation: Option B (Clean Break)**
Our current implementation is early enough that a clean break makes sense.

## Next Immediate Steps

1. **Create ClaudeCodeAgent** using Agent SDK
2. **Update requirements.txt** (already has `claude-agent-sdk`)
3. **Update orchestrator** to handle async/await pattern
4. **Test file operations** (Read, Write, Edit)
5. **Test tool use** (Bash, Grep, Glob)
6. **Validate cost tracking**

Then we can continue with Phase 1 Week 2 (Obsidian integration, automation workflows) as originally planned, but with FULL Claude Code capabilities.

## Questions Before Proceeding

1. ✅ **Language choice: Python** - Decided
2. ✅ **SDK validation: Works** - Tested and verified
3. **Fleet model:** One agent per workspace, or spawn on-demand?
4. **Permission mode:** `bypassPermissions` for automation, or `acceptEdits` for safety?
5. **Dashboard priority:** Build alongside or after core features?

## References

- Claude Agent SDK Python: https://github.com/anthropics/claude-agent-sdk-python
- Claude Agent SDK Docs: https://docs.claude.com/en/api/agent-sdk/overview
- Big-3 Super Agent: https://github.com/disler/big-3-super-agent
- Big-3 Observability: https://github.com/disler/claude-code-hooks-multi-agent-observability

---

**Status:** Ready to implement ClaudeCodeAgent integration
**Blocker:** None
**Risk:** Low (SDK proven, pattern validated)
**Timeline:** 1-2 weeks for full integration
