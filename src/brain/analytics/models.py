"""Data models for analytics."""

from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime


@dataclass
class Issue:
    """Represents a Jira issue or GitHub issue."""
    id: str
    title: str
    description: str
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

    # Optional fields
    assignee: Optional[str] = None
    reporter: Optional[str] = None
    labels: List[str] = None
    priority: Optional[str] = None
    issue_type: Optional[str] = None

    # Computed fields
    time_to_resolve: Optional[float] = None  # days

    def __post_init__(self):
        """Compute derived fields."""
        if self.labels is None:
            self.labels = []

        if self.created_at and self.resolved_at:
            delta = self.resolved_at - self.created_at
            self.time_to_resolve = delta.total_seconds() / 86400  # days


@dataclass
class PullRequest:
    """Represents a GitHub pull request."""
    id: str
    title: str
    description: str
    state: str
    created_at: datetime
    merged_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None

    # Optional fields
    author: Optional[str] = None
    reviewers: List[str] = None
    labels: List[str] = None
    files_changed: Optional[int] = None
    additions: Optional[int] = None
    deletions: Optional[int] = None

    # Computed fields
    time_to_merge: Optional[float] = None  # days

    def __post_init__(self):
        """Compute derived fields."""
        if self.reviewers is None:
            self.reviewers = []
        if self.labels is None:
            self.labels = []

        if self.created_at and self.merged_at:
            delta = self.merged_at - self.created_at
            self.time_to_merge = delta.total_seconds() / 86400  # days


@dataclass
class AnalysisResult:
    """Result of analytics operation."""
    summary: str
    insights: List[str]
    patterns: List[dict]
    metadata: dict
