"""Reasoning tools — BYOM, uses whatever model the user configured."""

from __future__ import annotations

import json

from agents import function_tool


@function_tool
def explain_anomaly(anomaly_json: str) -> str:
    """Generate a structured explanation template for detected anomalies.

    This provides the anomaly context in a format suitable for LLM reasoning.
    The LLM agent itself generates the causal explanation using its model.

    Args:
        anomaly_json: JSON string of detected anomalies (from detect_anomalies tool).
    """
    data = json.loads(anomaly_json)
    anomalies = data if isinstance(data, list) else data.get("anomalies", [])

    if not anomalies:
        return json.dumps({"explanation": "No anomalies detected. All metrics are within normal ranges.", "anomaly_count": 0})

    summaries = []
    for a in anomalies:
        severity_label = "Critical" if a.get("severity", 0) > 0.7 else "Warning" if a.get("severity", 0) > 0.4 else "Info"
        direction = a.get("direction", "changed")
        summaries.append({
            "metric": a.get("metric_name", a.get("metric_id", "unknown")),
            "severity": severity_label,
            "severity_score": a.get("severity", 0),
            "what_happened": f"{a.get('metric_name', 'Metric')} {direction} to {a.get('actual_value', 'N/A')}",
            "detection_method": a.get("detection_method", "unknown"),
            "deviation": a.get("deviation"),
            "baseline": a.get("baseline_value"),
            "actual": a.get("actual_value"),
            "change_percent": a.get("change_percent"),
        })

    summaries.sort(key=lambda x: x.get("severity_score", 0), reverse=True)

    return json.dumps({
        "anomaly_summaries": summaries,
        "anomaly_count": len(summaries),
        "most_severe": summaries[0] if summaries else None,
        "analysis_prompt": (
            "Based on these anomalies, provide a root cause analysis. "
            "Consider: (1) Which metrics are interconnected? (2) What business events "
            "could cause these patterns? (3) What actions should the team take?"
        ),
    }, default=str)
