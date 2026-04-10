"""Pure Python analysis engine — no LLM calls.

Computes time allocation, fragmentation, anomaly detection, priority alignment.
Adapted for single-user (personal coach) from the team-level pm-agent.
"""

import json
from collections import defaultdict
from datetime import datetime, timedelta

from backend.storage import db
from backend import config


def compute_summary(date_from: str = None, date_to: str = None) -> dict:
    """Compute a full summary for the user over a time range."""
    activities = db.get_activities(date_from=date_from, date_to=date_to, limit=5000)

    source_counts = defaultdict(int)
    type_counts = defaultdict(int)
    priority_hours = defaultdict(float)
    total_duration = 0
    priority_duration = 0
    meeting_hours = 0.0

    for a in activities:
        source_counts[a["source"]] += 1
        if a.get("activity_type"):
            type_counts[a["activity_type"]] += 1
        dur = a.get("duration_minutes") or _estimate_duration(a["source"])
        total_duration += dur
        if a.get("priority_name") and a["priority_name"] != "Other":
            priority_hours[a["priority_name"]] += dur / 60.0
            priority_duration += dur
        if a["source"] == "calendar":
            meeting_hours += dur / 60.0

    total_hours = total_duration / 60.0 if total_duration else 1.0
    alignment_pct = (priority_duration / total_duration * 100) if total_duration else 0

    # Priority breakdown as percentages
    priority_breakdown = {}
    for name, hours in priority_hours.items():
        priority_breakdown[name] = round(hours / total_hours * 100, 1)

    # Fragmentation score
    frag = _compute_fragmentation(activities)

    # Target vs actual breakdown
    priorities = db.get_priorities()
    priority_targets = {p["name"]: round(p["weight"] * 100, 1) for p in priorities}

    # Top priority by time spent
    top_priority = max(priority_hours, key=priority_hours.get) if priority_hours else "None"

    # Open questions count
    open_qs = db.get_open_questions(status="open")

    return {
        "total_activities": len(activities),
        "meetings": source_counts.get("calendar", 0),
        "messages": source_counts.get("slack", 0),
        "emails": source_counts.get("email", 0),
        "alignment_pct": round(alignment_pct, 1),
        "top_priority": top_priority,
        "meeting_hours": round(meeting_hours, 1),
        "fragmentation_score": round(frag, 2),
        "source_breakdown": dict(source_counts),
        "type_breakdown": dict(type_counts),
        "priority_breakdown": priority_breakdown,
        "priority_targets": priority_targets,
        "open_questions_count": len(open_qs),
        "total_hours": round(total_hours, 1),
    }


def compute_today_focus() -> dict:
    """Compute what the user has been doing today."""
    today = datetime.now().strftime("%Y-%m-%dT00:00:00")
    return compute_summary(date_from=today)


def compute_this_week() -> dict:
    """Compute summary for the current work week (Monday to now)."""
    now = datetime.now()
    day_of_week = now.weekday()  # 0=Monday
    monday = now - timedelta(days=day_of_week)
    date_from = monday.strftime("%Y-%m-%dT00:00:00")
    return compute_summary(date_from=date_from)


def compute_last_week() -> dict:
    """Compute summary for last full work week."""
    now = datetime.now()
    day_of_week = now.weekday()
    this_monday = now - timedelta(days=day_of_week)
    last_monday = this_monday - timedelta(weeks=1)
    last_friday = last_monday + timedelta(days=4)
    return compute_summary(
        date_from=last_monday.strftime("%Y-%m-%dT00:00:00"),
        date_to=last_friday.strftime("%Y-%m-%dT23:59:59"),
    )


def compute_weekly_trends(weeks: int = 4) -> list[dict]:
    """Compute weekly trend data."""
    today = datetime.now()
    trends = []

    for w in range(weeks):
        end = today - timedelta(weeks=w)
        start = end - timedelta(weeks=1)
        date_from = start.strftime("%Y-%m-%dT00:00:00")
        date_to = end.strftime("%Y-%m-%dT23:59:59")

        summary = compute_summary(date_from, date_to)
        week_iso = start.strftime("%G-W%V")
        summary["week_iso"] = week_iso
        trends.append(summary)

    trends.reverse()
    return trends


def detect_anomalies() -> list[dict]:
    """Detect anomalies in the user's work patterns."""
    summary = compute_this_week()
    anomalies = []

    # Meeting bloat
    if summary["meeting_hours"] > config.MEETING_HOURS_THRESHOLD:
        anomalies.append({
            "type": "meeting_bloat",
            "severity": "warning",
            "message": f"You have {summary['meeting_hours']} meeting hours this week (threshold: {config.MEETING_HOURS_THRESHOLD}h). Consider delegating or making some async.",
        })

    # Low alignment
    if summary["alignment_pct"] < 50 and summary["total_activities"] > 5:
        anomalies.append({
            "type": "priority_drift",
            "severity": "warning",
            "message": f"Your priority alignment is only {summary['alignment_pct']}%. Review whether you're spending time on your Q4 pillars.",
        })

    # High fragmentation
    if summary["fragmentation_score"] > config.FRAGMENTATION_THRESHOLD:
        anomalies.append({
            "type": "fragmentation",
            "severity": "info",
            "message": f"Your fragmentation score is {summary['fragmentation_score']} context switches/hour. Try blocking focus time.",
        })

    # Low-value time
    total = max(summary["total_activities"], 1)
    low_value_pct = summary["type_breakdown"].get("LowValue", 0) / total * 100
    if low_value_pct > config.LOW_VALUE_THRESHOLD * 100:
        anomalies.append({
            "type": "low_value",
            "severity": "info",
            "message": f"You spent {low_value_pct:.0f}% of time on low-value activities. Consider cutting or delegating.",
        })

    # Priority gap check
    priorities = db.get_priorities()
    for p in priorities:
        pct = summary["priority_breakdown"].get(p["name"], 0)
        target = p["weight"] * 100
        if pct < target * 0.5 and summary["total_activities"] > 10:
            anomalies.append({
                "type": "priority_gap",
                "severity": "info",
                "message": f"'{p['name']}' is at {pct:.0f}% vs. target {target:.0f}%. You may need to invest more time here.",
            })

    return anomalies


def generate_top_insight(summary: dict = None) -> str:
    """Generate a single top insight."""
    if summary is None:
        summary = compute_this_week()

    anomalies = detect_anomalies()
    if anomalies:
        # Return highest-severity anomaly
        for sev in ("warning", "info"):
            for a in anomalies:
                if a["severity"] == sev:
                    return a["message"]

    if summary["alignment_pct"] >= 70:
        return f"You're well-aligned at {summary['alignment_pct']}% this week. Your top focus is {summary['top_priority']}. Keep it up!"

    return f"Your priority alignment is {summary['alignment_pct']}%. Check if your time matches your Q4 pillars."


# ── Helpers ──────────────────────────────────────────────────────────────────

def _estimate_duration(source: str) -> int:
    """Estimate duration in minutes for activities without explicit duration."""
    return {"calendar": 30, "slack": 5, "email": 10, "jira": 15, "gdrive": 20, "transcript": 45}.get(source, 10)


def _compute_fragmentation(activities: list[dict]) -> float:
    """Compute context switches per hour based on source/priority changes."""
    if len(activities) < 2:
        return 0.0

    sorted_acts = sorted(activities, key=lambda a: a["occurred_at"])
    switches = 0
    for i in range(1, len(sorted_acts)):
        prev = sorted_acts[i - 1]
        curr = sorted_acts[i]
        if prev["source"] != curr["source"] or prev.get("priority_name") != curr.get("priority_name"):
            switches += 1

    if sorted_acts:
        try:
            first = datetime.fromisoformat(sorted_acts[0]["occurred_at"])
            last = datetime.fromisoformat(sorted_acts[-1]["occurred_at"])
            hours = max((last - first).total_seconds() / 3600, 1)
        except (ValueError, TypeError):
            hours = 40
    else:
        hours = 40

    return switches / hours
