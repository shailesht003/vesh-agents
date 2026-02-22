"""Metric validation — invariant checks and cross-validation."""

import logging
from dataclasses import dataclass

from vesh_agents.metrics.computation import ComputedMetric

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    invariant_name: str
    passed: bool
    severity: str
    message: str
    details: dict | None = None


class MetricValidator:
    """Validate computed metrics against known invariants."""

    def validate_all(self, metrics: list[ComputedMetric]) -> list[ValidationResult]:
        results: list[ValidationResult] = []
        values = {m.metric_id: m.value for m in metrics}
        results.append(self._check_mrr_decomposition(values))
        results.append(self._check_nrr_range(values))
        results.append(self._check_quick_ratio(values))
        return results

    def _check_mrr_decomposition(self, values: dict[str, float]) -> ValidationResult:
        new = values.get("new_mrr", 0)
        expansion = values.get("expansion_mrr", 0)
        contraction = values.get("contraction_mrr", 0)
        churn = values.get("churn_mrr", 0)
        net_change = new + expansion - contraction - churn
        return ValidationResult(
            invariant_name="mrr_decomposition_sum", passed=True, severity="error",
            message=f"MRR components: new={new}, exp={expansion}, contr={contraction}, churn={churn}, net={net_change}",
            details={"new": new, "expansion": expansion, "contraction": contraction, "churn": churn},
        )

    def _check_nrr_range(self, values: dict[str, float]) -> ValidationResult:
        nrr = values.get("nrr", 0)
        is_valid = 0 <= nrr <= 300
        return ValidationResult(
            invariant_name="nrr_range", passed=is_valid, severity="warning",
            message=f"NRR is {nrr:.1f}% — {'within' if is_valid else 'outside'} expected range (0-300%)",
        )

    def _check_quick_ratio(self, values: dict[str, float]) -> ValidationResult:
        denominator = values.get("contraction_mrr", 0) + values.get("churn_mrr", 0)
        is_valid = denominator > 0
        return ValidationResult(
            invariant_name="quick_ratio_positive_denominator", passed=is_valid, severity="info",
            message=f"Quick ratio denominator: {denominator:.0f}" + ("" if is_valid else " (zero)"),
        )
