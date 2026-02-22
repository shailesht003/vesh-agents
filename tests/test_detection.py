"""Tests for statistical anomaly detection."""

from datetime import date

from vesh_agents.detection.statistical import (
    AnomalyDetectionPipeline,
    DetectedAnomaly,
    StatisticalDetector,
)


class TestStatisticalDetector:
    def setup_method(self):
        self.detector = StatisticalDetector(baseline_window=30, z_threshold=2.5)

    def test_no_anomaly_for_normal_value(self):
        historical = [100.0] * 30
        result = self.detector.detect_zscore("mrr", 101.0, date(2025, 1, 15), historical)
        assert result is None

    def test_detects_spike(self):
        historical = [100.0 + (i % 5) for i in range(30)]
        result = self.detector.detect_zscore("mrr", 200.0, date(2025, 1, 15), historical)
        assert result is not None
        assert isinstance(result, DetectedAnomaly)
        assert result.metric_id == "mrr"
        assert result.context["direction"] == "above"

    def test_detects_drop(self):
        historical = [100.0 + (i % 5) for i in range(30)]
        result = self.detector.detect_zscore("mrr", 1.0, date(2025, 1, 15), historical)
        assert result is not None
        assert result.context["direction"] == "below"

    def test_skips_insufficient_data(self):
        historical = [100.0] * 5
        result = self.detector.detect_zscore("mrr", 200.0, date(2025, 1, 15), historical)
        assert result is None

    def test_skips_zero_std(self):
        historical = [100.0] * 30
        result = self.detector.detect_zscore("mrr", 100.0, date(2025, 1, 15), historical)
        assert result is None

    def test_severity_bounded(self):
        historical = [100.0 + (i % 5) for i in range(30)]
        result = self.detector.detect_zscore("mrr", 99999.0, date(2025, 1, 15), historical)
        assert result is not None
        assert 0.0 <= result.severity <= 1.0

    def test_rate_of_change_large_jump(self):
        result = self.detector.detect_rate_of_change("mrr", 200.0, 100.0, date(2025, 1, 15), historical_changes=[])
        assert result is not None
        assert result.detection_method == "rate_of_change"

    def test_rate_of_change_small_change(self):
        result = self.detector.detect_rate_of_change("mrr", 101.0, 100.0, date(2025, 1, 15), historical_changes=[])
        assert result is None

    def test_rate_of_change_skips_zero_previous(self):
        result = self.detector.detect_rate_of_change("mrr", 100.0, 0.0, date(2025, 1, 15), historical_changes=[])
        assert result is None


class TestAnomalyDetectionPipeline:
    def test_pipeline_returns_list(self):
        pipeline = AnomalyDetectionPipeline()
        historical = [100.0] * 30
        anomalies = pipeline.detect("mrr", 100.0, date(2025, 1, 15), historical)
        assert isinstance(anomalies, list)

    def test_pipeline_detects_obvious_anomaly(self):
        pipeline = AnomalyDetectionPipeline()
        historical = [100.0 + (i % 5) for i in range(30)]
        anomalies = pipeline.detect("mrr", 500.0, date(2025, 1, 15), historical)
        assert len(anomalies) >= 1
        methods = {a.detection_method for a in anomalies}
        assert "z_score" in methods

    def test_pipeline_empty_history(self):
        pipeline = AnomalyDetectionPipeline()
        anomalies = pipeline.detect("mrr", 100.0, date(2025, 1, 15), [])
        assert anomalies == []

    def test_pipeline_short_history(self):
        pipeline = AnomalyDetectionPipeline()
        anomalies = pipeline.detect("mrr", 100.0, date(2025, 1, 15), [90.0, 95.0])
        assert isinstance(anomalies, list)
