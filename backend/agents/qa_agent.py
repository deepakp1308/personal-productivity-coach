"""QA Mini-Agent: validates dashboard data quality before deployment.

Runs a suite of data integrity, consistency, and sanity checks on the
ingested activities, classifications, and computed metrics. Returns a
structured report with pass/warn/fail status for each check.

This agent is called:
1. During the weekly pipeline (Step 7.5, after export, before deploy)
2. On-demand via the /api/qa endpoint
3. From the chat interface ("run QA checks")
"""

import json
import logging
from datetime import datetime, timedelta
from collections import Counter

from backend.storage import db
from backend.analysis import engine
from backend import config

logger = logging.getLogger(__name__)


class QACheck:
    """Single QA check result."""
    def __init__(self, name: str, status: str, message: str, details: dict = None):
        self.name = name
        self.status = status  # "pass", "warn", "fail"
        self.message = message
        self.details = details or {}

    def to_dict(self):
        return {"name": self.name, "status": self.status, "message": self.message, "details": self.details}


def run_qa_suite() -> dict:
    """Run all QA checks and return a structured report."""
    checks = []

    checks.append(_check_activity_count())
    checks.append(_check_classification_coverage())
    checks.append(_check_priority_consistency())
    checks.append(_check_alignment_range())
    checks.append(_check_meeting_hours_sanity())
    checks.append(_check_fragmentation_sanity())
    checks.append(_check_source_diversity())
    checks.append(_check_duplicate_activities())
    checks.append(_check_timestamp_validity())
    checks.append(_check_recommendation_quality())
    checks.append(_check_decision_completeness())
    checks.append(_check_open_question_staleness())
    checks.append(_check_priority_weights())
    checks.append(_check_data_freshness())

    # Summary
    pass_count = sum(1 for c in checks if c.status == "pass")
    warn_count = sum(1 for c in checks if c.status == "warn")
    fail_count = sum(1 for c in checks if c.status == "fail")
    total = len(checks)

    overall = "pass" if fail_count == 0 else "fail"
    if warn_count > 3 and fail_count == 0:
        overall = "warn"

    return {
        "timestamp": datetime.now().isoformat(),
        "overall_status": overall,
        "summary": f"{pass_count}/{total} passed, {warn_count} warnings, {fail_count} failures",
        "pass_count": pass_count,
        "warn_count": warn_count,
        "fail_count": fail_count,
        "total_checks": total,
        "checks": [c.to_dict() for c in checks],
        "deploy_allowed": fail_count == 0,
    }


# ── Individual QA Checks ─────────────────────────────────────────────────────

def _check_activity_count() -> QACheck:
    """Verify we have a reasonable number of activities."""
    count = db.get_activity_count()
    if count == 0:
        return QACheck("activity_count", "fail", f"No activities in database", {"count": count})
    if count < 10:
        return QACheck("activity_count", "warn", f"Only {count} activities — may be incomplete data pull", {"count": count})
    if count > 1000:
        return QACheck("activity_count", "warn", f"{count} activities — unusually high, check for duplicates", {"count": count})
    return QACheck("activity_count", "pass", f"{count} activities ingested", {"count": count})


def _check_classification_coverage() -> QACheck:
    """Verify all activities are classified."""
    total = db.get_activity_count()
    unclassified = db.get_unclassified_activities(limit=1000)
    unclassified_count = len(unclassified)

    if total == 0:
        return QACheck("classification_coverage", "fail", "No activities to classify")

    coverage_pct = ((total - unclassified_count) / total) * 100
    if unclassified_count > 0:
        return QACheck("classification_coverage", "warn",
                        f"{unclassified_count}/{total} activities unclassified ({coverage_pct:.0f}% coverage)",
                        {"total": total, "unclassified": unclassified_count, "coverage_pct": round(coverage_pct, 1)})
    return QACheck("classification_coverage", "pass",
                    f"100% classification coverage ({total} activities)",
                    {"total": total, "coverage_pct": 100.0})


def _check_priority_consistency() -> QACheck:
    """Verify classified priorities match configured priorities."""
    priorities = db.get_priorities()
    valid_names = {p["name"] for p in priorities} | {"Other"}
    activities = db.get_activities(limit=5000)

    invalid = []
    for a in activities:
        pname = a.get("priority_name")
        if pname and pname not in valid_names:
            invalid.append({"id": a["id"], "title": a["title"][:50], "invalid_priority": pname})

    if invalid:
        return QACheck("priority_consistency", "fail",
                        f"{len(invalid)} activities have invalid priority names",
                        {"invalid_count": len(invalid), "examples": invalid[:5]})
    return QACheck("priority_consistency", "pass",
                    "All priority names match configured priorities",
                    {"valid_priorities": list(valid_names)})


def _check_alignment_range() -> QACheck:
    """Verify alignment % is within valid range (0-100)."""
    summary = engine.compute_this_week()
    pct = summary["alignment_pct"]
    if pct < 0 or pct > 100:
        return QACheck("alignment_range", "fail", f"Alignment {pct}% is out of range [0-100]", {"value": pct})
    if pct == 0 and summary["total_activities"] > 5:
        return QACheck("alignment_range", "warn", f"Alignment is 0% with {summary['total_activities']} activities — all classified as Other?", {"value": pct})
    return QACheck("alignment_range", "pass", f"Alignment {pct}% is within valid range", {"value": pct})


def _check_meeting_hours_sanity() -> QACheck:
    """Verify meeting hours are reasonable (0-60h/week)."""
    summary = engine.compute_this_week()
    hours = summary["meeting_hours"]
    if hours < 0:
        return QACheck("meeting_hours", "fail", f"Meeting hours {hours} is negative", {"value": hours})
    if hours > 60:
        return QACheck("meeting_hours", "fail", f"Meeting hours {hours} exceeds 60h/week maximum", {"value": hours})
    if hours == 0 and summary.get("meetings", 0) > 0:
        return QACheck("meeting_hours", "warn", f"0 meeting hours but {summary['meetings']} calendar events found", {"value": hours, "events": summary["meetings"]})
    return QACheck("meeting_hours", "pass", f"{hours}h meeting hours this week", {"value": hours})


def _check_fragmentation_sanity() -> QACheck:
    """Verify fragmentation score is reasonable."""
    summary = engine.compute_this_week()
    frag = summary["fragmentation_score"]
    if frag < 0:
        return QACheck("fragmentation", "fail", f"Fragmentation score {frag} is negative", {"value": frag})
    if frag > 50:
        return QACheck("fragmentation", "warn", f"Fragmentation score {frag} seems unusually high", {"value": frag})
    return QACheck("fragmentation", "pass", f"Fragmentation score: {frag} switches/hr", {"value": frag})


def _check_source_diversity() -> QACheck:
    """Verify data comes from multiple sources (not just one channel)."""
    activities = db.get_activities(limit=5000)
    sources = Counter(a["source"] for a in activities)

    if len(sources) < 2:
        return QACheck("source_diversity", "warn",
                        f"Data from only {len(sources)} source(s): {list(sources.keys())}. Expected Slack + Gmail + Calendar.",
                        {"sources": dict(sources)})
    if "calendar" not in sources:
        return QACheck("source_diversity", "warn",
                        f"No calendar data found. Meeting hours may be underreported.",
                        {"sources": dict(sources)})
    return QACheck("source_diversity", "pass",
                    f"Data from {len(sources)} sources: {dict(sources)}",
                    {"sources": dict(sources)})


def _check_duplicate_activities() -> QACheck:
    """Check for duplicate activities by source_id."""
    activities = db.get_activities(limit=5000)
    seen_ids = {}
    duplicates = []
    for a in activities:
        sid = a.get("source_id") or a.get("title")
        if sid in seen_ids:
            duplicates.append({"title": a["title"][:50], "source_id": sid})
        seen_ids[sid] = True

    if duplicates:
        return QACheck("duplicates", "warn",
                        f"{len(duplicates)} potential duplicate activities detected",
                        {"count": len(duplicates), "examples": duplicates[:5]})
    return QACheck("duplicates", "pass", "No duplicate activities detected")


def _check_timestamp_validity() -> QACheck:
    """Verify all timestamps are valid and within expected range."""
    activities = db.get_activities(limit=5000)
    now = datetime.now()
    future_count = 0
    ancient_count = 0

    for a in activities:
        try:
            ts = datetime.fromisoformat(a["occurred_at"])
            if ts > now + timedelta(days=1):
                future_count += 1
            if ts < now - timedelta(days=30):
                ancient_count += 1
        except (ValueError, TypeError):
            return QACheck("timestamps", "fail", f"Invalid timestamp format in activity {a.get('id')}")

    issues = []
    if future_count > 0:
        issues.append(f"{future_count} future-dated")
    if ancient_count > 0:
        issues.append(f"{ancient_count} older than 30 days")

    if issues:
        return QACheck("timestamps", "warn",
                        f"Timestamp issues: {', '.join(issues)}",
                        {"future": future_count, "ancient": ancient_count})
    return QACheck("timestamps", "pass", "All timestamps valid and within expected range")


def _check_recommendation_quality() -> QACheck:
    """Verify recommendations exist and pass judge quality gate."""
    recs = db.get_recommendations(status="published", limit=20)
    if not recs:
        return QACheck("recommendations", "warn", "No published recommendations found — run pipeline first")

    low_score = [r for r in recs if r.get("judge_score") and r["judge_score"] < 2.0]
    no_evidence = [r for r in recs if not r.get("evidence_ids")]

    issues = []
    if low_score:
        issues.append(f"{len(low_score)} with low judge score (<2.0)")
    if no_evidence:
        issues.append(f"{len(no_evidence)} without evidence")

    if issues:
        return QACheck("recommendations", "warn",
                        f"Recommendation quality issues: {', '.join(issues)}",
                        {"total": len(recs), "low_score": len(low_score), "no_evidence": len(no_evidence)})
    return QACheck("recommendations", "pass",
                    f"{len(recs)} recommendations, all passing quality gate",
                    {"total": len(recs)})


def _check_decision_completeness() -> QACheck:
    """Verify decisions have required fields."""
    decisions = db.get_decisions(limit=100)
    if not decisions:
        return QACheck("decisions", "pass", "No decisions tracked (OK if early in week)")

    incomplete = [d for d in decisions if not d.get("description") or len(d["description"]) < 10]
    if incomplete:
        return QACheck("decisions", "warn",
                        f"{len(incomplete)}/{len(decisions)} decisions have short/missing descriptions",
                        {"total": len(decisions), "incomplete": len(incomplete)})
    return QACheck("decisions", "pass", f"{len(decisions)} decisions tracked, all complete")


def _check_open_question_staleness() -> QACheck:
    """Check for stale open questions (older than 14 days)."""
    questions = db.get_open_questions(status="open")
    if not questions:
        return QACheck("question_staleness", "pass", "No open questions")

    stale = []
    now = datetime.now()
    for q in questions:
        try:
            created = datetime.fromisoformat(q["created_at"])
            if (now - created).days > 14:
                stale.append(q["description"][:50])
        except (ValueError, TypeError):
            pass

    if stale:
        return QACheck("question_staleness", "warn",
                        f"{len(stale)} open questions older than 14 days — may need resolution",
                        {"stale_count": len(stale), "examples": stale[:3]})
    return QACheck("question_staleness", "pass", f"{len(questions)} open questions, none stale")


def _check_priority_weights() -> QACheck:
    """Verify priority weights sum to ~1.0."""
    priorities = db.get_priorities()
    if not priorities:
        return QACheck("priority_weights", "fail", "No priorities configured")

    total_weight = sum(p["weight"] for p in priorities)
    if abs(total_weight - 1.0) > 0.05:
        return QACheck("priority_weights", "warn",
                        f"Priority weights sum to {total_weight:.2f} (expected ~1.0)",
                        {"total_weight": total_weight, "priorities": [{p["name"]: p["weight"]} for p in priorities]})
    return QACheck("priority_weights", "pass",
                    f"Priority weights sum to {total_weight:.2f}",
                    {"total_weight": total_weight})


def _check_data_freshness() -> QACheck:
    """Verify data has been updated recently."""
    activities = db.get_activities(limit=1)
    if not activities:
        return QACheck("data_freshness", "fail", "No activities found")

    latest = activities[0]
    try:
        ts = datetime.fromisoformat(latest["occurred_at"])
        age_days = (datetime.now() - ts).days
        if age_days > 7:
            return QACheck("data_freshness", "warn",
                            f"Latest activity is {age_days} days old — data may be stale",
                            {"latest_date": latest["occurred_at"][:10], "age_days": age_days})
        return QACheck("data_freshness", "pass",
                        f"Latest activity: {latest['occurred_at'][:10]} ({age_days} days ago)",
                        {"latest_date": latest["occurred_at"][:10], "age_days": age_days})
    except (ValueError, TypeError):
        return QACheck("data_freshness", "warn", "Could not parse latest activity timestamp")


# ── Formatted report ─────────────────────────────────────────────────────────

def format_qa_report(result: dict) -> str:
    """Format QA results as a human-readable report."""
    lines = [
        f"QA Report — {result['timestamp'][:19]}",
        f"Overall: {result['overall_status'].upper()} ({result['summary']})",
        f"Deploy allowed: {'YES' if result['deploy_allowed'] else 'BLOCKED'}",
        "",
    ]

    status_icons = {"pass": "PASS", "warn": "WARN", "fail": "FAIL"}
    for check in result["checks"]:
        icon = status_icons[check["status"]]
        lines.append(f"  [{icon}] {check['name']}: {check['message']}")

    return "\n".join(lines)
