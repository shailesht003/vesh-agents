<p align="center">
  <img src="social-preview.png" alt="Vesh Agents — Agentic Revenue Intelligence" width="800">
</p>

<p align="center">
  <h1 align="center">Vesh Agents</h1>
  <p align="center">
    <strong>Open-source agentic framework for revenue intelligence</strong>
  </p>
  <p align="center">
    6 AI agents that extract, resolve, compute, detect, and explain your business data.
  </p>
  <p align="center">
    <a href="https://github.com/shailesht003/Vesh-AI/actions/workflows/ci.yml"><img src="https://github.com/shailesht003/Vesh-AI/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
    <a href="https://github.com/shailesht003/Vesh-AI/tree/main/vesh-agents"><img src="https://img.shields.io/badge/license-Apache%202.0-blue.svg" alt="License"></a>
    <a href="https://pypi.org/project/vesh-agents/"><img src="https://img.shields.io/badge/python-3.11%2B-blue" alt="Python"></a>
    <a href="https://github.com/shailesht003/Vesh-AI"><img src="https://img.shields.io/github/stars/shailesht003/Vesh-AI?style=social" alt="Stars"></a>
  </p>
</p>

---

## What is Vesh Agents?

Vesh Agents is an agentic AI framework for business data analysis, starting with SaaS revenue intelligence. Built on the [OpenAI Agents SDK](https://github.com/openai/openai-agents-python), it provides:

- **6 specialized agents** that work together as a pipeline
- **BYOM (Bring Your Own Model)** — use Claude, DeepSeek, GPT, Llama, or any LiteLLM-compatible model
- **Entity resolution** — automatically match records across Stripe, Postgres, CSV, and more
- **SaaS metric computation** — MRR, churn, ARPU, NRR, Quick Ratio out of the box
- **Anomaly detection** — statistical methods find unusual patterns in your metrics
- **CLI + MCP server** — use from terminal or integrate with Cursor, OpenCode, Claude Desktop

## Quickstart

```bash
pip install vesh-agents
```

### Analyze a CSV in 30 seconds

```bash
vesh analyze csv examples/sample_data.csv
```

```
  VESH AI   Agentic Revenue Intelligence

  ▸ DataConnector  Loading CSV...
  ✓ DataConnector  40 records extracted
  ▸ EntityResolver  Resolving entities...
  ✓ EntityResolver  40 entities resolved
  ▸ MetricComputer  Computing SaaS metrics...
  ✓ MetricComputer  10 metrics computed

  ┌─────────────────────────────┬──────────┬─────────┐
  │ Metric                      │    Value │  Change │
  ├─────────────────────────────┼──────────┼─────────┤
  │ Monthly Recurring Revenue   │ $152,413 │    —    │
  │ Active Customers            │       36 │    —    │
  │ Average Revenue Per User    │   $4,234 │    —    │
  └─────────────────────────────┴──────────┴─────────┘
```

### Use with any LLM (BYOM)

```python
from agents import Runner
from vesh_agents.verticals.revenue import create_revenue_orchestrator

# Use Claude, DeepSeek, GPT, or any LiteLLM model
orchestrator = create_revenue_orchestrator(model="litellm/anthropic/claude-sonnet-4-20250514")

result = await Runner.run(
    orchestrator,
    "Analyze revenue from examples/sample_data.csv. Why is churn increasing?"
)
print(result.final_output)
```

### Connect to live Stripe

```bash
export STRIPE_API_KEY=sk_live_...
vesh analyze stripe
```

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    Vesh Orchestrator Agent                     │
│  Coordinates the pipeline based on natural language queries   │
└──────────┬───────────┬──────────┬──────────┬────────────────┘
           │           │          │          │
    ┌──────▼──┐  ┌─────▼───┐ ┌───▼────┐ ┌──▼──────┐ ┌────────┐
    │  Data   │  │ Entity  │ │ Metric │ │Anomaly │ │Insight │
    │Connector│→ │Resolver │→│Computer│→│Detector│→│Reasoner│
    └─────────┘  └─────────┘ └────────┘ └────────┘ └────────┘
         │            │           │           │          │
    CSV/Stripe/   Blocking    MRR/Churn   Z-score    BYOM LLM
    Postgres      Scoring     ARPU/NRR    Rate-of-   Explanation
                  Clustering  Quick Ratio change
```

Each agent has its own tools and instructions. The orchestrator delegates to specialists via handoffs. All agents use your chosen LLM model.

## Available Agents

| Agent | Role | MCP Tools |
|-------|------|-----------|
| **DataConnector** | Extract data from sources | `import_csv`, `extract_stripe`, `extract_postgres` |
| **EntityResolver** | Match records across sources | `resolve_entities` |
| **MetricComputer** | Compute SaaS metrics | `compute_metrics`, `list_metrics` |
| **AnomalyDetector** | Find statistical anomalies | `detect_anomalies` |
| **InsightReasoner** | Explain root causes | `explain_anomaly` |
| **Vesh Orchestrator** | Coordinate the pipeline | `analyze_csv` (full pipeline) |

## SaaS Metrics Computed

| Metric | Description |
|--------|-------------|
| **MRR** | Monthly Recurring Revenue |
| **New MRR** | Revenue from new subscriptions |
| **Expansion MRR** | Revenue increase from upgrades |
| **Contraction MRR** | Revenue decrease from downgrades |
| **Churned MRR** | Revenue lost from cancellations |
| **NRR** | Net Revenue Retention |
| **Active Customers** | Count of active subscriptions |
| **ARPU** | Average Revenue Per User |
| **Quick Ratio** | Growth efficiency ratio |
| **Logo Churn Rate** | Customer loss percentage |

## CLI Reference

```bash
# Quick offline analysis (no LLM needed)
vesh analyze csv revenue.csv
vesh analyze stripe                  # reads STRIPE_API_KEY from env
vesh analyze postgres --host db.example.com --database myapp  # reads PGUSER/PGPASSWORD from env

# Interactive AI chat (powered by OpenCode)
vesh setup                          # one-time: install OpenCode + configure MCP
vesh chat                           # open the TUI analyst
vesh chat --model anthropic/claude-sonnet-4-20250514

# Natural language analysis (requires LLM)
vesh run "Why did churn spike last week?" --source csv:revenue.csv

# Output formats
vesh analyze csv data.csv --output json    # JSON to stdout
vesh analyze csv data.csv --output rich    # Rich terminal (default)

# MCP server (for Cursor, Claude Desktop, or other MCP clients)
vesh mcp serve
```

## Using as a Python Library

```python
# Direct pipeline (no LLM needed)
from vesh_agents.connectors.csv import CsvConnector
from vesh_agents.metrics.computation import MetricComputationEngine
from datetime import date

connector = CsvConnector(connection_id="demo", config={"file_path": "data.csv"})
records = await connector.extract_full()
entities = [r.data for r in records]

engine = MetricComputationEngine()
metrics = engine.compute_all("tenant", date.today(), entities)

for m in metrics:
    print(f"{m.metric_id}: {m.value}")
```

## Verticals

Vesh Agents uses a vertical architecture. Each vertical packages domain-specific agents, prompts, and metrics for a particular business use case.

**Revenue Intelligence** (included) — SaaS metrics, churn analysis, revenue decomposition

More verticals coming soon. Or build your own:

```python
from vesh_agents.core.vertical import Vertical, VerticalConfig

class CustomerSuccess(Vertical):
    config = VerticalConfig(
        name="customer_success",
        description="Customer health scoring and churn prediction",
        metric_ids=["health_score", "nps", "usage_frequency"],
    )
```

## MCP Integration

Vesh Agents ships a real [MCP](https://modelcontextprotocol.io) server (FastMCP, stdio transport) exposing 6 tools: `analyze_csv`, `import_csv`, `compute_metrics`, `resolve_entities`, `detect_anomalies`, `list_metrics`.

### OpenCode (recommended)

```bash
vesh setup   # writes opencode.json + .opencode/agents/
vesh chat    # launches OpenCode TUI with the Vesh analyst agent
```

### Cursor / Claude Desktop

Add to your MCP config (`.cursor/mcp.json` or `claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "vesh": {
      "command": "vesh",
      "args": ["mcp", "serve"]
    }
  }
}
```

### Manual

```bash
vesh mcp serve   # starts stdio MCP server — any MCP client can connect
```

## Vesh AI Cloud (Optional)

The open-source framework runs entirely locally. For teams that want managed infrastructure:

- **Automated daily pipelines** — connect once, get daily insights
- **Cross-company benchmarks** — "Your NRR is 40th percentile for Series B SaaS"
- **Historical intelligence** — 90-day trends and institutional memory
- **Slack/Teams delivery** — daily revenue briefs, anomaly alerts
- **Agent Console** — visual dashboard for agent execution traces

Visit [vesh-ai.netlify.app](https://vesh-ai.netlify.app) to learn more.

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for setup instructions, coding standards, and areas where help is needed.

```bash
git clone https://github.com/shailesht003/Vesh-AI.git
cd Vesh-AI/vesh-agents
pip install -e ".[dev]"
pytest   # 83 tests
```

## License

Apache 2.0 — see [LICENSE](LICENSE) for details.

---

<p align="center">
  Built with ❤️ by <a href="https://vesh-ai.netlify.app">Vesh AI</a>
</p>
