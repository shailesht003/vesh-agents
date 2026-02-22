"""Statistical anomaly detection — z-score and rate-of-change methods."""

import logging
from dataclasses import dataclass
from datetime import date

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class DetectedAnomaly:
    """A detected anomaly on a metric."""

    metric_id: str
    period_date: date
    detection_method: str
    severity: float
    deviation: float
    baseline_value: float
    actual_value: float
    context: dict


class StatisticalDetector:
    """Detect anomalies using statistical methods on metric time series."""

    def __init__(self, baseline_window: int = 30, z_threshold: float = 2.5):
        self.baseline_window = baseline_window
        self.z_threshold = z_threshold

    def detect_zscore(self, metric_id: str, current_value: float, current_date: date,
                      historical_values: list[float]) -> DetectedAnomaly | None:
        if len(historical_values) < 7:
            return None
        baseline = historical_values[-self.baseline_window:]
        mean = np.mean(baseline)
        std = np.std(baseline)
        if std == 0:
            return None
        z_score = (current_value - mean) / std
        if abs(z_score) >= self.z_threshold:
            return DetectedAnomaly(
                metric_id=metric_id, period_date=current_date, detection_method="z_score",
                severity=min(1.0, abs(z_score) / 5.0), deviation=float(z_score),
                baseline_value=float(mean), actual_value=current_value,
                context={"z_score": float(z_score), "mean": float(mean), "std": float(std),
                         "baseline_window": len(baseline), "direction": "above" if z_score > 0 else "below"},
            )
        return None

    def detect_rate_of_change(self, metric_id: str, current_value: float, previous_value: float,
                              current_date: date, historical_changes: list[float],
                              threshold_multiplier: float = 2.0) -> DetectedAnomaly | None:
        if previous_value == 0:
            return None
        current_change = (current_value - previous_value) / abs(previous_value)
        if len(historical_changes) < 7:
            if abs(current_change) > 0.15:
                return DetectedAnomaly(
                    metric_id=metric_id, period_date=current_date, detection_method="rate_of_change",
                    severity=min(1.0, abs(current_change) / 0.5), deviation=current_change,
                    baseline_value=previous_value, actual_value=current_value,
                    context={"change_rate": current_change, "method": "simple_threshold"},
                )
            return None
        mean_change = np.mean(historical_changes)
        std_change = np.std(historical_changes)
        if std_change == 0:
            return None
        z_change = (current_change - mean_change) / std_change
        if abs(z_change) >= threshold_multiplier:
            return DetectedAnomaly(
                metric_id=metric_id, period_date=current_date, detection_method="rate_of_change",
                severity=min(1.0, abs(z_change) / 4.0), deviation=float(z_change),
                baseline_value=previous_value, actual_value=current_value,
                context={"change_rate": current_change, "z_change": float(z_change),
                         "mean_change": float(mean_change), "std_change": float(std_change)},
            )
        return None


class AnomalyDetectionPipeline:
    """Run all detection methods and aggregate results."""

    def __init__(self):
        self.detector = StatisticalDetector()

    def detect(self, metric_id: str, current_value: float, current_date: date,
               historical_values: list[float]) -> list[DetectedAnomaly]:
        anomalies: list[DetectedAnomaly] = []
        z_anomaly = self.detector.detect_zscore(metric_id, current_value, current_date, historical_values)
        if z_anomaly:
            anomalies.append(z_anomaly)
        if len(historical_values) >= 2:
            previous = historical_values[-1]
            changes = []
            for i in range(1, len(historical_values)):
                if historical_values[i - 1] != 0:
                    changes.append((historical_values[i] - historical_values[i - 1]) / abs(historical_values[i - 1]))
            roc_anomaly = self.detector.detect_rate_of_change(metric_id, current_value, previous, current_date, changes)
            if roc_anomaly:
                anomalies.append(roc_anomaly)
        return anomalies
