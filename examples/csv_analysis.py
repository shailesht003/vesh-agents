"""Vesh Agents — CSV Analysis Example

Full pipeline: extract CSV -> resolve entities -> compute metrics -> detect anomalies.
Uses the direct API (no LLM required).
"""

import asyncio
from datetime import date

from vesh_agents.connectors.csv import CsvConnector
from vesh_agents.metrics.computation import MetricComputationEngine
from vesh_agents.metrics.ontology import CORE_METRICS
from vesh_agents.output.console import (
    print_agent_complete,
    print_agent_start,
    print_anomalies,
    print_banner,
    print_metrics_table,
    print_result,
)


async def main():
    print_banner()

    # Step 1: Extract from CSV
    print_agent_start("DataConnector", "Loading sample_data.csv...")
    connector = CsvConnector(connection_id="demo", config={"file_path": "examples/sample_data.csv"})
    records = await connector.extract_full()
    print_agent_complete("DataConnector", f"{len(records)} records loaded")

    # Step 2: Use records directly as entities (single source)
    print_agent_start("EntityResolver", "Single source — pass-through")
    entities = [r.data for r in records]
    print_agent_complete("EntityResolver", f"{len(entities)} entities")

    # Step 3: Compute metrics
    print_agent_start("MetricComputer", "Computing SaaS metrics...")
    engine = MetricComputationEngine()
    computed = engine.compute_all(tenant_id="demo", period_date=date.today(), entity_data=entities)
    print_agent_complete("MetricComputer", f"{len(computed)} metrics computed")

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

    print()
    print_metrics_table(metrics_output)

    # Step 4: Detect anomalies
    print_agent_start("AnomalyDetector", "Scanning for anomalies...")
    anomalies = []
    for m in metrics_output:
        if m.get("change_percent") and abs(m["change_percent"]) > 15:
            anomalies.append(
                {
                    "metric_id": m["metric_id"],
                    "metric_name": m["name"],
                    "severity": min(1.0, abs(m["change_percent"]) / 50),
                    "direction": "increase" if m["change_percent"] > 0 else "decrease",
                }
            )
    print_agent_complete("AnomalyDetector", f"{len(anomalies)} anomalies")
    print()
    print_anomalies(anomalies)

    print()
    print_result(
        f"Pipeline complete: {len(records)} records -> {len(entities)} entities -> "
        f"{len(computed)} metrics -> {len(anomalies)} anomalies"
    )


if __name__ == "__main__":
    asyncio.run(main())
