# Daniel Miessler Patterns

## Overview

Daniel Miessler's [personal AI infrastructure article](https://danielmiessler.com/p/my-personal-ai-infrastructure-and-tooling-october-2024) provides battle-tested patterns for organizing AI-assisted workflows. Key concepts:

1. **UFC (Unified File Context)** - Hierarchical directory structure
2. **Mandatory Context Loading** - Always load relevant context
3. **Fabric Pattern Library** - 300+ community AI prompts
4. **Observable Verification** - Validate AI outputs

## 1. UFC (Unified File Context)

### Concept

A hierarchical directory structure that captures global patterns, project-specific context, and ephemeral session data.

### Miessler's UFC Structure

```
~/ufc/
├── system/          # System-level configs
├── fabric/          # Fabric patterns
├── projects/        # Project-specific context
└── sessions/        # Temporary session data
```

### Our Adaptation

We extend UFC for multi-domain research and agent-agnostic operation:

```
~/brain/workspace/
├── global_memory/              # Cross-project knowledge
│   ├── context/
│   │   ├── architecture/       # System design patterns
│   │   │   ├── agent_coordination.md
│   │   │   ├── routing_strategies.md
│   │   │   └── memory_hierarchy.md
│   │   ├── projects/           # Project templates
│   │   │   ├── research_workflow.md
│   │   │   ├── automation_patterns.md
│   │   │   └── integration_patterns.md
│   │   ├── tools/              # Tool knowledge
│   │   │   ├── claude_best_practices.md
│   │   │   ├── gemini_strengths.md
│   │   │   ├── aider_workflows.md
│   │   │   └── obsidian_patterns.md
│   │   └── philosophy/         # Principles and mental models
│   │       ├── agent_selection.md
│   │       ├── context_management.md
│   │       └── automation_principles.md
│   └── fabric_patterns/        # Custom Fabric patterns
│       ├── research_synthesis/
│       ├── code_analysis/
│       └── creative_ideation/
│
├── workspaces/                 # Domain-specific work
│   ├── watches/
│   │   ├── .workspace.yaml
│   │   ├── context/
│   │   │   ├── market_analysis.md
│   │   │   ├── dealers.md
│   │   │   └── price_history.md
│   │   ├── notes/
│   │   └── data/
│   ├── guitars/
│   ├── sound_design/
│   ├── ai_tooling/
│   └── coding_projects/
│
└── .sessions/                  # Ephemeral session data
    ├── watches/
    │   ├── session.json
    │   └── history/
    └── guitars/
```

### Context File Format

All context files use markdown with YAML frontmatter:

```markdown
---
title: Agent Coordination Patterns
type: architecture
tags: [agents, orchestration, routing]
updated: 2025-11-01
relevance: high
---

# Agent Coordination Patterns

## Overview
Strategies for coordinating multiple AI agents...

## Pattern: LLM-Based Routing
When to use:
- Complex task classification
- Multiple viable options
- Performance history exists

How it works:
...
```

## 2. Mandatory Context Loading

### Concept

**Never** run AI prompts without loading relevant context first. This ensures consistency and quality.

### Miessler's Approach

Before each AI interaction:
1. Identify relevant context files
2. Load them explicitly
3. Verify context is included in prompt

### Our Implementation

**Context Loader**:
```python
class ContextLoader:
    def __init__(self, base_dir: str = '~/brain/workspace'):
        self.base_dir = os.path.expanduser(base_dir)
        self.global_context_dir = os.path.join(base_dir, 'global_memory/context')
        self.workspace_dir = os.path.join(base_dir, 'workspaces')

    def load_global_context(self, categories: List[str]) -> str:
        """Load global context by category"""
        context_parts = []

        for category in categories:
            category_dir = os.path.join(self.global_context_dir, category)
            if not os.path.exists(category_dir):
                continue

            for filename in os.listdir(category_dir):
                if filename.endswith('.md'):
                    file_path = os.path.join(category_dir, filename)
                    context_parts.append(self._load_file(file_path))

        return "\n\n---\n\n".join(context_parts)

    def load_workspace_context(self, workspace: str) -> str:
        """Load workspace-specific context"""
        workspace_dir = os.path.join(self.workspace_dir, workspace, 'context')

        if not os.path.exists(workspace_dir):
            return ""

        context_parts = []
        for filename in os.listdir(workspace_dir):
            if filename.endswith('.md'):
                file_path = os.path.join(workspace_dir, filename)
                context_parts.append(self._load_file(file_path))

        return "\n\n---\n\n".join(context_parts)

    def load_full_context(self, workspace: str,
                         global_categories: List[str]) -> dict:
        """Load complete context for a task"""
        return {
            'global': self.load_global_context(global_categories),
            'workspace': self.load_workspace_context(workspace),
            'timestamp': datetime.now().isoformat()
        }

    def _load_file(self, file_path: str) -> str:
        with open(file_path) as f:
            content = f.read()

        # Extract frontmatter
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                frontmatter = yaml.safe_load(parts[1])
                content = parts[2].strip()
                return f"# {frontmatter.get('title', 'Untitled')}\n\n{content}"

        return content

    def find_relevant_context(self, task: str, workspace: str,
                             max_files: int = 5) -> List[str]:
        """Use embeddings to find relevant context files"""
        # Phase 2: Use ChromaDB to find most relevant context
        # For now, use simple keyword matching

        keywords = self._extract_keywords(task)
        relevant_files = []

        # Search global context
        for root, dirs, files in os.walk(self.global_context_dir):
            for file in files:
                if file.endswith('.md'):
                    file_path = os.path.join(root, file)
                    if self._matches_keywords(file_path, keywords):
                        relevant_files.append(file_path)

        # Search workspace context
        workspace_context_dir = os.path.join(self.workspace_dir, workspace, 'context')
        if os.path.exists(workspace_context_dir):
            for file in os.listdir(workspace_context_dir):
                if file.endswith('.md'):
                    file_path = os.path.join(workspace_context_dir, file)
                    if self._matches_keywords(file_path, keywords):
                        relevant_files.append(file_path)

        return relevant_files[:max_files]

    def _extract_keywords(self, text: str) -> List[str]:
        # Simple keyword extraction
        stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at'}
        words = text.lower().split()
        return [w for w in words if w not in stopwords and len(w) > 3]

    def _matches_keywords(self, file_path: str, keywords: List[str]) -> bool:
        with open(file_path) as f:
            content = f.read().lower()
        return any(keyword in content for keyword in keywords)
```

### Integration with Orchestrator

```python
class AgnosticOrchestrator:
    def __init__(self, primary: str, agent_configs: dict):
        # ... existing init
        self.context_loader = ContextLoader()

    def execute(self, user_input: str, mode: str = "single"):
        # Load relevant context
        workspace = self.session.context.get('workspace', 'default')

        # Find relevant context files
        relevant_files = self.context_loader.find_relevant_context(
            user_input,
            workspace
        )

        # Load context
        full_context = self.context_loader.load_full_context(
            workspace,
            global_categories=['architecture', 'tools', 'philosophy']
        )

        # Add to session context
        self.session.context.update({
            'global_context': full_context['global'],
            'workspace_context': full_context['workspace'],
            'relevant_files': relevant_files
        })

        # Continue with execution...
        return self._execute_with_context(user_input, mode)
```

### Context Verification

Ensure context is actually used:

```python
def verify_context_loaded(agent_input: str, required_files: List[str]) -> bool:
    """Verify that required context files are included"""
    for file_path in required_files:
        # Check if file content appears in agent input
        with open(file_path) as f:
            file_content = f.read()

        # Simple check: verify key sections are present
        if file_content[:200] not in agent_input:
            logging.warning(f"Context file {file_path} not included in prompt")
            return False

    return True
```

## 3. Fabric Pattern Library

### Concept

[Fabric](https://github.com/danielmiessler/fabric) provides 300+ community-contributed AI patterns (prompts) for common tasks.

**Categories**:
- Analysis: `analyze_claims`, `analyze_paper`, `analyze_tech_impact`
- Creation: `create_summary`, `create_keynote`, `create_quiz`
- Extraction: `extract_wisdom`, `extract_ideas`, `extract_insights`
- Rating: `rate_content`, `rate_ai_response`, `rate_value`

### Installation

```bash
# Install Fabric
pipx install fabric

# Setup (creates ~/.config/fabric/)
fabric --setup

# List patterns
fabric --list

# Use a pattern
echo "text" | fabric --pattern extract_wisdom
```

### Integration with Brain CLI

**Pattern Manager**:
```python
import subprocess

class FabricPatternManager:
    def __init__(self):
        self.fabric_dir = os.path.expanduser('~/.config/fabric/patterns')

    def list_patterns(self) -> List[str]:
        """List available Fabric patterns"""
        if not os.path.exists(self.fabric_dir):
            return []

        return [d for d in os.listdir(self.fabric_dir)
                if os.path.isdir(os.path.join(self.fabric_dir, d))]

    def apply_pattern(self, pattern: str, text: str) -> str:
        """Apply a Fabric pattern to text"""
        result = subprocess.run(
            ['fabric', '--pattern', pattern],
            input=text,
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode != 0:
            raise Exception(f"Fabric pattern failed: {result.stderr}")

        return result.stdout

    def get_pattern_info(self, pattern: str) -> dict:
        """Get pattern metadata"""
        pattern_dir = os.path.join(self.fabric_dir, pattern)
        system_file = os.path.join(pattern_dir, 'system.md')

        if not os.path.exists(system_file):
            return {}

        with open(system_file) as f:
            content = f.read()

        return {
            'name': pattern,
            'description': content[:200],
            'path': pattern_dir
        }

    def create_custom_pattern(self, name: str, system_prompt: str,
                            user_template: str = None):
        """Create a custom Fabric pattern"""
        pattern_dir = os.path.join(self.fabric_dir, name)
        os.makedirs(pattern_dir, exist_ok=True)

        # Write system prompt
        with open(os.path.join(pattern_dir, 'system.md'), 'w') as f:
            f.write(system_prompt)

        # Write user template if provided
        if user_template:
            with open(os.path.join(pattern_dir, 'user.md'), 'w') as f:
                f.write(user_template)
```

### Custom Patterns for Brain CLI

Create domain-specific patterns:

**Pattern: `research_synthesis`**
```markdown
# system.md
You are an expert research synthesizer. Given multiple sources of information about a topic, you:

1. Extract key insights from each source
2. Identify common themes and contradictions
3. Synthesize a coherent understanding
4. Highlight gaps requiring further research
5. Provide actionable recommendations

Output format:
## Key Insights
- [Source 1]: insight
- [Source 2]: insight

## Themes
- Theme 1: explanation
- Theme 2: explanation

## Contradictions
- [Issue]: what conflicts and why

## Knowledge Gaps
- What we still don't know

## Recommendations
- Next steps for research
```

**Pattern: `agent_comparison`**
```markdown
# system.md
You are an expert at comparing AI agent responses. Given multiple responses to the same task:

1. Evaluate each response on:
   - Accuracy and correctness
   - Completeness and thoroughness
   - Clarity and organization
   - Actionability and usefulness

2. Identify strengths and weaknesses of each

3. Determine which response is best overall and why

4. Suggest how to combine the best parts

Output format:
## Response Evaluation

### Agent 1: [name]
- Accuracy: X/10
- Completeness: X/10
- Clarity: X/10
- Actionability: X/10
- Strengths: ...
- Weaknesses: ...

### Agent 2: [name]
...

## Best Response
[Agent name] because...

## Synthesis Recommendation
Combine [aspect] from Agent 1 with [aspect] from Agent 2...
```

### Slash Command Integration

```python
def handle_fabric_command(pattern: str, text: str, console: Console):
    """Apply Fabric pattern via slash command"""
    fabric = FabricPatternManager()

    try:
        result = fabric.apply_pattern(pattern, text)
        console.print(Markdown(result))
    except Exception as e:
        console.print(f"[red]Fabric pattern failed: {e}[/red]")

# In REPL:
# > /fabric extract_wisdom <paste text>
# > /fabric research_synthesis <paste sources>
```

## 4. Observable Verification

### Concept

Always verify AI outputs don't hallucinate or make unfounded claims. Key strategies:

1. **Source Attribution**: Require citations
2. **Fact Checking**: Cross-reference claims
3. **Confidence Scores**: Explicit uncertainty
4. **Human Review**: Flag for manual verification

### Implementation

**Verification Hook**:
```python
def verification_hook(context: HookContext):
    """Check AI responses for verification needs"""
    if context.hook_type != HookType.POST_EXECUTE:
        return

    response = context.result.response

    # Check for claims without sources
    has_unsourced_claims = _detect_unsourced_claims(response)
    if has_unsourced_claims:
        context.metadata['verification_needed'] = True
        context.metadata['reason'] = 'Unsourced claims detected'

    # Check for specific facts
    has_specific_facts = _detect_specific_facts(response)
    if has_specific_facts:
        context.metadata['fact_check_needed'] = True
        context.metadata['facts'] = has_specific_facts

    # Check confidence language
    has_uncertainty = _detect_uncertainty(response)
    if not has_uncertainty and (has_unsourced_claims or has_specific_facts):
        context.metadata['confidence_warning'] = True

def _detect_unsourced_claims(text: str) -> bool:
    # Look for definitive statements without attribution
    claim_patterns = [
        r'\b(?:studies show|research indicates|experts say)\b',
        r'\b(?:the fact is|it is proven|everyone knows)\b',
        r'\b\d+%\b',  # Specific percentages
        r'\$\d+',      # Dollar amounts
    ]

    for pattern in claim_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            # Check if followed by citation
            if not re.search(r'\[[\d,]+\]|\(\w+ \d{4}\)', text):
                return True

    return False

def _detect_specific_facts(text: str) -> List[str]:
    # Extract specific factual claims
    facts = []

    # Numbers and statistics
    numbers = re.findall(r'\b\d+(?:\.\d+)?%|\$\d+(?:,\d{3})*(?:\.\d{2})?', text)
    facts.extend(numbers)

    # Dates
    dates = re.findall(r'\b\d{4}\b|\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}', text)
    facts.extend(dates)

    return facts

def _detect_uncertainty(text: str) -> bool:
    uncertainty_markers = [
        'likely', 'probably', 'possibly', 'may', 'might',
        'appears', 'seems', 'suggests', 'could', 'uncertain'
    ]

    return any(marker in text.lower() for marker in uncertainty_markers)

# Register hook
hook_manager.register(HookType.POST_EXECUTE, verification_hook)
```

**Verification Report**:
```python
def generate_verification_report(context: HookContext) -> str:
    """Generate verification report for human review"""
    metadata = context.metadata

    if not any(k.endswith('_needed') or k.endswith('_warning')
               for k in metadata.keys()):
        return "✅ No verification issues detected"

    report = ["⚠️ Verification Report\n"]

    if metadata.get('verification_needed'):
        report.append(f"- {metadata['reason']}")

    if metadata.get('fact_check_needed'):
        report.append(f"- Fact check needed for: {metadata['facts']}")

    if metadata.get('confidence_warning'):
        report.append("- Response lacks uncertainty markers despite factual claims")

    report.append("\n🔍 Recommendation: Human review suggested")

    return "\n".join(report)
```

## Summary

**Adopted from Miessler**:
- ✅ UFC directory structure (adapted for multi-domain)
- ✅ Mandatory context loading (with auto-discovery)
- ✅ Fabric pattern library integration
- ✅ Observable verification (automated checks)

**Our Enhancements**:
- ✅ Extended UFC for agent-agnostic operation
- ✅ Automatic context relevance detection
- ✅ Custom Fabric patterns for agent comparison
- ✅ Automated verification hooks with reporting

## Next Document

See `05-OBSIDIAN-INTEGRATION.md` for knowledge management and vault integration.
