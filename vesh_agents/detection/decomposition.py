"""Decomposition anomaly detection — detect anomalies within metric components."""

import logging
from datetime import date

from vesh_agents.detection.statistical import AnomalyDetectionPipeline, DetectedAnomaly
from vesh_agents.metrics.ontology import get_decomposition_children

logger = logging.getLogger(__name__)


class DecompositionDetector:
    """Detect anomalies by examining metric component contributions."""

    def __init__(self):
        self.pipeline = AnomalyDetectionPipeline()

    def detect_component_anomalies(
        self,
        parent_metric_id: str,
        current_decomposition: dict[str, float],
        historical_decompositions: list[dict[str, float]],
        current_date: date,
    ) -> list[DetectedAnomaly]:
        children = get_decomposition_children(parent_metric_id)
        anomalies: list[DetectedAnomaly] = []

        for child_id in children:
            current_val = current_decomposition.get(child_id, 0.0)
            historical_vals = [d.get(child_id, 0.0) for d in historical_decompositions]
            if not historical_vals:
                continue
            child_anomalies = self.pipeline.detect(child_id, current_val, current_date, historical_vals)
            for a in child_anomalies:
                a.context["parent_metric"] = parent_metric_id
                a.context["component"] = child_id
                anomalies.append(a)
        return anomalies
