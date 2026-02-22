"""Vesh CLI — terminal interface for the agentic revenue intelligence framework."""

from __future__ import annotations

import asyncio
import sys

import click
from rich.console import Console

from vesh_agents.output.console import (
    print_agent_complete,
    print_agent_start,
    print_anomalies,
    print_banner,
    print_metrics_table,
    print_result,
)

console = Console()

DEFAULT_MODEL = "litellm/deepseek/deepseek-chat"


@click.group()
@click.version_option(package_name="vesh-agents")
def cli():
    """Vesh AI — Agentic Revenue Intelligence Framework"""
    pass


@cli.command()
@click.argument("source", type=click.Choice(["csv", "stripe", "postgres"]))
@click.argument("target", required=False)
@click.option("--api-key", help="Stripe API key (for stripe source)")
@click.option("--host", default="localhost", help="Database host (for postgres)")
@click.option("--port", default=5432, help="Database port (for postgres)")
@click.option("--database", help="Database name (for postgres)")
@click.option("--user", help="Database user (for postgres)")
@click.option("--password", help="Database password (for postgres)")
@click.option("--model", default=DEFAULT_MODEL, help="LLM model to use (any litellm-compatible model)")
@click.option("--output", "-o", type=click.Choice(["rich", "json"]), default="rich", help="Output format")
def analyze(
    source: str,
    target: str | None,
    api_key: str | None,
    host: str,
    port: int,
    database: str | None,
    user: str | None,
    password: str | None,
    model: str,
    output: str,
):
    """Analyze revenue data from a source.

    \b
    Examples:
      vesh analyze csv customers.csv
      vesh analyze stripe --api-key sk_live_...
      vesh analyze postgres --host db.example.com --database myapp --user admin --password secret
    """
    if output == "rich":
        print_banner()

    try:
        asyncio.run(_run_analysis(source, target, api_key, host, port, database, user, password, model, output))
    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


async def _run_analysis(
    source: str,
    target: str | None,
    api_key: str | None,
    host: str,
    port: int,
    database: str | None,
    user: str | None,
    password: str | None,
    model: str,
    output: str,
):
    """Run the full analysis pipeline."""
    from datetime import date

    from vesh_agents.connectors.csv import CsvConnector
    from vesh_agents.metrics.computation import MetricComputationEngine
    from vesh_agents.metrics.ontology import CORE_METRICS
    from vesh_agents.resolution.blocking import BlockingEngine
    from vesh_agents.resolution.clustering import ClusteringEngine
    from vesh_agents.resolution.scoring import ScoringEngine

    is_rich = output == "rich"

    # Step 1: Extract
    if is_rich:
        print_agent_start("DataConnector", f"Extracting from {source}...")

    records = []
    if source == "csv":
        if not target:
            console.print("[red]Error: CSV file path required. Usage: vesh analyze csv <file.csv>[/red]")
            sys.exit(1)
        connector = CsvConnector(connection_id="cli", config={"file_path": target})
        records = await connector.extract_full()
    elif source == "stripe":
        if not api_key:
            console.print("[red]Error: --api-key required for Stripe. Usage: vesh analyze stripe --api-key sk_...[/red]")
            sys.exit(1)
        from vesh_agents.connectors.stripe import StripeConnector

        connector = StripeConnector(connection_id="cli", config={}, credentials={"api_key": api_key})
        records = await connector.extract_full()
    elif source == "postgres":
        if not all([database, user, password]):
            console.print("[red]Error: --database, --user, --password required for Postgres[/red]")
            sys.exit(1)
        from vesh_agents.connectors.postgres import PostgresConnector

        connector = PostgresConnector(
            connection_id="cli",
            config={"host": host, "port": port, "database": database},
            credentials={"user": user, "password": password},
        )
        records = await connector.extract_full()

    if is_rich:
        print_agent_complete("DataConnector", f"{len(records)} records extracted")
    if not records:
        console.print("[yellow]No records found. Check your data source.[/yellow]")
        return

    # Step 2: Entity resolution (single-source just passes through)
    if is_rich:
        print_agent_start("EntityResolver", "Resolving entities...")

    entity_data = []
    sources: dict[str, list[dict]] = {}
    records_by_id: dict[str, dict] = {}
    for r in records:
        rec_dict = r.to_dict()
        src = rec_dict.get("source_type", "unknown")
        sources.setdefault(src, []).append(rec_dict)
        records_by_id[f"{src}:{rec_dict.get('record_id', '')}"] = rec_dict

    if len(sources) >= 2:
        blocking = BlockingEngine()
        scoring = ScoringEngine()
        clustering = ClusteringEngine()
        source_list = list(sources.keys())
        all_candidates = []
        for i in range(len(source_list)):
            for j in range(i + 1, len(source_list)):
                all_candidates.extend(
                    blocking.generate_candidates(sources[source_list[i]], source_list[i], sources[source_list[j]], source_list[j])
                )
        scored = scoring.score_candidates(all_candidates, records_by_id)
        clusters = clustering.cluster(scored)
        from vesh_agents.resolution.canonical import compute_canonical_record

        for cluster in clusters:
            entity_data.append(compute_canonical_record(cluster, records_by_id))
    else:
        entity_data = [r.data for r in records]

    if is_rich:
        print_agent_complete("EntityResolver", f"{len(entity_data)} entities resolved")

    # Step 3: Compute metrics
    if is_rich:
        print_agent_start("MetricComputer", "Computing SaaS metrics...")

    engine = MetricComputationEngine()
    computed = engine.compute_all(tenant_id="cli", period_date=date.today(), entity_data=entity_data)

    metrics_output = []
    for m in computed:
        mdef = CORE_METRICS.get(m.metric_id)
        metrics_output.append(
            {
                "metric_id": m.metric_id,
                "name": mdef.name if mdef else m.metric_id,
                "value": m.value,
                "unit": mdef.unit.value if mdef else "unknown",
                "direction": mdef.direction.value if mdef else "neutral",
                "change_absolute": m.change_absolute,
                "change_percent": m.change_percent,
            }
        )

    if is_rich:
        print_agent_complete("MetricComputer", f"{len(computed)} metrics computed")
        console.print()
        print_metrics_table(metrics_output)

    # Step 4: Detect anomalies
    if is_rich:
        print_agent_start("AnomalyDetector", "Scanning for anomalies...")

    all_anomalies = []
    for m in metrics_output:
        if m.get("change_percent") is not None and abs(m["change_percent"]) > 15:
            all_anomalies.append(
                {
                    "metric_id": m["metric_id"],
                    "metric_name": m["name"],
                    "severity": min(1.0, abs(m["change_percent"]) / 50),
                    "direction": "increase" if m["change_percent"] > 0 else "decrease",
                    "change_percent": m["change_percent"],
                }
            )

    if is_rich:
        print_agent_complete("AnomalyDetector", f"{len(all_anomalies)} anomalies found")
        console.print()
        print_anomalies(all_anomalies)

    # JSON output mode
    if output == "json":
        from vesh_agents.output.json_out import write_json

        write_json(
            {
                "source": source,
                "records_extracted": len(records),
                "entities_resolved": len(entity_data),
                "metrics": metrics_output,
                "anomalies": all_anomalies,
            }
        )

    if is_rich:
        console.print()
        print_result(
            f"Analyzed {len(records)} records → {len(entity_data)} entities → "
            f"{len(computed)} metrics → {len(all_anomalies)} anomalies"
        )


@cli.command()
@click.argument("question")
@click.option("--source", help="Data source (csv:<path>, stripe:<key>, postgres:<dsn>)")
@click.option("--model", default=DEFAULT_MODEL, help="LLM model to use")
def run(question: str, source: str | None, model: str):
    """Run an agentic analysis using natural language.

    \b
    Examples:
      vesh run "Why did churn spike last week?" --source csv:revenue.csv
      vesh run "Analyze our MRR trends" --source stripe:sk_live_...
    """
    print_banner()
    console.print(f"[bold]Question:[/bold] {question}\n")

    try:
        from agents import Runner

        from vesh_agents.agents.orchestrator import create_orchestrator

        orchestrator = create_orchestrator(model=model)
        prompt = question
        if source:
            prompt += f"\n\nData source: {source}"

        result = asyncio.run(Runner.run(orchestrator, prompt))
        console.print()
        print_result(result.final_output)
    except ImportError:
        console.print("[red]Error: OpenAI Agents SDK required. Install with: pip install openai-agents[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument("api_key")
def login(api_key: str):
    """Authenticate with Vesh AI cloud for premium features.

    \b
    Example:
      vesh login vesh_ak_...
    """
    from vesh_agents.core.metering import set_api_key

    set_api_key(api_key)
    console.print("[green]✓[/green] API key saved to ~/.vesh/config")
    console.print("  You now have access to Vesh AI cloud features.")


@cli.command()
@click.option("--model", default=None, help="LLM model override (e.g. anthropic/claude-sonnet)")
@click.option("--agent", default="analyst", help="OpenCode agent to use (analyst, explorer)")
def chat(model: str | None, agent: str):
    """Open an interactive AI chat for revenue analysis (powered by OpenCode).

    \b
    Examples:
      vesh chat
      vesh chat --model anthropic/claude-sonnet-4-20250514
      vesh chat --agent explorer
    """
    from vesh_agents.cli.opencode import find_opencode, launch_chat

    if not find_opencode():
        console.print("[yellow]OpenCode not found. Run 'vesh setup' to install and configure it.[/yellow]")
        sys.exit(1)
    launch_chat(model=model, agent=agent)


@cli.command()
@click.option("--project-dir", default=None, type=click.Path(exists=True), help="Project directory (default: cwd)")
def setup(project_dir: str | None):
    """Install OpenCode and configure Vesh AI agents + MCP server.

    \b
    Creates:
      opencode.json        — MCP server config pointing to 'vesh mcp serve'
      .opencode/agents/    — AI agent definitions for revenue analysis
    """
    from pathlib import Path

    from rich.panel import Panel

    from vesh_agents.cli.opencode import setup as run_setup

    print_banner()
    console.print("[bold]Setting up Vesh AI + OpenCode integration...[/bold]\n")

    target = Path(project_dir) if project_dir else None
    result = run_setup(target)

    if result["opencode_installed"]:
        console.print(f"[green]✓[/green] OpenCode found: {result.get('opencode_path', 'installed')}")
    else:
        console.print(f"[yellow]⚠[/yellow] OpenCode not installed. {result.get('install_hint', '')}")

    if result["config_written"]:
        console.print(f"[green]✓[/green] Config written: {result['config_path']}")

    for agent_path in result.get("agents_created", []):
        console.print(f"[green]✓[/green] Agent created: {agent_path}")

    console.print()
    console.print(
        Panel(
            "[bold]Next steps:[/bold]\n"
            "  1. [cyan]vesh chat[/cyan]        — open interactive AI analysis\n"
            "  2. [cyan]vesh analyze csv data.csv[/cyan] — quick offline analysis\n"
            "  3. [cyan]vesh mcp serve[/cyan]   — start MCP server for external clients",
            title="Ready",
            border_style="green",
        )
    )


@cli.group()
def mcp():
    """Manage MCP server for external tool integration."""
    pass


@mcp.command()
def serve():
    """Start the Vesh AI MCP server (stdio transport).

    \b
    Used by OpenCode, Cursor, Claude Desktop, or any MCP-compatible client.
    Automatically started by 'vesh chat' — run this for manual MCP client setups.
    """
    from vesh_agents.mcp.server import start_server

    start_server()


if __name__ == "__main__":
    cli()
