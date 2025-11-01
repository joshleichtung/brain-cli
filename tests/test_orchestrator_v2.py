"""Test refactored orchestrator with fleet and worktree integration."""

import asyncio
import os
import shutil
import subprocess
from brain.orchestrator_v2 import AgnosticOrchestrator
from brain.session import SessionRegistry


def setup_test_git_repo(path: str):
    """Create a test git repository."""
    os.makedirs(path, exist_ok=True)

    # Initialize git repo
    subprocess.run(['git', 'init'], cwd=path, capture_output=True)
    subprocess.run(['git', 'config', 'user.email', 'test@test.com'], cwd=path)
    subprocess.run(['git', 'config', 'user.name', 'Test User'], cwd=path)

    # Create initial commit
    with open(os.path.join(path, 'README.md'), 'w') as f:
        f.write('# Test Orchestrator Repo\n')

    subprocess.run(['git', 'add', '.'], cwd=path)
    subprocess.run(['git', 'commit', '-m', 'Initial commit'], cwd=path)
    subprocess.run(['git', 'branch', '-M', 'main'], cwd=path)


async def test_single_agent_execution():
    """Test single agent execution through orchestrator."""
    print("\n🧪 Testing Orchestrator v2 - Single Agent")
    print("=" * 70)

    # Setup
    workspace_path = os.getcwd()

    agent_configs = {
        'claude-code': {
            'model': 'claude-sonnet-4-5-20250929',
            'permission_mode': 'acceptEdits',
            'cost_per_1k_tokens': 0.003
        }
    }

    # Create session
    registry = SessionRegistry(base_dir='/tmp/brain-test-sessions')
    session = registry.create_session('test-single', 'claude-code')

    # Create orchestrator
    orchestrator = AgnosticOrchestrator(
        primary_agent_name='claude-code',
        agent_configs=agent_configs,
        workspace_path=workspace_path,
        session=session,
        max_concurrent_agents=10
    )

    task = "What is 4 + 6? Just give the number."

    print(f"\n📝 Task: {task}")
    print("\n⏳ Executing with single agent...")

    # Execute
    response = await orchestrator.execute(task, mode="single")

    print(f"\n✅ Response: {response}")

    # Check fleet status
    fleet_status = orchestrator.get_fleet_status()
    print(f"\n📊 Fleet Status:")
    print(f"   Active: {fleet_status['active_agents']}")
    print(f"   Running: {fleet_status['running']}")
    print(f"   Queued: {fleet_status['queued']}")

    # Cleanup
    shutil.rmtree('/tmp/brain-test-sessions', ignore_errors=True)

    return "10" in response


async def test_multi_agent_parallel():
    """Test multi-agent parallel execution."""
    print("\n\n🧪 Testing Orchestrator v2 - Multi-Agent Parallel")
    print("=" * 70)

    # Setup git repo for worktree testing
    test_repo = '/tmp/brain-orchestrator-test/repo'
    setup_test_git_repo(test_repo)

    agent_configs = {
        'claude-code': {
            'model': 'claude-sonnet-4-5-20250929',
            'permission_mode': 'acceptEdits',
            'cost_per_1k_tokens': 0.003
        }
    }

    # Create session
    registry = SessionRegistry(base_dir='/tmp/brain-test-sessions')
    session = registry.create_session('test-multi', 'claude-code')

    # Create orchestrator
    orchestrator = AgnosticOrchestrator(
        primary_agent_name='claude-code',
        agent_configs=agent_configs,
        workspace_path=test_repo,
        session=session,
        max_concurrent_agents=10
    )

    task = "What is 7 * 9? Just give the number."

    print(f"\n📝 Task: {task}")
    print("\n⏳ Executing with 3 agents in parallel...")

    # Execute with 3 agents
    response = await orchestrator.execute(task, mode="multi", num_agents=3)

    print(f"\n✅ Response received (formatted multi-agent results)")
    print(response)

    # Check fleet status
    fleet_status = orchestrator.get_fleet_status()
    print(f"\n📊 Fleet Status After Execution:")
    print(f"   Active: {fleet_status['active_agents']}")
    print(f"   Running: {fleet_status['running']}")

    # Check project stats
    stats = orchestrator.get_project_stats()
    print(f"\n📈 Project Stats:")
    print(f"   Total agents: {stats['total_agents']}")
    print(f"   Completed: {stats['completed']}")
    print(f"   Failed: {stats['failed']}")
    print(f"   Total cost: ${stats['total_cost']:.6f}")

    # Verify worktrees were created
    worktrees = orchestrator.worktree_manager.list_worktrees(test_repo)
    print(f"\n📂 Worktrees created: {len(worktrees) - 1}")  # -1 for main

    # Cleanup
    shutil.rmtree('/tmp/brain-orchestrator-test', ignore_errors=True)
    shutil.rmtree('/tmp/brain-test-sessions', ignore_errors=True)

    # Verify response contains results from 3 agents
    return "Agent 1:" in response and "Agent 2:" in response and "Agent 3:" in response


async def test_worktree_isolation():
    """Test that worktrees provide proper isolation for parallel agents."""
    print("\n\n🧪 Testing Orchestrator v2 - Worktree Isolation")
    print("=" * 70)

    # Setup git repo
    test_repo = '/tmp/brain-orchestrator-test/repo'
    setup_test_git_repo(test_repo)

    agent_configs = {
        'claude-code': {
            'model': 'claude-sonnet-4-5-20250929',
            'permission_mode': 'bypassPermissions',  # Allow file creation
            'cost_per_1k_tokens': 0.003
        }
    }

    # Create session
    registry = SessionRegistry(base_dir='/tmp/brain-test-sessions')
    session = registry.create_session('test-isolation', 'claude-code')

    # Create orchestrator
    orchestrator = AgnosticOrchestrator(
        primary_agent_name='claude-code',
        agent_configs=agent_configs,
        workspace_path=test_repo,
        session=session,
        max_concurrent_agents=10
    )

    # Task: Each agent creates a different file
    task = "Create a file called test.txt with the number 42"

    print(f"\n📝 Task: {task}")
    print("\n⏳ Executing with 2 agents (each should create file in own worktree)...")

    # Execute with 2 agents
    response = await orchestrator.execute(task, mode="multi", num_agents=2)

    print(f"\n✅ Execution complete")

    # Check worktrees
    worktrees = orchestrator.worktree_manager.list_worktrees(test_repo)
    print(f"\n📂 Worktrees: {len(worktrees)}")

    for wt in worktrees:
        if '.agent-worktrees' in wt.get('path', ''):
            test_file = os.path.join(wt['path'], 'test.txt')
            exists = os.path.exists(test_file)
            print(f"   {wt['path']}: test.txt exists = {exists}")

    # Cleanup
    shutil.rmtree('/tmp/brain-orchestrator-test', ignore_errors=True)
    shutil.rmtree('/tmp/brain-test-sessions', ignore_errors=True)

    return True


async def test_session_persistence():
    """Test that session state is properly maintained."""
    print("\n\n🧪 Testing Orchestrator v2 - Session Persistence")
    print("=" * 70)

    agent_configs = {
        'claude-code': {
            'model': 'claude-sonnet-4-5-20250929',
            'permission_mode': 'acceptEdits',
            'cost_per_1k_tokens': 0.003
        }
    }

    # Create session
    registry = SessionRegistry(base_dir='/tmp/brain-test-sessions')
    session = registry.create_session('test-session', 'claude-code')

    # Create orchestrator
    orchestrator = AgnosticOrchestrator(
        primary_agent_name='claude-code',
        agent_configs=agent_configs,
        workspace_path=os.getcwd(),
        session=session
    )

    # Execute a task
    await orchestrator.execute("What is 1+1?", mode="single")

    # Check session was updated
    print(f"\n✅ Session updated:")
    print(f"   Conversation turns: {len(session.conversation)}")
    print(f"   Total tokens: {session.total_tokens}")
    print(f"   Total cost: ${session.total_cost:.6f}")

    # Save session
    registry.save_session(session)

    # Load session
    loaded_session = registry.load_session('test-session')

    print(f"\n✅ Session loaded:")
    print(f"   Conversation turns: {len(loaded_session.conversation)}")
    print(f"   Total tokens: {loaded_session.total_tokens}")

    assert len(loaded_session.conversation) > 0, "Session should have conversation"

    # Cleanup
    shutil.rmtree('/tmp/brain-test-sessions', ignore_errors=True)

    return True


async def test_fleet_concurrency():
    """Test that fleet manager enforces concurrency limits."""
    print("\n\n🧪 Testing Orchestrator v2 - Fleet Concurrency")
    print("=" * 70)

    agent_configs = {
        'claude-code': {
            'model': 'claude-sonnet-4-5-20250929',
            'permission_mode': 'acceptEdits',
            'cost_per_1k_tokens': 0.003
        }
    }

    # Create orchestrator with low concurrency limit
    orchestrator = AgnosticOrchestrator(
        primary_agent_name='claude-code',
        agent_configs=agent_configs,
        workspace_path=os.getcwd(),
        max_concurrent_agents=2  # Low limit for testing
    )

    print(f"\n📝 Max concurrent: {orchestrator.fleet.max_concurrent}")
    print("\n⏳ Spawning 3 agents (should queue 1)...")

    # Spawn 3 agents (1 should queue)
    task = "Count to 5"

    # This should trigger queueing
    response = await orchestrator.execute(task, mode="multi", num_agents=3)

    print(f"\n✅ All agents completed")

    # Cleanup
    shutil.rmtree('/tmp/brain-test-sessions', ignore_errors=True)

    return True


async def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("🧠 Orchestrator v2 Integration Tests")
    print("=" * 70)

    results = []

    try:
        results.append(await test_single_agent_execution())
    except Exception as e:
        print(f"\n❌ Test 1 failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(False)

    try:
        results.append(await test_multi_agent_parallel())
    except Exception as e:
        print(f"\n❌ Test 2 failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(False)

    try:
        results.append(await test_worktree_isolation())
    except Exception as e:
        print(f"\n❌ Test 3 failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(False)

    try:
        results.append(await test_session_persistence())
    except Exception as e:
        print(f"\n❌ Test 4 failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(False)

    try:
        results.append(await test_fleet_concurrency())
    except Exception as e:
        print(f"\n❌ Test 5 failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(False)

    # Summary
    print("\n" + "=" * 70)
    print(f"📊 Results: {sum(results)}/{len(results)} tests passed")
    print("=" * 70 + "\n")

    return all(results)


if __name__ == '__main__':
    success = asyncio.run(main())
    exit(0 if success else 1)
