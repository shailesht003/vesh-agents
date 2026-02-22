# r/Python Post

## Title

I built an open-source framework with 6 AI agents that compute SaaS metrics from your CSV/Stripe/Postgres data

## Body

Hey r/Python!

I just open-sourced **Vesh Agents** — a Python framework that uses 6 specialized AI agents to analyze business data and compute SaaS revenue metrics.

**30-second demo:**

```bash
pip install vesh-agents
vesh analyze csv revenue_data.csv
```

This gives you MRR, churn, ARPU, NRR, Quick Ratio, and more — instantly.

**What makes it interesting from a Python perspective:**

- Built on the new **OpenAI Agents SDK** — uses agent handoffs, function tools, and structured outputs
- **BYOM (Bring Your Own Model)** via **LiteLLM** — swap models with one line
- Entity resolution using **rapidfuzz** for fuzzy matching + custom blocking/scoring/clustering pipeline
- Anomaly detection with **NumPy** (z-score, rate-of-change)
- CLI built with **Click** + **Rich** for beautiful terminal output
- Metric ontology is declarative — add new metrics by defining a `MetricDef`, not writing computation code
- Full async support with proper typing (Python 3.10+)
- **83 tests**, CI on Python 3.10/3.11/3.12

**Architecture:**
```
Orchestrator → DataConnector → EntityResolver → MetricComputer → AnomalyDetector → InsightReasoner
```

Each agent has its own tools and instructions. The orchestrator delegates via handoffs based on natural language queries.

**Links:**
- GitHub: https://github.com/shailesht003/vesh-agents
- Apache 2.0 licensed
- Contributions welcome — 15 open issues labeled "good first issue"

Would love your feedback on the architecture and what you'd like to see added.
