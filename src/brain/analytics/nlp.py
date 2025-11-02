"""NLP analysis using spaCy."""

from typing import List, Dict, Any
from collections import Counter

try:
    import spacy
    from spacy.lang.en import English
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    print("Warning: spaCy not installed. NLP features will be limited.")

from .models import Issue, PullRequest, AnalysisResult


class NLPAnalyzer:
    """
    NLP analysis for issues and PRs.

    Features:
    - Entity extraction (people, products, technologies)
    - Key phrase extraction
    - Sentiment analysis
    - Text similarity
    """

    def __init__(self, model_name: str = "en_core_web_sm"):
        """
        Initialize NLP analyzer.

        Args:
            model_name: spaCy model to use
        """
        self.model_name = model_name
        self.nlp = None

        if SPACY_AVAILABLE:
            try:
                self.nlp = spacy.load(model_name)
            except OSError:
                print(f"spaCy model '{model_name}' not found.")
                print("Install with: python -m spacy download en_core_web_sm")
                # Fallback to basic English
                self.nlp = English()

    def extract_entities(
        self,
        issues: List[Issue]
    ) -> AnalysisResult:
        """
        Extract named entities from issues.

        Args:
            issues: List of issues

        Returns:
            Analysis with extracted entities
        """
        if not self.nlp:
            return AnalysisResult(
                summary="spaCy not available",
                insights=["Install spaCy to use NLP features"],
                patterns=[],
                metadata={}
            )

        # Combine all text
        all_entities = Counter()
        entity_by_type = {}

        for issue in issues:
            text = f"{issue.title}. {issue.description}"
            doc = self.nlp(text)

            for ent in doc.ents:
                all_entities[ent.text] += 1

                if ent.label_ not in entity_by_type:
                    entity_by_type[ent.label_] = Counter()
                entity_by_type[ent.label_][ent.text] += 1

        # Build patterns
        patterns = []

        # Top entities by type
        for ent_type, entities in entity_by_type.items():
            top_entities = entities.most_common(5)
            if top_entities:
                patterns.append({
                    'entity_type': ent_type,
                    'top_entities': [
                        {'text': text, 'count': count}
                        for text, count in top_entities
                    ]
                })

        # Generate insights
        insights = []
        if all_entities:
            most_common = all_entities.most_common(3)
            insights.append(
                f"Most mentioned: {', '.join([e[0] for e in most_common])}"
            )

        return AnalysisResult(
            summary=f"Extracted entities from {len(issues)} issues",
            insights=insights,
            patterns=patterns,
            metadata={
                'total_entities': len(all_entities),
                'entity_types': list(entity_by_type.keys())
            }
        )

    def extract_key_phrases(
        self,
        issues: List[Issue],
        top_n: int = 10
    ) -> AnalysisResult:
        """
        Extract key phrases (noun chunks) from issues.

        Args:
            issues: List of issues
            top_n: Number of top phrases to return

        Returns:
            Analysis with key phrases
        """
        if not self.nlp:
            return AnalysisResult(
                summary="spaCy not available",
                insights=[],
                patterns=[],
                metadata={}
            )

        phrase_counts = Counter()

        for issue in issues:
            text = f"{issue.title}. {issue.description}"
            doc = self.nlp(text)

            # Extract noun chunks (key phrases)
            for chunk in doc.noun_chunks:
                # Filter out very short or very long phrases
                if 2 <= len(chunk.text.split()) <= 4:
                    phrase_counts[chunk.text.lower()] += 1

        # Get top phrases
        top_phrases = phrase_counts.most_common(top_n)

        patterns = [
            {
                'phrase': phrase,
                'count': count,
                'percentage': count / len(issues) * 100
            }
            for phrase, count in top_phrases
        ]

        insights = [
            f"Key theme: '{top_phrases[0][0]}' ({top_phrases[0][1]} occurrences)"
        ] if top_phrases else []

        return AnalysisResult(
            summary=f"Extracted key phrases from {len(issues)} issues",
            insights=insights,
            patterns=patterns,
            metadata={'total_phrases': len(phrase_counts)}
        )

    def analyze_sentiment(
        self,
        issues: List[Issue]
    ) -> AnalysisResult:
        """
        Analyze sentiment of issues.

        Note: Basic implementation. For better results, use
        a dedicated sentiment model like transformers.

        Args:
            issues: List of issues

        Returns:
            Analysis with sentiment scores
        """
        # Simple sentiment based on keywords
        positive_words = {
            'fix', 'improve', 'enhance', 'upgrade', 'optimize',
            'feature', 'add', 'implement', 'success', 'complete'
        }

        negative_words = {
            'bug', 'error', 'fail', 'crash', 'broken', 'issue',
            'problem', 'regression', 'critical', 'urgent', 'blocker'
        }

        sentiments = []

        for issue in issues:
            text = f"{issue.title} {issue.description}".lower()
            words = set(text.split())

            pos_score = len(words & positive_words)
            neg_score = len(words & negative_words)

            # Normalize
            total = pos_score + neg_score
            if total > 0:
                sentiment = (pos_score - neg_score) / total
            else:
                sentiment = 0  # Neutral

            sentiments.append({
                'issue_id': issue.id,
                'sentiment': float(sentiment),
                'category': 'positive' if sentiment > 0.2 else
                           'negative' if sentiment < -0.2 else
                           'neutral'
            })

        # Aggregate stats
        avg_sentiment = sum(s['sentiment'] for s in sentiments) / len(sentiments)
        categories = Counter(s['category'] for s in sentiments)

        patterns = [
            {
                'category': cat,
                'count': count,
                'percentage': count / len(issues) * 100
            }
            for cat, count in categories.items()
        ]

        insights = [
            f"Overall sentiment: {avg_sentiment:.2f} "
            f"({'positive' if avg_sentiment > 0 else 'negative'})",
            f"Distribution: {categories['positive']} positive, "
            f"{categories['neutral']} neutral, {categories['negative']} negative"
        ]

        return AnalysisResult(
            summary=f"Analyzed sentiment for {len(issues)} issues",
            insights=insights,
            patterns=patterns,
            metadata={'avg_sentiment': float(avg_sentiment)}
        )

    def find_similar_issues(
        self,
        query_issue: Issue,
        all_issues: List[Issue],
        top_n: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find issues similar to a query issue.

        Args:
            query_issue: Issue to find similar ones for
            all_issues: Pool of issues to search
            top_n: Number of similar issues to return

        Returns:
            List of similar issues with similarity scores
        """
        if not self.nlp:
            return []

        query_text = f"{query_issue.title} {query_issue.description}"
        query_doc = self.nlp(query_text)

        similarities = []

        for issue in all_issues:
            if issue.id == query_issue.id:
                continue

            text = f"{issue.title} {issue.description}"
            doc = self.nlp(text)

            # Calculate similarity
            similarity = query_doc.similarity(doc)

            similarities.append({
                'issue_id': issue.id,
                'title': issue.title,
                'similarity': float(similarity),
                'labels': issue.labels
            })

        # Sort by similarity
        similarities.sort(key=lambda x: x['similarity'], reverse=True)

        return similarities[:top_n]
