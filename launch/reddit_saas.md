# r/SaaS Post

## Title

Open-sourced an AI tool that computes MRR, churn, ARPU, NRR from your Stripe/CSV data — no dashboards needed

## Body

Hey r/SaaS,

I built **Vesh Agents** — an open-source tool that analyzes your revenue data and gives you SaaS metrics instantly. No dashboard setup, no data warehouse, no $500/mo subscription.

**How it works:**

```bash
pip install vesh-agents
vesh analyze csv your_stripe_export.csv
```

30 seconds later:

```
  Monthly Recurring Revenue   $152,413
  Active Customers                  36
  Average Revenue Per User      $4,234
  Net Revenue Retention           112%
  Logo Churn Rate                 2.8%
  Quick Ratio                     3.2x
```

**What it computes:**
- MRR (with decomposition: New, Expansion, Contraction, Churned)
- Net Revenue Retention
- ARPU
- Quick Ratio
- Logo Churn Rate
- Active Customers

**Data sources:**
- CSV files (export from Stripe, ChartMogul, or any spreadsheet)
- Stripe API directly (`vesh analyze stripe --api-key sk_live_...`)
- PostgreSQL databases

**What's different from Baremetrics/ChartMogul/ProfitWell:**
- Free and open-source (Apache 2.0)
- Runs locally — your data never leaves your machine
- AI-powered anomaly detection flags unusual changes
- Entity resolution matches customers across multiple sources
- Use your own LLM to get explanations ("Why did churn spike?")

**GitHub:** https://github.com/shailesht003/vesh-agents

We're adding more connectors (HubSpot, Salesforce, BigQuery) — if you want a specific one, open an issue and we'll prioritize it.
