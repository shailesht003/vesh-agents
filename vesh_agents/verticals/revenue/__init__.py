"""Revenue Intelligence Vertical — the first Vesh AI vertical.

Pre-configured agents, prompts, and metric definitions for SaaS revenue analytics.
"""

from vesh_agents.verticals.revenue.agents import create_revenue_orchestrator
from vesh_agents.verticals.revenue.metrics import REVENUE_METRICS

__all__ = ["create_revenue_orchestrator", "REVENUE_METRICS"]
