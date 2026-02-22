"""Anomaly detection tools — @function_tool wrappers for statistical detection."""

from __future__ import annotations

import json
from datetime import date

from agents import function_tool

from vesh_agents.detection.statistical import AnomalyDetectionPipeline


@function_tool
def detect_anomalies(metrics_json: str) -> str:
    """Detect statistical anomalies in computed metrics.

    Looks for unusual values using z-score and rate-of-change methods.

    Args:
        metrics_json: JSON string of computed metrics (from compute_saas_metrics tool).
    """
    data = json.loads(metrics_json)
    metrics = data if isinstance(data, list) else data.get("metrics", [])

    pipeline = AnomalyDetectionPipeline()
    all_anomalies = []

    for metric in metrics:
        metric_id = metric.get("metric_id", "unknown")
        value = metric.get("value", 0)

        historical = metric.get("historical_values", [])
        if not historical and metric.get("change_percent") is not None:
            change_pct = abs(metric["change_percent"])
            if change_pct > 15:
                all_anomalies.append({
                    "metric_id": metric_id,
                    "metric_name": metric.get("name", metric_id),
                    "detection_method": "change_threshold",
                    "severity": min(1.0, change_pct / 50),
                    "actual_value": value,
                    "change_percent": metric["change_percent"],
                    "direction": "increase" if metric["change_percent"] > 0 else "decrease",
                })
            continue

        if historical:
            anomalies = pipeline.detect(metric_id, value, date.today(), historical)
            for a in anomalies:
                all_anomalies.append({
                    "metric_id": a.metric_id,
                    "metric_name": metric.get("name", a.metric_id),
                    "detection_method": a.detection_method,
                    "severity": a.severity,
                    "deviation": a.deviation,
                    "baseline_value": a.baseline_value,
                    "actual_value": a.actual_value,
                    "direction": a.context.get("direction", "unknown"),
                })

    return json.dumps({
        "anomalies": all_anomalies,
        "anomaly_count": len(all_anomalies),
        "metrics_analyzed": len(metrics),
    }, default=str)
