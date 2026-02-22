"""SaaS metric definitions, relationships, and the metric DAG."""

from dataclasses import dataclass, field
from enum import StrEnum


class MetricCategory(StrEnum):
    REVENUE = "revenue"
    RETENTION = "retention"
    GROWTH = "growth"
    EFFICIENCY = "efficiency"


class MetricUnit(StrEnum):
    CURRENCY = "currency"
    PERCENT = "percent"
    COUNT = "count"
    RATIO = "ratio"
    DAYS = "days"


class MetricDirection(StrEnum):
    UP_GOOD = "up_good"
    DOWN_GOOD = "down_good"
    NEUTRAL = "neutral"


@dataclass
class MetricDef:
    """Universal definition of a business metric."""

    metric_id: str
    name: str
    description: str
    category: MetricCategory
    unit: MetricUnit
    direction: MetricDirection
    computation_template: dict
    decomposition: list[str] = field(default_factory=list)
    parent: str | None = None
    related_metrics: list[str] = field(default_factory=list)


CORE_METRICS: dict[str, MetricDef] = {
    "mrr": MetricDef(
        metric_id="mrr",
        name="Monthly Recurring Revenue",
        description="Total recurring revenue normalized to a monthly period.",
        category=MetricCategory.REVENUE,
        unit=MetricUnit.CURRENCY,
        direction=MetricDirection.UP_GOOD,
        computation_template={"type": "sum", "source": "subscription", "filter": {"status": "active"}, "field": "mrr_amount"},
        decomposition=["new_mrr", "expansion_mrr", "contraction_mrr", "churn_mrr"],
        related_metrics=["arr", "arpu", "active_customers"],
    ),
    "new_mrr": MetricDef(
        metric_id="new_mrr",
        name="New MRR",
        description="MRR from newly created subscriptions in the period.",
        category=MetricCategory.GROWTH,
        unit=MetricUnit.CURRENCY,
        direction=MetricDirection.UP_GOOD,
        computation_template={
            "type": "sum",
            "source": "subscription",
            "filter": {"status": "active", "created_in_period": True},
            "field": "mrr_amount",
        },
        parent="mrr",
    ),
    "expansion_mrr": MetricDef(
        metric_id="expansion_mrr",
        name="Expansion MRR",
        description="Increase in MRR from existing customers.",
        category=MetricCategory.GROWTH,
        unit=MetricUnit.CURRENCY,
        direction=MetricDirection.UP_GOOD,
        computation_template={
            "type": "sum_positive_delta",
            "source": "subscription",
            "filter": {"status": "active", "existing_customer": True},
            "field": "mrr_amount",
        },
        parent="mrr",
    ),
    "contraction_mrr": MetricDef(
        metric_id="contraction_mrr",
        name="Contraction MRR",
        description="Decrease in MRR from existing customers.",
        category=MetricCategory.RETENTION,
        unit=MetricUnit.CURRENCY,
        direction=MetricDirection.DOWN_GOOD,
        computation_template={
            "type": "sum_negative_delta",
            "source": "subscription",
            "filter": {"status": "active", "existing_customer": True},
            "field": "mrr_amount",
        },
        parent="mrr",
    ),
    "churn_mrr": MetricDef(
        metric_id="churn_mrr",
        name="Churned MRR",
        description="MRR lost from cancelled subscriptions.",
        category=MetricCategory.RETENTION,
        unit=MetricUnit.CURRENCY,
        direction=MetricDirection.DOWN_GOOD,
        computation_template={
            "type": "sum",
            "source": "subscription",
            "filter": {"status": "canceled", "canceled_in_period": True},
            "field": "mrr_amount",
        },
        parent="mrr",
    ),
    "nrr": MetricDef(
        metric_id="nrr",
        name="Net Revenue Retention",
        description="Percentage of revenue retained from existing customers.",
        category=MetricCategory.RETENTION,
        unit=MetricUnit.PERCENT,
        direction=MetricDirection.UP_GOOD,
        computation_template={
            "type": "formula",
            "formula": "(mrr + expansion_mrr - contraction_mrr - churn_mrr) / mrr_previous * 100",
        },
        related_metrics=["mrr", "expansion_mrr", "contraction_mrr", "churn_mrr"],
    ),
    "active_customers": MetricDef(
        metric_id="active_customers",
        name="Active Customers",
        description="Count of customers with at least one active subscription.",
        category=MetricCategory.GROWTH,
        unit=MetricUnit.COUNT,
        direction=MetricDirection.UP_GOOD,
        computation_template={
            "type": "count_distinct",
            "source": "subscription",
            "filter": {"status": "active"},
            "field": "customer_entity_id",
        },
    ),
    "arpu": MetricDef(
        metric_id="arpu",
        name="Average Revenue Per User",
        description="MRR divided by active customers.",
        category=MetricCategory.EFFICIENCY,
        unit=MetricUnit.CURRENCY,
        direction=MetricDirection.UP_GOOD,
        computation_template={"type": "formula", "formula": "mrr / active_customers"},
        related_metrics=["mrr", "active_customers"],
    ),
    "quick_ratio": MetricDef(
        metric_id="quick_ratio",
        name="Quick Ratio",
        description="(New + Expansion) / (Contraction + Churn). Measures growth efficiency.",
        category=MetricCategory.EFFICIENCY,
        unit=MetricUnit.RATIO,
        direction=MetricDirection.UP_GOOD,
        computation_template={"type": "formula", "formula": "(new_mrr + expansion_mrr) / (contraction_mrr + churn_mrr)"},
        related_metrics=["new_mrr", "expansion_mrr", "contraction_mrr", "churn_mrr"],
    ),
    "logo_churn_rate": MetricDef(
        metric_id="logo_churn_rate",
        name="Logo Churn Rate",
        description="Percentage of customers lost in the period.",
        category=MetricCategory.RETENTION,
        unit=MetricUnit.PERCENT,
        direction=MetricDirection.DOWN_GOOD,
        computation_template={"type": "formula", "formula": "churned_customers / active_customers_start * 100"},
    ),
}


@dataclass
class MetricEdge:
    parent: str
    child: str
    relationship: str
    weight: float = 1.0


METRIC_DAG: list[MetricEdge] = [
    MetricEdge("mrr", "new_mrr", "decomposition"),
    MetricEdge("mrr", "expansion_mrr", "decomposition"),
    MetricEdge("mrr", "contraction_mrr", "decomposition"),
    MetricEdge("mrr", "churn_mrr", "decomposition"),
    MetricEdge("nrr", "mrr", "formula_input"),
    MetricEdge("nrr", "expansion_mrr", "formula_input"),
    MetricEdge("nrr", "contraction_mrr", "formula_input"),
    MetricEdge("nrr", "churn_mrr", "formula_input"),
    MetricEdge("arpu", "mrr", "formula_input"),
    MetricEdge("arpu", "active_customers", "formula_input"),
    MetricEdge("quick_ratio", "new_mrr", "formula_input"),
    MetricEdge("quick_ratio", "expansion_mrr", "formula_input"),
    MetricEdge("quick_ratio", "contraction_mrr", "formula_input"),
    MetricEdge("quick_ratio", "churn_mrr", "formula_input"),
]


def get_decomposition_children(metric_id: str) -> list[str]:
    return [e.child for e in METRIC_DAG if e.parent == metric_id and e.relationship == "decomposition"]


def get_parents(metric_id: str) -> list[str]:
    return [e.parent for e in METRIC_DAG if e.child == metric_id]
