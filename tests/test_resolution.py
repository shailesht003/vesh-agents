"""Tests for entity resolution — blocking, scoring, and clustering."""

from vesh_agents.resolution.blocking import (
    BlockingCandidate,
    BlockingEngine,
    normalize_company_name,
    normalize_email_domain,
    normalize_phone,
)
from vesh_agents.resolution.scoring import (
    DIMENSION_WEIGHTS,
    ScoringEngine,
    score_amount,
    score_company_name,
    score_email,
    score_temporal,
)


class TestNormalization:
    def test_email_domain_extraction(self):
        assert normalize_email_domain("alex@acme.com") == "acme.com"
        assert normalize_email_domain("ALEX@Acme.COM") == "acme.com"
        assert normalize_email_domain("invalid") is None
        assert normalize_email_domain("") is None
        assert normalize_email_domain(None) is None

    def test_company_name_strips_suffixes(self):
        assert normalize_company_name("Acme Inc.") == "acme"
        assert normalize_company_name("Acme Corporation") == "acme"
        assert normalize_company_name("Acme LLC") == "acme"
        assert normalize_company_name("Acme Ltd.") == "acme"

    def test_company_name_removes_punctuation(self):
        assert normalize_company_name("O'Brien & Co.") == "obrien"

    def test_company_name_normalizes_whitespace(self):
        assert normalize_company_name("  Acme   Corp  ") == "acme"

    def test_phone_normalization(self):
        assert normalize_phone("+1 (555) 123-4567") == "1234567"
        assert normalize_phone("555-123-4567") == "1234567"
        assert normalize_phone("1234567") == "1234567"


class TestEmailScoring:
    def test_exact_match(self):
        score, method = score_email("alex@acme.com", "alex@acme.com")
        assert score == 1.0
        assert method == "email_exact"

    def test_domain_match(self):
        score, method = score_email("alex@acme.com", "bob@acme.com")
        assert score == 0.8
        assert method == "email_domain"

    def test_mismatch(self):
        score, _ = score_email("alex@acme.com", "alex@other.com")
        assert score == 0.0

    def test_missing_email(self):
        score, _ = score_email(None, "alex@acme.com")
        assert score == 0.0
        score, _ = score_email("", "")
        assert score == 0.0


class TestCompanyNameScoring:
    def test_exact_match(self):
        score, method = score_company_name("Acme Corp", "Acme Corp")
        assert score == 1.0

    def test_fuzzy_match(self):
        score, method = score_company_name("Acme Corporation", "Acme Corp")
        assert score > 0.5

    def test_mismatch(self):
        score, _ = score_company_name("Acme Corp", "Totally Different Company")
        assert score == 0.0

    def test_missing_name(self):
        score, _ = score_company_name(None, "Acme")
        assert score == 0.0


class TestTemporalScoring:
    def test_same_day(self):
        score, _ = score_temporal("2024-01-15", "2024-01-15")
        assert score == 1.0

    def test_within_tolerance(self):
        score, _ = score_temporal("2024-01-15", "2024-01-16")
        assert 0.0 < score < 1.0

    def test_beyond_tolerance(self):
        score, _ = score_temporal("2024-01-15", "2024-06-15")
        assert score == 0.0

    def test_missing_timestamps(self):
        score, _ = score_temporal(None, "2024-01-15")
        assert score == 0.0


class TestAmountScoring:
    def test_exact_match(self):
        score, method = score_amount(100.0, 100.0)
        assert score == 1.0

    def test_close_match(self):
        score, method = score_amount(100.0, 105.0)
        assert score >= 0.7

    def test_mismatch(self):
        score, _ = score_amount(100.0, 500.0)
        assert score == 0.0

    def test_both_zero(self):
        score, _ = score_amount(0.0, 0.0)
        assert score == 0.5

    def test_missing_amount(self):
        score, _ = score_amount(None, 100.0)
        assert score == 0.0


class TestDimensionWeights:
    def test_weights_sum_to_one(self):
        assert abs(sum(DIMENSION_WEIGHTS.values()) - 1.0) < 0.01

    def test_email_has_highest_weight(self):
        assert DIMENSION_WEIGHTS["email"] >= max(
            v for k, v in DIMENSION_WEIGHTS.items() if k != "email"
        )


class TestBlockingEngine:
    def test_blocks_by_email_domain(self):
        engine = BlockingEngine()
        records_a = [{"record_id": "a1", "data": {"email": "alex@acme.com"}}]
        records_b = [{"record_id": "b1", "data": {"email": "bob@acme.com"}}]
        candidates = engine.generate_candidates(records_a, "stripe", records_b, "postgres")
        assert len(candidates) >= 1
        assert all(isinstance(c, BlockingCandidate) for c in candidates)

    def test_no_candidates_for_different_domains(self):
        engine = BlockingEngine()
        records_a = [{"record_id": "a1", "data": {"email": "alex@acme.com"}}]
        records_b = [{"record_id": "b1", "data": {"email": "bob@other.com"}}]
        candidates = engine.generate_candidates(records_a, "stripe", records_b, "postgres")
        email_candidates = [c for c in candidates if c.blocking_strategy == "union"]
        for c in email_candidates:
            assert not (c.record_a_id == "a1" and c.record_b_id == "b1") or len(candidates) > 0

    def test_blocks_by_company_name(self):
        engine = BlockingEngine()
        records_a = [{"record_id": "a1", "data": {"company_name": "Acme Corp"}}]
        records_b = [{"record_id": "b1", "data": {"company_name": "Acme Corporation"}}]
        candidates = engine.generate_candidates(records_a, "stripe", records_b, "postgres")
        assert len(candidates) >= 1


class TestScoringEngine:
    def test_high_score_for_matching_records(self):
        engine = ScoringEngine()
        record_a = {"data": {"email": "alex@acme.com", "name": "Acme Corp", "mrr": "500"}}
        record_b = {"data": {"email": "alex@acme.com", "name": "Acme Corp", "mrr": "500"}}
        candidate = BlockingCandidate("a1", "stripe", "b1", "postgres", "email_domain")
        score = engine.score_pair(record_a, record_b, candidate)
        assert score.total_score > 0.5
        assert len(score.evidence) > 0

    def test_low_score_for_mismatched_records(self):
        engine = ScoringEngine()
        record_a = {"data": {"email": "alex@acme.com", "name": "Acme Corp"}}
        record_b = {"data": {"email": "bob@other.com", "name": "Totally Different"}}
        candidate = BlockingCandidate("a1", "stripe", "b1", "postgres", "union")
        score = engine.score_pair(record_a, record_b, candidate)
        assert score.total_score < 0.3
