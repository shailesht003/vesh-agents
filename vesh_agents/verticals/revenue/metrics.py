"""SaaS revenue metric definitions for the revenue vertical."""

REVENUE_METRICS = [
    "mrr",
    "new_mrr",
    "expansion_mrr",
    "contraction_mrr",
    "churn_mrr",
    "nrr",
    "active_customers",
    "arpu",
    "quick_ratio",
    "logo_churn_rate",
]

METRIC_BENCHMARKS = {
    "nrr": {
        "excellent": 130,
        "good": 110,
        "ok": 100,
        "concern": 90,
        "description": "Net Revenue Retention. Best-in-class SaaS: >130%. Healthy: >110%.",
    },
    "quick_ratio": {
        "excellent": 4.0,
        "good": 2.0,
        "ok": 1.0,
        "concern": 0.5,
        "description": "Quick Ratio. Best-in-class: >4x. Healthy: >2x. Below 1x = shrinking.",
    },
    "logo_churn_rate": {
        "excellent": 1.0,
        "good": 3.0,
        "ok": 5.0,
        "concern": 8.0,
        "description": "Monthly logo churn. Best-in-class: <1%. Acceptable: <5%.",
    },
    "arpu": {
        "description": "Average Revenue Per User. Higher = more enterprise-focused.",
    },
}
