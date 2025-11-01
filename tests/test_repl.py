"""Test REPL functionality."""

import asyncio
import os
import shutil
from unittest.mock import AsyncMock, patch, MagicMock
from brain.repl import BrainREPL


async def test_repl_initialization():
    """Test REPL initializes correctly."""
    print("\n🧪 Testing REPL - Initialization")
    print("=" * 60)

    # Create REPL
    repl = BrainREPL(
        workspace_path=os.getcwd(),
        session_name='test-repl',
        primary_agent='claude-code'
    )

    print(f"\n✅ REPL initialized")
    print(f"   Workspace: {repl.workspace_path}")
    print(f"   Session: {repl.session.workspace if repl.session else 'None'}")
    print(f"   Primary: {repl.primary_agent}")

    # Check components
    assert repl.orchestrator is not None, "Should have orchestrator"
    assert repl.session is not None, "Should have session"
    assert repl.session_registry is not None, "Should have registry"

    print(f"\n✅ All components initialized")

    # Cleanup
    shutil.rmtree(os.path.expanduser('~/brain/workspace/.sessions/test-repl'), ignore_errors=True)

    return True


async def test_routing_suggestion_accept():
    """Test accepting multi-agent suggestion."""
    print("\n\n🧪 Testing REPL - Routing Suggestion (Accept)")
    print("=" * 60)

    repl = BrainREPL(workspace_path=os.getcwd())

    # Mock routing plan
    from brain.agents.base import RoutingPlan
    suggestion = RoutingPlan(
        task="Complex task",
        intent="complex_task",
        complexity=0.8,
        requires_multiple=True,
        recommended_agents=['claude-code', 'claude-code', 'claude-code'],
        parallel_execution=True,
        context={},
        estimated_tokens=1000
    )

    # Mock user input: Yes, 3 agents
    with patch('brain.repl.Confirm.ask', return_value=True):
        with patch('brain.repl.Prompt.ask', return_value='3'):
            mode, num_agents = await repl.handle_routing_suggestion(
                "Complex task",
                suggestion
            )

    print(f"\n✅ User accepted suggestion")
    print(f"   Mode: {mode}")
    print(f"   Num agents: {num_agents}")

    assert mode == "multi", "Should use multi mode"
    assert num_agents == 3, "Should use 3 agents"

    return True


async def test_routing_suggestion_decline():
    """Test declining multi-agent suggestion."""
    print("\n\n🧪 Testing REPL - Routing Suggestion (Decline)")
    print("=" * 60)

    repl = BrainREPL(workspace_path=os.getcwd())

    from brain.agents.base import RoutingPlan
    suggestion = RoutingPlan(
        task="Complex task",
        intent="complex_task",
        complexity=0.8,
        requires_multiple=True,
        recommended_agents=['claude-code', 'claude-code'],
        parallel_execution=True,
        context={},
        estimated_tokens=1000
    )

    # Mock user input: No
    with patch('brain.repl.Confirm.ask', return_value=False):
        mode, num_agents = await repl.handle_routing_suggestion(
            "Complex task",
            suggestion
        )

    print(f"\n✅ User declined suggestion")
    print(f"   Mode: {mode}")
    print(f"   Num agents: {num_agents}")

    assert mode == "single", "Should use single mode"
    assert num_agents is None, "Should not specify num_agents"

    return True


async def test_command_parsing():
    """Test command parsing."""
    print("\n\n🧪 Testing REPL - Command Parsing")
    print("=" * 60)

    repl = BrainREPL(workspace_path=os.getcwd())

    # Test /status command
    print("\n📝 Testing /status command...")
    await repl.handle_command('/status')
    print("✅ /status works")

    # Test /help command
    print("\n📝 Testing /help command...")
    await repl.handle_command('/help')
    print("✅ /help works")

    # Test /save command
    print("\n📝 Testing /save command...")
    await repl.handle_command('/save')
    print("✅ /save works")

    print("\n✅ All commands parsed successfully")

    # Cleanup
    shutil.rmtree(os.path.expanduser('~/brain/workspace/.sessions/default'), ignore_errors=True)

    return True


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("🧠 REPL Tests")
    print("=" * 60)

    results = []

    try:
        results.append(await test_repl_initialization())
    except Exception as e:
        print(f"\n❌ Test 1 failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(False)

    try:
        results.append(await test_routing_suggestion_accept())
    except Exception as e:
        print(f"\n❌ Test 2 failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(False)

    try:
        results.append(await test_routing_suggestion_decline())
    except Exception as e:
        print(f"\n❌ Test 3 failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(False)

    try:
        results.append(await test_command_parsing())
    except Exception as e:
        print(f"\n❌ Test 4 failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(False)

    # Summary
    print("\n" + "=" * 60)
    print(f"📊 Results: {sum(results)}/{len(results)} tests passed")
    print("=" * 60 + "\n")

    return all(results)


if __name__ == '__main__':
    success = asyncio.run(main())
    exit(0 if success else 1)
