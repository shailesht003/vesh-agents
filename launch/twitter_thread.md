# Twitter/X Launch Thread

## Tweet 1 (Main — include demo GIF if available)

I just open-sourced Vesh Agents — 6 AI agents that analyze your SaaS revenue data in 30 seconds.

pip install vesh-agents
vesh analyze csv data.csv

MRR, churn, ARPU, NRR — computed instantly from CSV, Stripe, or Postgres.

Built on @OpenAI Agents SDK. BYOM via @LiteLLM.

github.com/shailesht003/vesh-agents

## Tweet 2

How it works:

1/ DataConnector — pulls from CSV, Stripe, Postgres
2/ EntityResolver — matches records across sources
3/ MetricComputer — MRR, churn, ARPU, NRR, Quick Ratio
4/ AnomalyDetector — z-score + rate-of-change
5/ InsightReasoner — LLM explains root causes
6/ Orchestrator — coordinates via natural language

## Tweet 3

What makes it different:

- BYOM — use Claude, GPT, DeepSeek, Llama, or any model
- Core pipeline works WITHOUT any LLM
- Entity resolution without training data
- MCP server for Cursor/Claude Desktop
- 83 tests, CI on 3 Python versions
- Apache 2.0

## Tweet 4

Why I built this:

SaaS teams track revenue across 3-5 tools. Getting unified metrics means:
- Manual exports
- Spreadsheet gymnastics
- $500/mo for Baremetrics

Vesh Agents: pip install, point at your data, done.

## Tweet 5

Want to contribute?

15 open "good first issue" issues:
- New connectors (HubSpot, Salesforce, BigQuery)
- New metrics (ARR, CAC, LTV)
- New verticals (Customer Success)
- Jupyter notebook examples

github.com/shailesht003/vesh-agents

## Hashtags (add to Tweet 1)

#opensource #AIagents #SaaS #buildinpublic #Python

## People to tag (in a reply, not main tweet — less spammy)

@OpenAI @LiteLLM @alexalbert__ @kaboroevich @cursor_ai
