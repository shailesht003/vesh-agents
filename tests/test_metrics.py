"""Tests for the metric computation engine and ontology."""

from datetime import date

from vesh_agents.metrics.computation import ComputedMetric, MetricComputationEngine
from vesh_agents.metrics.ontology import (
    CORE_METRICS,
    METRIC_DAG,
    MetricCategory,
    MetricDirection,
    MetricUnit,
    get_decomposition_children,
    get_parents,
)

SAMPLE_ENTITIES = [
    {"customer_id": "c1", "status": "active", "mrr_amount": 500, "entity_id": "e1"},
    {"customer_id": "c2", "status": "active", "mrr_amount": 300, "entity_id": "e2"},
    {"customer_id": "c3", "status": "active", "mrr_amount": 200, "entity_id": "e3"},
    {"customer_id": "c4", "status": "canceled", "mrr_amount": 100, "canceled_in_period": True, "entity_id": "e4"},
]


class TestMetricOntology:
    def test_core_metrics_defined(self):
        assert len(CORE_METRICS) >= 10
        for metric_id, metric_def in CORE_METRICS.items():
            assert metric_def.metric_id == metric_id
            assert metric_def.name
            assert metric_def.description
            assert isinstance(metric_def.category, MetricCategory)
            assert isinstance(metric_def.unit, MetricUnit)
            assert isinstance(metric_def.direction, MetricDirection)

    def test_mrr_decomposition(self):
        children = get_decomposition_children("mrr")
        assert set(children) == {"new_mrr", "expansion_mrr", "contraction_mrr", "churn_mrr"}

    def test_non_decomposable_metric_has_no_children(self):
        assert get_decomposition_children("active_customers") == []

    def test_dag_edges_reference_valid_metrics(self):
        valid_ids = set(CORE_METRICS.keys())
        for edge in METRIC_DAG:
            assert edge.parent in valid_ids, f"DAG parent {edge.parent!r} not in CORE_METRICS"
            assert edge.child in valid_ids, f"DAG child {edge.child!r} not in CORE_METRICS"

    def test_get_parents(self):
        parents = get_parents("new_mrr")
        assert "mrr" in parents
        assert "quick_ratio" in parents

    def test_formula_metrics_have_formula_field(self):
        formula_metrics = [m for m in CORE_METRICS.values() if m.computation_template.get("type") == "formula"]
        for m in formula_metrics:
            assert "formula" in m.computation_template, f"{m.metric_id} missing formula"


class TestMetricComputationEngine:
    def setup_method(self):
        self.engine = MetricComputationEngine()

    def test_compute_all_returns_metrics(self):
        results = self.engine.compute_all("tenant-1", date(2025, 1, 15), SAMPLE_ENTITIES)
        assert len(results) > 0
        assert all(isinstance(m, ComputedMetric) for m in results)

    def test_mrr_sums_active_subscriptions(self):
        results = self.engine.compute_all("tenant-1", date(2025, 1, 15), SAMPLE_ENTITIES)
        mrr = next((m for m in results if m.metric_id == "mrr"), None)
        assert mrr is not None
        assert mrr.value == 1000.0  # 500 + 300 + 200 (active only)

    def test_active_customers_counts_distinct(self):
        results = self.engine.compute_all("tenant-1", date(2025, 1, 15), SAMPLE_ENTITIES)
        active = next((m for m in results if m.metric_id == "active_customers"), None)
        assert active is not None
        assert active.value == 3.0

    def test_arpu_formula(self):
        results = self.engine.compute_all("tenant-1", date(2025, 1, 15), SAMPLE_ENTITIES)
        arpu = next((m for m in results if m.metric_id == "arpu"), None)
        assert arpu is not None
        expected_arpu = 1000.0 / 3.0
        assert abs(arpu.value - expected_arpu) < 0.01

    def test_change_tracking_with_previous_snapshots(self):
        previous = {"mrr": 800.0}
        results = self.engine.compute_all("tenant-1", date(2025, 1, 15), SAMPLE_ENTITIES, previous)
        mrr = next(m for m in results if m.metric_id == "mrr")
        assert mrr.previous_value == 800.0
        assert mrr.change_absolute == 200.0
        assert abs(mrr.change_percent - 25.0) < 0.01

    def test_empty_entity_data(self):
        results = self.engine.compute_all("tenant-1", date(2025, 1, 15), [])
        assert len(results) > 0
        mrr = next(m for m in results if m.metric_id == "mrr")
        assert mrr.value == 0.0

    def test_computation_meta_included(self):
        results = self.engine.compute_all("tenant-1", date(2025, 1, 15), SAMPLE_ENTITIES)
        for m in results:
            assert m.computation_meta["tenant_id"] == "tenant-1"
            assert m.computation_meta["entity_count"] == len(SAMPLE_ENTITIES)

    def test_mrr_decomposition_populated(self):
        results = self.engine.compute_all("tenant-1", date(2025, 1, 15), SAMPLE_ENTITIES)
        mrr = next(m for m in results if m.metric_id == "mrr")
        assert mrr.decomposition is not None
        assert "new_mrr" in mrr.decomposition
        assert "expansion_mrr" in mrr.decomposition

    def test_formula_division_by_zero_returns_zero(self):
        results = self.engine.compute_all("tenant-1", date(2025, 1, 15), [])
        quick_ratio = next((m for m in results if m.metric_id == "quick_ratio"), None)
        assert quick_ratio is not None
        assert quick_ratio.value == 0.0
