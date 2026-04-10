"""Tiered activity classifier: rule-based fast path + LLM for ambiguous."""

import re
import json
import logging
from typing import Optional

from backend.config import RULE_BASED_PATTERNS, DEFAULT_PRIORITIES
from backend.storage import db

logger = logging.getLogger(__name__)

CLASSIFIER_SYSTEM = """You are classifying a single work activity for a PM Lead.
This person leads the Reporting & Analytics team at Mailchimp/Intuit.

Current priorities: {priorities_json}

Return JSON ONLY matching this exact schema:
{{
  "type": "Strategy|Discovery|Execution|Stakeholder|InternalOps|Reactive|LowValue",
  "priority": "<exact priority name or 'Other'>",
  "leverage": "High|Medium|Low",
  "confidence": 0.0-1.0,
  "reasoning": "<1 sentence>"
}}"""


def classify_activity(activity: dict, priorities: list[dict] = None, use_llm: bool = False) -> dict:
    """Classify a single activity. Returns classification dict.

    Uses rule-based fast path first, falls back to LLM for ambiguous cases.
    """
    if priorities is None:
        priorities = db.get_priorities()

    title = activity.get("title", "")
    summary = activity.get("summary", "")
    text = f"{title} {summary}"

    # ── Rule-based fast path ─────────────────────────────────────────
    rule_type = None
    rule_priority = None

    for pattern, act_type, pri_hint in RULE_BASED_PATTERNS:
        if re.search(pattern, text):
            if act_type and not rule_type:
                rule_type = act_type
            if pri_hint and not rule_priority:
                rule_priority = pri_hint

    # If both type and priority resolved, skip LLM
    if rule_type and rule_priority:
        return {
            "activity_id": activity["id"],
            "priority_name": rule_priority,
            "priority_id": _find_priority_id(rule_priority, priorities),
            "activity_type": rule_type,
            "leverage": _guess_leverage(text),
            "confidence": 0.85,
            "reasoning": f"Rule-based: matched patterns for {rule_type}/{rule_priority}",
        }

    # ── LLM classification (optional) ────────────────────────────────
    if use_llm:
        try:
            from backend.llm.claude import call_structured
            from backend.storage.models import ClassifierOutput

            priorities_json = json.dumps([{"name": p["name"], "description": p.get("description", "")}
                                           for p in priorities])
            system = CLASSIFIER_SYSTEM.format(priorities_json=priorities_json)

            activity_json = json.dumps({
                "source": activity.get("source", ""),
                "title": title,
                "summary": summary[:500],
                "duration_minutes": activity.get("duration_minutes"),
            })

            result = call_structured(
                stage="classify",
                system=system,
                user_message=f"Activity: {activity_json}",
                output_model=ClassifierOutput,
                max_tokens=512,
            )

            return {
                "activity_id": activity["id"],
                "priority_name": result.priority,
                "priority_id": _find_priority_id(result.priority, priorities),
                "activity_type": result.type.value,
                "leverage": result.leverage.value,
                "confidence": result.confidence,
                "reasoning": result.reasoning,
            }
        except Exception as e:
            logger.warning(f"LLM classification failed for activity {activity.get('id')}: {e}")

    # ── Fallback to rule-based partial result ────────────────────────
    return {
        "activity_id": activity.get("id"),
        "priority_name": rule_priority or "Other",
        "priority_id": _find_priority_id(rule_priority or "Other", priorities),
        "activity_type": rule_type or "Execution",
        "leverage": _guess_leverage(text),
        "confidence": 0.7 if (rule_type or rule_priority) else 0.5,
        "reasoning": f"Rule-based: {'partial match' if (rule_type or rule_priority) else 'no match, defaulting to Execution/Other'}",
    }


def classify_batch(activities: list[dict], use_llm: bool = False) -> list[dict]:
    """Classify a batch of activities."""
    priorities = db.get_priorities()
    return [classify_activity(act, priorities, use_llm=use_llm) for act in activities]


def _find_priority_id(name: str, priorities: list[dict]) -> Optional[int]:
    for p in priorities:
        if p["name"] == name:
            return p.get("id")
    return None


def _guess_leverage(text: str) -> str:
    text_lower = text.lower()
    if any(w in text_lower for w in ["shipped", "completed", "done", "approved", "merged", "decision", "unblocked", "launched", "ga"]):
        return "High"
    if any(w in text_lower for w in ["blocked", "waiting", "pending", "tbd", "tentative", "deferred"]):
        return "Low"
    return "Medium"
