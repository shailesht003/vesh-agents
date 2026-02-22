"""OpenCode integration — install, configure, and launch OpenCode with Vesh agents."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

OPENCODE_CONFIG_TEMPLATE = {
    "$schema": "https://opencode.ai/config.json",
    "mcp": {
        "vesh": {
            "type": "local",
            "command": "vesh",
            "args": ["mcp", "serve"],
        }
    },
}

ANALYST_AGENT = """\
---
description: Analyze SaaS revenue data — compute metrics, detect anomalies, explain trends
mode: primary
tools:
  write: false
  edit: false
---

You are the Vesh AI revenue analyst. You help users understand their business data.

You have access to MCP tools from the Vesh AI server:

- **analyze_csv** — Full pipeline: import CSV, compute all SaaS metrics, detect anomalies
- **import_csv** — Import raw records from a CSV file
- **compute_metrics** — Compute MRR, churn, ARPU, NRR, Quick Ratio from entity data
- **resolve_entities** — Match and deduplicate records across data sources
- **detect_anomalies** — Find statistical anomalies in metric time series
- **list_metrics** — Show all available metric definitions

Your workflow:
1. Start by understanding what data the user has (CSV file, Stripe, Postgres)
2. Use analyze_csv for a quick overview, or the individual tools for deeper analysis
3. Present metrics in a clear, formatted way
4. Highlight anomalies and explain what they mean in business terms
5. Suggest actions based on the data

Always format currency with $ signs and commas. Show percentages with one decimal.
When explaining anomalies, connect them to business impact.
"""

EXPLORER_AGENT = """\
---
description: Explore and understand revenue data sources before analysis
mode: subagent
tools:
  write: false
  edit: false
  bash: false
---

You are a data exploration specialist. Your job is to help users understand
their data before running the full analysis pipeline.

Use the import_csv tool to load data, then summarize:
- How many records and what fields are present
- Data quality issues (missing values, inconsistent formats)
- What entity types exist (customers, subscriptions, invoices)
- Date ranges and time coverage
- Revenue distribution patterns

Be concise. Present findings as bullet points.
"""


def find_opencode() -> str | None:
    """Return the path to the opencode binary, or None if not installed."""
    return shutil.which("opencode")


def install_opencode() -> bool:
    """Install OpenCode via npm. Returns True on success."""
    npm = shutil.which("npm")
    if not npm:
        return False
    try:
        subprocess.run([npm, "install", "-g", "opencode-ai"], check=True, capture_output=True)
        return find_opencode() is not None
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def get_config_dir(project_dir: Path | None = None) -> Path:
    """Return the .opencode directory for the given project (or cwd)."""
    base = project_dir or Path.cwd()
    return base / ".opencode"


def write_opencode_config(project_dir: Path | None = None) -> Path:
    """Write opencode.json with the Vesh MCP server configured."""
    base = project_dir or Path.cwd()
    config_path = base / "opencode.json"
    config_path.write_text(json.dumps(OPENCODE_CONFIG_TEMPLATE, indent=2) + "\n")
    return config_path


def write_agent_files(project_dir: Path | None = None) -> list[Path]:
    """Write Vesh agent markdown files to .opencode/agents/."""
    agents_dir = get_config_dir(project_dir) / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)

    created = []
    analyst_path = agents_dir / "analyst.md"
    analyst_path.write_text(ANALYST_AGENT)
    created.append(analyst_path)

    explorer_path = agents_dir / "explorer.md"
    explorer_path.write_text(EXPLORER_AGENT)
    created.append(explorer_path)

    return created


def setup(project_dir: Path | None = None) -> dict:
    """Full setup: check/install OpenCode, write config and agents. Returns status dict."""
    result = {"opencode_installed": False, "config_written": False, "agents_created": []}

    oc = find_opencode()
    if oc:
        result["opencode_installed"] = True
        result["opencode_path"] = oc
    else:
        if install_opencode():
            result["opencode_installed"] = True
            result["opencode_path"] = find_opencode()
        else:
            result["opencode_installed"] = False
            result["install_hint"] = "Install manually: npm install -g opencode-ai (or: curl -fsSL https://opencode.ai/install | bash)"

    config_path = write_opencode_config(project_dir)
    result["config_written"] = True
    result["config_path"] = str(config_path)

    agents = write_agent_files(project_dir)
    result["agents_created"] = [str(p) for p in agents]

    return result


def launch_chat(project_dir: Path | None = None, model: str | None = None, agent: str = "analyst") -> None:
    """Launch OpenCode TUI with Vesh configuration."""
    oc = find_opencode()
    if not oc:
        print("Error: OpenCode not installed. Run 'vesh setup' first.", file=sys.stderr)
        sys.exit(1)

    cmd = [oc, "--agent", agent]
    if model:
        cmd.extend(["--model", model])

    env = os.environ.copy()
    os.execvp(oc, cmd)


def launch_run(prompt: str, model: str | None = None, agent: str = "analyst") -> None:
    """Run a one-off prompt through OpenCode non-interactively."""
    oc = find_opencode()
    if not oc:
        print("Error: OpenCode not installed. Run 'vesh setup' first.", file=sys.stderr)
        sys.exit(1)

    cmd = [oc, "run", "--agent", agent]
    if model:
        cmd.extend(["--model", model])
    cmd.append(prompt)

    os.execvp(oc, cmd)
