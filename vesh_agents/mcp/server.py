"""MCP Server — expose Vesh AI pipeline as MCP tools.

Connect from OpenCode, Cursor, Claude Desktop, or any MCP-compatible client.
Start with: vesh mcp serve
"""

from __future__ import annotations

import json
import logging
from datetime import date

from mcp.server.fastmcp import FastMCP

from vesh_agents.connectors.csv import CsvConnector
from vesh_agents.metrics.computation import MetricComputationEngine
from vesh_agents.metrics.ontology import CORE_METRICS

logger = logging.getLogger(__name__)

mcp = FastMCP(
    "Vesh AI",
    instructions="Agentic revenue intelligence — extract, resolve, compute, detect, and explain SaaS metrics.",
)


@mcp.tool()
async def analyze_csv(file_path: str) -> str:
    """Full pipeline: import CSV, resolve entities, compute SaaS metrics, detect anomalies.

    Args:
        file_path: Path to a CSV file containing revenue/subscription data.
    """
    connector = CsvConnector(connection_id="mcp", config={"file_path": file_path})
    records = await connector.extract_full()
    entity_data = [r.data for r in records]

    engine = MetricComputationEngine()
    computed = engine.compute_all(tenant_id="mcp", period_date=date.today(), entity_data=entity_data)

    metrics = []
    for m in computed:
        mdef = CORE_METRICS.get(m.metric_id)
        metrics.append(
            {
                "metric_id": m.metric_id,
                "name": mdef.name if mdef else m.metric_id,
                "value": m.value,
                "unit": mdef.unit.value if mdef else "unknown",
                "change_percent": m.change_percent,
            }
        )

    anomalies = [
        {"metric": m["name"], "change": m["change_percent"]}
        for m in metrics
        if m.get("change_percent") is not None and abs(m["change_percent"]) > 15
    ]

    return json.dumps(
        {
            "records_extracted": len(records),
            "entities_resolved": len(entity_data),
            "metrics": metrics,
            "anomalies": anomalies,
        },
        default=str,
    )


@mcp.tool()
async def import_csv(file_path: str) -> str:
    """Import SaaS revenue data from a CSV file and return normalized records.

    Args:
        file_path: Path to the CSV file.
    """
    connector = CsvConnector(connection_id="mcp", config={"file_path": file_path})
    records = await connector.extract_full()
    return json.dumps(
        {
            "source": "csv",
            "file": file_path,
            "record_count": len(records),
            "records": [r.to_dict() for r in records[:500]],
        },
        default=str,
    )


@mcp.tool()
def compute_metrics(entities_json: str, period_date: str = "") -> str:
    """Compute SaaS metrics (MRR, churn, ARPU, NRR, Quick Ratio) from entity data.

    Args:
        entities_json: JSON array of entity records (from import_csv or resolve_entities).
        period_date: Optional date in YYYY-MM-DD format. Defaults to today.
    """
    data = json.loads(entities_json)
    entities = data if isinstance(data, list) else data.get("entities", data.get("records", []))
    if isinstance(entities, list) and entities and "data" in entities[0]:
        entities = [e["data"] for e in entities]

    pd = date.fromisoformat(period_date) if period_date else date.today()
    engine = MetricComputationEngine()
    computed = engine.compute_all(tenant_id="mcp", period_date=pd, entity_data=entities)

    metrics = []
    for m in computed:
        mdef = CORE_METRICS.get(m.metric_id)
        metrics.append(
            {
                "metric_id": m.metric_id,
                "name": mdef.name if mdef else m.metric_id,
                "value": m.value,
                "unit": mdef.unit.value if mdef else "unknown",
                "direction": mdef.direction.value if mdef else "neutral",
                "change_absolute": m.change_absolute,
                "change_percent": m.change_percent,
                "decomposition": m.decomposition,
            }
        )

    return json.dumps({"metrics": metrics, "metric_count": len(metrics), "period_date": pd.isoformat()}, default=str)


@mcp.tool()
def resolve_entities(records_json: str) -> str:
    """Match and deduplicate records across data sources using fuzzy matching.

    Uses email domain blocking, company name similarity, temporal proximity,
    and amount matching to resolve which records refer to the same entity.

    Args:
        records_json: JSON array of extracted records (from import_csv or extract tools).
    """
    from vesh_agents.resolution.blocking import BlockingEngine
    from vesh_agents.resolution.canonical import compute_canonical_record
    from vesh_agents.resolution.clustering import ClusteringEngine
    from vesh_agents.resolution.scoring import ScoringEngine

    data = json.loads(records_json)
    records = data if isinstance(data, list) else data.get("records", [])
    if not records:
        return json.dumps({"entities": [], "entity_count": 0})

    sources: dict[str, list[dict]] = {}
    records_by_id: dict[str, dict] = {}
    for rec in records:
        src = rec.get("source_type", "unknown")
        sources.setdefault(src, []).append(rec)
        records_by_id[f"{src}:{rec.get('record_id', '')}"] = rec

    if len(sources) < 2:
        entities = [rec.get("data", rec) for rec in records]
        return json.dumps({"entities": entities, "entity_count": len(entities), "source_count": 1}, default=str)

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

    entities = []
    matched: set[str] = set()
    for cluster in clusters:
        entities.append(compute_canonical_record(cluster, records_by_id))
        for src, rid in cluster.members:
            matched.add(f"{src}:{rid}")

    for key, rec in records_by_id.items():
        if key not in matched:
            entities.append(rec.get("data", rec))

    return json.dumps({"entities": entities, "entity_count": len(entities), "clusters_found": len(clusters)}, default=str)


@mcp.tool()
def detect_anomalies(metrics_json: str) -> str:
    """Detect statistical anomalies in SaaS metrics using z-score and rate-of-change methods.

    Args:
        metrics_json: JSON of computed metrics (from compute_metrics tool).
    """
    from vesh_agents.detection.statistical import AnomalyDetectionPipeline

    data = json.loads(metrics_json)
    metrics = data if isinstance(data, list) else data.get("metrics", [])
    pipeline = AnomalyDetectionPipeline()
    all_anomalies = []

    for metric in metrics:
        metric_id = metric.get("metric_id", "unknown")
        value = metric.get("value", 0)
        historical = metric.get("historical_values", [])

        if historical:
            for a in pipeline.detect(metric_id, value, date.today(), historical):
                all_anomalies.append(
                    {
                        "metric_id": a.metric_id,
                        "metric_name": metric.get("name", a.metric_id),
                        "method": a.detection_method,
                        "severity": a.severity,
                        "actual": a.actual_value,
                        "baseline": a.baseline_value,
                    }
                )
        elif metric.get("change_percent") is not None and abs(metric["change_percent"]) > 15:
            all_anomalies.append(
                {
                    "metric_id": metric_id,
                    "metric_name": metric.get("name", metric_id),
                    "method": "change_threshold",
                    "severity": min(1.0, abs(metric["change_percent"]) / 50),
                    "change_percent": metric["change_percent"],
                }
            )

    return json.dumps({"anomalies": all_anomalies, "anomaly_count": len(all_anomalies)}, default=str)


@mcp.tool()
def list_metrics() -> str:
    """List all available SaaS metric definitions."""
    return json.dumps(
        {
            "metrics": [
                {"id": mid, "name": m.name, "description": m.description, "category": m.category.value, "unit": m.unit.value}
                for mid, m in CORE_METRICS.items()
            ]
        }
    )


def start_server():
    """Start the MCP server in stdio mode."""
    logger.info("Starting Vesh AI MCP server (stdio)")
    mcp.run(transport="stdio")
