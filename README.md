# Personal Productivity Coach

A self-assist productivity coaching agent for PM leads. Built for Deepak Prabhakaran,
who leads the Reporting & Analytics team at Intuit/Mailchimp. The agent ingests
real work signals from Slack and Gmail, classifies activities against FY26 Q4
strategic pillars, and delivers weekly coaching briefings with evidence-grounded
recommendations.

Forked from the team-level PM agent (`pm-productivity-agent-demo`) and adapted
for single-user personal coaching. Priority framework based on the R&A Q4
Roadmap DPV1.3.

---

## Table of Contents

- [Architecture](#architecture)
- [Pipeline](#pipeline)
- [Classification System](#classification-system)
- [Analysis Engine](#analysis-engine)
- [Recommendation Engine](#recommendation-engine)
- [Chat Interface](#chat-interface)
- [Frontend Pages](#frontend-pages)
- [FY26 Q4 Strategic Pillars](#fy26-q4-strategic-pillars)
- [Key Stakeholders Tracked](#key-stakeholders-tracked)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Running Tests](#running-tests)
- [Deployment](#deployment)
- [Tech Stack](#tech-stack)

---

## Architecture

```
+----------------------------------------------------------------------+
|                        Data Sources (MCP)                            |
|  +------------+   +-------------+   +-----------------------------+  |
|  |  Slack MCP |   |  Gmail MCP  |   | Google Calendar (via email) |  |
|  | messages   |   |  emails     |   | meeting invites extracted   |  |
|  | DMs        |   |  calendar   |   | from email metadata        |  |
|  | mentions   |   |  invites    |   |                             |  |
|  +-----+------+   +------+------+   +--------------+--------------+  |
|        |                 |                          |                 |
+----------------------------------------------------------------------+
         |                 |                          |
         v                 v                          v
+----------------------------------------------------------------------+
|                     6-Phase Pipeline                                 |
|                                                                      |
|  +----------+  +----------+  +---------+  +-----------+  +--------+  |
|  |  Ingest  +->+ Classify +->+ Analyze +->+ Recommend +->+ Judge  |  |
|  +----------+  +----------+  +---------+  +-----------+  +---+----+  |
|                                                              |       |
|                                                              v       |
|                                                         +---------+  |
|                                                         | Publish |  |
|                                                         +---------+  |
+----------------------------------------------------------------------+
         |                                                     |
         v                                                     v
+------------------+                              +---------------------+
|  SQLite + FTS5   |                              |  Static JSON Export |
|  coach.db        |                              |  public/api/*.json  |
+------------------+                              +---------------------+
         |                                                     |
         v                                                     v
+------------------+                              +---------------------+
|  FastAPI Backend |                              |  Next.js 15 Static  |
|  localhost:8001  |                              |  localhost:3002      |
|  /api/*          |                              |  GitHub Pages       |
+------------------+                              +---------------------+
```

### Backend

- **Python FastAPI** with SQLite and FTS5 full-text search
- Pydantic v2 models for data validation
- Claude API integration (Sonnet 4.5 for classify/recommend/judge, Haiku 4.5 for filtering)
- Tenacity for retry logic on LLM calls

### Frontend

- **Next.js 15** static export with React 19 and Tailwind CSS 4
- Intuit FY27 design system: dark navy sidebar (`#162251`), AI teal (`#00b9a9`), Avenir Next font
- Dual-mode API client: reads pre-exported static JSON in production, hits live backend in development
- TypeScript throughout

---

## Pipeline

The orchestrator runs a 6-phase pipeline, either on-demand via CLI or on a
weekly schedule (every Friday at 8:54 AM):

| Phase | Module | Description |
|-------|--------|-------------|
| 1. Ingest | `orchestrator.py` | Pull activities from Slack MCP and Gmail MCP |
| 2. Classify | `classifier.py` | Assign activity type, priority, and leverage level |
| 3. Analyze | `engine.py` | Compute alignment, fragmentation, anomalies |
| 4. Recommend | `recommender.py` | Generate 3 coaching recommendations |
| 5. Judge | `judge.py` | Score recommendations on faithfulness, fit, specificity |
| 6. Publish | `orchestrator.py` | Export static JSON, trigger QA gate, deploy, Slack DM |

The scheduled task runs the full pipeline end-to-end, blocks on test failure,
deploys to GitHub Pages on success, and sends a summary DM to Slack.

---

## Classification System

A tiered classifier that maximizes speed and minimizes LLM cost:

1. **Rule-based fast path** (~70% coverage) -- regex patterns match activity
   titles against known keywords (Jira tickets, meeting types, product names,
   pillar-specific terms).
2. **Claude LLM fallback** -- ambiguous activities are sent to Claude Sonnet 4.5
   with full priority context for classification.

### Activity Types (7)

| Type | Description |
|------|-------------|
| Strategy | Strategic planning, roadmap, vision |
| Discovery | User research, interviews, data analysis |
| Execution | Ticket work, PRs, implementation |
| Stakeholder | Stakeholder management, exec alignment, cross-team |
| InternalOps | Team processes, hiring, admin |
| Reactive | Interrupts, escalations, firefighting |
| LowValue | Low-impact meetings, status updates, duplicate work |

### Leverage Levels (3)

- **High** -- directly advances a strategic pillar
- **Medium** -- supports a pillar indirectly
- **Low** -- operational overhead or low-impact work

---

## Analysis Engine

Pure Python, no LLM calls. Computes weekly metrics from classified activities:

- **Priority alignment %** -- actual time vs. target allocation across pillars
- **Fragmentation score** -- context switches per hour (rolling window)
- **Meeting load** -- total meeting hours per week
- **Activity type distribution** -- hours breakdown by type
- **Weekly trends** -- 4-week rolling comparison

### Anomaly Detection

Flags conditions that warrant coaching intervention:

| Anomaly | Threshold | Meaning |
|---------|-----------|---------|
| Meeting bloat | >20 hours/week | Calendar overload |
| Low alignment | <50% | Drifting from strategic priorities |
| High fragmentation | >5 switches/hour | Context-switching too often |
| Low-value excess | >20% of time | Too much time on LowValue activities |
| Priority drift | >2 consecutive weeks | Sustained misalignment |

---

## Recommendation Engine

Generates 3 coaching recommendations per week, one of each type:

| Type | Intent |
|------|--------|
| **Accelerate** | Double down on high-leverage work that is going well |
| **Cut** | Reduce or eliminate low-value or misaligned activities |
| **Redirect** | Shift effort toward an underserved strategic pillar |

### Evidence Grounding

Every recommendation must cite specific activity IDs from the current week.
Recommendations without evidence are rejected.

### Judge Quality Gate

Each recommendation is scored by a judge agent on three dimensions (1-3 scale):

| Dimension | Description |
|-----------|-------------|
| Faithfulness | Does it reflect actual data, not hallucinations? |
| Priority-fit | Does it align with current strategic pillars? |
| Specificity | Is it actionable with concrete next steps? |

**Hard block**: any dimension scoring 1 causes the recommendation to be rejected
and regenerated.

---

## Chat Interface

Pattern-based Q&A engine that answers 12+ question types without any LLM calls:

| Question Type | Example |
|---------------|---------|
| Time allocation | "How much time did I spend on Strategy?" |
| Priority alignment | "Am I on track with my priorities?" |
| Meeting load | "How many hours of meetings this week?" |
| Decisions | "What decisions were made this week?" |
| Open questions | "What questions are still unresolved?" |
| Anomalies | "Are there any red flags?" |
| Recommendations | "What should I focus on?" |
| Stakeholder activity | "What did Stephen Yu work on?" |
| Specific priority | "How is the Analytics Agent pillar going?" |
| Weekly summary | "Give me a weekly summary" |
| Trends | "How has my alignment changed over time?" |
| Help | "What can you do?" |

Falls back to Claude LLM for complex free-form queries when the
`ANTHROPIC_API_KEY` environment variable is set.

---

## Frontend Pages

Five routes, each with a distinct coaching purpose:

### Briefing (`/`)
Morning dashboard. KPI metric cards (alignment %, meeting hours, fragmentation
score, activities processed), AI insight banner with snowflake icon, priority
pulse bar chart, and a "Needs Your Attention" list of flagged anomalies.

### Ask Coach (`/chat`)
Conversational interface with 8 suggested prompt chips. Supports the full
Q&A engine. Messages persist within the session.

### Weekly Review (`/week`)
Alignment trend line chart (4-week rolling), priority breakdown donut,
activity type distribution, and the 3 coaching recommendations with
judge scores.

### Decisions (`/decisions`)
Decision log with timestamps and stakeholder attribution. Open question
tracker with urgency badges (high / medium / low). Filterable by week.

### Priorities (`/priorities`)
FY26 Q4 pillar cards with target weight percentages, key PRDs tracked
under each pillar, and upcoming key dates (GBSG BI Phase 1, WhatsApp GA).

---

## FY26 Q4 Strategic Pillars

| # | Pillar | Target Weight | Key Initiatives |
|---|--------|---------------|-----------------|
| 1 | Advanced Analytics & AI-Powered Insights | 40% | Analytics Agent GA, DSB intelligence, WhatsApp, contextual insights |
| 2 | Platform Intelligence Across MC & QBO | 35% | GBSG BI platform POC, L2C reporting, Omni integration |
| 3 | Trusted Data Foundation & Quality at Scale | 25% | Modernization, QA practices, data quality |

Source: R&A Q4 Roadmap DPV1.3

---

## Key Stakeholders Tracked

| Name | Role |
|------|------|
| Stephen Yu | PM - Analytics Agent, Omni, Contextual Insights |
| Nicole Jayne | PM - Dashboards/Reports, DSB, Omnichannel, L2C |
| Saikat Mukherjee | PD Driver - Modernization, QA |
| Dan Damkoehler | Engineering - CDP data quality |
| Nakib Khandaker | Engineering |
| Michael Walton | Leadership |

---

## Project Structure

```
personal-coach/
├── backend/
│   ├── agents/
│   │   ├── classifier.py      # Tiered rule-based + LLM classifier
│   │   ├── recommender.py     # Accelerate / Cut / Redirect generator
│   │   ├── judge.py           # Quality gate scoring (faithfulness, fit, specificity)
│   │   └── orchestrator.py    # 6-phase pipeline runner
│   ├── analysis/
│   │   └── engine.py          # Pure Python metrics engine (no LLM)
│   ├── api/
│   │   └── chat.py            # Pattern-based Q&A + LLM fallback
│   ├── llm/                   # Claude API integration (Sonnet 4.5 / Haiku 4.5)
│   ├── seed/
│   │   ├── seed_data.py       # Synthetic seed data for development
│   │   └── real_data.py       # Real ingested data from Slack/Gmail
│   ├── storage/
│   │   ├── db.py              # SQLite + FTS5 full-text search
│   │   └── models.py          # Pydantic v2 data models
│   ├── tests/
│   │   ├── test_analysis.py   # Analysis math and metrics
│   │   ├── test_chat.py       # Chat routing and Q&A patterns
│   │   ├── test_classifier.py # Classifier patterns and taxonomy
│   │   ├── test_db.py         # Database operations and FTS
│   │   ├── test_judge.py      # Judge scoring and hard blocks
│   │   └── test_recommender.py# Recommendation generation
│   ├── config.py              # Priorities, patterns, thresholds, model routing
│   ├── main.py                # FastAPI app + CLI entry point
│   └── requirements.txt       # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx       # Briefing (morning dashboard)
│   │   │   ├── chat/          # Ask Coach conversational UI
│   │   │   ├── week/          # Weekly Review trends + recs
│   │   │   ├── decisions/     # Decision log + open questions
│   │   │   ├── priorities/    # FY26 Q4 pillar cards
│   │   │   ├── layout.tsx     # Shell: dark navy sidebar + pillar badges
│   │   │   └── globals.css    # Intuit FY27 design tokens
│   │   └── lib/
│   │       └── api.ts         # Dual-mode API client (static JSON + live)
│   └── public/
│       └── api/               # Pre-exported static JSON data
│           ├── dashboard.json
│           ├── activities.json
│           ├── metrics.json
│           ├── weekly.json
│           ├── decisions.json
│           ├── questions.json
│           ├── priorities.json
│           └── recommendations.json
├── data/                      # Persistent data directory
└── README.md
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 20+
- (Optional) `ANTHROPIC_API_KEY` environment variable for LLM features

### Backend Setup

```bash
cd personal-coach

# Install Python dependencies
pip install -r backend/requirements.txt

# Initialize database and seed with sample data
python3 -m backend.main --seed

# Run the full pipeline (classify, analyze, recommend, judge, publish)
python3 -m backend.main --run-pipeline

# Start the API server on port 8001
python3 -m backend.main --serve
```

### Frontend Setup

```bash
cd personal-coach/frontend

# Install Node dependencies
npm install

# Start the dev server on port 3002
npm run dev
```

### Quick Reference

| Command | Description |
|---------|-------------|
| `python3 -m backend.main --seed` | Seed the database with sample data |
| `python3 -m backend.main --run-pipeline` | Run full 6-phase pipeline |
| `python3 -m backend.main --serve` | Start FastAPI backend (port 8001) |
| `cd frontend && npm run dev` | Start Next.js frontend (port 3002) |
| `cd frontend && npm run build` | Build static export for deployment |
| `python3 -m pytest backend/tests/ -v` | Run all tests |

---

## Running Tests

82+ unit tests cover every major subsystem:

```bash
python3 -m pytest backend/tests/ -v
```

| Test File | Coverage Area |
|-----------|---------------|
| `test_db.py` | SQLite operations, FTS5 search, CRUD |
| `test_classifier.py` | Regex patterns, taxonomy mapping, LLM fallback |
| `test_analysis.py` | Alignment math, fragmentation, anomaly detection |
| `test_judge.py` | Scoring dimensions, hard block logic |
| `test_chat.py` | Question routing, pattern matching, response format |
| `test_recommender.py` | Recommendation generation, evidence grounding |

The QA gate blocks deployment if any test fails.

---

## Deployment

### GitHub Pages (Production)

The frontend is deployed as a Next.js static export to GitHub Pages:

1. `npm run build` generates a static site in `out/`
2. Static JSON files in `public/api/` are bundled with the build
3. A QA gate runs all 82+ backend tests before deploy proceeds
4. On success, the static export is pushed to GitHub Pages

### Scheduled Automation

A Claude Code scheduled task runs every **Friday at 8:54 AM**:

1. Ingests the latest week of Slack messages and Gmail threads
2. Runs the full 6-phase pipeline
3. Executes the QA test suite
4. Deploys to GitHub Pages (blocked on test failure)
5. Sends a summary DM to Slack with key metrics and recommendations

---

## Tech Stack

### Backend
| Component | Technology |
|-----------|------------|
| Framework | FastAPI 0.110+ |
| Database | SQLite with FTS5 full-text search |
| Models | Pydantic v2 |
| LLM | Claude Sonnet 4.5 (classify, recommend, judge, chat) |
| LLM (fast) | Claude Haiku 4.5 (filtering) |
| Retry | Tenacity |
| Logging | structlog |

### Frontend
| Component | Technology |
|-----------|------------|
| Framework | Next.js 15 (static export) |
| UI | React 19 + TypeScript 5 |
| Styling | Tailwind CSS 4 + Intuit FY27 design tokens |
| Font | Avenir Next (Intuit standard) |
| Hosting | GitHub Pages |

### Design System
| Token | Value | Use |
|-------|-------|-----|
| Sidebar bg | `#162251` | Dark navy navigation |
| Page bg | `#f0f4f8` | Light blue-gray canvas |
| Primary text | `#1a1f36` | Headings |
| Secondary text | `#6b7c93` | Labels, metadata |
| Accent blue | `#0070d2` | Links, CTAs |
| AI teal | `#00b9a9` | AI feature accents, snowflake icon |
| Chart navy | `#1e3a6e` | Primary chart bars |
| Chart blue | `#4472c4` | Secondary chart bars |

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/dashboard` | Morning briefing data (KPIs, insights, anomalies) |
| GET | `/api/activities` | Paginated activity list with filters |
| GET | `/api/metrics` | Computed metrics (alignment, fragmentation, meetings) |
| GET | `/api/weekly` | Weekly trend data (4-week rolling) |
| GET | `/api/decisions` | Decision log entries |
| GET | `/api/questions` | Open questions with urgency levels |
| GET | `/api/priorities` | FY26 Q4 pillar definitions and weights |
| GET | `/api/recommendations` | Current coaching recommendations with judge scores |
| POST | `/api/chat` | Chat endpoint (pattern Q&A + optional LLM) |

---

## LLM Model Routing

| Task | Model | Rationale |
|------|-------|-----------|
| Filtering | Claude Haiku 4.5 | Fast, cheap pre-filter for noise |
| Classification | Claude Sonnet 4.5 | Accurate taxonomy mapping |
| Recommendation | Claude Sonnet 4.5 | Nuanced coaching advice |
| Judging | Claude Sonnet 4.5 | Reliable quality scoring |
| Chat (fallback) | Claude Sonnet 4.5 | Complex free-form queries |

---

## License

Internal tool -- Intuit/Mailchimp Reporting & Analytics team.
