"""Pre-configured revenue intelligence agents."""

from __future__ import annotations

from agents import Agent, handoff

from vesh_agents.tools.connectors import extract_postgres, extract_stripe, import_csv
from vesh_agents.tools.detection import detect_anomalies
from vesh_agents.tools.metrics import compute_saas_metrics, list_available_metrics
from vesh_agents.tools.reasoning import explain_anomaly
from vesh_agents.tools.resolution import resolve_entities
from vesh_agents.verticals.revenue.prompts import (
    CONNECTOR_PROMPT,
    DETECTOR_PROMPT,
    METRIC_PROMPT,
    REASONER_PROMPT,
    RESOLVER_PROMPT,
    REVENUE_ORCHESTRATOR_PROMPT,
)


def create_revenue_orchestrator(model: str = "litellm/deepseek/deepseek-chat") -> Agent:
    """Create a fully configured revenue intelligence orchestrator.

    This is the quickest way to get started with SaaS revenue analysis:

        from vesh_agents.verticals.revenue import create_revenue_orchestrator
        from agents import Runner

        orchestrator = create_revenue_orchestrator(model="litellm/deepseek/deepseek-chat")
        result = await Runner.run(orchestrator, "Analyze revenue from my Stripe data")
    """
    reasoner = Agent(name="InsightReasoner", instructions=REASONER_PROMPT, tools=[explain_anomaly], model=model)
    detector = Agent(
        name="AnomalyDetector", instructions=DETECTOR_PROMPT, tools=[detect_anomalies], model=model, handoffs=[handoff(reasoner)]
    )
    computer = Agent(
        name="MetricComputer",
        instructions=METRIC_PROMPT,
        tools=[compute_saas_metrics, list_available_metrics],
        model=model,
        handoffs=[handoff(detector)],
    )
    resolver = Agent(
        name="EntityResolver", instructions=RESOLVER_PROMPT, tools=[resolve_entities], model=model, handoffs=[handoff(computer)]
    )
    connector = Agent(
        name="DataConnector",
        instructions=CONNECTOR_PROMPT,
        tools=[import_csv, extract_stripe, extract_postgres],
        model=model,
        handoffs=[handoff(resolver)],
    )

    return Agent(
        name="Vesh Revenue Analyst",
        instructions=REVENUE_ORCHESTRATOR_PROMPT,
        model=model,
        handoffs=[handoff(connector), handoff(resolver), handoff(computer), handoff(detector), handoff(reasoner)],
    )
