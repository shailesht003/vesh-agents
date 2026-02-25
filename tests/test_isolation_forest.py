"""Tests for isolation forest anomaly detection."""

from datetime import date

import pytest

from vesh_agents.detection.isolation_forest import HAS_SKLEARN

if HAS_SKLEARN:
    from vesh_agents.detection.isolation_forest import IsolationForestDetector
from vesh_agents.detection.statistical import DetectedAnomaly

pytestmark = pytest.mark.skipif(not HAS_SKLEARN, reason="scikit-learn not installed")


class TestIsolationForestDetector:
    def setup_method(self):
        if HAS_SKLEARN:
            self.detector = IsolationForestDetector(contamination=0.1, random_state=42)

    def test_no_anomaly_for_normal_value(self):
        historical = [100.0 + (i % 2) for i in range(30)]
        result = self.detector.detect("mrr", 100.5, date(2025, 1, 15), historical)
        assert result is None

    def test_detects_spike(self):
        historical = [100.0 + (i % 5) for i in range(30)]
        result = self.detector.detect("mrr", 500.0, date(2025, 1, 15), historical)
        assert result is not None
        assert isinstance(result, DetectedAnomaly)
        assert result.metric_id == "mrr"
        assert result.detection_method == "isolation_forest"

    def test_detects_drop(self):
        historical = [100.0 + (i % 5) for i in range(30)]
        result = self.detector.detect("mrr", 10.0, date(2025, 1, 15), historical)
        assert result is not None
        assert result.detection_method == "isolation_forest"

    def test_skips_insufficient_data(self):
        historical = [100.0] * 5
        result = self.detector.detect("mrr", 200.0, date(2025, 1, 15), historical)
        assert result is None

    def test_detects_multivariate_anomaly(self):
        mrr_hist = [1000.0 + (i * 10) for i in range(30)]
        churn_hist = [5.0 + (i % 2) for i in range(30)]

        metrics = [
            {"metric_id": "mrr", "value": 1300.0, "historical_values": mrr_hist},
            {"metric_id": "churn", "value": 15.0, "historical_values": churn_hist},
        ]

        anomalies = self.detector.detect_multivariate(metrics, date(2025, 1, 15))
        assert anomalies
        assert len(anomalies) == 1
        assert anomalies[0].detection_method == "isolation_forest_multivariate"
        assert "mrr" in anomalies[0].context["involved_metrics"]
