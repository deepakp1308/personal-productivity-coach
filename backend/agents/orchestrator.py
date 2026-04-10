"""Pipeline orchestrator: classify -> analyze -> recommend -> judge -> publish."""

import logging
from datetime import datetime

from backend.storage import db
from backend.agents.classifier import classify_batch
from backend.agents.recommender import generate_recommendations
from backend.agents.judge import judge_batch
from backend.analysis.engine import compute_summary, generate_top_insight

logger = logging.getLogger(__name__)


def run_pipeline(week_iso: str = None, triggered_by: str = "manual",
                 use_llm: bool = False) -> dict:
    """Run the full analysis pipeline.

    Steps:
    1. Classify unclassified activities
    2. Compute analysis metrics
    3. Generate recommendations
    4. Run judge quality gate
    5. Persist results
    """
    if week_iso is None:
        week_iso = datetime.now().strftime("%G-W%V")

    run_id = db.start_pipeline_run(week_iso, triggered_by)
    logger.info(f"Pipeline run {run_id} started for {week_iso}")

    try:
        # Step 1: Classify
        unclassified = db.get_unclassified_activities()
        if unclassified:
            classifications = classify_batch(unclassified, use_llm=use_llm)
            db.insert_classifications_bulk(classifications)
            logger.info(f"Classified {len(classifications)} activities")
        else:
            classifications = []

        # Step 2: Analyze
        summary = compute_summary()
        top_insight = generate_top_insight(summary)

        # Step 3: Recommend
        rec_result = generate_recommendations(use_llm=use_llm)

        # Step 4: Judge
        judged_recs = judge_batch(rec_result["recommendations"])

        # Step 5: Persist
        published_count = 0
        for rec in judged_recs:
            if rec["status"] == "published":
                db.insert_recommendation(
                    week_iso=week_iso,
                    kind=rec["kind"],
                    action=rec["action"],
                    rationale=rec["rationale"],
                    evidence_ids=rec.get("evidence_ids", []),
                    judge_score=rec.get("judge_score"),
                    judge_reasoning=rec.get("judge_reasoning"),
                    status="published",
                )
                published_count += 1

        # Save weekly snapshot
        db.insert_weekly_snapshot(
            week_iso=week_iso,
            alignment_pct=summary["alignment_pct"],
            meeting_hours=summary["meeting_hours"],
            fragmentation_score=summary["fragmentation_score"],
            type_breakdown=summary["type_breakdown"],
            priority_breakdown=summary["priority_breakdown"],
            recommendations_json=[r for r in judged_recs if r["status"] == "published"],
            top_insight=top_insight,
        )

        db.update_pipeline_run(
            run_id,
            status="completed",
            activities_classified=len(classifications),
            recommendations_generated=published_count,
            completed_at=datetime.now().isoformat(),
        )

        logger.info(f"Pipeline run {run_id} completed: {len(classifications)} classified, {published_count} recommendations")

        return {
            "run_id": run_id,
            "week_iso": week_iso,
            "status": "completed",
            "activities_classified": len(classifications),
            "recommendations_generated": published_count,
            "alignment_pct": summary["alignment_pct"],
            "top_insight": top_insight,
        }

    except Exception as e:
        logger.error(f"Pipeline run {run_id} failed: {e}")
        db.update_pipeline_run(
            run_id,
            status="failed",
            error_message=str(e),
            completed_at=datetime.now().isoformat(),
        )
        raise
