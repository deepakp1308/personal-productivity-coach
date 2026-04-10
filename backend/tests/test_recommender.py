"""Tests for the recommendation generator."""

import pytest
from datetime import datetime, timedelta

from backend.storage import db
from backend.agents.recommender import generate_recommendations


@pytest.fixture(autouse=True)
def fresh_db(tmp_path):
    test_db = str(tmp_path / "test_coach.db")
    db.set_db_path(test_db)
    db.init_db()
    db.insert_priority("Advanced Analytics & AI-Powered Insights", "", 0.40, pillar=2)
    db.insert_priority("Platform Intelligence Across MC & QBO", "", 0.35, pillar=3)
    db.insert_priority("Trusted Data Foundation & Quality at Scale", "", 0.25, pillar=1)
    yield


def _seed_classified_activities():
    now = datetime.now()
    activities = [
        ("Analytics agent review", "Advanced Analytics & AI-Powered Insights", "Strategy"),
        ("BI platform launch prep", "Platform Intelligence Across MC & QBO", "Execution"),
        ("QA test plan review", "Trusted Data Foundation & Quality at Scale", "Execution"),
        ("Random status meeting", "Other", "LowValue"),
        ("Escalation handling", "Other", "Reactive"),
        ("Team standup notes", "Other", "InternalOps"),
        ("DSB benchmarks analysis", "Advanced Analytics & AI-Powered Insights", "Discovery"),
        ("L2C funnel design", "Platform Intelligence Across MC & QBO", "Strategy"),
    ]
    for i, (title, priority, atype) in enumerate(activities):
        occurred = (now - timedelta(hours=i)).isoformat()
        aid = db.insert_activity("slack", title, occurred, source_id=f"rec-{i}")
        if aid:
            db.insert_classification(aid, priority_name=priority, activity_type=atype, leverage="Medium", confidence=0.8)


class TestGenerateRecommendations:
    def test_returns_three_recommendations(self):
        _seed_classified_activities()
        result = generate_recommendations()
        assert len(result["recommendations"]) == 3

    def test_has_required_fields(self):
        _seed_classified_activities()
        result = generate_recommendations()
        assert "summary" in result
        assert "alignment_pct" in result
        assert "recommendations" in result
        for rec in result["recommendations"]:
            assert "kind" in rec
            assert "action" in rec
            assert "rationale" in rec
            assert rec["kind"] in ("Accelerate", "Cut", "Redirect")

    def test_recommends_cut_when_low_value_exists(self):
        _seed_classified_activities()
        result = generate_recommendations()
        kinds = [r["kind"] for r in result["recommendations"]]
        assert "Cut" in kinds

    def test_alignment_pct_in_range(self):
        _seed_classified_activities()
        result = generate_recommendations()
        assert 0 <= result["alignment_pct"] <= 100

    def test_empty_db_still_returns_three(self):
        result = generate_recommendations()
        assert len(result["recommendations"]) == 3
