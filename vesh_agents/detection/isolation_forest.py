"""Isolation Forest anomaly detection method."""

import logging
from datetime import date

import numpy as np

from vesh_agents.detection.statistical import DetectedAnomaly

logger = logging.getLogger(__name__)

try:
    from sklearn.ensemble import IsolationForest
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False


class IsolationForestDetector:
    """Detect anomalies using scikit-learn's Isolation Forest."""

    def __init__(self, contamination: float = 0.05, random_state: int = 42):
        if not HAS_SKLEARN:
            raise ImportError(
                "scikit-learn is required for IsolationForestDetector. "
                "Install it with `pip install vesh-agents[ml]` or `pip install scikit-learn`."
            )
        self.contamination = contamination
        self.random_state = random_state

    def detect(
        self, metric_id: str, current_value: float, current_date: date, historical_values: list[float]
    ) -> DetectedAnomaly | None:
        """Detect anomaly in a single 1D metric."""
        if len(historical_values) < 7:
            return None

        # Prepare 1D data for Isolation Forest
        X_combined = np.array(historical_values + [current_value]).reshape(-1, 1)

        model = IsolationForest(
            contamination=self.contamination, random_state=self.random_state
        )
        # Predict returns 1 for inliers, -1 for outliers
        predictions = model.fit_predict(X_combined)
        
        if predictions[-1] == -1:
            mean_baseline = float(np.mean(historical_values))
            
            # Avoid false positives if the actual deviation is tiny
            if abs(current_value - mean_baseline) < 1.0:
                mean_hist = np.mean(historical_values)
                std_hist = np.std(historical_values)
                if std_hist > 0 and abs(current_value - mean_hist) < 2 * std_hist:
                    return None
                    
            # Calculate anomaly score (negative means anomaly)
            scores = model.score_samples(X_combined)[-1]
            
            mean_baseline = float(np.mean(historical_values))
            
            return DetectedAnomaly(
                metric_id=metric_id,
                period_date=current_date,
                detection_method="isolation_forest",
                # Severity mapped from score. Scores max magnitude around -1.0
                severity=min(1.0, abs(scores) * 2),  # Heuristic scaling
                deviation=current_value - mean_baseline,
                baseline_value=mean_baseline,
                actual_value=current_value,
                context={
                    "isolation_forest_score": float(scores),
                    "model_contamination": self.contamination,
                },
            )
        
        return None

    def detect_multivariate(
        self,
        metrics: list[dict],
        current_date: date,
    ) -> list[DetectedAnomaly]:
        """Detect simultaneous multivariate anomalies across multiple metrics."""
        from collections import defaultdict
        
        valid_metrics = []
        for m in metrics:
            hist = m.get("historical_values", [])
            val = m.get("value")
            if len(hist) >= 7 and val is not None:
                valid_metrics.append(m)
                
        groups = defaultdict(list)
        for m in valid_metrics:
            groups[len(m["historical_values"])].append(m)
            
        anomalies = []
        
        for length, group in groups.items():
            if len(group) < 2:
                continue
                
            hist_matrix = np.column_stack([m["historical_values"] for m in group])
            curr_vector = np.array([[m["value"] for m in group]])
            
            X_combined = np.vstack([hist_matrix, curr_vector])
            
            model = IsolationForest(
                contamination=self.contamination, random_state=self.random_state
            )
            predictions = model.fit_predict(X_combined)
            
            if predictions[-1] == -1:
                scores = model.score_samples(X_combined)
                curr_score = scores[-1]
                
                metric_ids = [m.get("metric_id", "unknown") for m in group]
                anomaly_id = "multivariate_" + "_".join(metric_ids[:3]) + ("_etc" if len(metric_ids) > 3 else "")
                
                anomalies.append(
                    DetectedAnomaly(
                        metric_id=anomaly_id,
                        period_date=current_date,
                        detection_method="isolation_forest_multivariate",
                        severity=min(1.0, abs(curr_score) * 2),
                        deviation=0.0,
                        baseline_value=0.0,
                        actual_value=0.0,
                        context={
                            "isolation_forest_score": float(curr_score),
                            "involved_metrics": metric_ids,
                            "current_values": {m.get("metric_id", "unknown"): m["value"] for m in group}
                        },
                    )
                )
        return anomalies
