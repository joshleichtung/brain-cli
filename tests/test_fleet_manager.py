"""Test AgentFleetManager."""

import asyncio
import os
import shutil
from brain.fleet import AgentFleetManager, AgentStatus
from brain.agents import ClaudeCodeAgent


async def test_single_agent_spawn():
    """Test spawning a single agent."""
    print("\n🧪 Testing Fleet Manager - Single Agent Spawn")
    print("=" * 60)

    # Create test database
    db_path = '/tmp/brain-fleet-test/agents.db'
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    fleet = AgentFleetManager(db_path=db_path, max_concurrent=10)

    config = {
        'name': 'claude-code',
        'model': 'claude-sonnet-4-5-20250929',
        'workspace_path': os.getcwd(),
        'permission_mode': 'acceptEdits',
        'cost_per_1k_tokens': 0.003
    }

    task = "What is 3 + 7? Just give the number."
    project = "test-project"

    print(f"\n📝 Spawning agent for: {task}")

    agent_id = await fleet.spawn_agent(
        agent_class=ClaudeCodeAgent,
        task=task,
        project=project,
        config=config
    )

    print(f"\n🚀 Agent spawned: {agent_id}")
    print(f"   Running agents: {fleet.get_running_count()}")

    # Wait for completion
    print(f"\n⏳ Waiting for agent to complete...")

    result = await fleet.wait_for_agent(agent_id, timeout=30.0)

    print(f"\n✅ Agent completed!")
    print(f"   Response: {result.response}")
    print(f"   Tokens: {result.tokens_used}")
    print(f"   Cost: ${result.cost:.6f}")
    print(f"   Time: {result.time_taken:.2f}s")

    # Check status
    instance = fleet.get_agent_status(agent_id)
    print(f"\n📊 Agent Status: {instance.status.value}")

    # Cleanup
    fleet.cleanup_completed()
    shutil.rmtree('/tmp/brain-fleet-test', ignore_errors=True)

    return result


async def test_multi_agent_parallel():
    """Test spawning multiple agents in parallel."""
    print("\n\n🧪 Testing Fleet Manager - Multi-Agent Parallel")
    print("=" * 60)

    db_path = '/tmp/brain-fleet-test/agents.db'
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    fleet = AgentFleetManager(db_path=db_path, max_concurrent=10)

    config = {
        'name': 'claude-code',
        'workspace_path': os.getcwd(),
        'permission_mode': 'acceptEdits',
        'cost_per_1k_tokens': 0.003
    }

    tasks = [
        "What is 2+2?",
        "What is 5*3?",
        "What is 10-4?"
    ]

    print(f"\n📝 Spawning {len(tasks)} agents in parallel...")

    agent_ids = []
    for task in tasks:
        agent_id = await fleet.spawn_agent(
            agent_class=ClaudeCodeAgent,
            task=task,
            project="math-tasks",
            config=config
        )
        agent_ids.append(agent_id)
        print(f"   🚀 {agent_id}: {task}")

    print(f"\n⏳ Running agents: {fleet.get_running_count()}")
    print(f"   Waiting for all to complete...")

    # Wait for all
    results = await fleet.wait_for_all(timeout=60.0)

    print(f"\n✅ All agents completed!")
    print(f"\n📊 Results:")
    for agent_id, result in results.items():
        print(f"   {agent_id}:")
        print(f"      Response: {result.response}")
        print(f"      Cost: ${result.cost:.6f}")

    # Get project stats
    stats = fleet.get_project_stats("math-tasks")
    print(f"\n📈 Project Stats:")
    print(f"   Total agents: {stats['total_agents']}")
    print(f"   Total tokens: {stats['total_tokens']}")
    print(f"   Total cost: ${stats['total_cost']:.6f}")
    print(f"   Completed: {stats['completed']}")
    print(f"   Failed: {stats['failed']}")

    # Cleanup
    fleet.cleanup_completed()
    shutil.rmtree('/tmp/brain-fleet-test', ignore_errors=True)

    return results


async def test_concurrency_limit():
    """Test that concurrency limit is enforced."""
    print("\n\n🧪 Testing Fleet Manager - Concurrency Limit")
    print("=" * 60)

    db_path = '/tmp/brain-fleet-test/agents.db'
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    # Set low limit for testing
    fleet = AgentFleetManager(db_path=db_path, max_concurrent=2)

    config = {
        'name': 'claude-code',
        'workspace_path': os.getcwd(),
        'permission_mode': 'acceptEdits',
        'cost_per_1k_tokens': 0.003
    }

    print(f"\n📝 Max concurrent: {fleet.max_concurrent}")
    print(f"   Spawning 4 agents (should queue 2)...")

    tasks = ["Task 1", "Task 2", "Task 3", "Task 4"]

    for i, task in enumerate(tasks, 1):
        await fleet.spawn_agent(
            agent_class=ClaudeCodeAgent,
            task=f"Count to {i}",
            project="test",
            config=config
        )

    print(f"\n📊 Status:")
    print(f"   Running: {fleet.get_running_count()}")
    print(f"   Queued: {fleet.get_queue_size()}")

    # Should have 2 running, 2 queued
    assert fleet.get_running_count() <= 2, "Should not exceed max concurrent"
    print(f"\n✅ Concurrency limit enforced!")

    # Wait for all (queue should process automatically)
    await fleet.wait_for_all(timeout=120.0)

    print(f"\n✅ All agents completed (including queued)")

    # Cleanup
    fleet.cleanup_completed()
    shutil.rmtree('/tmp/brain-fleet-test', ignore_errors=True)


async def test_agent_listing():
    """Test listing agents by project."""
    print("\n\n🧪 Testing Fleet Manager - Agent Listing")
    print("=" * 60)

    db_path = '/tmp/brain-fleet-test/agents.db'
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    fleet = AgentFleetManager(db_path=db_path, max_concurrent=10)

    config = {
        'name': 'claude-code',
        'workspace_path': os.getcwd(),
        'permission_mode': 'acceptEdits',
        'cost_per_1k_tokens': 0.003
    }

    # Spawn agents on different projects
    await fleet.spawn_agent(ClaudeCodeAgent, "Task A1", "project-a", config)
    await fleet.spawn_agent(ClaudeCodeAgent, "Task A2", "project-a", config)
    await fleet.spawn_agent(ClaudeCodeAgent, "Task B1", "project-b", config)

    print(f"\n📊 Active agents: {len(fleet.list_active_agents())}")

    project_a_agents = fleet.list_agents_by_project("project-a")
    project_b_agents = fleet.list_agents_by_project("project-b")

    print(f"   Project A: {len(project_a_agents)} agents")
    print(f"   Project B: {len(project_b_agents)} agents")

    assert len(project_a_agents) == 2, "Should have 2 agents on project-a"
    assert len(project_b_agents) == 1, "Should have 1 agent on project-b"

    print(f"\n✅ Agent listing works correctly!")

    # Cleanup
    await fleet.wait_for_all(timeout=60.0)
    fleet.cleanup_completed()
    shutil.rmtree('/tmp/brain-fleet-test', ignore_errors=True)


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("🧠 AgentFleetManager Tests")
    print("=" * 60)

    results = []

    try:
        await test_single_agent_spawn()
        results.append(True)
    except Exception as e:
        print(f"\n❌ Test 1 failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(False)

    try:
        await test_multi_agent_parallel()
        results.append(True)
    except Exception as e:
        print(f"\n❌ Test 2 failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(False)

    try:
        await test_concurrency_limit()
        results.append(True)
    except Exception as e:
        print(f"\n❌ Test 3 failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(False)

    try:
        await test_agent_listing()
        results.append(True)
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
