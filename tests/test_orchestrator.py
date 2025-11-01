"""Tests for orchestrator functionality."""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from brain.agents import ClaudeAgent, GeminiAgent
from brain.orchestrator import AgnosticOrchestrator
from brain.router import SimpleRouter
from brain.session import SessionRegistry


def test_router():
    """Test the simple router."""
    print("\n=== Testing Router ===")
    router = SimpleRouter()

    # Test intent classification
    test_cases = [
        ("Write a Python function", "code"),
        ("Research quantum computing", "research"),
        ("Explain how this works", "analysis"),
        ("Design a creative logo", "creative"),
        ("Hello, how are you?", "general"),
    ]

    for task, expected_intent in test_cases:
        intent = router.classify_intent(task)
        status = "✅" if intent == expected_intent else "❌"
        print(f"{status} '{task}' -> {intent} (expected: {expected_intent})")

    print("✅ Router tests complete")


def test_agent_creation():
    """Test agent creation and health checks."""
    print("\n=== Testing Agent Creation ===")

    # Claude agent
    claude_config = {
        'name': 'claude',
        'model': 'claude-sonnet-4-5-20250929',
        'cost_per_1k_tokens': 0.003
    }

    # Gemini agent
    gemini_config = {
        'name': 'gemini',
        'model': 'gemini-1.5-pro',
        'cost_per_1k_tokens': 0.00125
    }

    agents = {}

    try:
        claude = ClaudeAgent(claude_config)
        agents['claude'] = claude
        print("✅ Claude agent created")
    except Exception as e:
        print(f"⚠️  Claude agent creation failed: {e}")

    try:
        gemini = GeminiAgent(gemini_config)
        agents['gemini'] = gemini
        print("✅ Gemini agent created")
    except Exception as e:
        print(f"⚠️  Gemini agent creation failed: {e}")

    # Health checks
    print("\n=== Agent Health Checks ===")
    for name, agent in agents.items():
        try:
            is_healthy = agent.ping()
            status = "✅" if is_healthy else "❌"
            print(f"{status} {name} health check")
        except Exception as e:
            print(f"❌ {name} health check failed: {e}")

    return agents


def test_orchestrator(agents):
    """Test orchestrator functionality."""
    if not agents:
        print("\n⚠️  Skipping orchestrator tests (no agents available)")
        return

    print("\n=== Testing Orchestrator ===")

    # Create orchestrator with Claude as primary
    orchestrator = AgnosticOrchestrator('claude', agents)
    print(f"✅ Orchestrator created with primary: {orchestrator.primary_name}")

    # Test agent status
    status = orchestrator.get_agent_status()
    print("\nAgent Status:")
    for name, healthy in status.items():
        status_str = "✅" if healthy else "❌"
        print(f"  {status_str} {name}")

    # Test execution (if we have a working agent)
    working_agents = [name for name, healthy in status.items() if healthy]
    if working_agents:
        print(f"\n=== Testing Execution with {working_agents[0]} ===")
        try:
            response = orchestrator.execute("What is 2+2?")
            print(f"✅ Got response: {response[:100]}...")
        except Exception as e:
            print(f"❌ Execution failed: {e}")

        # Test agent switching
        if len(working_agents) > 1:
            print(f"\n=== Testing Agent Switching ===")
            try:
                orchestrator.switch_orchestrator(working_agents[1])
                print(f"✅ Switched to {working_agents[1]}")

                response = orchestrator.execute("What is 3+3?")
                print(f"✅ Got response from {working_agents[1]}: {response[:100]}...")
            except Exception as e:
                print(f"❌ Agent switching failed: {e}")
    else:
        print("\n⚠️  Skipping execution tests (no working agents)")

    print("\n✅ Orchestrator tests complete")


def test_session_management():
    """Test session registry."""
    print("\n=== Testing Session Management ===")

    # Use a test directory
    test_dir = '/tmp/brain-test-sessions'
    registry = SessionRegistry(base_dir=test_dir)

    # Create session
    session = registry.create_session('test-workspace', 'claude')
    print(f"✅ Created session: {session.id}")

    # Add turn
    from brain.session import Turn
    from datetime import datetime

    turn = Turn(
        role='user',
        content='Test message',
        agent='claude',
        timestamp=datetime.now(),
        tokens=10,
        cost=0.0001
    )
    registry.add_turn(session, turn)
    print(f"✅ Added turn to session")

    # Save session
    registry.save_session(session)
    print(f"✅ Saved session")

    # Load session
    loaded_session = registry.load_session('test-workspace')
    assert loaded_session is not None, "Failed to load session"
    assert len(loaded_session.conversation) == 1, "Conversation not preserved"
    print(f"✅ Loaded session with {len(loaded_session.conversation)} turns")

    # Clean up
    import shutil
    shutil.rmtree(test_dir, ignore_errors=True)
    print(f"✅ Cleaned up test directory")

    print("\n✅ Session management tests complete")


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("Brain CLI - Orchestrator Tests")
    print("="*60)

    # Test router
    test_router()

    # Test agents
    agents = test_agent_creation()

    # Test orchestrator
    test_orchestrator(agents)

    # Test session management
    test_session_management()

    print("\n" + "="*60)
    print("All tests complete!")
    print("="*60 + "\n")


if __name__ == '__main__':
    main()
