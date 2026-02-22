"""Metric computation tools — @function_tool wrappers for SaaS metrics."""

from __future__ import annotations

import json
from datetime import date

from agents import function_tool

from vesh_agents.metrics.computation import MetricComputationEngine
from vesh_agents.metrics.ontology import CORE_METRICS
from vesh_agents.metrics.validation import MetricValidator


@function_tool
def compute_saas_metrics(entities_json: str, period_date: str = "") -> str:
    """Compute SaaS metrics (MRR, churn, ARPU, etc.) from resolved entity data.

    Args:
        entities_json: JSON string of resolved entities (from resolve_entities tool).
        period_date: Date to compute metrics for (YYYY-MM-DD). Defaults to today.
    """
    data = json.loads(entities_json)
    entities = data if isinstance(data, list) else data.get("entities", [])

    if period_date:
        pd = date.fromisoformat(period_date)
    else:
        pd = date.today()

    engine = MetricComputationEngine()
    computed = engine.compute_all(tenant_id="cli", period_date=pd, entity_data=entities)

    validator = MetricValidator()
    validations = validator.validate_all(computed)

    metrics_output = []
    for m in computed:
        metric_def = CORE_METRICS.get(m.metric_id)
        metrics_output.append({
            "metric_id": m.metric_id,
            "name": metric_def.name if metric_def else m.metric_id,
            "value": m.value,
            "unit": metric_def.unit.value if metric_def else "unknown",
            "direction": metric_def.direction.value if metric_def else "neutral",
            "change_absolute": m.change_absolute,
            "change_percent": m.change_percent,
            "decomposition": m.decomposition,
        })

    return json.dumps({
        "metrics": metrics_output,
        "metric_count": len(metrics_output),
        "period_date": pd.isoformat(),
        "entity_count": len(entities),
        "validations": [{"name": v.invariant_name, "passed": v.passed, "message": v.message} for v in validations],
    }, default=str)


@function_tool
def list_available_metrics() -> str:
    """List all available SaaS metric definitions with their descriptions."""
    metrics = []
    for mid, mdef in CORE_METRICS.items():
        metrics.append({
            "metric_id": mid,
            "name": mdef.name,
            "description": mdef.description,
            "category": mdef.category.value,
            "unit": mdef.unit.value,
            "direction": mdef.direction.value,
        })
    return json.dumps({"metrics": metrics, "count": len(metrics)})
