"""Brain CLI - Agent-agnostic research and automation hub."""

from .orchestrator import AgnosticOrchestrator
from .router import SimpleRouter

__version__ = "0.1.0"

__all__ = [
    "AgnosticOrchestrator",
    "SimpleRouter",
]
