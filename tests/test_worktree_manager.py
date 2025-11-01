"""Test WorktreeManager."""

import os
import subprocess
import shutil
from brain.worktree import WorktreeManager


def setup_test_repo(path: str):
    """Create a test git repository."""
    os.makedirs(path, exist_ok=True)

    # Initialize git repo
    subprocess.run(['git', 'init'], cwd=path, capture_output=True)
    subprocess.run(['git', 'config', 'user.email', 'test@test.com'], cwd=path)
    subprocess.run(['git', 'config', 'user.name', 'Test User'], cwd=path)

    # Create initial commit
    with open(os.path.join(path, 'README.md'), 'w') as f:
        f.write('# Test Repo\n')

    subprocess.run(['git', 'add', '.'], cwd=path)
    subprocess.run(['git', 'commit', '-m', 'Initial commit'], cwd=path)

    # Create main branch if not exists
    subprocess.run(['git', 'branch', '-M', 'main'], cwd=path)


def test_git_detection():
    """Test git repository detection."""
    print("\n🧪 Testing WorktreeManager - Git Detection")
    print("=" * 60)

    manager = WorktreeManager()

    # Create test repo
    test_repo = '/tmp/brain-worktree-test/repo'
    setup_test_repo(test_repo)

    # Test detection
    is_repo = manager.is_git_repo(test_repo)
    print(f"\n✅ Git repo detected: {is_repo}")

    assert is_repo, "Should detect git repository"

    # Test non-repo
    non_repo = '/tmp/brain-worktree-test/non-repo'
    os.makedirs(non_repo, exist_ok=True)

    is_not_repo = manager.is_git_repo(non_repo)
    print(f"✅ Non-repo detected correctly: {not is_not_repo}")

    assert not is_not_repo, "Should not detect non-git directory as repo"

    # Get repo root
    root = manager.get_repo_root(test_repo)
    print(f"✅ Repo root: {root}")

    # Resolve both paths to handle symlinks (e.g., /tmp -> /private/tmp on macOS)
    assert os.path.realpath(root) == os.path.realpath(test_repo), "Should get correct repo root"

    # Cleanup
    shutil.rmtree('/tmp/brain-worktree-test', ignore_errors=True)

    return True


def test_worktree_creation():
    """Test creating worktrees."""
    print("\n\n🧪 Testing WorktreeManager - Worktree Creation")
    print("=" * 60)

    manager = WorktreeManager()

    # Setup test repo
    test_repo = '/tmp/brain-worktree-test/repo'
    setup_test_repo(test_repo)

    # Create worktree
    agent_id = 'test-agent-123'
    worktree_path = manager.create_worktree(test_repo, agent_id)

    print(f"\n✅ Worktree created: {worktree_path}")

    assert worktree_path is not None, "Should create worktree"
    assert os.path.exists(worktree_path), "Worktree path should exist"
    assert '.agent-worktrees' in worktree_path, "Should be in .agent-worktrees directory"

    # Verify it's tracked
    assert agent_id in manager.active_worktrees, "Should track worktree"
    worktree = manager.active_worktrees[agent_id]

    print(f"   Path: {worktree.path}")
    print(f"   Branch: {worktree.branch}")
    print(f"   Locked: {worktree.locked}")

    # Cleanup
    manager.remove_worktree(agent_id, force=True)
    shutil.rmtree('/tmp/brain-worktree-test', ignore_errors=True)

    return True


def test_get_or_create():
    """Test get_or_create_worktree logic."""
    print("\n\n🧪 Testing WorktreeManager - Get or Create")
    print("=" * 60)

    manager = WorktreeManager()

    # Setup test repo
    test_repo = '/tmp/brain-worktree-test/repo'
    setup_test_repo(test_repo)

    agent_id = 'test-agent-456'

    # First call - should create
    path1 = manager.get_or_create_worktree(test_repo, agent_id)
    print(f"\n✅ First call created: {path1}")

    # Second call - should reuse
    path2 = manager.get_or_create_worktree(test_repo, agent_id)
    print(f"✅ Second call reused: {path2}")

    assert path1 == path2, "Should return same path on second call"
    assert '.agent-worktrees' in path1, "Should be worktree path"

    # Test with non-git directory
    non_repo = '/tmp/brain-worktree-test/non-repo'
    os.makedirs(non_repo, exist_ok=True)

    path3 = manager.get_or_create_worktree(non_repo, 'agent-789')
    print(f"✅ Non-repo fallback: {path3}")

    assert path3 == non_repo, "Should return original path for non-repo"

    # Cleanup
    manager.remove_worktree(agent_id, force=True)
    shutil.rmtree('/tmp/brain-worktree-test', ignore_errors=True)

    return True


def test_multiple_worktrees():
    """Test creating multiple worktrees for same repo."""
    print("\n\n🧪 Testing WorktreeManager - Multiple Worktrees")
    print("=" * 60)

    manager = WorktreeManager()

    # Setup test repo
    test_repo = '/tmp/brain-worktree-test/repo'
    setup_test_repo(test_repo)

    # Create 3 worktrees
    agents = ['agent-1', 'agent-2', 'agent-3']
    paths = []

    print(f"\n📝 Creating {len(agents)} worktrees...")

    for agent_id in agents:
        path = manager.create_worktree(test_repo, agent_id)
        paths.append(path)
        print(f"   ✅ {agent_id}: {path}")

    # Verify all exist
    for path in paths:
        assert os.path.exists(path), f"Worktree should exist: {path}"

    # Verify all tracked
    assert len(manager.active_worktrees) == 3, "Should track 3 worktrees"

    print(f"\n✅ All {len(agents)} worktrees created successfully")

    # List worktrees
    worktrees = manager.list_worktrees(test_repo)
    print(f"\n📊 Git worktree list ({len(worktrees)} total):")
    for wt in worktrees:
        print(f"   - {wt.get('path', 'unknown')}")

    # Should have main + 3 agent worktrees = 4 total
    assert len(worktrees) >= 4, "Should have at least 4 worktrees (main + 3 agents)"

    # Cleanup
    for agent_id in agents:
        manager.remove_worktree(agent_id, force=True)
    shutil.rmtree('/tmp/brain-worktree-test', ignore_errors=True)

    return True


def test_worktree_isolation():
    """Test that worktrees are isolated."""
    print("\n\n🧪 Testing WorktreeManager - Worktree Isolation")
    print("=" * 60)

    manager = WorktreeManager()

    # Setup test repo
    test_repo = '/tmp/brain-worktree-test/repo'
    setup_test_repo(test_repo)

    # Create 2 worktrees
    path1 = manager.create_worktree(test_repo, 'agent-A')
    path2 = manager.create_worktree(test_repo, 'agent-B')

    # Create different files in each worktree
    with open(os.path.join(path1, 'agent-A-file.txt'), 'w') as f:
        f.write('Agent A was here')

    with open(os.path.join(path2, 'agent-B-file.txt'), 'w') as f:
        f.write('Agent B was here')

    # Verify isolation
    a_file_in_b = os.path.exists(os.path.join(path2, 'agent-A-file.txt'))
    b_file_in_a = os.path.exists(os.path.join(path1, 'agent-B-file.txt'))

    print(f"\n✅ Worktrees are isolated:")
    print(f"   Agent A file in B worktree: {a_file_in_b} (should be False)")
    print(f"   Agent B file in A worktree: {b_file_in_a} (should be False)")

    assert not a_file_in_b, "Worktrees should be isolated"
    assert not b_file_in_a, "Worktrees should be isolated"

    # Cleanup
    manager.remove_worktree('agent-A', force=True)
    manager.remove_worktree('agent-B', force=True)
    shutil.rmtree('/tmp/brain-worktree-test', ignore_errors=True)

    return True


def test_cleanup():
    """Test worktree cleanup."""
    print("\n\n🧪 Testing WorktreeManager - Cleanup")
    print("=" * 60)

    manager = WorktreeManager(cleanup_after_hours=0)  # Immediate cleanup

    # Setup test repo
    test_repo = '/tmp/brain-worktree-test/repo'
    setup_test_repo(test_repo)

    # Create worktree
    agent_id = 'cleanup-test'
    path = manager.create_worktree(test_repo, agent_id)

    print(f"\n✅ Created worktree: {path}")

    # Unlock it (simulate agent completion)
    manager.unlock_worktree(agent_id)
    print(f"🔓 Unlocked worktree")

    # Run cleanup
    manager.cleanup_old_worktrees(test_repo)

    # Verify removal
    removed = agent_id not in manager.active_worktrees
    print(f"\n✅ Cleanup removed worktree: {removed}")

    assert removed, "Cleanup should remove old unlocked worktrees"

    # Cleanup
    shutil.rmtree('/tmp/brain-worktree-test', ignore_errors=True)

    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("🧠 WorktreeManager Tests")
    print("=" * 60)

    results = []

    try:
        results.append(test_git_detection())
    except Exception as e:
        print(f"\n❌ Test 1 failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(False)

    try:
        results.append(test_worktree_creation())
    except Exception as e:
        print(f"\n❌ Test 2 failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(False)

    try:
        results.append(test_get_or_create())
    except Exception as e:
        print(f"\n❌ Test 3 failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(False)

    try:
        results.append(test_multiple_worktrees())
    except Exception as e:
        print(f"\n❌ Test 4 failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(False)

    try:
        results.append(test_worktree_isolation())
    except Exception as e:
        print(f"\n❌ Test 5 failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(False)

    try:
        results.append(test_cleanup())
    except Exception as e:
        print(f"\n❌ Test 6 failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(False)

    # Summary
    print("\n" + "=" * 60)
    print(f"📊 Results: {sum(results)}/{len(results)} tests passed")
    print("=" * 60 + "\n")

    return all(results)


if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
