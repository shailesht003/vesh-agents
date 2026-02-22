# Hacker News — Show HN Post

## Title (80 chars max)

Show HN: Vesh Agents – 6 AI agents that compute SaaS metrics from your data (OSS)

## URL

https://github.com/shailesht003/vesh-agents

## First Comment (post this immediately after submitting)

Hi HN, I built Vesh Agents — an open-source framework that uses 6 AI agents to analyze your business data and compute SaaS metrics automatically.

The problem: SaaS companies track revenue across Stripe, Postgres, spreadsheets, and CRMs. Getting a unified view of MRR, churn, and NRR means stitching together multiple sources, resolving duplicate entities, and building custom dashboards. Most teams either pay $500+/mo for Baremetrics/ChartMogul or write fragile scripts.

Vesh Agents takes a different approach — it's an agentic pipeline:

1. **DataConnector** — pulls data from CSV, Stripe, or Postgres
2. **EntityResolver** — matches records across sources (blocking → scoring → clustering)
3. **MetricComputer** — computes MRR, churn, ARPU, NRR, Quick Ratio from an ontology
4. **AnomalyDetector** — z-score and rate-of-change detection
5. **InsightReasoner** — uses your LLM to explain root causes
6. **Orchestrator** — coordinates everything via natural language

The key design decisions:
- **BYOM (Bring Your Own Model)** — swap Claude, GPT, DeepSeek, or Llama via LiteLLM. The core pipeline (metrics, resolution, detection) works without any LLM.
- **Built on OpenAI Agents SDK** — agents hand off to each other, each with specialized tools
- **MCP server** — works with Cursor, Claude Desktop, OpenCode
- **No LLM needed for basic analysis** — `pip install vesh-agents && vesh analyze csv data.csv` gives you metrics in 30 seconds with zero API keys

The entity resolution is the part I'm most proud of — it uses email domain blocking, fuzzy company name matching (rapidfuzz), temporal scoring, and amount matching to resolve records across sources without training data.

Tech: Python, OpenAI Agents SDK, LiteLLM, NumPy, Click, Rich. Apache 2.0.

Would love feedback on the architecture and what connectors/metrics to add next.
