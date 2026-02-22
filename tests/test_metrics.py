"""Tests for metric computation and ontology."""

from datetime import date

from vesh_agents.metrics.computation import MetricComputationEngine
from vesh_agents.metrics.ontology import CORE_METRICS, get_decomposition_children
from vesh_agents.metrics.validation import MetricValidator


def test_core_metrics_defined():
    """All 10 core SaaS metrics should be defined."""
    assert len(CORE_METRICS) == 10
    assert "mrr" in CORE_METRICS
    assert "nrr" in CORE_METRICS
    assert "arpu" in CORE_METRICS
    assert "quick_ratio" in CORE_METRICS


def test_mrr_decomposition():
    """MRR should decompose into 4 components."""
    children = get_decomposition_children("mrr")
    assert set(children) == {"new_mrr", "expansion_mrr", "contraction_mrr", "churn_mrr"}


def test_compute_metrics():
    """MetricComputationEngine should compute metrics from entity data."""
    entities = [
        {"status": "active", "mrr_amount": 1000, "customer_entity_id": "c1"},
        {"status": "active", "mrr_amount": 2000, "customer_entity_id": "c2"},
        {"status": "canceled", "mrr_amount": 500, "customer_entity_id": "c3"},
    ]
    engine = MetricComputationEngine()
    computed = engine.compute_all("test", date.today(), entities)
    assert len(computed) > 0

    values = {m.metric_id: m.value for m in computed}
    assert values["mrr"] == 3000.0
    assert values["active_customers"] == 2


def test_validation():
    """MetricValidator should validate computed metrics."""
    engine = MetricComputationEngine()
    computed = engine.compute_all("test", date.today(), [
        {"status": "active", "mrr_amount": 5000, "customer_entity_id": "c1"},
    ])
    validator = MetricValidator()
    results = validator.validate_all(computed)
    assert len(results) > 0
    assert all(hasattr(r, "passed") for r in results)
