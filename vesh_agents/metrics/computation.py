"""Metric computation engine — computes metric values from resolved entity data."""

import logging
from dataclasses import dataclass
from datetime import date

from vesh_agents.metrics.ontology import CORE_METRICS, MetricDef, get_decomposition_children

logger = logging.getLogger(__name__)


@dataclass
class ComputedMetric:
    """Result of computing a single metric."""

    metric_id: str
    period_date: date
    grain: str
    value: float
    previous_value: float | None
    change_absolute: float | None
    change_percent: float | None
    decomposition: dict | None
    computation_meta: dict


class MetricComputationEngine:
    """Compute all configured metrics for a tenant from resolved entity data."""

    def compute_all(
        self, tenant_id: str, period_date: date, entity_data: list[dict],
        previous_snapshots: dict[str, float] | None = None,
    ) -> list[ComputedMetric]:
        previous = previous_snapshots or {}
        results: dict[str, float] = {}

        for metric_id, metric_def in CORE_METRICS.items():
            if metric_def.computation_template.get("type") != "formula":
                results[metric_id] = self._compute_direct_metric(metric_def, entity_data, period_date)

        for metric_id, metric_def in CORE_METRICS.items():
            if metric_def.computation_template.get("type") == "formula":
                results[metric_id] = self._compute_formula_metric(metric_def, results)

        computed: list[ComputedMetric] = []
        for metric_id, value in results.items():
            prev = previous.get(metric_id)
            change_abs = (value - prev) if prev is not None else None
            change_pct = ((value - prev) / prev * 100) if prev is not None and prev != 0 else None
            decomposition = None
            children = get_decomposition_children(metric_id)
            if children:
                decomposition = {child: results.get(child, 0.0) for child in children}
            computed.append(
                ComputedMetric(
                    metric_id=metric_id, period_date=period_date, grain="daily", value=value,
                    previous_value=prev, change_absolute=change_abs, change_percent=change_pct,
                    decomposition=decomposition,
                    computation_meta={"tenant_id": tenant_id, "entity_count": len(entity_data), "computed_at": period_date.isoformat()},
                )
            )
        logger.info("Computed %d metrics for tenant %s on %s", len(computed), tenant_id, period_date)
        return computed

    def _compute_direct_metric(self, metric_def: MetricDef, entity_data: list[dict], period_date: date) -> float:
        template = metric_def.computation_template
        comp_type = template.get("type", "sum")
        field_name = template.get("field", "")
        filters = template.get("filter", {})
        filtered = [e for e in entity_data if self._matches_filter(e, filters, period_date)]

        if comp_type == "sum":
            return sum(self._get_numeric_field(e, field_name) for e in filtered)
        elif comp_type == "count_distinct":
            return len(set(e.get(field_name, e.get("entity_id", "")) for e in filtered))
        elif comp_type == "sum_positive_delta":
            return sum(max(0, self._get_numeric_field(e, "delta")) for e in filtered)
        elif comp_type == "sum_negative_delta":
            return abs(sum(min(0, self._get_numeric_field(e, "delta")) for e in filtered))
        return 0.0

    def _compute_formula_metric(self, metric_def: MetricDef, computed_values: dict[str, float]) -> float:
        formula = metric_def.computation_template.get("formula", "")
        try:
            ctx = {k: v for k, v in computed_values.items()}
            result = eval(formula, {"__builtins__": {}}, ctx)  # noqa: S307
            return float(result) if result is not None else 0.0
        except (ZeroDivisionError, TypeError, NameError):
            return 0.0

    @staticmethod
    def _matches_filter(entity: dict, filters: dict, period_date: date) -> bool:
        for key, expected in filters.items():
            actual = entity.get(key)
            if isinstance(expected, list):
                if actual not in expected:
                    return False
            elif isinstance(expected, bool) and expected:
                if not actual:
                    return False
            elif actual != expected:
                return False
        return True

    @staticmethod
    def _get_numeric_field(entity: dict, field_name: str) -> float:
        value = entity.get(field_name, 0)
        try:
            return float(value) if value is not None else 0.0
        except (ValueError, TypeError):
            return 0.0
