"""Parsers for Jira and GitHub data exports."""

import csv
from datetime import datetime
from typing import List, Optional
from pathlib import Path

from .models import Issue, PullRequest


class JiraParser:
    """
    Parse Jira CSV exports.

    Expected columns:
    - Issue key, Summary, Description, Status, Created, Updated, Resolved
    - Assignee, Reporter, Labels, Priority, Issue Type
    """

    def __init__(self, csv_path: str):
        """Initialize parser with CSV file path."""
        self.csv_path = Path(csv_path)

    def parse(self) -> List[Issue]:
        """Parse Jira CSV into Issue objects."""
        issues = []

        with open(self.csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                issue = self._parse_row(row)
                if issue:
                    issues.append(issue)

        return issues

    def _parse_row(self, row: dict) -> Optional[Issue]:
        """Parse a single CSV row into an Issue."""
        try:
            # Handle various column name formats
            issue_id = row.get('Issue key') or row.get('Key') or row.get('Issue Key')
            title = row.get('Summary') or row.get('Title')
            description = row.get('Description') or ''
            status = row.get('Status') or 'Unknown'

            # Parse dates
            created_str = row.get('Created') or row.get('Created Date')
            created_at = self._parse_date(created_str)

            updated_str = row.get('Updated') or row.get('Updated Date')
            updated_at = self._parse_date(updated_str) if updated_str else None

            resolved_str = row.get('Resolved') or row.get('Resolution Date')
            resolved_at = self._parse_date(resolved_str) if resolved_str else None

            # Parse labels (comma-separated)
            labels_str = row.get('Labels') or ''
            labels = [l.strip() for l in labels_str.split(',') if l.strip()]

            return Issue(
                id=issue_id,
                title=title,
                description=description,
                status=status,
                created_at=created_at,
                updated_at=updated_at,
                resolved_at=resolved_at,
                assignee=row.get('Assignee'),
                reporter=row.get('Reporter'),
                labels=labels,
                priority=row.get('Priority'),
                issue_type=row.get('Issue Type') or row.get('Type')
            )

        except Exception as e:
            print(f"Warning: Failed to parse row: {e}")
            return None

    def _parse_date(self, date_str: str) -> datetime:
        """Parse date string to datetime object."""
        if not date_str:
            return datetime.now()

        # Try common date formats
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d %H:%M',
            '%Y-%m-%d',
            '%m/%d/%Y %H:%M:%S',
            '%m/%d/%Y',
            '%d/%m/%Y %H:%M:%S',
            '%d/%m/%Y',
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        # Fallback
        print(f"Warning: Could not parse date '{date_str}', using now()")
        return datetime.now()


class GitHubParser:
    """
    Parse GitHub CSV exports (Issues or Pull Requests).

    Expected columns:
    - number, title, body, state, created_at, updated_at
    - user, assignees, labels, closed_at, merged_at (for PRs)
    """

    def __init__(self, csv_path: str, export_type: str = 'issues'):
        """
        Initialize parser.

        Args:
            csv_path: Path to CSV file
            export_type: 'issues' or 'prs'
        """
        self.csv_path = Path(csv_path)
        self.export_type = export_type

    def parse_issues(self) -> List[Issue]:
        """Parse GitHub issues CSV."""
        issues = []

        with open(self.csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                issue = self._parse_issue_row(row)
                if issue:
                    issues.append(issue)

        return issues

    def parse_prs(self) -> List[PullRequest]:
        """Parse GitHub pull requests CSV."""
        prs = []

        with open(self.csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                pr = self._parse_pr_row(row)
                if pr:
                    prs.append(pr)

        return prs

    def _parse_issue_row(self, row: dict) -> Optional[Issue]:
        """Parse issue row."""
        try:
            issue_id = row.get('number') or row.get('Number')
            title = row.get('title') or row.get('Title')
            description = row.get('body') or row.get('Body') or ''
            status = row.get('state') or row.get('State') or 'open'

            created_str = row.get('created_at') or row.get('Created')
            created_at = self._parse_iso_date(created_str)

            closed_str = row.get('closed_at') or row.get('Closed')
            resolved_at = self._parse_iso_date(closed_str) if closed_str else None

            # Parse labels
            labels_str = row.get('labels') or row.get('Labels') or ''
            labels = [l.strip() for l in labels_str.split(',') if l.strip()]

            return Issue(
                id=f"#{issue_id}",
                title=title,
                description=description,
                status=status,
                created_at=created_at,
                resolved_at=resolved_at,
                assignee=row.get('assignees') or row.get('Assignee'),
                reporter=row.get('user') or row.get('Author'),
                labels=labels
            )

        except Exception as e:
            print(f"Warning: Failed to parse issue row: {e}")
            return None

    def _parse_pr_row(self, row: dict) -> Optional[PullRequest]:
        """Parse PR row."""
        try:
            pr_id = row.get('number') or row.get('Number')
            title = row.get('title') or row.get('Title')
            description = row.get('body') or row.get('Body') or ''
            state = row.get('state') or row.get('State') or 'open'

            created_str = row.get('created_at') or row.get('Created')
            created_at = self._parse_iso_date(created_str)

            merged_str = row.get('merged_at') or row.get('Merged')
            merged_at = self._parse_iso_date(merged_str) if merged_str else None

            closed_str = row.get('closed_at') or row.get('Closed')
            closed_at = self._parse_iso_date(closed_str) if closed_str else None

            # Parse labels
            labels_str = row.get('labels') or row.get('Labels') or ''
            labels = [l.strip() for l in labels_str.split(',') if l.strip()]

            # Parse reviewers
            reviewers_str = row.get('reviewers') or ''
            reviewers = [r.strip() for r in reviewers_str.split(',') if r.strip()]

            return PullRequest(
                id=f"#{pr_id}",
                title=title,
                description=description,
                state=state,
                created_at=created_at,
                merged_at=merged_at,
                closed_at=closed_at,
                author=row.get('user') or row.get('Author'),
                reviewers=reviewers,
                labels=labels,
                files_changed=self._parse_int(row.get('changed_files')),
                additions=self._parse_int(row.get('additions')),
                deletions=self._parse_int(row.get('deletions'))
            )

        except Exception as e:
            print(f"Warning: Failed to parse PR row: {e}")
            return None

    def _parse_iso_date(self, date_str: str) -> datetime:
        """Parse ISO 8601 date string."""
        if not date_str:
            return datetime.now()

        try:
            # Handle ISO 8601 with timezone
            if 'T' in date_str:
                # Remove timezone info for simplicity
                date_str = date_str.split('+')[0].split('Z')[0]
                return datetime.fromisoformat(date_str)
            else:
                return datetime.fromisoformat(date_str)
        except ValueError:
            print(f"Warning: Could not parse date '{date_str}'")
            return datetime.now()

    def _parse_int(self, value: str) -> Optional[int]:
        """Parse integer value."""
        try:
            return int(value) if value else None
        except ValueError:
            return None
