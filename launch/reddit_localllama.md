# r/LocalLLaMA Post

## Title

Open-source agentic framework that works with any local model — 6 AI agents for revenue intelligence (LiteLLM + OpenAI Agents SDK)

## Body

Built an open-source framework called **Vesh Agents** that's designed to work with any model — local or API — via LiteLLM.

**Why this is relevant to r/LocalLLaMA:**

The framework uses 6 AI agents for business data analysis, and every agent supports BYOM (Bring Your Own Model):

```python
from vesh_agents.verticals.revenue import create_revenue_orchestrator

# Use any local model via LiteLLM
orchestrator = create_revenue_orchestrator(model="litellm/ollama/llama3.1")
# or: model="litellm/ollama/deepseek-r1"
# or: model="litellm/ollama/qwen2.5"
```

**The key insight:** Most of the pipeline doesn't even need an LLM. The data extraction, entity resolution, metric computation, and anomaly detection are all deterministic Python code. Only the InsightReasoner (the "explain why churn spiked" agent) uses the LLM. So even with a smaller local model, you get accurate metrics — the LLM just adds the narrative layer.

**What it does:**
- Extracts data from CSV/Stripe/Postgres
- Resolves entities across sources (fuzzy matching, no training data)
- Computes SaaS metrics (MRR, churn, ARPU, NRR)
- Detects anomalies (z-score, rate-of-change)
- Explains findings using your chosen LLM

**Zero API keys needed for basic use:**
```bash
pip install vesh-agents
vesh analyze csv data.csv
```

MCP server included — works with Cursor, Claude Desktop, etc.

**GitHub:** https://github.com/shailesht003/vesh-agents (Apache 2.0)

Curious if anyone has tried running the OpenAI Agents SDK with local models via LiteLLM — would love to hear about performance with different model sizes.
