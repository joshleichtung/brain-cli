"""Test ClaudeCodeAgent using Agent SDK."""

import asyncio
import os
from brain.agents import ClaudeCodeAgent


async def test_simple_execution():
    """Test simple task execution."""
    print("\n🧪 Testing ClaudeCodeAgent - Simple Execution")
    print("=" * 60)

    config = {
        'name': 'claude-code',
        'model': 'claude-sonnet-4-5-20250929',
        'workspace_path': os.getcwd(),
        'permission_mode': 'acceptEdits',
        'cost_per_1k_tokens': 0.003
    }

    agent = ClaudeCodeAgent(config)

    task = "What is the capital of France? Just give the city name."

    print(f"\n📝 Task: {task}")
    print("\n💬 Executing...")

    result = await agent.execute(task, context={})

    print(f"\n✅ Response: {result.response}")
    print(f"\n📊 Stats:")
    print(f"   Agent: {result.agent_name}")
    print(f"   Time: {result.time_taken:.2f}s")
    print(f"   Tokens: {result.tokens_used}")
    print(f"   Cost: ${result.cost:.6f}")
    print(f"   Tools used: {result.metadata.get('num_tools_used', 0)}")

    return result


async def test_file_operations():
    """Test file operation tool use."""
    print("\n\n🧪 Testing ClaudeCodeAgent - File Operations")
    print("=" * 60)

    config = {
        'name': 'claude-code',
        'workspace_path': '/tmp/brain-test',
        'permission_mode': 'bypassPermissions',  # Auto-approve for testing
        'cost_per_1k_tokens': 0.003
    }

    # Create test directory
    os.makedirs('/tmp/brain-test', exist_ok=True)

    agent = ClaudeCodeAgent(config)

    task = "Create a file called hello.txt with the content 'Hello from ClaudeCodeAgent!'"

    print(f"\n📝 Task: {task}")
    print("\n💬 Executing...")

    result = await agent.execute(task, context={})

    print(f"\n✅ Response: {result.response}")
    print(f"\n📊 Stats:")
    print(f"   Tools used: {result.metadata.get('num_tools_used', 0)}")
    print(f"   Cost: ${result.cost:.6f}")

    # Verify file was created
    if os.path.exists('/tmp/brain-test/hello.txt'):
        with open('/tmp/brain-test/hello.txt') as f:
            content = f.read()
        print(f"\n✅ File created successfully!")
        print(f"   Content: {content}")
    else:
        print(f"\n⚠️  File was not created")

    # Cleanup
    import shutil
    shutil.rmtree('/tmp/brain-test', ignore_errors=True)

    return result


async def test_routing_plan():
    """Test routing plan creation."""
    print("\n\n🧪 Testing ClaudeCodeAgent - Routing Plan")
    print("=" * 60)

    config = {
        'name': 'claude-code',
        'permission_mode': 'acceptEdits',
        'cost_per_1k_tokens': 0.003
    }

    agent = ClaudeCodeAgent(config)

    task = "Analyze my codebase and find all TODO comments"

    available_agents = {
        'claude-code': agent,
        'gemini': None,  # Mock
        'aider': None    # Mock
    }

    print(f"\n📝 Task: {task}")
    print(f"\n🤖 Available agents: {', '.join(available_agents.keys())}")
    print("\n💬 Creating routing plan...")

    plan = await agent.create_routing_plan(task, available_agents, context={})

    print(f"\n✅ Routing Plan:")
    print(f"   Intent: {plan.intent}")
    print(f"   Complexity: {plan.complexity}")
    print(f"   Requires multiple: {plan.requires_multiple}")
    print(f"   Recommended agents: {', '.join(plan.recommended_agents)}")
    print(f"   Parallel execution: {plan.parallel_execution}")
    print(f"   Estimated tokens: {plan.estimated_tokens}")

    return plan


async def test_health_check():
    """Test agent health check."""
    print("\n\n🧪 Testing ClaudeCodeAgent - Health Check")
    print("=" * 60)

    config = {
        'name': 'claude-code',
        'permission_mode': 'acceptEdits',
        'cost_per_1k_tokens': 0.003
    }

    agent = ClaudeCodeAgent(config)

    print("\n💬 Pinging agent...")

    is_healthy = await agent.ping()

    if is_healthy:
        print("\n✅ Agent is healthy and responsive")
    else:
        print("\n❌ Agent is not responding")

    return is_healthy


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("🧠 ClaudeCodeAgent Integration Tests")
    print("=" * 60)

    results = []

    try:
        # Test 1: Simple execution
        result1 = await test_simple_execution()
        results.append(True)
    except Exception as e:
        print(f"\n❌ Test 1 failed: {e}")
        results.append(False)

    try:
        # Test 2: File operations
        result2 = await test_file_operations()
        results.append(True)
    except Exception as e:
        print(f"\n❌ Test 2 failed: {e}")
        results.append(False)

    try:
        # Test 3: Routing plan
        result3 = await test_routing_plan()
        results.append(True)
    except Exception as e:
        print(f"\n❌ Test 3 failed: {e}")
        results.append(False)

    try:
        # Test 4: Health check
        result4 = await test_health_check()
        results.append(result4)
    except Exception as e:
        print(f"\n❌ Test 4 failed: {e}")
        results.append(False)

    # Summary
    print("\n" + "=" * 60)
    print(f"📊 Results: {sum(results)}/{len(results)} tests passed")
    print("=" * 60 + "\n")

    return all(results)


if __name__ == '__main__':
    success = asyncio.run(main())
    exit(0 if success else 1)
