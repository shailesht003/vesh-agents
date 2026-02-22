"""Vesh Agents — Quickstart Example

Analyze a CSV file with 6 AI agents in 10 lines of code.
"""

import asyncio
from agents import Runner
from vesh_agents.verticals.revenue import create_revenue_orchestrator

async def main():
    orchestrator = create_revenue_orchestrator(model="litellm/deepseek/deepseek-chat")
    result = await Runner.run(
        orchestrator,
        "Analyze the revenue data in examples/sample_data.csv. "
        "Compute all SaaS metrics and identify any anomalies.",
    )
    print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())
