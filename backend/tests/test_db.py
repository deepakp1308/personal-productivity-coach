"""Tests for SQLite storage layer."""

import os
import tempfile
import pytest

from backend.storage import db


@pytest.fixture(autouse=True)
def fresh_db(tmp_path):
    """Use a fresh temp DB for each test."""
    test_db = str(tmp_path / "test_coach.db")
    db.set_db_path(test_db)
    db.init_db()
    yield test_db


class TestPriorities:
    def test_insert_and_get(self):
        pid = db.insert_priority("Test Priority", "desc", 0.5, pillar=1)
        assert pid > 0
        priorities = db.get_priorities()
        assert len(priorities) == 1
        assert priorities[0]["name"] == "Test Priority"
        assert priorities[0]["weight"] == 0.5
        assert priorities[0]["pillar"] == 1

    def test_update_priority(self):
        pid = db.insert_priority("Old Name", "old desc", 0.3)
        db.update_priority(pid, name="New Name", weight=0.7)
        priorities = db.get_priorities()
        assert priorities[0]["name"] == "New Name"
        assert priorities[0]["weight"] == 0.7

    def test_multiple_priorities_ordered_by_weight(self):
        db.insert_priority("Low", "", 0.2)
        db.insert_priority("High", "", 0.5)
        db.insert_priority("Mid", "", 0.3)
        priorities = db.get_priorities()
        weights = [p["weight"] for p in priorities]
        assert weights == sorted(weights, reverse=True)


class TestActivities:
    def test_insert_and_get(self):
        aid = db.insert_activity("slack", "Test message", "2026-04-01T10:00:00",
                                  source_id="s1", summary="test", channel="general")
        assert aid > 0
        activities = db.get_activities()
        assert len(activities) == 1
        assert activities[0]["title"] == "Test message"
        assert activities[0]["source"] == "slack"

    def test_dedup_by_source_id(self):
        db.insert_activity("slack", "Msg 1", "2026-04-01T10:00:00", source_id="dup1")
        db.insert_activity("slack", "Msg 2", "2026-04-01T11:00:00", source_id="dup1")
        assert db.get_activity_count() == 1

    def test_bulk_insert(self):
        rows = [
            {"source": "slack", "source_id": f"bulk-{i}", "title": f"Activity {i}",
             "occurred_at": f"2026-04-0{i+1}T10:00:00"}
            for i in range(5)
        ]
        count = db.insert_activities_bulk(rows)
        assert count == 5
        assert db.get_activity_count() == 5

    def test_filter_by_source(self):
        db.insert_activity("slack", "Slack msg", "2026-04-01T10:00:00", source_id="s1")
        db.insert_activity("email", "Email msg", "2026-04-01T11:00:00", source_id="e1")
        slack_only = db.get_activities(source="slack")
        assert len(slack_only) == 1
        assert slack_only[0]["source"] == "slack"

    def test_filter_by_date_range(self):
        db.insert_activity("slack", "Old", "2026-03-01T10:00:00", source_id="old1")
        db.insert_activity("slack", "New", "2026-04-01T10:00:00", source_id="new1")
        recent = db.get_activities(date_from="2026-03-15T00:00:00")
        assert len(recent) == 1
        assert recent[0]["title"] == "New"

    def test_fts_search(self):
        db.insert_activity("slack", "Analytics agent beta review", "2026-04-01T10:00:00", source_id="fts1")
        db.insert_activity("slack", "Team standup notes", "2026-04-01T11:00:00", source_id="fts2")
        results = db.search_activities_fts("analytics agent")
        assert len(results) >= 1
        assert "analytics" in results[0]["title"].lower()


class TestClassifications:
    def test_insert_and_get_with_activity(self):
        aid = db.insert_activity("slack", "Test activity", "2026-04-01T10:00:00", source_id="c1")
        db.insert_classification(aid, priority_name="Test Priority", activity_type="Strategy",
                                  leverage="High", confidence=0.9, reasoning="test")
        activity = db.get_activity(aid)
        assert activity["priority_name"] == "Test Priority"
        assert activity["activity_type"] == "Strategy"

    def test_unclassified_detection(self):
        db.insert_activity("slack", "Unclassified", "2026-04-01T10:00:00", source_id="uc1")
        aid2 = db.insert_activity("slack", "Classified", "2026-04-01T11:00:00", source_id="uc2")
        db.insert_classification(aid2, activity_type="Execution")
        unclassified = db.get_unclassified_activities()
        assert len(unclassified) == 1
        assert unclassified[0]["title"] == "Unclassified"


class TestDecisions:
    def test_insert_and_get(self):
        did = db.insert_decision("Decided to ship feature X", channel="product", related_priority="Test")
        assert did > 0
        decisions = db.get_decisions()
        assert len(decisions) == 1
        assert "ship feature X" in decisions[0]["description"]

    def test_filter_by_priority(self):
        db.insert_decision("Decision A", related_priority="P1")
        db.insert_decision("Decision B", related_priority="P2")
        p1_only = db.get_decisions(related_priority="P1")
        assert len(p1_only) == 1


class TestOpenQuestions:
    def test_insert_and_get(self):
        qid = db.insert_open_question("What is the data strategy?", urgency="high", owner="Stephen")
        assert qid > 0
        questions = db.get_open_questions()
        assert len(questions) == 1
        assert questions[0]["urgency"] == "high"

    def test_status_update(self):
        qid = db.insert_open_question("Open Q")
        db.update_question_status(qid, "resolved")
        resolved = db.get_open_questions(status="resolved")
        assert len(resolved) == 1
        assert resolved[0]["resolved_at"] is not None

    def test_filter_by_urgency(self):
        db.insert_open_question("High Q", urgency="high")
        db.insert_open_question("Low Q", urgency="low")
        high_only = db.get_open_questions(urgency="high")
        assert len(high_only) == 1


class TestRecommendations:
    def test_insert_and_get(self):
        rid = db.insert_recommendation("2026-W15", "Accelerate", "Do more X", "Because Y",
                                        evidence_ids=[1, 2], judge_score=4.0)
        assert rid > 0
        recs = db.get_recommendations()
        assert len(recs) == 1
        assert recs[0]["kind"] == "Accelerate"
        assert recs[0]["evidence_ids"] == [1, 2]

    def test_filter_by_week(self):
        db.insert_recommendation("2026-W14", "Cut", "Stop X", "Wasting time", [])
        db.insert_recommendation("2026-W15", "Accelerate", "Do Y", "Important", [])
        w15 = db.get_recommendations(week_iso="2026-W15")
        assert len(w15) == 1


class TestBriefings:
    def test_insert_and_get(self):
        import json
        content = {"summary": "test", "alignment_pct": 75.0}
        db.insert_briefing("2026-04-10", json.dumps(content), "web")
        b = db.get_briefing("2026-04-10")
        assert b is not None
        assert b["content"]["alignment_pct"] == 75.0

    def test_latest_briefing(self):
        import json
        db.insert_briefing("2026-04-09", json.dumps({"day": "old"}))
        db.insert_briefing("2026-04-10", json.dumps({"day": "new"}))
        latest = db.get_latest_briefing()
        assert latest["content"]["day"] == "new"


class TestWeeklySnapshots:
    def test_insert_and_get(self):
        db.insert_weekly_snapshot("2026-W15", 72.5, 15.0, 3.2,
                                  {"Strategy": 5}, {"P1": 40.0}, [], "Good week")
        snapshots = db.get_weekly_snapshots()
        assert len(snapshots) == 1
        assert snapshots[0]["alignment_pct"] == 72.5


class TestReadOnlySQL:
    def test_select_works(self):
        db.insert_activity("slack", "SQL test", "2026-04-01T10:00:00", source_id="sql1")
        rows = db.run_read_only_sql("SELECT COUNT(*) as cnt FROM activities")
        assert rows[0]["cnt"] == 1

    def test_non_select_blocked(self):
        with pytest.raises(ValueError, match="Only SELECT"):
            db.run_read_only_sql("DELETE FROM activities")
