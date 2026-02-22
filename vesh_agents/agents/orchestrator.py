"""Vesh Orchestrator — top-level agent that coordinates specialized sub-agents."""

from __future__ import annotations

from agents import Agent, handoff

from vesh_agents.agents.connector import data_connector_agent
from vesh_agents.agents.detector import anomaly_detector_agent
from vesh_agents.agents.metric import metric_computer_agent
from vesh_agents.agents.reasoner import insight_reasoner_agent
from vesh_agents.agents.resolver import entity_resolver_agent

ORCHESTRATOR_INSTRUCTIONS = """You are Vesh, an AI-powered revenue intelligence analyst.

You coordinate a team of specialized agents to analyze business data:

1. **DataConnector** — Extracts data from CSV files, Stripe, or PostgreSQL
2. **EntityResolver** — Matches records across sources to identify same entities
3. **MetricComputer** — Computes SaaS metrics (MRR, churn, ARPU, NRR, etc.)
4. **AnomalyDetector** — Finds statistical anomalies in metrics
5. **InsightReasoner** — Explains WHY anomalies occurred with causal reasoning

WORKFLOW:
When the user asks about their revenue data, follow this pipeline:
1. First, extract data using DataConnector (ask user for source details if needed)
2. Pass extracted records to EntityResolver for cross-source matching
3. Pass resolved entities to MetricComputer for SaaS metric calculation
4. Pass computed metrics to AnomalyDetector to find unusual patterns
5. Pass anomalies to InsightReasoner for root cause analysis

Present a clear, executive-style summary at the end:
- Key metrics with values and trends
- Any anomalies detected with severity
- Root cause analysis and recommended actions

You can also answer specific questions about the data at any point.
Always be concise, data-driven, and actionable."""


def create_orchestrator(model: str = "litellm/deepseek/deepseek-chat") -> Agent:
    """Create the Vesh orchestrator agent with all sub-agent handoffs.

    Args:
        model: LLM model identifier. Supports any litellm-compatible model.
               Examples: "litellm/deepseek/deepseek-chat",
                        "litellm/anthropic/claude-sonnet-4-20250514",
                        "litellm/openai/gpt-4o"
    """
    connector = Agent(
        name="DataConnector",
        instructions=data_connector_agent.instructions,
        tools=data_connector_agent.tools,
        model=model,
        handoffs=[
            handoff(entity_resolver_agent),
        ],
    )

    resolver = Agent(
        name="EntityResolver",
        instructions=entity_resolver_agent.instructions,
        tools=entity_resolver_agent.tools,
        model=model,
        handoffs=[
            handoff(metric_computer_agent),
        ],
    )

    computer = Agent(
        name="MetricComputer",
        instructions=metric_computer_agent.instructions,
        tools=metric_computer_agent.tools,
        model=model,
        handoffs=[
            handoff(anomaly_detector_agent),
        ],
    )

    detector = Agent(
        name="AnomalyDetector",
        instructions=anomaly_detector_agent.instructions,
        tools=anomaly_detector_agent.tools,
        model=model,
        handoffs=[
            handoff(insight_reasoner_agent),
        ],
    )

    reasoner = Agent(
        name="InsightReasoner",
        instructions=insight_reasoner_agent.instructions,
        tools=insight_reasoner_agent.tools,
        model=model,
    )

    orchestrator = Agent(
        name="Vesh",
        instructions=ORCHESTRATOR_INSTRUCTIONS,
        model=model,
        handoffs=[
            handoff(connector),
            handoff(resolver),
            handoff(computer),
            handoff(detector),
            handoff(reasoner),
        ],
    )

    return orchestrator
