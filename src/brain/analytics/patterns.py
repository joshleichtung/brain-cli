"""Pattern detection using scikit-learn."""

from typing import List, Dict, Any
import numpy as np
from collections import Counter

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.decomposition import LatentDirichletAllocation

from .models import Issue, PullRequest, AnalysisResult


class PatternDetector:
    """
    Detect patterns in issues/PRs using machine learning.

    Features:
    - Clustering (group similar issues)
    - Topic modeling (discover themes)
    - Temporal patterns (identify trends over time)
    - Label analysis (common combinations)
    """

    def __init__(self):
        """Initialize pattern detector."""
        self.vectorizer = TfidfVectorizer(
            max_features=100,
            stop_words='english',
            ngram_range=(1, 2)
        )

    def cluster_issues(
        self,
        issues: List[Issue],
        n_clusters: int = 5
    ) -> AnalysisResult:
        """
        Cluster issues by similarity.

        Args:
            issues: List of issues to cluster
            n_clusters: Number of clusters to create

        Returns:
            Analysis result with cluster assignments
        """
        if len(issues) < n_clusters:
            n_clusters = max(2, len(issues) // 2)

        # Extract text features
        texts = [f"{issue.title} {issue.description}" for issue in issues]
        X = self.vectorizer.fit_transform(texts)

        # Perform clustering
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        clusters = kmeans.fit_predict(X)

        # Analyze clusters
        patterns = []
        for cluster_id in range(n_clusters):
            cluster_issues = [
                issues[i] for i, c in enumerate(clusters) if c == cluster_id
            ]

            # Get top terms for this cluster
            cluster_center = kmeans.cluster_centers_[cluster_id]
            top_indices = cluster_center.argsort()[-10:][::-1]
            feature_names = self.vectorizer.get_feature_names_out()
            top_terms = [feature_names[i] for i in top_indices]

            # Compute cluster stats
            avg_time_to_resolve = np.mean([
                i.time_to_resolve for i in cluster_issues
                if i.time_to_resolve is not None
            ]) if cluster_issues else 0

            patterns.append({
                'cluster_id': int(cluster_id),
                'size': len(cluster_issues),
                'top_terms': top_terms[:5],
                'avg_time_to_resolve_days': float(avg_time_to_resolve),
                'common_labels': self._get_common_labels(cluster_issues)
            })

        insights = self._generate_cluster_insights(patterns)

        return AnalysisResult(
            summary=f"Found {n_clusters} clusters in {len(issues)} issues",
            insights=insights,
            patterns=patterns,
            metadata={
                'n_clusters': n_clusters,
                'n_issues': len(issues)
            }
        )

    def extract_topics(
        self,
        issues: List[Issue],
        n_topics: int = 5
    ) -> AnalysisResult:
        """
        Extract topics using LDA.

        Args:
            issues: List of issues
            n_topics: Number of topics to extract

        Returns:
            Analysis result with topics
        """
        # Extract text features
        texts = [f"{issue.title} {issue.description}" for issue in issues]
        X = self.vectorizer.fit_transform(texts)

        # Perform LDA
        lda = LatentDirichletAllocation(
            n_components=n_topics,
            random_state=42,
            max_iter=10
        )
        lda.fit(X)

        # Extract topics
        feature_names = self.vectorizer.get_feature_names_out()
        patterns = []

        for topic_idx, topic in enumerate(lda.components_):
            top_indices = topic.argsort()[-10:][::-1]
            top_words = [feature_names[i] for i in top_indices]

            patterns.append({
                'topic_id': int(topic_idx),
                'top_words': top_words[:5],
                'weight': float(topic.sum())
            })

        insights = [
            f"Topic {p['topic_id']}: {', '.join(p['top_words'][:3])}"
            for p in patterns
        ]

        return AnalysisResult(
            summary=f"Extracted {n_topics} topics from {len(issues)} issues",
            insights=insights,
            patterns=patterns,
            metadata={
                'n_topics': n_topics,
                'n_issues': len(issues)
            }
        )

    def analyze_temporal_patterns(
        self,
        issues: List[Issue]
    ) -> AnalysisResult:
        """
        Analyze temporal patterns in issues.

        Args:
            issues: List of issues

        Returns:
            Analysis with temporal patterns
        """
        # Group by month
        monthly_counts = Counter()
        monthly_resolved = Counter()

        for issue in issues:
            month_key = issue.created_at.strftime('%Y-%m')
            monthly_counts[month_key] += 1

            if issue.resolved_at:
                resolved_month = issue.resolved_at.strftime('%Y-%m')
                monthly_resolved[resolved_month] += 1

        # Find trends
        patterns = []
        for month in sorted(monthly_counts.keys()):
            patterns.append({
                'month': month,
                'created': monthly_counts[month],
                'resolved': monthly_resolved.get(month, 0)
            })

        # Generate insights
        insights = []

        if patterns:
            peak_month = max(patterns, key=lambda x: x['created'])
            insights.append(
                f"Peak activity: {peak_month['month']} "
                f"({peak_month['created']} issues created)"
            )

            recent_patterns = patterns[-3:]
            avg_recent = np.mean([p['created'] for p in recent_patterns])
            insights.append(
                f"Recent average: {avg_recent:.1f} issues/month"
            )

        return AnalysisResult(
            summary=f"Analyzed temporal patterns for {len(issues)} issues",
            insights=insights,
            patterns=patterns,
            metadata={'total_months': len(patterns)}
        )

    def analyze_labels(
        self,
        issues: List[Issue]
    ) -> AnalysisResult:
        """
        Analyze label usage patterns.

        Args:
            issues: List of issues

        Returns:
            Analysis of label patterns
        """
        # Count individual labels
        label_counts = Counter()
        for issue in issues:
            for label in issue.labels:
                label_counts[label] += 1

        # Find label combinations
        label_combos = Counter()
        for issue in issues:
            if len(issue.labels) > 1:
                combo = tuple(sorted(issue.labels))
                label_combos[combo] += 1

        # Build patterns
        patterns = []

        # Top labels
        for label, count in label_counts.most_common(10):
            patterns.append({
                'type': 'single_label',
                'label': label,
                'count': count,
                'percentage': count / len(issues) * 100
            })

        # Top combinations
        for combo, count in label_combos.most_common(5):
            patterns.append({
                'type': 'label_combination',
                'labels': list(combo),
                'count': count
            })

        insights = [
            f"Most common label: {label_counts.most_common(1)[0][0]}"
            if label_counts else "No labels found"
        ]

        return AnalysisResult(
            summary=f"Analyzed labels for {len(issues)} issues",
            insights=insights,
            patterns=patterns,
            metadata={'unique_labels': len(label_counts)}
        )

    def _get_common_labels(self, issues: List[Issue], top_n: int = 3) -> List[str]:
        """Get most common labels in a set of issues."""
        label_counts = Counter()
        for issue in issues:
            for label in issue.labels:
                label_counts[label] += 1

        return [label for label, _ in label_counts.most_common(top_n)]

    def _generate_cluster_insights(self, patterns: List[dict]) -> List[str]:
        """Generate insights from cluster patterns."""
        insights = []

        # Largest cluster
        largest = max(patterns, key=lambda x: x['size'])
        insights.append(
            f"Largest cluster: {largest['size']} issues "
            f"(topics: {', '.join(largest['top_terms'][:2])})"
        )

        # Fastest to resolve
        with_times = [p for p in patterns if p['avg_time_to_resolve_days'] > 0]
        if with_times:
            fastest = min(with_times, key=lambda x: x['avg_time_to_resolve_days'])
            insights.append(
                f"Fastest resolution: Cluster {fastest['cluster_id']} "
                f"(avg {fastest['avg_time_to_resolve_days']:.1f} days)"
            )

        return insights
