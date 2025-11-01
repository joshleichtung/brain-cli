# Orchestrator Design - Agent-Agnostic Architecture

## Core Principle

**The orchestrator is NOT tied to any specific AI agent**. Any agent can be the primary orchestrator, and you can switch mid-session without losing context.

This solves:
- Token limit exhaustion
- Agent-specific weaknesses
- Vendor lock-in
- Cost optimization

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                   Interactive REPL                       │
│  (Natural language + slash commands)                    │
└────────────────────┬────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────┐
│              Agent-Agnostic Orchestrator                 │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Primary Agent (Swappable)                       │  │
│  │  - Routes tasks to agents                        │  │
│  │  - Synthesizes results                           │  │
│  │  - Maintains conversation                        │  │
│  └──────────────────────────────────────────────────┘  │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Router                                          │  │
│  │  - Intent classification                         │  │
│  │  - Agent selection                               │  │
│  │  - Parallel dispatch                             │  │
│  └──────────────────────────────────────────────────┘  │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Agent Registry                                  │  │
│  │  - Agent capabilities                            │  │
│  │  - Performance history                           │  │
│  │  - Availability status                           │  │
│  └──────────────────────────────────────────────────┘  │
└────────┬────────────┬────────────┬────────────┬────────┘
         ↓            ↓            ↓            ↓
    ┌────────┐  ┌─────────┐  ┌────────┐  ┌──────────┐
    │ Claude │  │ Gemini  │  │ Codex  │  │  Aider   │
    │  API   │  │   API   │  │  API   │  │   CLI    │
    └────────┘  └─────────┘  └────────┘  └──────────┘
         ↓            ↓            ↓            ↓
┌─────────────────────────────────────────────────────────┐
│                Result Aggregator                         │
│  - Comparison mode                                      │
│  - Voting mechanisms                                    │
│  - Synthesis strategies                                 │
└─────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Orchestrator Core

**Responsibilities**:
- Manage primary agent lifecycle
- Coordinate agent switching
- Maintain session context across switches
- Handle conversation flow

**Key Methods**:
```python
class AgnosticOrchestrator:
    def __init__(self, primary: str, agent_configs: dict):
        self.primary_name = primary
        self.agents = self._initialize_agents(agent_configs)
        self.primary = self.agents[primary]
        self.session = Session()
        self.router = Router(self.agents)
        self.aggregator = ResultAggregator()

    def switch_orchestrator(self, new_primary: str):
        """Switch which agent orchestrates - preserves context"""
        if new_primary not in self.agents:
            raise ValueError(f"Agent {new_primary} not available")

        # Transfer context
        context = self.primary.export_context()
        self.primary = self.agents[new_primary]
        self.primary.import_context(context)
        self.primary_name = new_primary

        return f"🔄 Switched to {new_primary} as orchestrator"

    def execute(self, user_input: str, mode: str = "single"):
        """Main execution flow"""
        # Primary routes the task
        routing_plan = self.primary.create_routing_plan(
            user_input,
            self.agents,
            self.session.context
        )

        # Execute based on mode
        if mode == "single":
            result = self._execute_single(routing_plan)
        elif mode == "compare":
            result = self._execute_compare(routing_plan)
        elif mode == "vote":
            result = self._execute_vote(routing_plan)

        # Primary synthesizes
        final_response = self.primary.synthesize(result, user_input)

        # Update session
        self.session.add_turn(user_input, final_response)

        return final_response

    def _execute_single(self, plan):
        """Route to best agent, get single result"""
        agent = self.router.select_best_agent(plan)
        return agent.execute(plan.task, plan.context)

    def _execute_compare(self, plan):
        """Send to multiple agents, compare results"""
        agents = self.router.select_multiple_agents(plan, n=3)
        results = [agent.execute(plan.task, plan.context)
                   for agent in agents]
        return self.aggregator.compare(results)

    def _execute_vote(self, plan):
        """Multiple agents vote on best approach"""
        agents = self.router.select_multiple_agents(plan, n=5)
        results = [agent.execute(plan.task, plan.context)
                   for agent in agents]
        return self.aggregator.vote(results, self.primary)
```

### 2. Router

**Responsibilities**:
- Classify task intent
- Select optimal agent(s)
- Consider agent capabilities, performance history, availability
- Support multiple routing strategies

**Routing Strategies**:

**Rule-Based** (Phase 1):
```python
class RuleBasedRouter:
    RULES = {
        'code': ['codex', 'claude', 'aider'],
        'research': ['claude', 'gemini'],
        'refactor': ['aider', 'codex'],
        'analysis': ['claude', 'gemini'],
        'creative': ['claude', 'gemini'],
        'terminal': ['opencode', 'aider']
    }

    def select_best_agent(self, plan):
        intent = self._classify_intent(plan.task)
        candidates = self.RULES.get(intent, ['claude'])

        # Filter by availability
        available = [a for a in candidates if self.agents[a].available]

        # Select by performance history
        return self._select_by_performance(available, intent)
```

**LLM-Based** (Phase 2):
```python
class LLMRouter:
    def select_best_agent(self, plan):
        # Use primary agent to analyze task
        analysis = self.primary.analyze_task(
            task=plan.task,
            agent_capabilities=self._get_capabilities(),
            performance_history=self._get_history()
        )

        return self.agents[analysis['best_agent']]

    def _get_capabilities(self):
        return {
            name: agent.capabilities
            for name, agent in self.agents.items()
        }

    def _get_history(self):
        return self.analytics.get_agent_performance(
            task_type=self._classify_intent(plan.task),
            window='7d'
        )
```

**Hybrid** (Phase 3):
```python
class HybridRouter:
    def select_best_agent(self, plan):
        # Rule-based for known patterns
        rule_result = self.rule_router.select(plan)

        # LLM-based for ambiguous cases
        if rule_result['confidence'] < 0.7:
            return self.llm_router.select(plan)

        return rule_result['agent']
```

### 3. Agent Registry

**Responsibilities**:
- Track agent availability
- Store capabilities and metadata
- Record performance metrics
- Manage API keys and configuration

**Schema**:
```python
@dataclass
class AgentMetadata:
    name: str
    type: str  # 'api', 'cli', 'hybrid'
    capabilities: List[str]
    cost_per_1k_tokens: float
    avg_response_time: float
    reliability: float  # 0-1
    specialties: List[str]
    api_key: Optional[str]
    max_tokens: int
    supports_streaming: bool

class AgentRegistry:
    def __init__(self):
        self.agents = {}
        self.performance_db = PerformanceDatabase()

    def register(self, name: str, agent: BaseAgent, metadata: AgentMetadata):
        self.agents[name] = {
            'agent': agent,
            'metadata': metadata,
            'available': True,
            'last_used': None
        }

    def get_capabilities(self, name: str) -> List[str]:
        return self.agents[name]['metadata'].capabilities

    def get_performance(self, name: str, task_type: str) -> dict:
        return self.performance_db.query(
            agent=name,
            task_type=task_type
        )

    def mark_unavailable(self, name: str, reason: str):
        self.agents[name]['available'] = False
        self.agents[name]['unavailable_reason'] = reason

    def health_check(self):
        """Verify all agents are responsive"""
        for name, data in self.agents.items():
            try:
                data['agent'].ping()
                data['available'] = True
            except Exception as e:
                data['available'] = False
                data['unavailable_reason'] = str(e)
```

### 4. Result Aggregator

**Responsibilities**:
- Compare results from multiple agents
- Implement voting mechanisms
- Synthesize diverse responses
- Present comparison UI

**Modes**:

**Comparison Mode**:
```python
class ResultAggregator:
    def compare(self, results: List[AgentResult]) -> ComparisonResult:
        """Show results side-by-side for user evaluation"""
        return ComparisonResult(
            results=results,
            display_format='side_by_side',
            metrics={
                'response_time': [r.time for r in results],
                'quality': [r.quality_score for r in results],
                'cost': [r.cost for r in results]
            }
        )
```

**Voting Mode**:
```python
    def vote(self, results: List[AgentResult], judge: BaseAgent) -> VoteResult:
        """Use primary agent to judge which result is best"""
        votes = judge.evaluate_results(
            results=results,
            criteria=['accuracy', 'completeness', 'clarity']
        )

        winner = max(votes, key=lambda x: x.total_score)

        return VoteResult(
            winner=winner,
            votes=votes,
            reasoning=judge.explain_vote(winner)
        )
```

**Synthesis Mode**:
```python
    def synthesize(self, results: List[AgentResult], judge: BaseAgent) -> str:
        """Combine best parts of multiple responses"""
        synthesis = judge.synthesize_results(
            results=results,
            strategy='best_of_each'
        )

        return synthesis
```

## Switching Mechanisms

### Context Preservation

**What to preserve**:
- Conversation history
- Session memory (decisions, files modified)
- Current task context
- User preferences

**Implementation**:
```python
class Context:
    def __init__(self):
        self.conversation: List[Turn] = []
        self.session_memory: dict = {}
        self.task_context: dict = {}
        self.user_prefs: dict = {}

    def export(self) -> dict:
        return {
            'conversation': [t.to_dict() for t in self.conversation],
            'memory': self.session_memory,
            'task': self.task_context,
            'prefs': self.user_prefs
        }

    def import_from(self, data: dict):
        self.conversation = [Turn.from_dict(t) for t in data['conversation']]
        self.session_memory = data['memory']
        self.task_context = data['task']
        self.user_prefs = data['prefs']

class BaseAgent:
    def export_context(self) -> dict:
        return self.context.export()

    def import_context(self, data: dict):
        self.context = Context()
        self.context.import_from(data)
```

### Switch Triggers

**Manual**:
```bash
> /switch gemini
🔄 Switched to Gemini as orchestrator
> continue with analysis
```

**Automatic** (token limit):
```python
def execute(self, user_input: str):
    try:
        result = self.primary.execute(user_input)
    except TokenLimitError:
        # Auto-switch to agent with most tokens remaining
        backup = self._find_agent_with_tokens()
        print(f"⚠️ Token limit reached. Switching to {backup.name}")
        self.switch_orchestrator(backup.name)
        result = self.primary.execute(user_input)

    return result
```

**Adaptive** (performance-based):
```python
def execute(self, user_input: str):
    # Check if current agent is struggling
    if self._is_struggling(user_input):
        better_agent = self.router.find_better_agent(
            task=user_input,
            current=self.primary_name
        )
        if better_agent:
            print(f"💡 Switching to {better_agent} for better results")
            self.switch_orchestrator(better_agent)
```

## Agent Communication Protocol

All agents must implement:

```python
class BaseAgent(ABC):
    @abstractmethod
    def execute(self, task: str, context: dict) -> AgentResult:
        """Execute a task with context"""
        pass

    @abstractmethod
    def create_routing_plan(self, task: str, available_agents: dict,
                           context: dict) -> RoutingPlan:
        """Analyze task and create routing plan"""
        pass

    @abstractmethod
    def synthesize(self, results: List[AgentResult],
                   original_task: str) -> str:
        """Synthesize results into final response"""
        pass

    @abstractmethod
    def export_context(self) -> dict:
        """Export current context for switching"""
        pass

    @abstractmethod
    def import_context(self, data: dict):
        """Import context from another agent"""
        pass

    @abstractmethod
    def ping(self) -> bool:
        """Health check"""
        pass
```

## Routing Plan Structure

```python
@dataclass
class RoutingPlan:
    task: str
    intent: str  # 'code', 'research', 'analysis', etc.
    complexity: float  # 0-1
    requires_multiple: bool
    recommended_agents: List[str]
    parallel_execution: bool
    context: dict
    estimated_tokens: int

    def to_dict(self):
        return asdict(self)

@dataclass
class AgentResult:
    agent_name: str
    task: str
    response: str
    time_taken: float
    tokens_used: int
    cost: float
    quality_score: Optional[float]
    metadata: dict
```

## Performance Tracking

Track every execution:

```python
class PerformanceDatabase:
    def __init__(self):
        self.db = sqlite3.connect('agent_analytics.db')
        self._create_schema()

    def log_execution(self, agent: str, task_type: str,
                     result: AgentResult, user_rating: Optional[int]):
        self.db.execute("""
            INSERT INTO executions
            (agent, task_type, response_time, tokens, cost,
             quality_score, user_rating, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (agent, task_type, result.time_taken, result.tokens_used,
              result.cost, result.quality_score, user_rating,
              datetime.now()))
        self.db.commit()

    def get_agent_performance(self, agent: str, task_type: str,
                             window: str = '7d') -> dict:
        """Get recent performance metrics"""
        cutoff = self._parse_window(window)

        return self.db.execute("""
            SELECT
                AVG(response_time) as avg_time,
                AVG(quality_score) as avg_quality,
                AVG(user_rating) as avg_rating,
                COUNT(*) as total_tasks
            FROM executions
            WHERE agent = ? AND task_type = ?
              AND timestamp > ?
        """, (agent, task_type, cutoff)).fetchone()
```

## Example Flows

### Flow 1: Single Agent Execution
```
User: "Analyze the authentication system architecture"
    ↓
Primary (Claude): Creates routing plan
    ↓
Router: Selects best agent (Claude) based on 'analysis' intent
    ↓
Claude: Executes analysis
    ↓
Primary (Claude): Synthesizes (just returns result)
    ↓
User: Sees response
```

### Flow 2: Multi-Agent Comparison
```
User: "/compare Explain quantum computing"
    ↓
Primary (Claude): Creates routing plan
    ↓
Router: Selects 3 agents (Claude, Gemini, Codex)
    ↓
Parallel execution → 3 explanations
    ↓
Aggregator: Formats side-by-side comparison
    ↓
User: Sees all 3, rates best
    ↓
Performance DB: Records ratings
```

### Flow 3: Auto-Switch on Token Limit
```
User: "Continue debugging this complex system"
    ↓
Primary (Claude): Starts execution
    ↓
TokenLimitError raised (90% tokens used)
    ↓
Orchestrator: Finds agent with most tokens (Gemini)
    ↓
Context transfer: Claude → Gemini
    ↓
Primary (Gemini): Continues execution
    ↓
User: Seamless continuation
```

### Flow 4: Manual Switch for Specialization
```
User: Working on research task with Claude
User: "/switch codex"
    ↓
Orchestrator: Transfers context Claude → Codex
    ↓
User: "Now refactor this code"
    ↓
Primary (Codex): Better at code, executes efficiently
    ↓
User: "/switch claude"  (back to research)
```

## Design Principles

1. **Agent Neutrality**: No hardcoded assumptions about which agent is primary
2. **Stateless Agents**: Agents don't maintain session state, orchestrator does
3. **Clean Interfaces**: Common protocol for all agents
4. **Graceful Degradation**: If agent fails, fallback to others
5. **Transparent Switching**: User always knows who's orchestrating
6. **Context Preservation**: Switching doesn't lose conversation
7. **Performance Learning**: System improves routing over time

## Next Document

See `02-AGENT-WRAPPERS.md` for implementation details of each agent wrapper.
