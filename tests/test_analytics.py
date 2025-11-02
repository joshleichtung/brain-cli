"""Test analytics module."""

import os
import tempfile
import csv
from datetime import datetime, timedelta

from brain.analytics import JiraParser, GitHubParser, PatternDetector, NLPAnalyzer
from brain.analytics.models import Issue


def create_test_jira_csv():
    """Create a test Jira CSV file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'Issue key', 'Summary', 'Description', 'Status',
            'Created', 'Resolved', 'Labels', 'Priority'
        ])
        writer.writeheader()

        base_date = datetime.now() - timedelta(days=30)

        issues = [
            {
                'Issue key': 'PROJ-1',
                'Summary': 'Bug in authentication system',
                'Description': 'Users cannot log in with OAuth',
                'Status': 'Resolved',
                'Created': base_date.strftime('%Y-%m-%d'),
                'Resolved': (base_date + timedelta(days=2)).strftime('%Y-%m-%d'),
                'Labels': 'bug,authentication',
                'Priority': 'High'
            },
            {
                'Issue key': 'PROJ-2',
                'Summary': 'Add dark mode feature',
                'Description': 'Implement dark mode for better UX',
                'Status': 'In Progress',
                'Created': (base_date + timedelta(days=5)).strftime('%Y-%m-%d'),
                'Resolved': '',
                'Labels': 'feature,ui',
                'Priority': 'Medium'
            },
            {
                'Issue key': 'PROJ-3',
                'Summary': 'Database connection timeout',
                'Description': 'Connections timeout after 30 seconds',
                'Status': 'Resolved',
                'Created': (base_date + timedelta(days=10)).strftime('%Y-%m-%d'),
                'Resolved': (base_date + timedelta(days=11)).strftime('%Y-%m-%d'),
                'Labels': 'bug,database',
                'Priority': 'Critical'
            },
            {
                'Issue key': 'PROJ-4',
                'Summary': 'Improve API documentation',
                'Description': 'Add examples and better explanations',
                'Status': 'Open',
                'Created': (base_date + timedelta(days=15)).strftime('%Y-%m-%d'),
                'Resolved': '',
                'Labels': 'documentation',
                'Priority': 'Low'
            },
            {
                'Issue key': 'PROJ-5',
                'Summary': 'Authentication error on mobile',
                'Description': 'Mobile OAuth flow is broken',
                'Status': 'Resolved',
                'Created': (base_date + timedelta(days=20)).strftime('%Y-%m-%d'),
                'Resolved': (base_date + timedelta(days=21)).strftime('%Y-%m-%d'),
                'Labels': 'bug,authentication,mobile',
                'Priority': 'High'
            }
        ]

        writer.writerows(issues)
        return f.name


def test_jira_parser():
    """Test Jira CSV parser."""
    print("\n🧪 Testing Analytics - Jira Parser")
    print("=" * 60)

    csv_path = create_test_jira_csv()

    try:
        parser = JiraParser(csv_path)
        issues = parser.parse()

        assert len(issues) == 5, "Should parse 5 issues"
        assert issues[0].id == 'PROJ-1'
        assert issues[0].title == 'Bug in authentication system'
        assert 'bug' in issues[0].labels
        assert issues[0].time_to_resolve is not None

        print(f"\n✅ Parsed {len(issues)} issues")
        print(f"   First issue: {issues[0].id} - {issues[0].title}")
        print(f"   Labels: {issues[0].labels}")
        print(f"   Time to resolve: {issues[0].time_to_resolve:.1f} days")

    finally:
        os.unlink(csv_path)

    return True


def test_pattern_detector_clustering():
    """Test pattern detection clustering."""
    print("\n\n🧪 Testing Analytics - Clustering")
    print("=" * 60)

    csv_path = create_test_jira_csv()

    try:
        parser = JiraParser(csv_path)
        issues = parser.parse()

        detector = PatternDetector()
        result = detector.cluster_issues(issues, n_clusters=2)

        assert len(result.patterns) == 2, "Should have 2 clusters"
        assert len(result.insights) > 0, "Should have insights"

        print(f"\n✅ {result.summary}")
        for insight in result.insights:
            print(f"   💡 {insight}")

        print(f"\n📊 Clusters:")
        for pattern in result.patterns:
            print(f"   Cluster {pattern['cluster_id']}: {pattern['size']} issues")
            print(f"      Topics: {', '.join(pattern['top_terms'][:3])}")

    finally:
        os.unlink(csv_path)

    return True


def test_pattern_detector_topics():
    """Test topic extraction."""
    print("\n\n🧪 Testing Analytics - Topic Extraction")
    print("=" * 60)

    csv_path = create_test_jira_csv()

    try:
        parser = JiraParser(csv_path)
        issues = parser.parse()

        detector = PatternDetector()
        result = detector.extract_topics(issues, n_topics=3)

        assert len(result.patterns) == 3, "Should have 3 topics"

        print(f"\n✅ {result.summary}")
        print(f"\n📚 Topics discovered:")
        for pattern in result.patterns:
            print(f"   Topic {pattern['topic_id']}: {', '.join(pattern['top_words'][:5])}")

    finally:
        os.unlink(csv_path)

    return True


def test_pattern_detector_labels():
    """Test label analysis."""
    print("\n\n🧪 Testing Analytics - Label Analysis")
    print("=" * 60)

    csv_path = create_test_jira_csv()

    try:
        parser = JiraParser(csv_path)
        issues = parser.parse()

        detector = PatternDetector()
        result = detector.analyze_labels(issues)

        assert len(result.patterns) > 0, "Should find label patterns"

        print(f"\n✅ {result.summary}")
        print(f"\n🏷️  Label patterns:")
        for pattern in result.patterns[:5]:
            if pattern['type'] == 'single_label':
                print(f"   {pattern['label']}: {pattern['count']} issues ({pattern['percentage']:.1f}%)")

    finally:
        os.unlink(csv_path)

    return True


def test_nlp_analyzer():
    """Test NLP analyzer."""
    print("\n\n🧪 Testing Analytics - NLP Analysis")
    print("=" * 60)

    csv_path = create_test_jira_csv()

    try:
        parser = JiraParser(csv_path)
        issues = parser.parse()

        analyzer = NLPAnalyzer()

        # Test sentiment analysis (works without spaCy model)
        result = analyzer.analyze_sentiment(issues)

        print(f"\n✅ {result.summary}")
        if result.insights:
            for insight in result.insights:
                print(f"   💡 {insight}")

        print(f"\n😊 Sentiment distribution:")
        for pattern in result.patterns:
            print(f"   {pattern['category']}: {pattern['count']} ({pattern['percentage']:.1f}%)")

    finally:
        os.unlink(csv_path)

    return True


def test_temporal_patterns():
    """Test temporal pattern analysis."""
    print("\n\n🧪 Testing Analytics - Temporal Patterns")
    print("=" * 60)

    csv_path = create_test_jira_csv()

    try:
        parser = JiraParser(csv_path)
        issues = parser.parse()

        detector = PatternDetector()
        result = detector.analyze_temporal_patterns(issues)

        assert len(result.patterns) > 0, "Should find temporal patterns"

        print(f"\n✅ {result.summary}")
        for insight in result.insights:
            print(f"   💡 {insight}")

        print(f"\n📅 Monthly activity:")
        for pattern in result.patterns[-3:]:
            print(f"   {pattern['month']}: {pattern['created']} created, {pattern['resolved']} resolved")

    finally:
        os.unlink(csv_path)

    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("🧠 Analytics Module Tests")
    print("=" * 60)

    results = []

    try:
        results.append(test_jira_parser())
    except Exception as e:
        print(f"\n❌ Test 1 failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(False)

    try:
        results.append(test_pattern_detector_clustering())
    except Exception as e:
        print(f"\n❌ Test 2 failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(False)

    try:
        results.append(test_pattern_detector_topics())
    except Exception as e:
        print(f"\n❌ Test 3 failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(False)

    try:
        results.append(test_pattern_detector_labels())
    except Exception as e:
        print(f"\n❌ Test 4 failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(False)

    try:
        results.append(test_nlp_analyzer())
    except Exception as e:
        print(f"\n❌ Test 5 failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(False)

    try:
        results.append(test_temporal_patterns())
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
