"""SQLite storage with FTS5 for the Personal Productivity Coach."""

import json
import os
import sqlite3
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

_db_path: Optional[str] = None


def _get_db_path() -> str:
    global _db_path
    if _db_path is None:
        _db_path = os.environ.get("DB_PATH", os.path.join(os.path.dirname(__file__), "..", "coach.db"))
    return os.path.abspath(_db_path)


def set_db_path(path: str):
    """Override DB path (useful for testing)."""
    global _db_path
    _db_path = path


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(_get_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Create tables and FTS5 index if they don't exist."""
    conn = _get_conn()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS priorities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                weight REAL DEFAULT 1.0,
                pillar INTEGER DEFAULT 0,
                active INTEGER DEFAULT 1,
                quarter TEXT DEFAULT 'FY26-Q4',
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                source_id TEXT,
                title TEXT NOT NULL,
                summary TEXT DEFAULT '',
                duration_minutes INTEGER,
                participants TEXT DEFAULT '[]',
                channel TEXT DEFAULT '',
                url TEXT DEFAULT '',
                occurred_at TEXT NOT NULL,
                ingested_at TEXT NOT NULL DEFAULT (datetime('now')),
                UNIQUE(source, source_id)
            );

            CREATE TABLE IF NOT EXISTS activity_classifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                activity_id INTEGER NOT NULL REFERENCES activities(id),
                priority_id INTEGER REFERENCES priorities(id),
                priority_name TEXT,
                activity_type TEXT,
                leverage TEXT,
                confidence REAL,
                reasoning TEXT DEFAULT '',
                classified_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                week_iso TEXT NOT NULL,
                kind TEXT NOT NULL,
                action TEXT NOT NULL,
                rationale TEXT NOT NULL,
                evidence_ids TEXT DEFAULT '[]',
                judge_score REAL,
                judge_reasoning TEXT,
                status TEXT DEFAULT 'published',
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                channel TEXT DEFAULT '',
                related_priority TEXT,
                stakeholders TEXT DEFAULT '[]',
                evidence_activity_ids TEXT DEFAULT '[]',
                decided_at TEXT NOT NULL DEFAULT (datetime('now')),
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS open_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                urgency TEXT DEFAULT 'medium',
                owner TEXT DEFAULT '',
                channel TEXT DEFAULT '',
                related_priority TEXT,
                status TEXT DEFAULT 'open',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                resolved_at TEXT
            );

            CREATE TABLE IF NOT EXISTS focus_blocks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                label TEXT DEFAULT '',
                priority_name TEXT,
                started_at TEXT NOT NULL,
                ended_at TEXT,
                interrupted_by TEXT DEFAULT '[]',
                quality_score INTEGER
            );

            CREATE TABLE IF NOT EXISTS briefings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL UNIQUE,
                content_json TEXT NOT NULL,
                delivered_via TEXT DEFAULT '',
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS weekly_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                week_iso TEXT NOT NULL UNIQUE,
                alignment_pct REAL,
                meeting_hours REAL,
                fragmentation_score REAL,
                type_breakdown TEXT DEFAULT '{}',
                priority_breakdown TEXT DEFAULT '{}',
                recommendations_json TEXT DEFAULT '[]',
                top_insight TEXT DEFAULT '',
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS pipeline_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                week_iso TEXT NOT NULL,
                triggered_by TEXT NOT NULL,
                status TEXT DEFAULT 'running',
                activities_ingested INTEGER DEFAULT 0,
                activities_classified INTEGER DEFAULT 0,
                recommendations_generated INTEGER DEFAULT 0,
                error_message TEXT,
                started_at TEXT NOT NULL DEFAULT (datetime('now')),
                completed_at TEXT
            );

            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                context_json TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE INDEX IF NOT EXISTS idx_activities_source ON activities(source);
            CREATE INDEX IF NOT EXISTS idx_activities_occurred ON activities(occurred_at DESC);
            CREATE INDEX IF NOT EXISTS idx_classifications_activity ON activity_classifications(activity_id);
            CREATE INDEX IF NOT EXISTS idx_recommendations_week ON recommendations(week_iso);
            CREATE INDEX IF NOT EXISTS idx_decisions_priority ON decisions(related_priority);
            CREATE INDEX IF NOT EXISTS idx_questions_status ON open_questions(status);
            CREATE INDEX IF NOT EXISTS idx_questions_urgency ON open_questions(urgency);
        """)
        conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS activities_fts
            USING fts5(title, summary, source, content=activities, content_rowid=id)
        """)
        conn.commit()
        logger.info(f"Database initialized at {_get_db_path()}")
    finally:
        conn.close()


def reset_db():
    """Drop all tables and reinitialize."""
    path = _get_db_path()
    if os.path.exists(path):
        os.remove(path)
        logger.info(f"Removed existing database at {path}")
    # Also remove WAL files
    for suffix in ("-shm", "-wal"):
        p = path + suffix
        if os.path.exists(p):
            os.remove(p)
    init_db()


# ── Priorities ───────────────────────────────────────────────────────────────

def insert_priority(name: str, description: str = "", weight: float = 1.0, pillar: int = 0) -> int:
    conn = _get_conn()
    try:
        cur = conn.execute(
            "INSERT INTO priorities (name, description, weight, pillar) VALUES (?, ?, ?, ?)",
            (name, description, weight, pillar),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_priorities(active_only: bool = True) -> list[dict]:
    conn = _get_conn()
    try:
        q = "SELECT * FROM priorities"
        if active_only:
            q += " WHERE active = 1"
        q += " ORDER BY weight DESC"
        rows = conn.execute(q).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def update_priority(id: int, **kwargs):
    conn = _get_conn()
    try:
        sets = []
        vals = []
        for k, v in kwargs.items():
            if k in ("name", "description", "weight", "active", "pillar"):
                sets.append(f"{k} = ?")
                vals.append(v)
        if not sets:
            return
        sets.append("updated_at = datetime('now')")
        vals.append(id)
        conn.execute(f"UPDATE priorities SET {', '.join(sets)} WHERE id = ?", vals)
        conn.commit()
    finally:
        conn.close()


# ── Activities ───────────────────────────────────────────────────────────────

def insert_activity(source: str, title: str, occurred_at: str,
                    source_id: str = None, summary: str = "", duration_minutes: int = None,
                    participants: list[str] = None, channel: str = "", url: str = "") -> Optional[int]:
    conn = _get_conn()
    try:
        cur = conn.execute(
            """INSERT OR IGNORE INTO activities
               (source, source_id, title, summary, duration_minutes, participants, channel, url, occurred_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (source, source_id, title, summary, duration_minutes,
             json.dumps(participants or []), channel, url, occurred_at),
        )
        conn.commit()
        if cur.lastrowid:
            conn.execute(
                "INSERT INTO activities_fts(rowid, title, summary, source) VALUES (?, ?, ?, ?)",
                (cur.lastrowid, title, summary, source),
            )
            conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def insert_activities_bulk(rows: list[dict]) -> int:
    """Bulk insert activities. Returns count inserted."""
    conn = _get_conn()
    count = 0
    try:
        for r in rows:
            cur = conn.execute(
                """INSERT OR IGNORE INTO activities
                   (source, source_id, title, summary, duration_minutes, participants, channel, url, occurred_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (r["source"], r.get("source_id"), r["title"],
                 r.get("summary", ""), r.get("duration_minutes"),
                 json.dumps(r.get("participants", [])), r.get("channel", ""), r.get("url", ""), r["occurred_at"]),
            )
            if cur.lastrowid:
                conn.execute(
                    "INSERT INTO activities_fts(rowid, title, summary, source) VALUES (?, ?, ?, ?)",
                    (cur.lastrowid, r["title"], r.get("summary", ""), r["source"]),
                )
                count += 1
        conn.commit()
        return count
    finally:
        conn.close()


def get_activities(source: str = None, priority_name: str = None,
                   activity_type: str = None,
                   date_from: str = None, date_to: str = None,
                   limit: int = 200, offset: int = 0) -> list[dict]:
    conn = _get_conn()
    try:
        q = """SELECT a.*, ac.priority_name, ac.activity_type, ac.leverage, ac.confidence, ac.reasoning
               FROM activities a
               LEFT JOIN activity_classifications ac ON ac.activity_id = a.id"""
        wheres = []
        params = []
        if source:
            wheres.append("a.source = ?")
            params.append(source)
        if priority_name:
            wheres.append("ac.priority_name = ?")
            params.append(priority_name)
        if activity_type:
            wheres.append("ac.activity_type = ?")
            params.append(activity_type)
        if date_from:
            wheres.append("a.occurred_at >= ?")
            params.append(date_from)
        if date_to:
            wheres.append("a.occurred_at <= ?")
            params.append(date_to)
        if wheres:
            q += " WHERE " + " AND ".join(wheres)
        q += " ORDER BY a.occurred_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        rows = conn.execute(q, params).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_activity(activity_id: int) -> Optional[dict]:
    conn = _get_conn()
    try:
        row = conn.execute(
            """SELECT a.*, ac.priority_name, ac.activity_type, ac.leverage, ac.confidence, ac.reasoning
               FROM activities a
               LEFT JOIN activity_classifications ac ON ac.activity_id = a.id
               WHERE a.id = ?""",
            (activity_id,),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_activity_count() -> int:
    conn = _get_conn()
    try:
        return conn.execute("SELECT COUNT(*) as cnt FROM activities").fetchone()["cnt"]
    finally:
        conn.close()


def search_activities_fts(query: str, limit: int = 50) -> list[dict]:
    """Full-text search using FTS5."""
    conn = _get_conn()
    try:
        rows = conn.execute(
            """SELECT a.*, ac.priority_name, ac.activity_type, ac.leverage, ac.confidence
               FROM activities_fts fts
               JOIN activities a ON a.id = fts.rowid
               LEFT JOIN activity_classifications ac ON ac.activity_id = a.id
               WHERE activities_fts MATCH ?
               ORDER BY rank
               LIMIT ?""",
            (query, limit),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# ── Classifications ──────────────────────────────────────────────────────────

def insert_classification(activity_id: int, priority_id: int = None, priority_name: str = None,
                          activity_type: str = None, leverage: str = None,
                          confidence: float = None, reasoning: str = "") -> int:
    conn = _get_conn()
    try:
        cur = conn.execute(
            """INSERT INTO activity_classifications
               (activity_id, priority_id, priority_name, activity_type, leverage, confidence, reasoning)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (activity_id, priority_id, priority_name, activity_type, leverage, confidence, reasoning),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def insert_classifications_bulk(rows: list[dict]) -> int:
    conn = _get_conn()
    count = 0
    try:
        for r in rows:
            conn.execute(
                """INSERT INTO activity_classifications
                   (activity_id, priority_id, priority_name, activity_type, leverage, confidence, reasoning)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (r["activity_id"], r.get("priority_id"), r.get("priority_name"),
                 r.get("activity_type"), r.get("leverage"), r.get("confidence"), r.get("reasoning", "")),
            )
            count += 1
        conn.commit()
        return count
    finally:
        conn.close()


def get_unclassified_activities(limit: int = 500) -> list[dict]:
    conn = _get_conn()
    try:
        rows = conn.execute(
            """SELECT a.* FROM activities a
               LEFT JOIN activity_classifications ac ON ac.activity_id = a.id
               WHERE ac.id IS NULL
               ORDER BY a.occurred_at DESC
               LIMIT ?""",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# ── Recommendations ──────────────────────────────────────────────────────────

def insert_recommendation(week_iso: str, kind: str, action: str, rationale: str,
                          evidence_ids: list[int], judge_score: float = None,
                          judge_reasoning: str = None, status: str = "published") -> int:
    conn = _get_conn()
    try:
        cur = conn.execute(
            """INSERT INTO recommendations
               (week_iso, kind, action, rationale, evidence_ids, judge_score, judge_reasoning, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (week_iso, kind, action, rationale,
             json.dumps(evidence_ids), judge_score, judge_reasoning, status),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_recommendations(week_iso: str = None, status: str = None, limit: int = 50) -> list[dict]:
    conn = _get_conn()
    try:
        q = "SELECT * FROM recommendations"
        wheres = []
        params = []
        if week_iso:
            wheres.append("week_iso = ?")
            params.append(week_iso)
        if status:
            wheres.append("status = ?")
            params.append(status)
        if wheres:
            q += " WHERE " + " AND ".join(wheres)
        q += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        rows = conn.execute(q, params).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["evidence_ids"] = json.loads(d.get("evidence_ids") or "[]")
            result.append(d)
        return result
    finally:
        conn.close()


def get_latest_week_iso() -> Optional[str]:
    conn = _get_conn()
    try:
        row = conn.execute(
            "SELECT DISTINCT week_iso FROM recommendations ORDER BY week_iso DESC LIMIT 1"
        ).fetchone()
        return row["week_iso"] if row else None
    finally:
        conn.close()


# ── Decisions ────────────────────────────────────────────────────────────────

def insert_decision(description: str, channel: str = "", related_priority: str = None,
                    stakeholders: list[str] = None, evidence_activity_ids: list[int] = None,
                    decided_at: str = None) -> int:
    conn = _get_conn()
    try:
        cur = conn.execute(
            """INSERT INTO decisions
               (description, channel, related_priority, stakeholders, evidence_activity_ids, decided_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (description, channel, related_priority,
             json.dumps(stakeholders or []), json.dumps(evidence_activity_ids or []),
             decided_at or datetime.now().isoformat()),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_decisions(related_priority: str = None, limit: int = 50) -> list[dict]:
    conn = _get_conn()
    try:
        q = "SELECT * FROM decisions"
        params = []
        if related_priority:
            q += " WHERE related_priority = ?"
            params.append(related_priority)
        q += " ORDER BY decided_at DESC LIMIT ?"
        params.append(limit)
        rows = conn.execute(q, params).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["stakeholders"] = json.loads(d.get("stakeholders") or "[]")
            d["evidence_activity_ids"] = json.loads(d.get("evidence_activity_ids") or "[]")
            result.append(d)
        return result
    finally:
        conn.close()


# ── Open Questions ───────────────────────────────────────────────────────────

def insert_open_question(description: str, urgency: str = "medium", owner: str = "",
                         channel: str = "", related_priority: str = None) -> int:
    conn = _get_conn()
    try:
        cur = conn.execute(
            """INSERT INTO open_questions (description, urgency, owner, channel, related_priority)
               VALUES (?, ?, ?, ?, ?)""",
            (description, urgency, owner, channel, related_priority),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_open_questions(status: str = None, urgency: str = None, limit: int = 50) -> list[dict]:
    conn = _get_conn()
    try:
        q = "SELECT * FROM open_questions"
        wheres = []
        params = []
        if status:
            wheres.append("status = ?")
            params.append(status)
        if urgency:
            wheres.append("urgency = ?")
            params.append(urgency)
        if wheres:
            q += " WHERE " + " AND ".join(wheres)
        q += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        rows = conn.execute(q, params).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def update_question_status(question_id: int, status: str):
    conn = _get_conn()
    try:
        resolved_at = datetime.now().isoformat() if status == "resolved" else None
        conn.execute(
            "UPDATE open_questions SET status = ?, resolved_at = ? WHERE id = ?",
            (status, resolved_at, question_id),
        )
        conn.commit()
    finally:
        conn.close()


# ── Briefings ────────────────────────────────────────────────────────────────

def insert_briefing(date: str, content_json: str, delivered_via: str = "") -> int:
    conn = _get_conn()
    try:
        cur = conn.execute(
            "INSERT OR REPLACE INTO briefings (date, content_json, delivered_via) VALUES (?, ?, ?)",
            (date, content_json, delivered_via),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_briefing(date: str) -> Optional[dict]:
    conn = _get_conn()
    try:
        row = conn.execute("SELECT * FROM briefings WHERE date = ?", (date,)).fetchone()
        if row:
            d = dict(row)
            d["content"] = json.loads(d["content_json"])
            return d
        return None
    finally:
        conn.close()


def get_latest_briefing() -> Optional[dict]:
    conn = _get_conn()
    try:
        row = conn.execute("SELECT * FROM briefings ORDER BY date DESC LIMIT 1").fetchone()
        if row:
            d = dict(row)
            d["content"] = json.loads(d["content_json"])
            return d
        return None
    finally:
        conn.close()


# ── Weekly Snapshots ─────────────────────────────────────────────────────────

def insert_weekly_snapshot(week_iso: str, alignment_pct: float, meeting_hours: float,
                           fragmentation_score: float, type_breakdown: dict,
                           priority_breakdown: dict, recommendations_json: list,
                           top_insight: str = "") -> int:
    conn = _get_conn()
    try:
        cur = conn.execute(
            """INSERT OR REPLACE INTO weekly_snapshots
               (week_iso, alignment_pct, meeting_hours, fragmentation_score,
                type_breakdown, priority_breakdown, recommendations_json, top_insight)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (week_iso, alignment_pct, meeting_hours, fragmentation_score,
             json.dumps(type_breakdown), json.dumps(priority_breakdown),
             json.dumps(recommendations_json), top_insight),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_weekly_snapshots(limit: int = 10) -> list[dict]:
    conn = _get_conn()
    try:
        rows = conn.execute(
            "SELECT * FROM weekly_snapshots ORDER BY week_iso DESC LIMIT ?", (limit,)
        ).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["type_breakdown"] = json.loads(d.get("type_breakdown") or "{}")
            d["priority_breakdown"] = json.loads(d.get("priority_breakdown") or "{}")
            d["recommendations_json"] = json.loads(d.get("recommendations_json") or "[]")
            result.append(d)
        return result
    finally:
        conn.close()


# ── Pipeline runs ────────────────────────────────────────────────────────────

def start_pipeline_run(week_iso: str, triggered_by: str) -> int:
    conn = _get_conn()
    try:
        cur = conn.execute(
            "INSERT INTO pipeline_runs (week_iso, triggered_by) VALUES (?, ?)",
            (week_iso, triggered_by),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def update_pipeline_run(run_id: int, **kwargs):
    conn = _get_conn()
    try:
        sets = []
        vals = []
        for k, v in kwargs.items():
            if k in ("status", "activities_ingested", "activities_classified",
                      "recommendations_generated", "error_message", "completed_at"):
                sets.append(f"{k} = ?")
                vals.append(v)
        if not sets:
            return
        vals.append(run_id)
        conn.execute(f"UPDATE pipeline_runs SET {', '.join(sets)} WHERE id = ?", vals)
        conn.commit()
    finally:
        conn.close()


# ── Chat ─────────────────────────────────────────────────────────────────────

def save_chat_message(session_id: str, role: str, content: str, context_json: str = None):
    conn = _get_conn()
    try:
        conn.execute(
            "INSERT INTO chat_messages (session_id, role, content, context_json) VALUES (?, ?, ?, ?)",
            (session_id, role, content, context_json),
        )
        conn.commit()
    finally:
        conn.close()


def get_chat_history(session_id: str, limit: int = 20) -> list[dict]:
    conn = _get_conn()
    try:
        rows = conn.execute(
            "SELECT role, content FROM chat_messages WHERE session_id = ? ORDER BY created_at LIMIT ?",
            (session_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# ── Generic SQL (for chat tool_use) ──────────────────────────────────────────

def run_read_only_sql(query: str, params: list = None) -> list[dict]:
    """Execute a read-only SQL query. Used by the chat agent's tool_use."""
    q = query.strip().upper()
    if not q.startswith("SELECT"):
        raise ValueError("Only SELECT queries are allowed")
    conn = _get_conn()
    try:
        rows = conn.execute(query, params or []).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
