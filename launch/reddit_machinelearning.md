# r/MachineLearning Post (Saturday — Show-and-tell flair)

## Title

[P] Vesh Agents: Open-source agentic framework for revenue intelligence — entity resolution + anomaly detection + LLM reasoning

## Body

**TL;DR:** 6 specialized AI agents that form a pipeline: data extraction → entity resolution → metric computation → anomaly detection → causal reasoning. Built on OpenAI Agents SDK, BYOM via LiteLLM.

**GitHub:** https://github.com/shailesht003/vesh-agents

---

**The ML-relevant parts:**

**1. Entity Resolution without training data**

We use a multi-stage pipeline to match records across data sources:
- **Blocking** — reduces O(n*m) to tractable candidate sets using email domain, company name prefix, and phone number blocking
- **Pairwise scoring** — weighted scoring across 6 dimensions (email: 0.35, company name: 0.25, domain: 0.15, temporal: 0.10, amount: 0.10, phone: 0.05)
- **Fuzzy matching** — rapidfuzz WRatio for company names, exact + domain-level email matching
- **Clustering** — connected components to merge transitive matches into canonical entities

No labeled data needed. Works out of the box on messy real-world data.

**2. Anomaly Detection**

Two statistical methods running in parallel:
- **Z-score** — sliding window baseline (configurable window + threshold)
- **Rate-of-change** — detects sudden velocity changes even when absolute values are normal

Severity scoring is bounded [0, 1] and used downstream for insight prioritization.

**3. Agentic Architecture**

Built on the OpenAI Agents SDK, but model-agnostic via LiteLLM. Each agent has:
- Specialized system prompt
- Domain-specific tools (function calling)
- Handoff capability to other agents

The InsightReasoner uses the LLM to generate natural-language explanations of detected anomalies, incorporating metric decomposition trees and data lineage.

**4. Ontology-driven Metrics**

Metrics are defined declaratively as a DAG:
```
MRR → [New MRR, Expansion MRR, Contraction MRR, Churn MRR]
ARPU = MRR / Active Customers
Quick Ratio = (New + Expansion) / (Contraction + Churn)
```

Adding a new metric = adding a `MetricDef` to the ontology. The computation engine handles everything else.

---

Apache 2.0. Would appreciate feedback on the entity resolution approach — particularly interested in whether adding a lightweight learned scorer would meaningfully improve matching quality over the current heuristic approach.
