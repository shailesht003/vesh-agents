"""Tests for entity resolution pipeline."""

from vesh_agents.resolution.blocking import BlockingEngine, normalize_company_name, normalize_email_domain
from vesh_agents.resolution.clustering import ClusteringEngine
from vesh_agents.resolution.scoring import ScoringEngine, score_email, score_company_name


def test_normalize_email_domain():
    assert normalize_email_domain("alice@acme.com") == "acme.com"
    assert normalize_email_domain("BOB@BETA.IO") == "beta.io"
    assert normalize_email_domain("invalid") is None
    assert normalize_email_domain("") is None


def test_normalize_company_name():
    assert normalize_company_name("Acme Corp.") == "acme"
    assert normalize_company_name("Beta Inc") == "beta"
    assert normalize_company_name("  Gamma LLC  ") == "gamma"
    assert normalize_company_name("") == ""


def test_score_email_exact():
    score, method = score_email("alice@acme.com", "alice@acme.com")
    assert score == 1.0
    assert method == "email_exact"


def test_score_email_domain():
    score, method = score_email("alice@acme.com", "bob@acme.com")
    assert score == 0.8
    assert method == "email_domain"


def test_score_company_name_exact():
    score, method = score_company_name("Acme Corporation", "Acme Corp")
    assert score >= 0.8


def test_blocking_engine():
    """BlockingEngine should find candidate pairs by email domain."""
    records_a = [{"record_id": "a1", "data": {"email": "alice@acme.com"}}]
    records_b = [{"record_id": "b1", "data": {"email": "bob@acme.com"}}]
    engine = BlockingEngine()
    candidates = engine.generate_candidates(records_a, "stripe", records_b, "postgres")
    assert len(candidates) >= 1
    assert candidates[0].record_a_id == "a1"
    assert candidates[0].record_b_id == "b1"


def test_full_resolution_pipeline():
    """Full pipeline: blocking -> scoring -> clustering."""
    records_a = [
        {"record_id": "a1", "data": {"email": "alice@acme.com", "name": "Acme Corp", "mrr": "1200"}},
    ]
    records_b = [
        {"record_id": "b1", "data": {"email": "support@acme.com", "name": "Acme Corporation", "mrr": "1200"}},
    ]
    records_by_id = {
        "stripe:a1": records_a[0],
        "postgres:b1": records_b[0],
    }

    blocking = BlockingEngine()
    scoring = ScoringEngine()
    clustering = ClusteringEngine()

    candidates = blocking.generate_candidates(records_a, "stripe", records_b, "postgres")
    scored = scoring.score_candidates(candidates, records_by_id, threshold=0.3)
    clusters = clustering.cluster(scored)

    assert len(scored) >= 1
