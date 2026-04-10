"""Chat API endpoint with local Q&A engine (no LLM required for basic queries)."""

import json
import re
import logging
import uuid
from datetime import datetime, timedelta

from backend.storage import db
from backend.analysis import engine

logger = logging.getLogger(__name__)


def handle_chat(user_message: str, session_id: str = None) -> dict:
    """Process a chat message and return a response.

    Uses pattern matching + SQL queries for common questions (no LLM needed).
    Falls back to a helpful message for complex queries.
    """
    if not session_id:
        session_id = str(uuid.uuid4())

    db.save_chat_message(session_id, "user", user_message)

    response = _route_question(user_message)

    db.save_chat_message(session_id, "assistant", response, json.dumps({"matched": True}))

    return {
        "response": response,
        "context": {"session_id": session_id},
    }


def _route_question(text: str) -> str:
    """Route question to appropriate handler."""
    t = text.lower().strip()

    # Time/priority questions
    if any(w in t for w in ["time spent", "spending time", "spend time", "how much time", "what did i"]):
        return _answer_time_question(text)

    # Alignment questions
    if any(w in t for w in ["alignment", "aligned", "on track", "priority alignment"]):
        return _answer_alignment()

    # Meeting questions
    if any(w in t for w in ["meeting", "meetings", "calendar"]):
        return _answer_meetings()

    # Activity breakdown
    if any(w in t for w in ["breakdown", "activity", "activities", "overview", "summary"]):
        return _answer_summary()

    # Priority questions
    if any(w in t for w in ["priorit", "pillar"]):
        return _answer_priorities()

    # Decision questions
    if any(w in t for w in ["decision", "decided"]):
        return _answer_decisions()

    # Open question tracking
    if any(w in t for w in ["open question", "unresolved", "blocking", "blocker"]):
        return _answer_open_questions()

    # Today focus
    if any(w in t for w in ["today", "focus", "right now", "this morning", "this afternoon"]):
        return _answer_today()

    # This week
    if any(w in t for w in ["this week", "week so far"]):
        return _answer_this_week()

    # Last week
    if "last week" in t:
        return _answer_last_week()

    # Recommendations
    if any(w in t for w in ["recommend", "coaching", "advice", "suggestion"]):
        return _answer_recommendations()

    # Anomalies
    if any(w in t for w in ["anomal", "alert", "warning", "issue", "concern"]):
        return _answer_anomalies()

    # Default
    return _answer_default()


def _answer_time_question(text: str) -> str:
    t = text.lower()
    if "yesterday" in t:
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%dT00:00:00")
        today_start = datetime.now().strftime("%Y-%m-%dT00:00:00")
        summary = engine.compute_summary(date_from=yesterday, date_to=today_start)
    elif "today" in t:
        summary = engine.compute_today_focus()
    elif "this week" in t:
        summary = engine.compute_this_week()
    elif "last week" in t:
        summary = engine.compute_last_week()
    else:
        summary = engine.compute_this_week()

    lines = [f"**Time Allocation Summary** ({summary['total_activities']} activities, {summary['total_hours']}h total)\n"]

    if summary["priority_breakdown"]:
        lines.append("**By Priority:**")
        for name, pct in sorted(summary["priority_breakdown"].items(), key=lambda x: -x[1]):
            target = summary["priority_targets"].get(name, 0)
            delta = pct - target
            arrow = "▲" if delta > 0 else "▼" if delta < 0 else "="
            lines.append(f"  - {name}: **{pct}%** (target: {target}%) {arrow} {abs(delta):.0f}pp")

    if summary["type_breakdown"]:
        lines.append("\n**By Activity Type:**")
        for name, count in sorted(summary["type_breakdown"].items(), key=lambda x: -x[1]):
            lines.append(f"  - {name}: {count} activities")

    lines.append(f"\n**Alignment:** {summary['alignment_pct']:.0f}% | **Meetings:** {summary['meeting_hours']}h")
    return "\n".join(lines)


def _answer_alignment() -> str:
    summary = engine.compute_this_week()
    lines = [f"**Priority Alignment: {summary['alignment_pct']:.0f}%**\n"]
    for name, pct in sorted(summary["priority_breakdown"].items(), key=lambda x: -x[1]):
        target = summary["priority_targets"].get(name, 0)
        status = "on track" if pct >= target * 0.8 else "**needs attention**"
        lines.append(f"  - {name}: {pct:.0f}% vs. target {target:.0f}% — {status}")
    return "\n".join(lines)


def _answer_meetings() -> str:
    summary = engine.compute_this_week()
    return (
        f"**Meeting Load This Week:** {summary['meeting_hours']}h\n"
        f"**Total Activities:** {summary['total_activities']}\n"
        f"**Calendar events:** {summary['meetings']}\n\n"
        f"{'Meeting hours are within normal range.' if summary['meeting_hours'] <= 20 else 'Meeting load is high — consider declining or going async on some.'}"
    )


def _answer_summary() -> str:
    summary = engine.compute_this_week()
    lines = [
        f"**This Week's Summary** ({summary['total_activities']} activities)\n",
        f"**Sources:** {summary['messages']} Slack · {summary['emails']} emails · {summary['meetings']} meetings",
        f"**Alignment:** {summary['alignment_pct']:.0f}% | **Fragmentation:** {summary['fragmentation_score']} switches/hr",
    ]
    if summary["priority_breakdown"]:
        lines.append("\n**Priority Mix:**")
        for name, pct in sorted(summary["priority_breakdown"].items(), key=lambda x: -x[1]):
            lines.append(f"  - {name}: {pct:.0f}%")
    return "\n".join(lines)


def _answer_priorities() -> str:
    priorities = db.get_priorities()
    lines = ["**FY26 Q4 Priorities:**\n"]
    for p in priorities:
        lines.append(f"  - **{p['name']}** (target: {p['weight']*100:.0f}%, Pillar {p.get('pillar', '?')})")
        if p.get("description"):
            lines.append(f"    {p['description']}")
    return "\n".join(lines)


def _answer_decisions() -> str:
    decisions = db.get_decisions(limit=10)
    if not decisions:
        return "No decisions tracked yet. Use the Decisions page or tell me about a decision to log it."
    lines = [f"**Recent Decisions** ({len(decisions)}):\n"]
    for d in decisions[:5]:
        pri = f" [{d['related_priority']}]" if d.get("related_priority") else ""
        lines.append(f"  - {d['description']}{pri} ({d['decided_at'][:10]})")
    return "\n".join(lines)


def _answer_open_questions() -> str:
    questions = db.get_open_questions(status="open")
    if not questions:
        return "No open questions tracked. Use the Decisions page or tell me about a question to log it."
    lines = [f"**Open Questions** ({len(questions)}):\n"]
    for q in questions:
        badge = {"high": "🔴", "medium": "🟡", "low": "🔵"}.get(q["urgency"], "")
        owner = f" (owner: {q['owner']})" if q.get("owner") else ""
        lines.append(f"  {badge} {q['description']}{owner}")
    return "\n".join(lines)


def _answer_today() -> str:
    summary = engine.compute_today_focus()
    if summary["total_activities"] == 0:
        return "No activities ingested for today yet. Data gets refreshed by the morning briefing task."
    return _format_brief_summary("Today's Focus", summary)


def _answer_this_week() -> str:
    summary = engine.compute_this_week()
    return _format_brief_summary("This Week", summary)


def _answer_last_week() -> str:
    summary = engine.compute_last_week()
    return _format_brief_summary("Last Week", summary)


def _answer_recommendations() -> str:
    recs = db.get_recommendations(status="published", limit=6)
    if not recs:
        return "No recommendations yet. Run the weekly pipeline to generate coaching advice."
    lines = ["**Latest Coaching Recommendations:**\n"]
    for r in recs[:3]:
        score = f" (judge: {r['judge_score']}/5)" if r.get("judge_score") else ""
        lines.append(f"  **{r['kind']}**: {r['action']}{score}")
        lines.append(f"  _{r['rationale']}_\n")
    return "\n".join(lines)


def _answer_anomalies() -> str:
    anomalies = engine.detect_anomalies()
    if not anomalies:
        return "No anomalies detected. Your work patterns look healthy this week!"
    lines = ["**Detected Patterns:**\n"]
    for a in anomalies:
        icon = {"warning": "⚠️", "info": "ℹ️"}.get(a["severity"], "")
        lines.append(f"  {icon} **{a['type']}**: {a['message']}")
    return "\n".join(lines)


def _answer_default() -> str:
    return (
        "I can help you with:\n"
        "  - **Time allocation** — \"What did I spend time on this week?\"\n"
        "  - **Priority alignment** — \"Am I on track for Analytics Agent?\"\n"
        "  - **Meeting load** — \"How many meeting hours this week?\"\n"
        "  - **Decisions** — \"What decisions did I make?\"\n"
        "  - **Open questions** — \"What's unresolved?\"\n"
        "  - **Recommendations** — \"Give me coaching advice\"\n"
        "  - **Anomalies** — \"Are there any concerns?\"\n\n"
        "Try asking a specific question!"
    )


def _format_brief_summary(label: str, summary: dict) -> str:
    lines = [
        f"**{label}** — {summary['total_activities']} activities, {summary['total_hours']}h\n",
        f"**Alignment:** {summary['alignment_pct']:.0f}% | **Meetings:** {summary['meeting_hours']}h | **Fragmentation:** {summary['fragmentation_score']}",
    ]
    if summary["priority_breakdown"]:
        top = sorted(summary["priority_breakdown"].items(), key=lambda x: -x[1])[:3]
        lines.append("**Top focuses:** " + ", ".join(f"{n} ({p:.0f}%)" for n, p in top))
    insight = engine.generate_top_insight(summary)
    lines.append(f"\n✦ _{insight}_")
    return "\n".join(lines)
