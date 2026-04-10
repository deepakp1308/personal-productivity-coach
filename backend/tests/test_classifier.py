"""Tests for the activity classifier."""

import pytest
from backend.storage import db
from backend.agents.classifier import classify_activity, classify_batch, _guess_leverage


@pytest.fixture(autouse=True)
def fresh_db(tmp_path):
    test_db = str(tmp_path / "test_coach.db")
    db.set_db_path(test_db)
    db.init_db()
    # Seed priorities
    db.insert_priority("Advanced Analytics & AI-Powered Insights", "", 0.40, pillar=2)
    db.insert_priority("Platform Intelligence Across MC & QBO", "", 0.35, pillar=3)
    db.insert_priority("Trusted Data Foundation & Quality at Scale", "", 0.25, pillar=1)
    yield


class TestRuleBasedClassification:
    def test_insights_agent_matches_pillar2(self):
        activity = {"id": 1, "title": "Analytics agent beta review with Stephen", "summary": "", "source": "slack"}
        result = classify_activity(activity)
        assert result["priority_name"] == "Advanced Analytics & AI-Powered Insights"

    def test_bi_platform_matches_pillar3(self):
        activity = {"id": 2, "title": "GBSG BI platform Phase 1 launch review", "summary": "", "source": "slack"}
        result = classify_activity(activity)
        assert result["priority_name"] == "Platform Intelligence Across MC & QBO"

    def test_qa_matches_pillar1(self):
        activity = {"id": 3, "title": "QA regression test coverage plan review", "summary": "", "source": "slack"}
        result = classify_activity(activity)
        assert result["priority_name"] == "Trusted Data Foundation & Quality at Scale"

    def test_standup_classified_as_internal_ops(self):
        activity = {"id": 4, "title": "R&A team standup", "summary": "", "source": "slack"}
        result = classify_activity(activity)
        assert result["activity_type"] == "InternalOps"

    def test_1on1_classified_as_stakeholder(self):
        activity = {"id": 5, "title": "1:1 with Stephen Yu", "summary": "", "source": "slack"}
        result = classify_activity(activity)
        assert result["activity_type"] == "Stakeholder"

    def test_ticket_classified_as_execution(self):
        activity = {"id": 6, "title": "REPORTING-1234 fix data mismatch", "summary": "", "source": "slack"}
        result = classify_activity(activity)
        assert result["activity_type"] == "Execution"

    def test_prd_classified_as_strategy(self):
        activity = {"id": 7, "title": "PRD review for analytics agent GA", "summary": "", "source": "email"}
        result = classify_activity(activity)
        assert result["activity_type"] == "Strategy"

    def test_dsb_matches_pillar2(self):
        activity = {"id": 8, "title": "DSB conversion analytics benchmarks", "summary": "", "source": "slack"}
        result = classify_activity(activity)
        assert result["priority_name"] == "Advanced Analytics & AI-Powered Insights"

    def test_l2c_matches_pillar3(self):
        activity = {"id": 9, "title": "L2C funnel chart requirements", "summary": "", "source": "slack"}
        result = classify_activity(activity)
        assert result["priority_name"] == "Platform Intelligence Across MC & QBO"

    def test_whatsapp_matches_pillar2(self):
        activity = {"id": 10, "title": "WhatsApp analytics for July GA", "summary": "", "source": "email"}
        result = classify_activity(activity)
        assert result["priority_name"] == "Advanced Analytics & AI-Powered Insights"

    def test_modernization_matches_pillar1(self):
        activity = {"id": 11, "title": "Classic automation modernization status", "summary": "", "source": "slack"}
        result = classify_activity(activity)
        assert result["priority_name"] == "Trusted Data Foundation & Quality at Scale"

    def test_omni_matches_pillar3(self):
        activity = {"id": 12, "title": "Omni orchestration layer data access strategy", "summary": "", "source": "slack"}
        result = classify_activity(activity)
        assert result["priority_name"] == "Platform Intelligence Across MC & QBO"

    def test_unknown_defaults_to_other(self):
        activity = {"id": 13, "title": "Random unrelated meeting", "summary": "general chat", "source": "slack"}
        result = classify_activity(activity)
        assert result["priority_name"] == "Other"
        assert result["confidence"] <= 0.5

    def test_confidence_higher_for_strong_match(self):
        activity = {"id": 14, "title": "1:1 with Stephen about analytics agent", "summary": "", "source": "slack"}
        result = classify_activity(activity)
        assert result["confidence"] >= 0.7


class TestBatchClassification:
    def test_batch_returns_correct_count(self):
        activities = [
            {"id": i, "title": f"Activity {i}", "summary": "", "source": "slack"}
            for i in range(5)
        ]
        results = classify_batch(activities, use_llm=False)
        assert len(results) == 5

    def test_batch_preserves_activity_ids(self):
        activities = [
            {"id": 100, "title": "Analytics agent review", "summary": "", "source": "slack"},
            {"id": 200, "title": "Team standup", "summary": "", "source": "slack"},
        ]
        results = classify_batch(activities, use_llm=False)
        ids = [r["activity_id"] for r in results]
        assert 100 in ids
        assert 200 in ids


class TestLeverageGuessing:
    def test_shipped_is_high(self):
        assert _guess_leverage("Feature shipped to production") == "High"

    def test_blocked_is_low(self):
        assert _guess_leverage("Waiting on design review, blocked") == "Low"

    def test_neutral_is_medium(self):
        assert _guess_leverage("Discussed project timeline") == "Medium"

    def test_launched_is_high(self):
        assert _guess_leverage("Launched WhatsApp GA") == "High"
