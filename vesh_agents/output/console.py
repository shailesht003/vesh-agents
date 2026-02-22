"""Rich terminal output for agent execution traces and results."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.tree import Tree

console = Console()


def print_banner() -> None:
    banner = Text()
    banner.append("  VESH AI  ", style="bold white on blue")
    banner.append("  Agentic Revenue Intelligence  ", style="dim")
    console.print()
    console.print(Panel(banner, border_style="blue", expand=False))
    console.print()


def print_agent_start(agent_name: str, description: str = "") -> None:
    console.print(f"  [bold cyan]▸[/bold cyan] [bold]{agent_name}[/bold]  {description}")


def print_agent_complete(agent_name: str, summary: str, duration_ms: float = 0) -> None:
    timing = f"  [dim]{duration_ms:.0f}ms[/dim]" if duration_ms else ""
    console.print(f"  [bold green]✓[/bold green] [bold]{agent_name}[/bold]  {summary}{timing}")


def print_agent_error(agent_name: str, error: str) -> None:
    console.print(f"  [bold red]✗[/bold red] [bold]{agent_name}[/bold]  {error}")


def print_metrics_table(metrics: list[dict]) -> None:
    table = Table(title="SaaS Metrics", border_style="blue", show_lines=True)
    table.add_column("Metric", style="bold")
    table.add_column("Value", justify="right")
    table.add_column("Change", justify="right")
    table.add_column("Direction", justify="center")

    for m in metrics:
        value = m.get("value", 0)
        unit = m.get("unit", "")
        if unit == "currency":
            val_str = f"${value:,.0f}"
        elif unit == "percent":
            val_str = f"{value:.1f}%"
        elif unit == "ratio":
            val_str = f"{value:.2f}"
        else:
            val_str = f"{value:,.0f}"

        change_pct = m.get("change_percent")
        if change_pct is not None:
            arrow = "↑" if change_pct > 0 else "↓" if change_pct < 0 else "→"
            change_str = f"{arrow} {abs(change_pct):.1f}%"
            change_style = "green" if (change_pct > 0) == (m.get("direction") == "up_good") else "red"
        else:
            change_str = "—"
            change_style = "dim"

        direction = m.get("direction", "")
        dir_icon = "📈" if direction == "up_good" else "📉" if direction == "down_good" else "➡️"

        table.add_row(m.get("name", m.get("metric_id", "")), val_str, f"[{change_style}]{change_str}[/]", dir_icon)

    console.print(table)


def print_anomalies(anomalies: list[dict]) -> None:
    if not anomalies:
        console.print("  [green]No anomalies detected.[/green] All metrics within normal ranges.")
        return

    console.print(f"\n  [bold yellow]⚠ {len(anomalies)} Anomalies Detected[/bold yellow]\n")
    for a in anomalies:
        severity = a.get("severity", 0)
        if severity > 0.7:
            icon, style = "🔴", "bold red"
        elif severity > 0.4:
            icon, style = "🟡", "bold yellow"
        else:
            icon, style = "🔵", "bold blue"

        name = a.get("metric_name", a.get("metric_id", "Unknown"))
        direction = a.get("direction", "changed")
        console.print(f"  {icon} [{style}]{name}[/] — {direction} (severity: {severity:.2f})")


def print_trace_tree(spans: list[dict]) -> None:
    tree = Tree("[bold blue]Vesh AI Pipeline[/bold blue]")
    for span in spans:
        name = span.get("agent_name", "Unknown")
        duration = span.get("duration_ms", 0)
        status = span.get("status", "done")
        icon = "✓" if status == "success" else "✗" if status == "error" else "▸"
        style = "green" if status == "success" else "red" if status == "error" else "cyan"
        label = f"[{style}]{icon}[/] {name}"
        if duration:
            label += f"  [dim]{duration:.0f}ms[/dim]"
        tool = span.get("tool_name")
        if tool:
            label += f"  [dim]→ {tool}[/dim]"
        tree.add(label)
    console.print(tree)


def print_result(text: str) -> None:
    console.print(Panel(text, title="[bold]Analysis Result[/bold]", border_style="green", padding=(1, 2)))
