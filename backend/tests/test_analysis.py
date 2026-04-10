"""Tests for the analysis engine."""

import pytest
from datetime import datetime, timedelta

from backend.storage import db
from backend.analysis.engine import (
    compute_summary, compute_today_focus, compute_this_week,
    detect_anomalies, generate_top_insight, _estimate_duration, _compute_fragmentation,
)


@pytest.fixture(autouse=True)
def fresh_db(tmp_path):
    test_db = str(tmp_path / "test_coach.db")
    db.set_db_path(test_db)
    db.init_db()
    db.insert_priority("Priority A", "", 0.5, pillar=1)
    db.insert_priority("Priority B", "", 0.3, pillar=2)
    db.insert_priority("Priority C", "", 0.2, pillar=3)
    yield


def _seed_activities(count=10, source="slack", priority_name="Priority A", activity_type="Execution"):
    """Helper to seed classified activities."""
    now = datetime.now()
    for i in range(count):
        occurred = (now - timedelta(hours=i)).isoformat()
        aid = db.insert_activity(source, f"Activity {i}", occurred, source_id=f"test-{source}-{i}-{now.timestamp()}")
        if aid:
            db.insert_classification(aid, priority_name=priority_name, activity_type=activity_type,
                                      leverage="Medium", confidence=0.8)


class TestComputeSummary:
    def test_empty_db_returns_zero(self):
        summary = compute_summary()
        assert summary["total_activities"] == 0
        assert summary["alignment_pct"] == 0

    def test_counts_activities(self):
        _seed_activities(5, source="slack")
        _seed_activities(3, source="email")
        summary = compute_summary()
        assert summary["total_activities"] == 8
        assert summary["messages"] == 5
        assert summary["emails"] == 3

    def test_alignment_calculation(self):
        _seed_activities(7, priority_name="Priority A")
        _seed_activities(3, priority_name="Other")
        summary = compute_summary()
        # 7 out of 10 are on-priority
        assert summary["alignment_pct"] == pytest.approx(70.0, abs=5)

    def test_priority_breakdown(self):
        _seed_activities(6, priority_name="Priority A")
        _seed_activities(4, priority_name="Priority B")
        summary = compute_summary()
        assert "Priority A" in summary["priority_breakdown"]
        assert "Priority B" in summary["priority_breakdown"]
        assert summary["priority_breakdown"]["Priority A"] > summary["priority_breakdown"]["Priority B"]

    def test_type_breakdown(self):
        _seed_activities(4, activity_type="Strategy")
        _seed_activities(3, activity_type="Execution")
        _seed_activities(3, activity_type="LowValue")
        summary = compute_summary()
        assert summary["type_breakdown"]["Strategy"] == 4
        assert summary["type_breakdown"]["Execution"] == 3
        assert summary["type_breakdown"]["LowValue"] == 3


class TestAnomalyDetection:
    def test_no_anomalies_when_healthy(self):
        _seed_activities(10, priority_name="Priority A")
        anomalies = detect_anomalies()
        # Should not flag meeting bloat since source is slack not calendar
        meeting_alerts = [a for a in anomalies if a["type"] == "meeting_bloat"]
        assert len(meeting_alerts) == 0

    def test_low_alignment_flagged(self):
        _seed_activities(8, priority_name="Other")
        _seed_activities(2, priority_name="Priority A")
        anomalies = detect_anomalies()
        drift_alerts = [a for a in anomalies if a["type"] == "priority_drift"]
        assert len(drift_alerts) >= 1

    def test_priority_gap_flagged(self):
        # Only invest in Priority A, neglect B and C
        _seed_activities(20, priority_name="Priority A")
        anomalies = detect_anomalies()
        gap_alerts = [a for a in anomalies if a["type"] == "priority_gap"]
        assert len(gap_alerts) >= 1


class TestTopInsight:
    def test_generates_string(self):
        _seed_activities(10, priority_name="Priority A")
        insight = generate_top_insight()
        assert isinstance(insight, str)
        assert len(insight) > 0

    def test_positive_when_aligned(self):
        _seed_activities(10, priority_name="Priority A")
        summary = compute_summary()
        # Manually set high alignment for test
        summary["alignment_pct"] = 80.0
        summary["top_priority"] = "Priority A"
        insight = generate_top_insight(summary)
        assert "well-aligned" in insight.lower() or "aligned" in insight.lower() or "80" in insight


class TestHelpers:
    def test_estimate_duration_slack(self):
        assert _estimate_duration("slack") == 5

    def test_estimate_duration_email(self):
        assert _estimate_duration("email") == 10

    def test_estimate_duration_calendar(self):
        assert _estimate_duration("calendar") == 30

    def test_fragmentation_empty(self):
        assert _compute_fragmentation([]) == 0.0

    def test_fragmentation_single(self):
        assert _compute_fragmentation([{"occurred_at": "2026-04-01T10:00:00", "source": "slack"}]) == 0.0

    def test_fragmentation_with_switches(self):
        activities = [
            {"occurred_at": "2026-04-01T10:00:00", "source": "slack", "priority_name": "A"},
            {"occurred_at": "2026-04-01T10:30:00", "source": "email", "priority_name": "B"},
            {"occurred_at": "2026-04-01T11:00:00", "source": "slack", "priority_name": "A"},
            {"occurred_at": "2026-04-01T11:30:00", "source": "calendar", "priority_name": "C"},
        ]
        frag = _compute_fragmentation(activities)
        assert frag > 0  # Should detect switches
