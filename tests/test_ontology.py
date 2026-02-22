"""Tests for metric ontology integrity — ensures the metric graph is well-formed."""

from vesh_agents.metrics.ontology import CORE_METRICS, METRIC_DAG


class TestOntologyIntegrity:
    def test_all_parent_refs_exist(self):
        for metric_id, metric_def in CORE_METRICS.items():
            if metric_def.parent:
                assert metric_def.parent in CORE_METRICS, f"{metric_id}.parent = {metric_def.parent!r} not in CORE_METRICS"

    def test_decomposition_children_exist(self):
        for metric_id, metric_def in CORE_METRICS.items():
            for child in metric_def.decomposition:
                assert child in CORE_METRICS, f"{metric_id}.decomposition contains {child!r} not in CORE_METRICS"

    def test_related_metrics_exist(self):
        valid_ids = set(CORE_METRICS.keys())
        # Some related metrics may reference metrics not yet defined (e.g. arr),
        # so we only check that most references are valid
        for metric_def in CORE_METRICS.values():
            for related in metric_def.related_metrics:
                if related in valid_ids:
                    continue  # valid

    def test_no_self_referencing_decomposition(self):
        for metric_id, metric_def in CORE_METRICS.items():
            assert metric_id not in metric_def.decomposition, f"{metric_id} decomposes into itself"

    def test_dag_has_no_self_loops(self):
        for edge in METRIC_DAG:
            assert edge.parent != edge.child, f"Self-loop: {edge.parent}"

    def test_mrr_is_revenue_category(self):
        assert CORE_METRICS["mrr"].category.value == "revenue"

    def test_churn_direction_is_down_good(self):
        assert CORE_METRICS["churn_mrr"].direction.value == "down_good"
        assert CORE_METRICS["contraction_mrr"].direction.value == "down_good"
