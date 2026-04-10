"""Judge layer: quality gate for recommendations."""

import json
import logging

logger = logging.getLogger(__name__)


def judge_recommendation(rec: dict, activities: list[dict] = None) -> dict:
    """Score a recommendation for quality. Returns scored rec with judge fields.

    Scores:
    - faithfulness (1-3): Does the recommendation follow from evidence?
    - priority_fit (1-3): Does it align with stated priorities?
    - specificity (1-3): Is the action specific and actionable?

    Hard blocks: any score = 1 -> status = 'blocked'
    """
    evidence_ids = rec.get("evidence_ids", [])
    action = rec.get("action", "")
    rationale = rec.get("rationale", "")
    kind = rec.get("kind", "")

    # ── Faithfulness ─────────────────────────────────────────────────
    faithfulness = 2  # default: acceptable
    if evidence_ids and len(evidence_ids) >= 2:
        faithfulness = 3  # strong evidence
    elif not evidence_ids:
        faithfulness = 1  # no evidence cited

    # ── Priority Fit ─────────────────────────────────────────────────
    priority_fit = 2
    priority_keywords = ["pillar", "priority", "q4", "target", "alignment", "analytics agent",
                          "bi platform", "data foundation", "omni", "l2c", "whatsapp", "dsb"]
    matched = sum(1 for kw in priority_keywords if kw.lower() in (action + rationale).lower())
    if matched >= 2:
        priority_fit = 3
    elif matched == 0:
        priority_fit = 1

    # ── Specificity ──────────────────────────────────────────────────
    specificity = 2
    if len(action) > 50 and any(c in action for c in ["'", '"', "%", "h ", "activities"]):
        specificity = 3  # detailed and specific
    elif len(action) < 20:
        specificity = 1  # too vague

    # ── Judge score (0-5 scale) ──────────────────────────────────────
    total = faithfulness + priority_fit + specificity  # 3-9
    judge_score = round(total / 9 * 5, 1)

    # Hard block check
    blocked = faithfulness == 1 or priority_fit == 1 or specificity == 1
    status = "blocked" if blocked else "published"

    reasoning_parts = []
    if faithfulness < 3:
        reasoning_parts.append(f"faithfulness={faithfulness}/3")
    if priority_fit < 3:
        reasoning_parts.append(f"priority_fit={priority_fit}/3")
    if specificity < 3:
        reasoning_parts.append(f"specificity={specificity}/3")

    reasoning = "; ".join(reasoning_parts) if reasoning_parts else "All checks passed"
    if blocked:
        reasoning = f"BLOCKED: {reasoning}"

    return {
        **rec,
        "judge_score": judge_score,
        "judge_reasoning": reasoning,
        "status": status,
        "_scores": {
            "faithfulness": faithfulness,
            "priority_fit": priority_fit,
            "specificity": specificity,
        },
    }


def judge_batch(recommendations: list[dict], activities: list[dict] = None) -> list[dict]:
    """Judge a batch of recommendations."""
    return [judge_recommendation(rec, activities) for rec in recommendations]
