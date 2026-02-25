# Changelog

All notable changes to this project will be documented in this file.

## [0.1.0] — 2026-02-22

### Added

- **6 AI agents**: DataConnector, EntityResolver, MetricComputer, AnomalyDetector, InsightReasoner, Orchestrator
- **BYOM (Bring Your Own Model)**: swap Claude, DeepSeek, GPT, Llama, or any LiteLLM-compatible model
- **Connectors**: CSV, Stripe, PostgreSQL with schema detection and normalization
- **Entity resolution**: multi-stage pipeline (blocking → fuzzy scoring → clustering → canonical selection) — no training data required
- **SaaS metric computation**: MRR, NRR, ARPU, churn, Quick Ratio, and 5 more from a declarative ontology
- **Anomaly detection**: z-score and rate-of-change statistical methods with configurable thresholds
- **CLI**: `vesh analyze`, `vesh run`, `vesh chat`, `vesh setup`, `vesh mcp serve`
- **MCP server**: FastMCP with 6 tools — works with Cursor, Claude Desktop, OpenCode
- **OpenCode integration**: `vesh setup` + `vesh chat` for interactive AI analysis
- **Output formats**: Rich terminal tables and JSON
- **CI**: GitHub Actions for lint + test on Python 3.11 and 3.12
- **PyPI publishing**: automated via GitHub Releases with OIDC trusted publishing
- **83 tests** covering connectors, metrics, detection, resolution, and ontology
- **Apache 2.0 license**

### Security

- Credentials read from environment variables (STRIPE_API_KEY, PGUSER, PGPASSWORD) — never passed through LLM prompts
- Vesh Cloud URL configurable via VESH_CLOUD_URL env var

[0.1.0]: https://github.com/shailesht003/vesh-agents/releases/tag/v0.1.0
