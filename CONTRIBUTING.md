# Contributing to Vesh Agents

Thank you for your interest in contributing to Vesh Agents! We welcome contributions from everyone.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/vesh-agents.git`
3. Install in development mode: `pip install -e ".[dev]"`
4. Create a branch: `git checkout -b my-feature`

## Development Setup

```bash
cd vesh-agents
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Running Tests

```bash
pytest
ruff check .
```

## What Can I Contribute?

- **New connectors** — add support for HubSpot, Salesforce, MySQL, BigQuery, etc.
- **New verticals** — extend beyond revenue intelligence (customer success, sales ops, etc.)
- **Improved detection** — new anomaly detection algorithms
- **Better CLI** — new commands, output formats, interactive mode
- **Documentation** — tutorials, examples, API docs
- **Bug fixes** — always welcome

## Pull Request Process

1. Ensure your code passes `ruff check` and `pytest`
2. Update the README if you've added new features
3. Keep PRs focused — one feature or fix per PR
4. Write descriptive commit messages

## Code Style

- We use `ruff` for linting and formatting
- Type hints required for all public functions
- Docstrings for all public classes and functions

## Questions?

Open an issue or reach out at https://vesh-ai.netlify.app/contact
