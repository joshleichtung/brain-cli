# Phase 3: Intelligence (Weeks 7-12, Optional)

## Goal

AI-powered research assistant with deep memory, knowledge graph, hybrid RAG, advanced analytics, learning system, and optional Cursor extension.

**Note**: This phase is optional and aspirational. Implement only if Phase 1-2 prove valuable and there's strong user demand.

**Success Criteria**:
- ✅ Neo4j knowledge graph operational
- ✅ HybridRAG combining vector + graph search
- ✅ Advanced analytics dashboard
- ✅ Learning system optimizes agent routing
- ✅ Cursor extension functional (optional)

## Week 7-8: Knowledge Graph

### Neo4j Setup

**Installation**:
```bash
# Download Neo4j Desktop (free for local use)
# https://neo4j.com/download/

# Or use Docker
docker run \
    --name neo4j \
    -p7474:7474 -p7687:7687 \
    -d \
    -v $HOME/brain/workspace/.memory/neo4j/data:/data \
    -v $HOME/brain/workspace/.memory/neo4j/logs:/logs \
    -v $HOME/brain/workspace/.memory/neo4j/import:/var/lib/neo4j/import \
    --env NEO4J_AUTH=neo4j/your-password \
    neo4j:latest
```

### Graph Schema

**Nodes**:
- `Person` (user)
- `Agent` (AI agents)
- `Task` (user requests)
- `Concept` (knowledge entities)
- `Project` (coding projects, research topics)
- `Note` (Obsidian notes)
- `File` (code files, documents)

**Relationships**:
- `(Person)-[:ASKED]->(Task)`
- `(Agent)-[:EXECUTED]->(Task)`
- `(Task)-[:ABOUT]->(Concept)`
- `(Task)-[:RELATES_TO]->(Project)`
- `(Concept)-[:CONNECTED_TO]->(Concept)`
- `(Project)-[:HAS_NOTE]->(Note)`
- `(Note)-[:REFERENCES]->(Concept)`

### Implementation

**Neo4j Client** (`knowledge_graph.py`):
```python
from neo4j import GraphDatabase

class KnowledgeGraph:
    def __init__(self, uri="bolt://localhost:7687",
                 user="neo4j", password="your-password"):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def add_task(self, task: str, agent: str, concepts: List[str],
                project: str = None):
        """Add task to knowledge graph"""
        with self.driver.session() as session:
            session.write_transaction(
                self._create_task,
                task, agent, concepts, project
            )

    @staticmethod
    def _create_task(tx, task, agent, concepts, project):
        # Create task node
        tx.run("""
            MERGE (t:Task {content: $task, timestamp: datetime()})
            MERGE (a:Agent {name: $agent})
            MERGE (a)-[:EXECUTED]->(t)
        """, task=task, agent=agent)

        # Link concepts
        for concept in concepts:
            tx.run("""
                MATCH (t:Task {content: $task})
                MERGE (c:Concept {name: $concept})
                MERGE (t)-[:ABOUT]->(c)
            """, task=task, concept=concept)

        # Link project
        if project:
            tx.run("""
                MATCH (t:Task {content: $task})
                MERGE (p:Project {name: $project})
                MERGE (t)-[:RELATES_TO]->(p)
            """, task=task, project=project)

    def find_related_concepts(self, concept: str, depth: int = 2) -> List[str]:
        """Find concepts related to given concept"""
        with self.driver.session() as session:
            result = session.read_transaction(
                self._find_related,
                concept, depth
            )
            return result

    @staticmethod
    def _find_related(tx, concept, depth):
        result = tx.run("""
            MATCH (c1:Concept {name: $concept})
            MATCH (c1)-[:CONNECTED_TO*1..$depth]-(c2:Concept)
            RETURN DISTINCT c2.name as name
        """, concept=concept, depth=depth)
        return [record['name'] for record in result]

    def find_expert_agent(self, concept: str) -> str:
        """Find which agent has most experience with concept"""
        with self.driver.session() as session:
            result = session.read_transaction(
                self._find_expert,
                concept
            )
            return result

    @staticmethod
    def _find_expert(tx, concept):
        result = tx.run("""
            MATCH (a:Agent)-[:EXECUTED]->(t:Task)-[:ABOUT]->(c:Concept {name: $concept})
            RETURN a.name as agent, count(t) as task_count
            ORDER BY task_count DESC
            LIMIT 1
        """, concept=concept)
        record = result.single()
        return record['agent'] if record else None

    def get_project_context(self, project: str) -> dict:
        """Get all context for a project"""
        with self.driver.session() as session:
            return session.read_transaction(
                self._get_project_context,
                project
            )

    @staticmethod
    def _get_project_context(tx, project):
        # Get tasks
        tasks = tx.run("""
            MATCH (p:Project {name: $project})<-[:RELATES_TO]-(t:Task)
            RETURN t.content as content, t.timestamp as timestamp
            ORDER BY t.timestamp DESC
            LIMIT 10
        """, project=project)

        # Get concepts
        concepts = tx.run("""
            MATCH (p:Project {name: $project})<-[:RELATES_TO]-(t:Task)-[:ABOUT]->(c:Concept)
            RETURN DISTINCT c.name as name
        """, project=project)

        # Get notes
        notes = tx.run("""
            MATCH (p:Project {name: $project})-[:HAS_NOTE]->(n:Note)
            RETURN n.path as path, n.title as title
        """, project=project)

        return {
            'tasks': [dict(record) for record in tasks],
            'concepts': [record['name'] for record in concepts],
            'notes': [dict(record) for record in notes]
        }
```

### Integration

**Hook for Graph Updates**:
```python
def knowledge_graph_hook(context: HookContext):
    """Update knowledge graph with task execution"""
    if context.hook_type != HookType.POST_EXECUTE:
        return

    kg = KnowledgeGraph()

    # Extract concepts from task (use NER or LLM)
    concepts = extract_concepts(context.task)

    # Add to graph
    kg.add_task(
        task=context.task,
        agent=context.agent_name,
        concepts=concepts,
        project=context.session.workspace
    )

    kg.close()

hook_manager.register(HookType.POST_EXECUTE, knowledge_graph_hook)
```

## Week 9: HybridRAG

### Concept

Combine vector search (ChromaDB) with graph search (Neo4j) for richer context retrieval.

**Vector Search**: Semantic similarity
**Graph Search**: Conceptual relationships

### Implementation

**HybridRAG** (`hybrid_rag.py`):
```python
class HybridRAG:
    def __init__(self):
        self.semantic_memory = SemanticMemory()  # ChromaDB
        self.knowledge_graph = KnowledgeGraph()  # Neo4j

    def get_context(self, query: str, max_tokens: int = 3000) -> dict:
        """Get context from both vector and graph search"""

        # Vector search (semantic similarity)
        vector_results = self.semantic_memory.search(query, n_results=10)

        # Extract concepts from query
        concepts = extract_concepts(query)

        # Graph search (related concepts and tasks)
        graph_results = []
        for concept in concepts:
            related = self.knowledge_graph.find_related_concepts(concept)
            graph_results.extend(related)

        # Get expert agent recommendation
        expert_agents = {}
        for concept in concepts:
            expert = self.knowledge_graph.find_expert_agent(concept)
            if expert:
                expert_agents[concept] = expert

        # Combine and rank
        combined_context = self._combine_results(
            vector_results,
            graph_results,
            max_tokens
        )

        return {
            'context': combined_context,
            'expert_agents': expert_agents,
            'related_concepts': list(set(graph_results))
        }

    def _combine_results(self, vector_results, graph_concepts, max_tokens):
        """Combine vector and graph results intelligently"""
        context_parts = []
        total_tokens = 0

        # Priority 1: Vector results with graph-related concepts
        for vr in vector_results:
            if any(concept in vr['content'] for concept in graph_concepts):
                tokens = len(vr['content']) // 4
                if total_tokens + tokens > max_tokens:
                    break
                context_parts.append(vr['content'])
                total_tokens += tokens

        # Priority 2: Remaining vector results
        for vr in vector_results:
            if vr['content'] not in context_parts:
                tokens = len(vr['content']) // 4
                if total_tokens + tokens > max_tokens:
                    break
                context_parts.append(vr['content'])
                total_tokens += tokens

        return "\n\n".join(context_parts)

def extract_concepts(text: str) -> List[str]:
    """Extract key concepts from text using NER or LLM"""
    # Simple version: extract capitalized words and technical terms
    import re
    words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)

    # Or use spaCy for proper NER
    # import spacy
    # nlp = spacy.load("en_core_web_sm")
    # doc = nlp(text)
    # concepts = [ent.text for ent in doc.ents]

    return list(set(words))[:10]  # Top 10 concepts
```

**Integration**:
```python
# In orchestrator
self.hybrid_rag = HybridRAG()

def execute(self, user_input: str, mode: str = "single"):
    # Get hybrid context
    rag_context = self.hybrid_rag.get_context(user_input, max_tokens=3000)

    # Use expert agent recommendations
    if rag_context['expert_agents']:
        recommended_agent = list(rag_context['expert_agents'].values())[0]
        console.print(f"💡 Recommended agent: {recommended_agent}")

    # Add to session context
    self.session.context.update({
        'hybrid_rag_context': rag_context['context'],
        'related_concepts': rag_context['related_concepts']
    })

    # Continue with execution...
```

## Week 10: Advanced Analytics

### Analytics Dashboard

**Metrics to Track**:
- Agent performance by task type
- Cost analysis (total, per agent, per workspace)
- Success rate (user ratings)
- Response time trends
- Token usage patterns
- Concept frequency (knowledge graph)

**Implementation** (`analytics.py`):
```python
class AnalyticsDashboard:
    def __init__(self):
        self.perf_db = PerformanceDatabase()
        self.kg = KnowledgeGraph()

    def generate_dashboard(self, days: int = 30) -> str:
        """Generate comprehensive analytics dashboard"""

        dashboard = ["# Brain CLI Analytics Dashboard\n"]

        # Overall stats
        dashboard.append("## Overall Performance (Last 30 Days)")
        overall = self._get_overall_stats(days)
        dashboard.append(f"- Total Tasks: {overall['total_tasks']}")
        dashboard.append(f"- Total Cost: ${overall['total_cost']:.2f}")
        dashboard.append(f"- Total Tokens: {overall['total_tokens']:,}")
        dashboard.append(f"- Avg Rating: {overall['avg_rating']:.1f}/10\n")

        # Agent comparison
        dashboard.append("## Agent Performance")
        agent_stats = self._get_agent_comparison(days)
        dashboard.append(self._format_agent_table(agent_stats))

        # Task type analysis
        dashboard.append("\n## Task Type Analysis")
        task_analysis = self._get_task_type_analysis(days)
        dashboard.append(self._format_task_table(task_analysis))

        # Cost breakdown
        dashboard.append("\n## Cost Breakdown")
        cost_breakdown = self._get_cost_breakdown(days)
        dashboard.append(self._format_cost_chart(cost_breakdown))

        # Trending concepts
        dashboard.append("\n## Trending Concepts")
        concepts = self._get_trending_concepts(days)
        dashboard.append("\n".join([f"- {c['name']} ({c['count']} mentions)"
                                   for c in concepts[:10]]))

        return "\n".join(dashboard)

    def _get_overall_stats(self, days):
        # Query performance DB
        pass

    def _get_agent_comparison(self, days):
        # Compare agents across metrics
        pass

    def _get_task_type_analysis(self, days):
        # Analyze performance by task type
        pass

    def _get_cost_breakdown(self, days):
        # Cost by agent, workspace, time period
        pass

    def _get_trending_concepts(self, days):
        # Query knowledge graph for frequent concepts
        with self.kg.driver.session() as session:
            result = session.run("""
                MATCH (c:Concept)<-[:ABOUT]-(t:Task)
                WHERE t.timestamp > datetime() - duration({days: $days})
                RETURN c.name as name, count(t) as count
                ORDER BY count DESC
                LIMIT 10
            """, days=days)
            return [dict(record) for record in result]
```

**Slash Command**:
```python
elif command == 'dashboard':
    days = int(args[0]) if args else 30
    analytics = AnalyticsDashboard()
    dashboard = analytics.generate_dashboard(days)

    # Save to Obsidian
    obsidian.create_note(
        f"Analytics/Dashboard_{datetime.now().strftime('%Y-%m-%d')}.md",
        dashboard
    )

    console.print(Markdown(dashboard))
```

## Week 11: Learning System

### Concept

System learns from user feedback to improve agent routing over time.

**Learning Signals**:
- User ratings (explicit)
- Task completion time
- Follow-up questions (implicit dissatisfaction)
- Agent switches (first choice wasn't optimal)

### Implementation

**Learning Engine** (`learning.py`):
```python
class LearningEngine:
    def __init__(self):
        self.perf_db = PerformanceDatabase()
        self.model = self._initialize_model()

    def _initialize_model(self):
        """Simple ML model for agent selection"""
        from sklearn.ensemble import RandomForestClassifier
        return RandomForestClassifier(n_estimators=100)

    def train(self):
        """Train model on historical data"""
        # Get training data from performance DB
        data = self.perf_db.get_training_data()

        if len(data) < 100:
            print("⚠️ Not enough data for training (need 100+ samples)")
            return

        # Features: task type, keywords, length, complexity
        X = self._extract_features(data)

        # Labels: best performing agent
        y = [self._determine_best_agent(row) for row in data]

        # Train
        self.model.fit(X, y)
        print(f"✅ Model trained on {len(data)} samples")

    def predict_best_agent(self, task: str, available_agents: List[str]) -> str:
        """Predict best agent for task"""
        features = self._extract_task_features(task)
        prediction = self.model.predict([features])[0]

        if prediction in available_agents:
            return prediction
        else:
            # Fallback to rule-based
            return available_agents[0]

    def _extract_features(self, data):
        """Extract features from task data"""
        features = []
        for row in data:
            features.append([
                self._classify_task_type(row['task']),
                len(row['task'].split()),
                row['complexity_score'],
                self._count_keywords(row['task'])
            ])
        return features

    def _extract_task_features(self, task: str):
        """Extract features from single task"""
        return [
            self._classify_task_type(task),
            len(task.split()),
            self._estimate_complexity(task),
            self._count_keywords(task)
        ]

    def _determine_best_agent(self, row):
        """Determine which agent performed best"""
        # Based on user rating, response time, follow-ups
        if row['user_rating'] >= 8:
            return row['agent']
        elif row['follow_ups'] == 0 and row['response_time'] < 5.0:
            return row['agent']
        else:
            return 'claude'  # Default

    def _classify_task_type(self, task):
        # 0: code, 1: research, 2: analysis, 3: creative
        if any(kw in task.lower() for kw in ['code', 'function', 'debug']):
            return 0
        elif any(kw in task.lower() for kw in ['research', 'find', 'search']):
            return 1
        elif any(kw in task.lower() for kw in ['analyze', 'explain', 'why']):
            return 2
        else:
            return 3

    def _estimate_complexity(self, task):
        # Simple heuristic: length + question marks
        return len(task) + task.count('?') * 10

    def _count_keywords(self, task):
        keywords = ['code', 'research', 'analyze', 'creative', 'explain']
        return sum(1 for kw in keywords if kw in task.lower())
```

**Integration**:
```python
# In orchestrator
self.learning_engine = LearningEngine()

# Train periodically
if should_retrain():  # e.g., every 100 tasks
    self.learning_engine.train()

# Use for routing
def _select_agent_with_learning(self, task):
    # Get ML prediction
    ml_prediction = self.learning_engine.predict_best_agent(
        task,
        list(self.agents.keys())
    )

    # Combine with LLM routing
    llm_prediction = self.router.select_best_agent(task)

    # If they agree, use that
    if ml_prediction == llm_prediction:
        return self.agents[ml_prediction]

    # If disagree, prefer ML (it's learned from feedback)
    return self.agents[ml_prediction]
```

## Week 12: Polish & Cursor Extension

### Cursor Extension (Optional)

**Only implement if**:
- Strong user demand
- Terminal workflow proves limiting
- Budget and time allow

See `07-CURSOR-INTEGRATION.md` for complete implementation details.

### Final Polish

**Tasks**:
1. Performance optimization
2. Error handling improvements
3. Documentation updates
4. Video tutorials
5. Community feedback integration

**Performance Optimization**:
- Cache agent responses
- Parallel agent initialization
- Lazy loading of heavy dependencies
- Connection pooling for databases

**Error Handling**:
- Graceful degradation
- Automatic retries
- Detailed error messages
- Recovery suggestions

## Phase 3 Completion Checklist

### Knowledge Graph
- [ ] Neo4j installed and configured
- [ ] Graph schema implemented
- [ ] Task indexing working
- [ ] Concept extraction functional
- [ ] Expert agent recommendations

### HybridRAG
- [ ] Vector + graph search combined
- [ ] Context ranking intelligent
- [ ] Expert recommendations used
- [ ] Related concepts surfaced

### Analytics
- [ ] Dashboard generation working
- [ ] All metrics tracked
- [ ] Visualizations clear
- [ ] Obsidian export functional

### Learning System
- [ ] ML model trained
- [ ] Feature extraction working
- [ ] Predictions improve over time
- [ ] Routing optimized

### Cursor Extension (Optional)
- [ ] Extension published
- [ ] Sidebar panel functional
- [ ] Commands registered
- [ ] Context sharing working

## Deliverables

1. **Knowledge Graph**: Neo4j with rich relationships
2. **HybridRAG**: Combined vector + graph search
3. **Advanced Analytics**: Comprehensive dashboard
4. **Learning System**: ML-powered agent routing
5. **Cursor Extension**: Native IDE integration (optional)
6. **Complete Documentation**: All features documented
7. **Video Tutorials**: Usage demonstrations
8. **Community Feedback**: Incorporated improvements

## Beyond Phase 3

**Future Enhancements** (Phase 4+):
- OpenAI Realtime API for full-duplex voice
- Multi-modal support (images, documents)
- Team collaboration features
- Cloud sync (optional)
- Mobile app integration
- Web dashboard
- Plugin ecosystem

**Remember**: Phase 3 is optional. Only pursue if Phase 1-2 deliver value and there's clear demand for advanced features.

## Success Metrics

**Knowledge**: Graph contains 1000+ nodes
**RAG**: Context relevance >80%
**Analytics**: Daily dashboard generation
**Learning**: Routing accuracy improvement >20%
**Extension**: 100+ active users (if built)

## Next Document

See `11-IMPLEMENTATION-EXAMPLES.md` for code templates and patterns.
