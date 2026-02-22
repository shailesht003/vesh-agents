# Contributing to Vesh Agents

Thank you for your interest in contributing to Vesh Agents! We welcome contributions of all kinds — bug fixes, new connectors, better detection algorithms, documentation, and more.

## Quick Start

```bash
git clone https://github.com/shailesht003/vesh-agents.git
cd vesh-agents
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

Verify everything works:

```bash
pytest -v
ruff check .
```

## What Can I Contribute?

### High Impact (great for first-timers)

| Area | Examples | Label |
|------|----------|-------|
| **New connectors** | HubSpot, Salesforce, BigQuery, Snowflake, MongoDB | `connector` |
| **New verticals** | Customer success, sales ops, marketing analytics | `vertical` |
| **CLI improvements** | New output formats, interactive mode, progress bars | `cli` |
| **Documentation** | Tutorials, examples, Jupyter notebooks | `docs` |

### Technical Contributions

| Area | Examples |
|------|----------|
| **Detection algorithms** | Isolation Forest, DBSCAN, Prophet integration |
| **Resolution strategies** | ML-based scoring, graph-based resolution |
| **Metric definitions** | ARR, CAC, LTV, payback period |
| **Performance** | Async improvements, caching, batch processing |

Look for issues labeled [`good first issue`](https://github.com/shailesht003/vesh-agents/labels/good%20first%20issue) to find beginner-friendly tasks.

## Development Workflow

1. **Fork** the repository
2. **Create a branch** from `main`: `git checkout -b feat/my-feature`
3. **Make your changes** with tests
4. **Run the checks**:
   ```bash
   pytest -v
   ruff check .
   ruff format --check .
   ```
5. **Commit** with a descriptive message (see below)
6. **Push** and open a Pull Request

## Commit Messages

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add BigQuery connector
fix: handle empty CSV files gracefully
docs: add Jupyter notebook example for Stripe analysis
test: add unit tests for anomaly detection
refactor: simplify metric computation pipeline
```

## Code Style

- **Linter/formatter**: `ruff` (config in `pyproject.toml`)
- **Type hints**: Required for all public functions and methods
- **Docstrings**: Required for all public classes, functions, and modules
- **Line length**: 130 characters max
- **Python**: 3.10+ (use modern syntax — `X | Y` unions, `match/case`, etc.)

## Adding a New Connector

1. Create `vesh_agents/connectors/your_source.py`
2. Extend `BaseConnector` from `vesh_agents.connectors.base`
3. Implement: `test_connection`, `discover`, `extract_full`, `extract_incremental`, `get_capabilities`
4. Add a CLI command in `vesh_agents/cli/main.py`
5. Add an optional dependency group in `pyproject.toml`
6. Add tests in `tests/test_connector_your_source.py`
7. Update `README.md`

Example skeleton:

```python
from vesh_agents.connectors.base import BaseConnector, NormalizedRecord, DiscoveredSchema, ConnectorCapabilities

class MySourceConnector(BaseConnector):
    async def test_connection(self) -> bool: ...
    async def discover(self) -> DiscoveredSchema: ...
    async def extract_full(self, object_types=None) -> list[NormalizedRecord]: ...
    async def extract_incremental(self, since, object_types=None) -> list[NormalizedRecord]: ...
    def get_capabilities(self) -> ConnectorCapabilities: ...
```

## Adding a New Vertical

1. Create a directory under `vesh_agents/verticals/your_vertical/`
2. Add `__init__.py`, `agents.py`, `metrics.py`, `prompts.py`
3. Define domain-specific metric ontology in `metrics.py`
4. Create specialized agent prompts in `prompts.py`
5. Wire up agents and orchestrator in `agents.py`
6. Add tests and update the README

## Running Tests

```bash
# All tests
pytest -v

# Specific file
pytest tests/test_metrics.py -v

# With coverage
pytest --cov=vesh_agents --cov-report=term-missing
```

## Pull Request Checklist

- [ ] Tests pass (`pytest -v`)
- [ ] Linter passes (`ruff check .`)
- [ ] New code has type hints
- [ ] New public API has docstrings
- [ ] README updated if adding user-facing features
- [ ] One feature or fix per PR (keep it focused)

## Questions?

- Open a [GitHub Discussion](https://github.com/shailesht003/vesh-agents/discussions) or issue
- Tag `@shailesht003` for maintainer input

---

Thank you for helping make Vesh Agents better!
