"""FastAPI app and CLI entry point for the Personal Productivity Coach."""

import argparse
import logging
import json
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from backend.storage import db
from backend.agents.orchestrator import run_pipeline
from backend.agents.qa_agent import run_qa_suite, format_qa_report
from backend.analysis import engine
from backend.api.chat import handle_chat
from backend import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    # Seed priorities if empty
    priorities = db.get_priorities()
    if not priorities:
        for p in config.DEFAULT_PRIORITIES:
            db.insert_priority(p["name"], p.get("description", ""), p["weight"], p.get("pillar", 0))
        logger.info("Seeded default priorities")
    yield


app = FastAPI(title="Personal Productivity Coach", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Dashboard / Briefing ─────────────────────────────────────────────────────

@app.get("/api/dashboard")
def api_dashboard():
    summary = engine.compute_this_week()
    recs = db.get_recommendations(status="published", limit=6)
    anomalies = engine.detect_anomalies()
    decisions = db.get_decisions(limit=5)
    open_qs = db.get_open_questions(status="open", limit=10)
    insight = engine.generate_top_insight(summary)

    return {
        **summary,
        "top_insight": insight,
        "recommendations": recs,
        "anomalies": anomalies,
        "recent_decisions": decisions,
        "open_questions": open_qs,
    }


@app.get("/api/briefing")
def api_briefing(date: str = None):
    if date:
        briefing = db.get_briefing(date)
    else:
        briefing = db.get_latest_briefing()
    if briefing:
        return briefing
    # Generate live if no cached briefing
    return api_dashboard()


# ── Metrics ──────────────────────────────────────────────────────────────────

@app.get("/api/metrics")
def api_metrics(period: str = "this_week"):
    if period == "today":
        return engine.compute_today_focus()
    elif period == "last_week":
        return engine.compute_last_week()
    elif period == "this_month":
        return engine.compute_summary()
    return engine.compute_this_week()


@app.get("/api/trends")
def api_trends(weeks: int = 4):
    return engine.compute_weekly_trends(weeks)


@app.get("/api/anomalies")
def api_anomalies():
    return engine.detect_anomalies()


# ── Activities ───────────────────────────────────────────────────────────────

@app.get("/api/activities")
def api_activities(source: str = None, priority_name: str = None,
                   activity_type: str = None,
                   date_from: str = None, date_to: str = None,
                   limit: int = 200, offset: int = 0):
    return db.get_activities(source=source, priority_name=priority_name,
                             activity_type=activity_type,
                             date_from=date_from, date_to=date_to,
                             limit=limit, offset=offset)


@app.get("/api/activities/search")
def api_search_activities(q: str = Query(..., min_length=2), limit: int = 50):
    return db.search_activities_fts(q, limit)


# ── Priorities ───────────────────────────────────────────────────────────────

@app.get("/api/priorities")
def api_priorities():
    return db.get_priorities()


class PriorityUpdate(BaseModel):
    name: str = None
    description: str = None
    weight: float = None
    active: int = None


@app.put("/api/priorities/{priority_id}")
def api_update_priority(priority_id: int, body: PriorityUpdate):
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    db.update_priority(priority_id, **updates)
    return {"status": "updated"}


# ── Recommendations ──────────────────────────────────────────────────────────

@app.get("/api/recommendations")
def api_recommendations(week_iso: str = None, limit: int = 50):
    return db.get_recommendations(week_iso=week_iso, limit=limit)


# ── Decisions ────────────────────────────────────────────────────────────────

@app.get("/api/decisions")
def api_decisions(related_priority: str = None, limit: int = 50):
    return db.get_decisions(related_priority=related_priority, limit=limit)


class DecisionCreate(BaseModel):
    description: str
    channel: str = ""
    related_priority: str = None
    stakeholders: list[str] = []


@app.post("/api/decisions")
def api_create_decision(body: DecisionCreate):
    did = db.insert_decision(body.description, body.channel, body.related_priority, body.stakeholders)
    return {"id": did, "status": "created"}


# ── Open Questions ───────────────────────────────────────────────────────────

@app.get("/api/questions")
def api_questions(status: str = None, urgency: str = None, limit: int = 50):
    return db.get_open_questions(status=status, urgency=urgency, limit=limit)


class QuestionCreate(BaseModel):
    description: str
    urgency: str = "medium"
    owner: str = ""
    channel: str = ""
    related_priority: str = None


@app.post("/api/questions")
def api_create_question(body: QuestionCreate):
    qid = db.insert_open_question(body.description, body.urgency, body.owner, body.channel, body.related_priority)
    return {"id": qid, "status": "created"}


class QuestionStatusUpdate(BaseModel):
    status: str


@app.put("/api/questions/{question_id}/status")
def api_update_question_status(question_id: int, body: QuestionStatusUpdate):
    db.update_question_status(question_id, body.status)
    return {"status": "updated"}


# ── Weekly Snapshots ─────────────────────────────────────────────────────────

@app.get("/api/weekly")
def api_weekly_snapshots(limit: int = 10):
    return db.get_weekly_snapshots(limit)


# ── Chat ─────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    session_id: str = None


@app.post("/api/chat")
def api_chat(body: ChatRequest):
    return handle_chat(body.message, body.session_id)


# ── Pipeline ─────────────────────────────────────────────────────────────────

@app.post("/api/pipeline/run")
def api_run_pipeline(use_llm: bool = False):
    result = run_pipeline(use_llm=use_llm)
    return result


# ── QA Agent ─────────────────────────────────────────────────────────────────

@app.get("/api/qa")
def api_qa():
    return run_qa_suite()

@app.get("/api/qa/report")
def api_qa_report():
    result = run_qa_suite()
    return {"report": format_qa_report(result), **result}


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Personal Productivity Coach")
    parser.add_argument("--seed", action="store_true", help="Seed with sample data")
    parser.add_argument("--run-pipeline", action="store_true", help="Run analysis pipeline")
    parser.add_argument("--serve", action="store_true", help="Start API server")
    parser.add_argument("--use-llm", action="store_true", help="Use LLM for classification/recommendations")
    parser.add_argument("--port", type=int, default=config.API_PORT, help="Server port")
    args = parser.parse_args()

    db.init_db()

    # Seed priorities if empty
    priorities = db.get_priorities()
    if not priorities:
        for p in config.DEFAULT_PRIORITIES:
            db.insert_priority(p["name"], p.get("description", ""), p["weight"], p.get("pillar", 0))
        logger.info("Seeded default priorities")

    if args.seed:
        from backend.seed.seed_data import seed
        seed()
        logger.info("Seed data loaded")

    if args.run_pipeline:
        result = run_pipeline(use_llm=args.use_llm)
        logger.info(f"Pipeline result: {json.dumps(result, indent=2)}")

    if args.serve:
        import uvicorn
        uvicorn.run(app, host=config.API_HOST, port=args.port)


if __name__ == "__main__":
    main()
