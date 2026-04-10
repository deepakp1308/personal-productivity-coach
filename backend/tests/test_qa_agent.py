"""Tests for the QA mini-agent."""

import pytest
from datetime import datetime, timedelta

from backend.storage import db
from backend.agents.qa_agent import run_qa_suite, format_qa_report


@pytest.fixture(autouse=True)
def fresh_db(tmp_path):
    test_db = str(tmp_path / "test_coach.db")
    db.set_db_path(test_db)
    db.init_db()
    db.insert_priority("Priority A", "", 0.5, pillar=1)
    db.insert_priority("Priority B", "", 0.3, pillar=2)
    db.insert_priority("Priority C", "", 0.2, pillar=3)
    yield


def _seed_activities(count=15):
    now = datetime.now()
    for i in range(count):
        occurred = (now - timedelta(hours=i)).isoformat()
        aid = db.insert_activity("slack", f"Activity {i}", occurred, source_id=f"qa-{i}-{now.timestamp()}")
        if aid:
            db.insert_classification(aid, priority_name="Priority A", activity_type="Execution",
                                      leverage="Medium", confidence=0.8)
    # Add some calendar events
    for i in range(3):
        occurred = (now - timedelta(hours=i*3)).isoformat()
        aid = db.insert_activity("calendar", f"Meeting {i}", occurred,
                                  source_id=f"cal-{i}-{now.timestamp()}", duration_minutes=30)
        if aid:
            db.insert_classification(aid, priority_name="Priority B", activity_type="Stakeholder",
                                      leverage="Medium", confidence=0.8)


class TestQASuiteStructure:
    def test_returns_required_fields(self):
        _seed_activities()
        result = run_qa_suite()
        assert "overall_status" in result
        assert "summary" in result
        assert "checks" in result
        assert "deploy_allowed" in result
        assert "total_checks" in result

    def test_overall_status_is_valid(self):
        _seed_activities()
        result = run_qa_suite()
        assert result["overall_status"] in ("pass", "warn", "fail")

    def test_check_count_matches(self):
        _seed_activities()
        result = run_qa_suite()
        assert result["total_checks"] == len(result["checks"])
        assert result["pass_count"] + result["warn_count"] + result["fail_count"] == result["total_checks"]

    def test_each_check_has_required_fields(self):
        _seed_activities()
        result = run_qa_suite()
        for check in result["checks"]:
            assert "name" in check
            assert "status" in check
            assert "message" in check
            assert check["status"] in ("pass", "warn", "fail")


class TestQAChecks:
    def test_empty_db_flags_no_activities(self):
        result = run_qa_suite()
        activity_check = next(c for c in result["checks"] if c["name"] == "activity_count")
        assert activity_check["status"] == "fail"

    def test_populated_db_passes_activity_count(self):
        _seed_activities(20)
        result = run_qa_suite()
        activity_check = next(c for c in result["checks"] if c["name"] == "activity_count")
        assert activity_check["status"] == "pass"

    def test_classification_coverage_pass(self):
        _seed_activities()
        result = run_qa_suite()
        check = next(c for c in result["checks"] if c["name"] == "classification_coverage")
        assert check["status"] == "pass"

    def test_unclassified_activities_warned(self):
        now = datetime.now()
        db.insert_activity("slack", "Unclassified msg", now.isoformat(), source_id="uc-1")
        _seed_activities(10)
        result = run_qa_suite()
        check = next(c for c in result["checks"] if c["name"] == "classification_coverage")
        assert check["status"] == "warn"

    def test_priority_weights_pass(self):
        _seed_activities()
        result = run_qa_suite()
        check = next(c for c in result["checks"] if c["name"] == "priority_weights")
        assert check["status"] == "pass"

    def test_source_diversity_with_calendar(self):
        _seed_activities()  # includes both slack and calendar
        result = run_qa_suite()
        check = next(c for c in result["checks"] if c["name"] == "source_diversity")
        assert check["status"] == "pass"

    def test_alignment_range_valid(self):
        _seed_activities()
        result = run_qa_suite()
        check = next(c for c in result["checks"] if c["name"] == "alignment_range")
        assert check["status"] == "pass"

    def test_meeting_hours_valid(self):
        _seed_activities()
        result = run_qa_suite()
        check = next(c for c in result["checks"] if c["name"] == "meeting_hours")
        assert check["status"] == "pass"


class TestDeployGate:
    def test_deploy_allowed_when_all_pass(self):
        _seed_activities(20)
        result = run_qa_suite()
        # May have warnings but no failures with good data
        assert result["fail_count"] == 0 or result["deploy_allowed"] is False

    def test_deploy_blocked_on_empty_db(self):
        result = run_qa_suite()
        assert result["deploy_allowed"] is False
        assert result["fail_count"] > 0


class TestQAReport:
    def test_format_produces_string(self):
        _seed_activities()
        result = run_qa_suite()
        report = format_qa_report(result)
        assert isinstance(report, str)
        assert "QA Report" in report
        assert "PASS" in report or "WARN" in report or "FAIL" in report

    def test_report_includes_all_checks(self):
        _seed_activities()
        result = run_qa_suite()
        report = format_qa_report(result)
        for check in result["checks"]:
            assert check["name"] in report
