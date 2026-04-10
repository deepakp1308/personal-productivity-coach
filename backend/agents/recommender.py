"""Recommendation generator: produces Accelerate/Cut/Redirect coaching advice."""

import json
import logging

from backend.storage import db
from backend.analysis import engine

logger = logging.getLogger(__name__)

RECOMMENDER_SYSTEM = """You are a personal productivity coach for a PM Lead at Intuit/Mailchimp.
Your job is to generate 3 coaching recommendations based on the PM's actual activity data.

The PM's current priorities and their target weights:
{priorities_json}

The PM's summary for this period:
{summary_json}

Evidence activities (recent, classified):
{evidence_json}

Generate exactly 3 recommendations in this JSON format:
{{
  "summary": "2-3 sentences on time allocation patterns",
  "alignment_pct": <number 0-100>,
  "recommendations": [
    {{
      "kind": "Accelerate|Cut|Redirect",
      "action": "specific actionable advice",
      "rationale": "why, citing evidence",
      "evidence_ids": [<activity ids that support this>]
    }}
  ],
  "uncertainty_flags": ["any caveats"]
}}

Rules:
- Accelerate: something they should do MORE of (already working, needs doubling down)
- Cut: something they should STOP or reduce (low value, off-priority)
- Redirect: something they should CHANGE approach on (right priority, wrong execution)
- Every recommendation MUST cite specific evidence_ids from the activity list
- Tone: coaching, not judging. Respect invisible work.
- Be specific: name channels, people, or activity types."""


def generate_recommendations(date_from: str = None, date_to: str = None,
                              use_llm: bool = False) -> dict:
    """Generate coaching recommendations for the given period."""
    summary = engine.compute_summary(date_from, date_to)
    activities = db.get_activities(date_from=date_from, date_to=date_to, limit=100)
    priorities = db.get_priorities()

    if use_llm:
        return _generate_with_llm(summary, activities, priorities)
    return _generate_rule_based(summary, activities, priorities)


def _generate_rule_based(summary: dict, activities: list[dict], priorities: list[dict]) -> dict:
    """Generate recommendations using heuristics (no LLM needed)."""
    recs = []
    evidence_map = {}
    for a in activities:
        pname = a.get("priority_name", "Other")
        if pname not in evidence_map:
            evidence_map[pname] = []
        evidence_map[pname].append(a.get("id"))

    # Find under-invested priority (Accelerate)
    for p in priorities:
        target = p["weight"] * 100
        actual = summary["priority_breakdown"].get(p["name"], 0)
        if actual < target * 0.6:
            ids = evidence_map.get(p["name"], [])[:3]
            recs.append({
                "kind": "Accelerate",
                "action": f"Increase time on '{p['name']}' — currently at {actual:.0f}% vs. target {target:.0f}%.",
                "rationale": f"This pillar needs more attention to hit Q4 goals. Only {len(evidence_map.get(p['name'], []))} activities this period.",
                "evidence_ids": ids,
            })
            break

    # Find time sinks (Cut)
    low_value = [a for a in activities if a.get("activity_type") == "LowValue"]
    reactive = [a for a in activities if a.get("activity_type") == "Reactive"]
    cut_activities = low_value + reactive
    if cut_activities:
        ids = [a["id"] for a in cut_activities[:3]]
        recs.append({
            "kind": "Cut",
            "action": f"Reduce time on {'low-value' if low_value else 'reactive'} work — {len(cut_activities)} activities this period.",
            "rationale": f"These activities don't map to your Q4 pillars. Consider delegating or declining.",
            "evidence_ids": ids,
        })

    # Find redirect opportunity
    other_activities = [a for a in activities if a.get("priority_name") == "Other" and a.get("activity_type") not in ("LowValue", "Reactive")]
    if other_activities:
        ids = [a["id"] for a in other_activities[:3]]
        recs.append({
            "kind": "Redirect",
            "action": f"{len(other_activities)} activities classified as 'Other' — review if any align to your pillars.",
            "rationale": "Some of these may be priority-aligned but not matching classification patterns. Consider reclassifying or delegating.",
            "evidence_ids": ids,
        })

    # Fill to 3 if needed
    if len(recs) < 3 and summary["meeting_hours"] > 10:
        recs.append({
            "kind": "Redirect",
            "action": f"Review your {summary['meeting_hours']}h of meetings — can any be async?",
            "rationale": "High meeting load reduces deep work time for strategy and execution.",
            "evidence_ids": [],
        })

    while len(recs) < 3:
        recs.append({
            "kind": "Accelerate",
            "action": f"Continue investing in '{summary.get('top_priority', 'your top priority')}'.",
            "rationale": "You're making good progress — maintain momentum.",
            "evidence_ids": [],
        })

    return {
        "summary": f"This period: {summary['total_activities']} activities, {summary['alignment_pct']:.0f}% aligned to priorities, {summary['meeting_hours']}h meetings.",
        "alignment_pct": summary["alignment_pct"],
        "recommendations": recs[:3],
        "uncertainty_flags": [],
    }


def _generate_with_llm(summary: dict, activities: list[dict], priorities: list[dict]) -> dict:
    """Generate recommendations using Claude."""
    from backend.llm.claude import call_structured
    from backend.storage.models import BriefingOutput

    priorities_json = json.dumps([{"name": p["name"], "weight": p["weight"], "description": p.get("description", "")}
                                   for p in priorities])
    summary_json = json.dumps(summary, default=str)
    evidence_json = json.dumps([{"id": a.get("id"), "title": a.get("title", ""), "source": a.get("source", ""),
                                  "priority_name": a.get("priority_name", ""), "activity_type": a.get("activity_type", "")}
                                 for a in activities[:50]])

    system = RECOMMENDER_SYSTEM.format(
        priorities_json=priorities_json,
        summary_json=summary_json,
        evidence_json=evidence_json,
    )

    result = call_structured(
        stage="recommend",
        system=system,
        user_message="Generate 3 coaching recommendations based on my activity data.",
        output_model=BriefingOutput,
        max_tokens=2048,
    )

    return {
        "summary": result.summary,
        "alignment_pct": result.alignment_pct,
        "recommendations": [r.model_dump() for r in result.recommendations],
        "uncertainty_flags": result.uncertainty_flags,
    }
