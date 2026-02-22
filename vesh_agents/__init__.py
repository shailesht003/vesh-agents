"""Vesh Agents — Open-source agentic framework for revenue intelligence.

Built on OpenAI Agents SDK. BYOM (Bring Your Own Model).
"""

__version__ = "0.1.0"

from vesh_agents.agents.orchestrator import create_orchestrator
from vesh_agents.core.vertical import Vertical

__all__ = [
    "__version__",
    "create_orchestrator",
    "Vertical",
]
