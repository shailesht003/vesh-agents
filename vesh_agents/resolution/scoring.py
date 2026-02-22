"""Pairwise scoring — compare candidate pairs across all available dimensions."""

import logging
from dataclasses import dataclass
from datetime import datetime

from rapidfuzz import fuzz

from vesh_agents.resolution.blocking import BlockingCandidate, normalize_email_domain

logger = logging.getLogger(__name__)


@dataclass
class PairScore:
    """Score for a candidate pair with per-dimension breakdown."""

    record_a_id: str
    record_a_source: str
    record_b_id: str
    record_b_source: str
    total_score: float
    dimension_scores: dict[str, float]
    evidence: list[str]


DIMENSION_WEIGHTS = {
    "email": 0.35,
    "company_name": 0.25,
    "domain": 0.15,
    "temporal": 0.10,
    "amount": 0.10,
    "phone": 0.05,
}


def score_email(email_a: str | None, email_b: str | None) -> tuple[float, str]:
    if not email_a or not email_b:
        return 0.0, "no_email"
    a, b = email_a.strip().lower(), email_b.strip().lower()
    if a == b:
        return 1.0, "email_exact"
    domain_a, domain_b = normalize_email_domain(a), normalize_email_domain(b)
    if domain_a and domain_b and domain_a == domain_b:
        return 0.8, "email_domain"
    return 0.0, "email_mismatch"


def score_company_name(name_a: str | None, name_b: str | None) -> tuple[float, str]:
    if not name_a or not name_b:
        return 0.0, "no_name"
    similarity = fuzz.WRatio(name_a.lower(), name_b.lower()) / 100.0
    if similarity >= 0.95:
        return 1.0, "name_exact"
    if similarity >= 0.80:
        return similarity, "name_fuzzy"
    return 0.0, "name_mismatch"


def score_temporal(ts_a: datetime | str | None, ts_b: datetime | str | None, tolerance_days: int = 3) -> tuple[float, str]:
    if not ts_a or not ts_b:
        return 0.0, "no_timestamp"
    try:
        if isinstance(ts_a, str):
            ts_a = datetime.fromisoformat(ts_a.replace("Z", "+00:00"))
        if isinstance(ts_b, str):
            ts_b = datetime.fromisoformat(ts_b.replace("Z", "+00:00"))
        delta = abs((ts_a - ts_b).days)
        if delta <= tolerance_days:
            return 1.0 - (delta / (tolerance_days + 1)), f"temporal_match_{delta}d"
    except (ValueError, TypeError):
        pass
    return 0.0, "temporal_mismatch"


def score_amount(amount_a: float | None, amount_b: float | None, tolerance_pct: float = 0.05) -> tuple[float, str]:
    if amount_a is None or amount_b is None:
        return 0.0, "no_amount"
    try:
        a, b = float(amount_a), float(amount_b)
        if a == 0 and b == 0:
            return 0.5, "both_zero"
        max_val = max(abs(a), abs(b))
        if max_val == 0:
            return 0.0, "amount_zero"
        diff_pct = abs(a - b) / max_val
        if diff_pct <= tolerance_pct:
            return 1.0, "amount_exact"
        if diff_pct <= 0.10:
            return 0.7, "amount_close"
    except (ValueError, TypeError):
        pass
    return 0.0, "amount_mismatch"


def _get_field(record: dict, field_names: list[str]) -> str | None:
    data = record.get("data", record)
    for name in field_names:
        val = data.get(name)
        if val is not None:
            return str(val) if not isinstance(val, str) else val
    return None


class ScoringEngine:
    """Compute pairwise match scores for candidate pairs."""

    def score_pair(self, record_a: dict, record_b: dict, candidate: BlockingCandidate) -> PairScore:
        dimension_scores: dict[str, float] = {}
        evidence: list[str] = []

        email_a = _get_field(record_a, ["email", "email_address", "owner_email", "contact_email"])
        email_b = _get_field(record_b, ["email", "email_address", "owner_email", "contact_email"])
        score, method = score_email(email_a, email_b)
        dimension_scores["email"] = score
        if score > 0:
            evidence.append(f"{method}: {email_a} <> {email_b}")

        name_a = _get_field(record_a, ["name", "company_name", "company", "account_name"])
        name_b = _get_field(record_b, ["name", "company_name", "company", "account_name"])
        score, method = score_company_name(name_a, name_b)
        dimension_scores["company_name"] = score
        if score > 0:
            evidence.append(f"{method}: {name_a} <> {name_b}")

        ts_a = _get_field(record_a, ["created", "created_at", "signup_date"])
        ts_b = _get_field(record_b, ["created", "created_at", "signup_date"])
        score, method = score_temporal(ts_a, ts_b)
        dimension_scores["temporal"] = score
        if score > 0:
            evidence.append(method)

        amt_a = _get_field(record_a, ["mrr", "amount", "revenue", "plan_amount"])
        amt_b = _get_field(record_b, ["mrr", "amount", "revenue", "plan_amount"])
        try:
            score, method = score_amount(float(amt_a) if amt_a else None, float(amt_b) if amt_b else None)
        except ValueError:
            score, method = 0.0, "amount_parse_error"
        dimension_scores["amount"] = score
        if score > 0:
            evidence.append(method)

        total = sum(dimension_scores.get(dim, 0.0) * weight for dim, weight in DIMENSION_WEIGHTS.items())

        return PairScore(
            record_a_id=candidate.record_a_id, record_a_source=candidate.record_a_source,
            record_b_id=candidate.record_b_id, record_b_source=candidate.record_b_source,
            total_score=round(total, 4), dimension_scores=dimension_scores, evidence=evidence,
        )

    def score_candidates(self, candidates: list[BlockingCandidate], records_by_id: dict[str, dict],
                         threshold: float = 0.50) -> list[PairScore]:
        scored: list[PairScore] = []
        for candidate in candidates:
            record_a = records_by_id.get(f"{candidate.record_a_source}:{candidate.record_a_id}")
            record_b = records_by_id.get(f"{candidate.record_b_source}:{candidate.record_b_id}")
            if not record_a or not record_b:
                continue
            pair_score = self.score_pair(record_a, record_b, candidate)
            if pair_score.total_score >= threshold:
                scored.append(pair_score)
        logger.info("Scored %d/%d candidates above threshold %.2f", len(scored), len(candidates), threshold)
        return scored
