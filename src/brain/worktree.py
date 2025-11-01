"""Git worktree manager for parallel agent work."""

import os
import subprocess
import shutil
from datetime import datetime, timedelta
from typing import Optional, List
from dataclasses import dataclass


@dataclass
class Worktree:
    """Represents a git worktree."""
    path: str
    branch: str
    agent_id: str
    created_at: datetime
    locked: bool = False


class WorktreeManager:
    """
    Manages git worktrees for parallel agent execution.

    When multiple agents work on the same project, each gets an isolated
    worktree to avoid conflicts. Worktrees share the same git history
    but have separate working directories.
    """

    def __init__(self, cleanup_after_hours: int = 24):
        """
        Initialize worktree manager.

        Args:
            cleanup_after_hours: Delete unused worktrees after this many hours
        """
        self.cleanup_after_hours = cleanup_after_hours
        self.active_worktrees: dict[str, Worktree] = {}

    def is_git_repo(self, path: str) -> bool:
        """Check if path is a git repository."""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--git-dir'],
                cwd=path,
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False

    def get_repo_root(self, path: str) -> Optional[str]:
        """Get the root directory of a git repository."""
        if not self.is_git_repo(path):
            return None

        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--show-toplevel'],
                cwd=path,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                # Resolve symlinks (e.g., /tmp -> /private/tmp on macOS)
                return os.path.realpath(result.stdout.strip())
        except Exception:
            pass

        return None

    def create_worktree(
        self,
        repo_path: str,
        agent_id: str,
        branch: Optional[str] = None
    ) -> Optional[str]:
        """
        Create a new worktree for an agent.

        Args:
            repo_path: Path to git repository
            agent_id: Unique agent identifier
            branch: Optional branch name (defaults to agent-{agent_id})

        Returns:
            Path to created worktree, or None if not a git repo
        """
        # Check if git repo
        if not self.is_git_repo(repo_path):
            print(f"⚠️  Not a git repo: {repo_path}")
            return None

        # Get repo root
        repo_root = self.get_repo_root(repo_path)
        if not repo_root:
            return None

        # Create worktree directory
        worktree_base = os.path.join(repo_root, '.agent-worktrees')
        os.makedirs(worktree_base, exist_ok=True)

        worktree_path = os.path.join(worktree_base, agent_id)

        # Check if worktree already exists
        if os.path.exists(worktree_path):
            print(f"⚠️  Worktree already exists: {worktree_path}")
            return worktree_path

        # Generate branch name
        if branch is None:
            branch = f"agent-{agent_id}"

        try:
            # Create worktree
            # Use -b to create new branch, or --detach if branch exists
            result = subprocess.run(
                ['git', 'worktree', 'add', '-b', branch, worktree_path],
                cwd=repo_root,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                # Branch might already exist, try without -b
                result = subprocess.run(
                    ['git', 'worktree', 'add', worktree_path, branch],
                    cwd=repo_root,
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.returncode != 0:
                    print(f"❌ Failed to create worktree: {result.stderr}")
                    return None

            # Track worktree
            worktree = Worktree(
                path=worktree_path,
                branch=branch,
                agent_id=agent_id,
                created_at=datetime.now(),
                locked=True
            )
            self.active_worktrees[agent_id] = worktree

            print(f"✅ Created worktree: {worktree_path}")
            print(f"   Branch: {branch}")

            return worktree_path

        except subprocess.TimeoutExpired:
            print(f"❌ Timeout creating worktree")
            return None
        except Exception as e:
            print(f"❌ Error creating worktree: {e}")
            return None

    def remove_worktree(self, agent_id: str, force: bool = False):
        """
        Remove a worktree.

        Args:
            agent_id: Agent whose worktree to remove
            force: Force removal even if locked
        """
        if agent_id not in self.active_worktrees:
            print(f"⚠️  No worktree found for agent: {agent_id}")
            return

        worktree = self.active_worktrees[agent_id]

        if worktree.locked and not force:
            print(f"⚠️  Worktree is locked: {worktree.path}")
            return

        try:
            # Get repo root from worktree path
            # .agent-worktrees/{agent_id} -> parent is repo root
            repo_root = os.path.dirname(os.path.dirname(worktree.path))

            # Build command
            cmd = ['git', 'worktree', 'remove', worktree.path]
            if force:
                cmd.append('--force')

            # Remove worktree
            result = subprocess.run(
                cmd,
                cwd=repo_root,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                # Remove from tracking
                del self.active_worktrees[agent_id]
                print(f"✅ Removed worktree: {worktree.path}")
            else:
                print(f"❌ Failed to remove worktree: {result.stderr}")

        except Exception as e:
            print(f"❌ Error removing worktree: {e}")

    def unlock_worktree(self, agent_id: str):
        """Unlock a worktree after agent completes."""
        if agent_id in self.active_worktrees:
            self.active_worktrees[agent_id].locked = False
            print(f"🔓 Unlocked worktree for: {agent_id}")

    def cleanup_old_worktrees(self, repo_path: str):
        """
        Clean up worktrees older than cleanup_after_hours.

        Args:
            repo_path: Path to git repository
        """
        if not self.is_git_repo(repo_path):
            return

        repo_root = self.get_repo_root(repo_path)
        if not repo_root:
            return

        worktree_base = os.path.join(repo_root, '.agent-worktrees')
        if not os.path.exists(worktree_base):
            return

        cutoff_time = datetime.now() - timedelta(hours=self.cleanup_after_hours)
        removed_count = 0

        # Check each worktree
        for agent_id in list(self.active_worktrees.keys()):
            worktree = self.active_worktrees[agent_id]

            # Skip locked worktrees
            if worktree.locked:
                continue

            # Remove if old enough
            if worktree.created_at < cutoff_time:
                self.remove_worktree(agent_id, force=False)
                removed_count += 1

        if removed_count > 0:
            print(f"🧹 Cleaned up {removed_count} old worktrees")

    def list_worktrees(self, repo_path: str) -> List[dict]:
        """
        List all worktrees in a repository.

        Args:
            repo_path: Path to git repository

        Returns:
            List of worktree info dicts
        """
        if not self.is_git_repo(repo_path):
            return []

        try:
            result = subprocess.run(
                ['git', 'worktree', 'list', '--porcelain'],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                return []

            # Parse porcelain output
            worktrees = []
            current = {}

            for line in result.stdout.split('\n'):
                if line.startswith('worktree '):
                    if current:
                        worktrees.append(current)
                    current = {'path': line.replace('worktree ', '')}
                elif line.startswith('branch '):
                    current['branch'] = line.replace('branch ', '')
                elif line.startswith('HEAD '):
                    current['head'] = line.replace('HEAD ', '')
                elif line == '':
                    if current:
                        worktrees.append(current)
                        current = {}

            if current:
                worktrees.append(current)

            return worktrees

        except Exception as e:
            print(f"❌ Error listing worktrees: {e}")
            return []

    def get_or_create_worktree(
        self,
        repo_path: str,
        agent_id: str,
        branch: Optional[str] = None
    ) -> str:
        """
        Get existing worktree or create new one.

        This is the main method agents should use. It handles the logic of:
        1. Check if git repo
        2. Return repo_path if not git (fallback)
        3. Check if worktree exists
        4. Create worktree if needed
        5. Return worktree path

        Args:
            repo_path: Path to project
            agent_id: Unique agent identifier
            branch: Optional branch name

        Returns:
            Path to use for agent execution (worktree or original path)
        """
        # Not a git repo - use original path
        if not self.is_git_repo(repo_path):
            return repo_path

        # Check if worktree already exists
        if agent_id in self.active_worktrees:
            worktree = self.active_worktrees[agent_id]
            print(f"📂 Using existing worktree: {worktree.path}")
            return worktree.path

        # Create new worktree
        worktree_path = self.create_worktree(repo_path, agent_id, branch)

        # Fallback to original path if creation failed
        if worktree_path is None:
            print(f"⚠️  Falling back to original path: {repo_path}")
            return repo_path

        return worktree_path

    def sync_worktree_to_main(self, agent_id: str) -> bool:
        """
        Sync worktree changes back to main branch.

        This commits changes in the worktree and merges to main.
        Useful when agent completes successful work.

        Args:
            agent_id: Agent whose worktree to sync

        Returns:
            True if sync successful, False otherwise
        """
        if agent_id not in self.active_worktrees:
            print(f"⚠️  No worktree found for: {agent_id}")
            return False

        worktree = self.active_worktrees[agent_id]

        try:
            # Get repo root
            repo_root = os.path.dirname(os.path.dirname(worktree.path))

            # Check if there are changes
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=worktree.path,
                capture_output=True,
                text=True,
                timeout=10
            )

            if not result.stdout.strip():
                print(f"ℹ️  No changes to sync in worktree: {agent_id}")
                return True

            # Commit changes in worktree
            subprocess.run(
                ['git', 'add', '.'],
                cwd=worktree.path,
                timeout=10
            )

            subprocess.run(
                ['git', 'commit', '-m', f'Agent {agent_id} changes'],
                cwd=worktree.path,
                timeout=10
            )

            # Switch to main branch
            subprocess.run(
                ['git', 'checkout', 'main'],
                cwd=repo_root,
                timeout=10
            )

            # Merge worktree branch
            result = subprocess.run(
                ['git', 'merge', '--no-ff', worktree.branch,
                 '-m', f'Merge agent {agent_id} changes'],
                cwd=repo_root,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                print(f"✅ Synced worktree changes to main: {agent_id}")
                return True
            else:
                print(f"❌ Failed to merge: {result.stderr}")
                return False

        except Exception as e:
            print(f"❌ Error syncing worktree: {e}")
            return False
