# Phase 2: Scale (Weeks 3-6)

## Goal

Production-ready Brain CLI with all 7 agents, multi-agent comparison, TTS voice output, semantic memory (ChromaDB), all 11 automation workflows, and Fabric pattern integration.

**Success Criteria**:
- ✅ All 7 agents integrated and working
- ✅ Multi-agent comparison mode functional
- ✅ TTS voice output toggle working
- ✅ Performance tracking database operational
- ✅ ChromaDB semantic memory active
- ✅ All 11 automation workflows running
- ✅ Fabric patterns integrated
- ✅ Intelligent (LLM-based) routing implemented

## Week 3: Additional Agents & Comparison Mode

### Day 15-16: Add Remaining Agents

**New Agents**:
- Codex (OpenAI)
- Aider (CLI-based)
- OpenCode (Go binary)
- Continue (IDE integration)
- Open Interpreter (code execution)

**Tasks**:
1. Implement Codex wrapper
2. Implement Aider wrapper
3. Implement OpenCode wrapper
4. Create stub wrappers for Continue and Open Interpreter
5. Update agent registry

**Implementation**: See `02-AGENT-WRAPPERS.md` for complete code.

**Updated Config** (`~/.brain-config.yaml`):
```yaml
agents:
  claude:
    enabled: true
    api_key: ${ANTHROPIC_API_KEY}
    model: claude-sonnet-4-5-20250929
    cost_per_1k_tokens: 0.003
    capabilities: [analysis, research, conversation, reasoning]

  gemini:
    enabled: true
    api_key: ${GOOGLE_API_KEY}
    model: gemini-1.5-pro
    cost_per_1k_tokens: 0.00125
    capabilities: [research, creative, multimodal]

  codex:
    enabled: true
    api_key: ${OPENAI_API_KEY}
    model: gpt-4-turbo
    cost_per_1k_tokens: 0.01
    capabilities: [code, refactor, debugging]

  aider:
    enabled: true
    aider_path: /usr/local/bin/aider
    model: gpt-4-turbo
    cost_per_1k_tokens: 0.01
    capabilities: [code, refactor, git]

  opencode:
    enabled: true
    opencode_path: /usr/local/bin/opencode
    cost_per_1k_tokens: 0.0
    capabilities: [terminal, system]

  continue:
    enabled: false  # Placeholder for future
    capabilities: [code, ide]

  open_interpreter:
    enabled: false  # Placeholder for future
    capabilities: [code, execution]

default_orchestrator: claude
```

**Agent Registry Enhancement**:
```python
# src/brain/registry.py
from .agents import (
    ClaudeAgent, GeminiAgent, CodexAgent,
    AiderAgent, OpenCodeAgent
)

class AgentFactory:
    AGENT_CLASSES = {
        'claude': ClaudeAgent,
        'gemini': GeminiAgent,
        'codex': CodexAgent,
        'aider': AiderAgent,
        'opencode': OpenCodeAgent,
    }

    @classmethod
    def create_all_enabled_agents(cls, config_file: str) -> dict:
        with open(os.path.expanduser(config_file)) as f:
            config = yaml.safe_load(f)

        agents = {}
        for name, agent_config in config['agents'].items():
            if agent_config.get('enabled', False):
                agent_config['name'] = name
                try:
                    agents[name] = cls.create_agent(name, agent_config)
                    print(f"✅ {name} initialized")
                except Exception as e:
                    print(f"❌ {name} failed: {e}")

        return agents
```

### Day 17-18: Multi-Agent Comparison Mode

**Features**:
- Send task to multiple agents simultaneously
- Display results side-by-side
- Allow user to rate responses
- Track which agents perform best for task types

**Implementation**:

**Comparison Executor** (`orchestrator.py`):
```python
def execute_compare(self, task: str, agent_names: List[str] = None) -> ComparisonResult:
    """Execute task on multiple agents and compare"""
    if not agent_names:
        # Auto-select 3 agents
        agent_names = self._auto_select_comparison_agents(task)

    console.print(f"\n🔄 Running on {len(agent_names)} agents...")

    # Execute in parallel
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(agent_names)) as executor:
        futures = {
            executor.submit(
                self.agents[name].execute,
                task,
                self.session.context
            ): name
            for name in agent_names
        }

        results = []
        for future in concurrent.futures.as_completed(futures):
            agent_name = futures[future]
            try:
                result = future.result()
                results.append(result)
                console.print(f"✅ {agent_name} completed")
            except Exception as e:
                console.print(f"❌ {agent_name} failed: {e}")

    return ComparisonResult(results=results)

def _auto_select_comparison_agents(self, task: str) -> List[str]:
    """Select 3 most relevant agents for task"""
    # Use primary agent to analyze task
    analysis = self.primary.analyze_task(task)

    # Select agents based on capabilities
    candidates = []
    for name, agent in self.agents.items():
        if any(cap in analysis['required_capabilities']
               for cap in agent.config['capabilities']):
            candidates.append(name)

    # Return top 3 (or all if fewer)
    return candidates[:3] if len(candidates) > 3 else candidates
```

**Comparison Display** (`cli.py`):
```python
def display_comparison(results: List[AgentResult], console: Console):
    """Display comparison in rich format"""
    from rich.table import Table

    # Metrics table
    metrics_table = Table(title="📊 Performance Metrics")
    metrics_table.add_column("Agent", style="cyan")
    metrics_table.add_column("Time (s)", justify="right")
    metrics_table.add_column("Tokens", justify="right")
    metrics_table.add_column("Cost", justify="right")

    for r in results:
        metrics_table.add_row(
            r.agent_name,
            f"{r.time_taken:.2f}",
            str(r.tokens_used),
            f"${r.cost:.4f}"
        )

    console.print(metrics_table)
    console.print()

    # Responses
    for i, r in enumerate(results, 1):
        console.print(f"\n[bold cyan]━━━ {r.agent_name} ━━━[/bold cyan]")
        console.print(Markdown(r.response))

    # User rating
    console.print("\n[bold]Rate the responses (1-10):[/bold]")
    ratings = {}
    for r in results:
        try:
            rating = int(console.input(f"{r.agent_name}: "))
            ratings[r.agent_name] = rating
        except:
            ratings[r.agent_name] = None

    return ratings
```

**Slash Command**:
```python
# In handle_slash_command()
elif command == 'compare':
    if not args:
        console.print("[red]Usage: /compare <prompt>[/red]")
        return

    task = ' '.join(args)
    results = orchestrator.execute_compare(task)
    ratings = display_comparison(results.results, console)

    # Log to performance DB
    for result in results.results:
        rating = ratings.get(result.agent_name)
        perf_db.log_execution(result.agent_name, 'comparison',
                             result, rating)
```

### Day 19-20: Performance Tracking Database

**Database Schema** (`performance.py`):
```python
import sqlite3
from datetime import datetime

class PerformanceDatabase:
    def __init__(self, db_path: str = '~/brain/workspace/.analytics/performance.db'):
        self.db_path = os.path.expanduser(db_path)
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self._create_schema()

    def _create_schema(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS executions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent TEXT NOT NULL,
                task_type TEXT,
                task TEXT,
                response_time REAL,
                tokens_used INTEGER,
                cost REAL,
                quality_score REAL,
                user_rating INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS comparisons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task TEXT,
                winner TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_agent ON executions(agent);
            CREATE INDEX IF NOT EXISTS idx_task_type ON executions(task_type);
            CREATE INDEX IF NOT EXISTS idx_timestamp ON executions(timestamp);
        """)
        self.conn.commit()

    def log_execution(self, agent: str, task_type: str,
                     result: AgentResult, user_rating: int = None):
        self.conn.execute("""
            INSERT INTO executions
            (agent, task_type, task, response_time, tokens_used,
             cost, user_rating)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (agent, task_type, result.task, result.time_taken,
              result.tokens_used, result.cost, user_rating))
        self.conn.commit()

    def get_agent_stats(self, agent: str, days: int = 7) -> dict:
        cutoff = datetime.now() - timedelta(days=days)

        stats = self.conn.execute("""
            SELECT
                COUNT(*) as total_tasks,
                AVG(response_time) as avg_time,
                SUM(tokens_used) as total_tokens,
                SUM(cost) as total_cost,
                AVG(user_rating) as avg_rating
            FROM executions
            WHERE agent = ? AND timestamp > ?
        """, (agent, cutoff)).fetchone()

        return {
            'total_tasks': stats[0],
            'avg_time': stats[1],
            'total_tokens': stats[2],
            'total_cost': stats[3],
            'avg_rating': stats[4]
        }

    def get_best_agent_for_task(self, task_type: str) -> str:
        """Find best performing agent for task type"""
        result = self.conn.execute("""
            SELECT agent, AVG(user_rating) as avg_rating
            FROM executions
            WHERE task_type = ? AND user_rating IS NOT NULL
            GROUP BY agent
            ORDER BY avg_rating DESC
            LIMIT 1
        """, (task_type,)).fetchone()

        return result[0] if result else None

    def generate_report(self, days: int = 7) -> str:
        """Generate analytics report"""
        cutoff = datetime.now() - timedelta(days=days)

        report = ["# Performance Report\n"]

        # Per-agent stats
        agents = self.conn.execute("""
            SELECT DISTINCT agent FROM executions
            WHERE timestamp > ?
        """, (cutoff,)).fetchall()

        for (agent,) in agents:
            stats = self.get_agent_stats(agent, days)
            report.append(f"## {agent}")
            report.append(f"- Tasks: {stats['total_tasks']}")
            report.append(f"- Avg Time: {stats['avg_time']:.2f}s")
            report.append(f"- Total Cost: ${stats['total_cost']:.4f}")
            report.append(f"- Avg Rating: {stats['avg_rating']:.1f}/10\n")

        return "\n".join(report)
```

**Slash Command**:
```python
elif command == 'stats':
    agent_name = args[0] if args else orchestrator.primary_name
    stats = perf_db.get_agent_stats(agent_name, days=7)

    console.print(f"\n📊 Stats for {agent_name} (last 7 days):")
    console.print(f"  Tasks: {stats['total_tasks']}")
    console.print(f"  Avg Time: {stats['avg_time']:.2f}s")
    console.print(f"  Total Tokens: {stats['total_tokens']:,}")
    console.print(f"  Total Cost: ${stats['total_cost']:.4f}")
    console.print(f"  Avg Rating: {stats['avg_rating']:.1f}/10")

elif command == 'report':
    report = perf_db.generate_report(days=7)
    console.print(Markdown(report))
```

### Day 21: TTS Voice Integration

**Goal**: Toggle-able text-to-speech output

**Implementation**: See `13-VOICE-INTEGRATION.md` for complete details.

**Quick Implementation** (`tts.py`):
```python
import pyttsx3

class TTSManager:
    def __init__(self):
        self.engine = None
        self.enabled = False

    def toggle(self, provider: str = 'pyttsx3'):
        if self.enabled:
            self.enabled = False
            if self.engine:
                self.engine.stop()
            print("🔇 TTS disabled")
        else:
            if provider == 'pyttsx3':
                self.engine = pyttsx3.init()
                self.engine.setProperty('rate', 150)
                self.engine.setProperty('volume', 0.9)
            self.enabled = True
            print("🔊 TTS enabled")

    def speak(self, text: str):
        if self.enabled and self.engine:
            # Clean markdown for speech
            clean_text = self._clean_markdown(text)
            self.engine.say(clean_text)
            self.engine.runAndWait()

    def _clean_markdown(self, text: str) -> str:
        # Remove markdown formatting for speech
        import re
        text = re.sub(r'```.*?```', '[code block]', text, flags=re.DOTALL)
        text = re.sub(r'`([^`]+)`', r'\1', text)
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
        text = re.sub(r'\*([^*]+)\*', r'\1', text)
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        text = re.sub(r'#+\s+', '', text)
        return text
```

**Integration** (`cli.py`):
```python
# In main()
tts = TTSManager()

# In REPL loop
response = orchestrator.execute(user_input)
console.print(Markdown(response))

# TTS output
if tts.enabled:
    tts.speak(response)

# Slash command
elif command == 'tts':
    provider = args[0] if args else 'pyttsx3'
    tts.toggle(provider)
```

## Week 4: Semantic Memory & Context

### Day 22-23: ChromaDB Integration

**Goal**: Semantic search across all past conversations and notes

**Setup**:
```bash
pip install chromadb
```

**Implementation** (`memory.py`):
```python
import chromadb
from chromadb.config import Settings

class SemanticMemory:
    def __init__(self, persist_dir: str = '~/brain/workspace/.memory/chroma'):
        self.persist_dir = os.path.expanduser(persist_dir)
        os.makedirs(self.persist_dir, exist_ok=True)

        self.client = chromadb.Client(Settings(
            persist_directory=self.persist_dir,
            anonymized_telemetry=False
        ))

        self.collection = self.client.get_or_create_collection(
            name="brain_memory",
            metadata={"hnsw:space": "cosine"}
        )

    def add_conversation_turn(self, turn: Turn, session_id: str):
        """Add conversation turn to memory"""
        self.collection.add(
            documents=[turn.content],
            metadatas=[{
                'session_id': session_id,
                'agent': turn.agent,
                'timestamp': turn.timestamp.isoformat(),
                'role': turn.role
            }],
            ids=[f"{session_id}_{turn.timestamp.timestamp()}"]
        )

    def search(self, query: str, n_results: int = 5) -> List[dict]:
        """Semantic search across all memory"""
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )

        return [
            {
                'content': doc,
                'metadata': meta,
                'distance': dist
            }
            for doc, meta, dist in zip(
                results['documents'][0],
                results['metadatas'][0],
                results['distances'][0]
            )
        ]

    def get_relevant_context(self, query: str, max_tokens: int = 2000) -> str:
        """Get relevant context for query"""
        results = self.search(query, n_results=10)

        context_parts = []
        total_tokens = 0

        for r in results:
            # Estimate tokens (rough: 1 token ≈ 4 chars)
            tokens = len(r['content']) // 4

            if total_tokens + tokens > max_tokens:
                break

            context_parts.append(f"[{r['metadata']['timestamp']}] {r['content']}")
            total_tokens += tokens

        return "\n\n".join(context_parts)
```

**Integration with Orchestrator**:
```python
class AgnosticOrchestrator:
    def __init__(self, primary: str, agent_configs: dict):
        # ... existing init
        self.semantic_memory = SemanticMemory()

    def execute(self, user_input: str, mode: str = "single"):
        # Get relevant context from semantic memory
        relevant_context = self.semantic_memory.get_relevant_context(
            user_input,
            max_tokens=2000
        )

        # Add to session context
        self.session.context['semantic_memory'] = relevant_context

        # ... continue with execution

        # After execution, store in memory
        turn = Turn(
            role='assistant',
            content=final_response,
            agent=self.primary_name,
            timestamp=datetime.now(),
            tokens=result.tokens_used,
            cost=result.cost
        )
        self.semantic_memory.add_conversation_turn(turn, self.session.id)
```

### Day 24-25: Context Loading & UFC

**Implementation**: See `04-MIESSLER-PATTERNS.md` for complete details.

**Key Features**:
- Auto-load relevant context files
- Mandatory context for workspaces
- UFC directory structure
- Context verification

**Context Loader Integration**:
```python
# In orchestrator execute()
context_loader = ContextLoader()

# Find relevant context files
relevant_files = context_loader.find_relevant_context(
    user_input,
    self.session.workspace,
    max_files=5
)

# Load global + workspace context
full_context = context_loader.load_full_context(
    self.session.workspace,
    global_categories=['architecture', 'tools', 'philosophy']
)

# Add to session
self.session.context.update({
    'global_context': full_context['global'],
    'workspace_context': full_context['workspace'],
    'relevant_files': relevant_files
})
```

## Week 5: Advanced Automation

### Day 26-28: Implement Remaining 8 Workflows

**Workflows to Add** (see `06-AUTOMATION-WORKFLOWS.md` for complete implementations):
2. Watch monitor (Reddit/eBay)
4. Self-updating research projects
5. GitHub project launcher
6. Shopping list integration
7. Paper pipeline (arXiv)
9. Hackathon ideation
10. AI tool discovery
11. Communication generator

**Setup Scripts**:
```bash
# Create all workflow scripts
mkdir -p ~/brain/workspace/scripts

# Setup all cron jobs
cat > ~/brain/workspace/scripts/setup_cron.sh << 'EOF'
#!/bin/bash

# Add all cron jobs
(crontab -l 2>/dev/null
echo "# Brain CLI Automation Workflows"
echo "0 * * * * bash ~/brain/workspace/scripts/watch_monitor.sh"
echo "0 9 * * * bash ~/brain/workspace/scripts/research_update.sh watches"
echo "0 10 * * * bash ~/brain/workspace/scripts/paper_pipeline.sh"
echo "0 11 * * 1,4 bash ~/brain/workspace/scripts/ai_tool_discovery.sh"
echo "0 17 * * 5 bash ~/brain/workspace/scripts/weekly_review.sh"
) | crontab -

echo "✅ Cron jobs installed"
EOF

chmod +x ~/brain/workspace/scripts/setup_cron.sh
bash ~/brain/workspace/scripts/setup_cron.sh
```

### Day 29-30: Fabric Pattern Integration

**Setup**:
```bash
pip install fabric
fabric --setup
```

**Integration** (`fabric_integration.py`):
```python
# See 04-MIESSLER-PATTERNS.md for complete implementation

class FabricPatternManager:
    # ... implementation

# In CLI
fabric = FabricPatternManager()

# Slash command
elif command == 'fabric':
    if len(args) < 2:
        console.print("[red]Usage: /fabric <pattern> <text>[/red]")
        return

    pattern = args[0]
    text = ' '.join(args[1:])

    result = fabric.apply_pattern(pattern, text)
    console.print(Markdown(result))
```

**Create Custom Patterns**:
```bash
# Research synthesis pattern
fabric.create_custom_pattern(
    'research_synthesis',
    system_prompt='...',  # See 04-MIESSLER-PATTERNS.md
)

# Agent comparison pattern
fabric.create_custom_pattern(
    'agent_comparison',
    system_prompt='...',
)
```

## Week 6: Intelligent Routing & Polish

### Day 31-33: LLM-Based Routing

**Goal**: Use primary agent to intelligently route tasks

**Implementation** (already in `01-ORCHESTRATOR-DESIGN.md`):
```python
class LLMRouter:
    def select_best_agent(self, plan: RoutingPlan) -> BaseAgent:
        # Use primary agent to analyze task
        analysis = self.primary.analyze_task(
            task=plan.task,
            agent_capabilities=self._get_capabilities(),
            performance_history=self._get_history()
        )

        return self.agents[analysis['best_agent']]
```

**Enable in Config**:
```yaml
routing:
  strategy: llm  # 'rule' or 'llm' or 'hybrid'
  use_performance_history: true
  confidence_threshold: 0.7
```

### Day 34-36: Testing & Refinement

**Comprehensive Test Suite**:
```python
# tests/test_phase2.py

def test_all_agents():
    """Test all 5 agents"""
    for agent_name in ['claude', 'gemini', 'codex', 'aider', 'opencode']:
        agent = agents[agent_name]
        assert agent.ping(), f"{agent_name} not responding"

def test_comparison_mode():
    """Test multi-agent comparison"""
    task = "Explain quantum computing"
    results = orchestrator.execute_compare(task, ['claude', 'gemini', 'codex'])
    assert len(results.results) == 3

def test_tts():
    """Test TTS toggle"""
    tts = TTSManager()
    tts.toggle()
    assert tts.enabled
    tts.speak("Test")
    tts.toggle()
    assert not tts.enabled

def test_semantic_memory():
    """Test ChromaDB integration"""
    memory = SemanticMemory()
    memory.add_conversation_turn(test_turn, 'test_session')
    results = memory.search("test query")
    assert len(results) > 0

def test_all_workflows():
    """Test all 11 automation workflows"""
    workflows = [
        'project_check.sh',
        'watch_monitor.sh',
        'research_update.sh',
        'paper_pipeline.sh',
        'ai_tool_discovery.sh',
        'weekly_review.sh',
        # ... etc
    ]

    for workflow in workflows:
        result = subprocess.run(['bash', f'~/brain/workspace/scripts/{workflow}'])
        assert result.returncode == 0, f"{workflow} failed"
```

## Phase 2 Completion Checklist

### Agents
- [ ] All 5 agents working (Claude, Gemini, Codex, Aider, OpenCode)
- [ ] Agent factory creates all enabled agents
- [ ] Health checks pass for all agents
- [ ] Error handling robust

### Multi-Agent Features
- [ ] Comparison mode functional
- [ ] Parallel execution working
- [ ] Results display formatted
- [ ] User ratings captured
- [ ] Performance DB logging

### TTS Voice
- [ ] TTS toggle working
- [ ] pyttsx3 provider functional
- [ ] Markdown cleaning for speech
- [ ] Alternative providers researched

### Memory & Context
- [ ] ChromaDB initialized
- [ ] Conversation turns indexed
- [ ] Semantic search working
- [ ] Context loader integrated
- [ ] UFC structure implemented

### Automation
- [ ] All 11 workflows implemented
- [ ] Cron jobs scheduled
- [ ] Scripts executable
- [ ] Error notifications working

### Fabric Integration
- [ ] Fabric installed
- [ ] Pattern manager implemented
- [ ] Custom patterns created
- [ ] Slash command working

### Routing
- [ ] LLM-based routing implemented
- [ ] Performance history considered
- [ ] Confidence thresholds working
- [ ] Fallback to rule-based

### Performance
- [ ] Database schema created
- [ ] Execution logging working
- [ ] Stats commands functional
- [ ] Report generation working

## Deliverables

1. **5+ Agent Support**: Claude, Gemini, Codex, Aider, OpenCode
2. **Multi-Agent Comparison**: Side-by-side with ratings
3. **TTS Voice Output**: Toggle-able, swappable providers
4. **Performance Tracking**: SQLite database with analytics
5. **Semantic Memory**: ChromaDB search across history
6. **11 Automation Workflows**: All functional with cron
7. **Fabric Integration**: Pattern library + custom patterns
8. **Intelligent Routing**: LLM-based task routing
9. **Documentation**: Updated for all new features
10. **Tests**: Full test suite passing

## Next Phase

See `10-PHASE-3-INTELLIGENCE.md` for:
- Neo4j knowledge graph
- HybridRAG (vector + graph)
- Advanced analytics
- Learning system
- Cursor extension (maybe)
