"""
Analytics module for Brain CLI.

Provides:
- Data parsers (Jira, GitHub exports)
- Pattern detection (clustering, topic modeling)
- NLP analysis (entity extraction, sentiment)
- Integration with agent queries
"""

from .parsers import JiraParser, GitHubParser
from .patterns import PatternDetector
from .nlp import NLPAnalyzer

__all__ = [
    'JiraParser',
    'GitHubParser',
    'PatternDetector',
    'NLPAnalyzer'
]
