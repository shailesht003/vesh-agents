"""Vesh Agents — Live Stripe Analysis Example

Connect to your Stripe account and analyze real revenue data.
Requires: pip install vesh-agents[stripe]
"""

import asyncio
import os
import sys

from agents import Runner

from vesh_agents.verticals.revenue import create_revenue_orchestrator


async def main():
    if not os.environ.get("STRIPE_API_KEY"):
        print("Set STRIPE_API_KEY environment variable:")
        print("  export STRIPE_API_KEY=sk_live_...")
        sys.exit(1)

    orchestrator = create_revenue_orchestrator(model="litellm/deepseek/deepseek-chat")
    result = await Runner.run(
        orchestrator,
        "Extract data from Stripe (credentials are in the environment). "
        "Compute all SaaS metrics, detect anomalies, and explain any issues found.",
    )
    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
