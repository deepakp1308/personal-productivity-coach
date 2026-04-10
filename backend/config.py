"""Central configuration for the Personal Productivity Coach."""

import os

# ── User (single-user agent) ─────────────────────────────────────────────────

USER = {
    "id": "deepak",
    "name": "Deepak Prabhakaran",
    "email": "deepak_kumar2@intuit.com",
    "role": "pm_lead",
    "slack_id": "W8FL6URHQ",
}

# ── Key stakeholders to track ────────────────────────────────────────────────

STAKEHOLDERS = [
    {"id": "stephen-yu", "name": "Stephen Yu", "slack_id": "U040C49798T", "role": "PM - Analytics Agent, Omni, Contextual Insights"},
    {"id": "nicole-jayne", "name": "Nicole Jayne", "slack_id": "U02LB4JPAEL", "role": "PM - Dashboards/Reports, DSB, Omnichannel, L2C"},
    {"id": "saikat-mukherjee", "name": "Saikat Mukherjee", "slack_id": None, "role": "PD Driver - Modernization, QA"},
    {"id": "dan-damkoehler", "name": "Dan Damkoehler", "slack_id": None, "role": "Engineering - CDP data quality"},
]

# ── FY26 Q4 Priorities (from R&A Q4 Roadmap DPV1.3) ─────────────────────────

DEFAULT_PRIORITIES = [
    {
        "name": "Advanced Analytics & AI-Powered Insights",
        "description": "Analytics Agent GA, DSB intelligence, omnichannel cross-channel + WhatsApp, contextual insights in workflows.",
        "weight": 0.40,
        "pillar": 2,
    },
    {
        "name": "Platform Intelligence Across MC & QBO",
        "description": "GBSG BI platform POC, L2C reporting, MC Analytics Agent as sub-agent in Intuit Intelligence (Omni).",
        "weight": 0.35,
        "pillar": 3,
    },
    {
        "name": "Trusted Data Foundation & Quality at Scale",
        "description": "Complete modernization of outstanding surfaces, strengthen QA practices across full dev lifecycle.",
        "weight": 0.25,
        "pillar": 1,
    },
]

# ── Key PRDs to monitor ──────────────────────────────────────────────────────

KEY_PRDS = [
    "Analytics Agent GA",
    "Actionable Intelligence for DSB Q4FY26",
    "Messaging & WhatsApp Public Beta Q4",
    "Marketing KPI via QBO BI_DPV1.3",
    "L2C Reporting",
    "Contextual Insights Scaling Plan",
    "AI-driven QA Automation",
    "Omni Integration",
]

# ── LLM Model Routing ────────────────────────────────────────────────────────

MODEL_MAP = {
    "filter": "claude-haiku-4-5-20251001",
    "classify": "claude-sonnet-4-5-20250514",
    "recommend": "claude-sonnet-4-5-20250514",
    "judge": "claude-sonnet-4-5-20250514",
    "chat": "claude-sonnet-4-5-20250514",
}

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# ── Classification taxonomy ──────────────────────────────────────────────────

ACTIVITY_TYPES = [
    "Strategy",       # strategic planning, roadmap, vision
    "Discovery",      # user research, interviews, data analysis
    "Execution",      # ticket work, PRs, implementation
    "Stakeholder",    # stakeholder mgmt, exec alignment, cross-team
    "InternalOps",    # team processes, hiring, admin
    "Reactive",       # interrupts, escalations, firefighting
    "LowValue",       # low-impact meetings, status updates, duplicate work
]

LEVERAGE_LEVELS = ["High", "Medium", "Low"]

# ── Rule-based classification patterns ───────────────────────────────────────
# Format: (title_pattern, activity_type, priority_hint)

RULE_BASED_PATTERNS = [
    # Jira/ticket patterns -> Execution
    (r"(?i)\bREPORTING-\d+", "Execution", None),
    (r"(?i)\b(ticket|bug|sprint|story|epic)\b", "Execution", None),
    # 1:1 patterns -> Stakeholder
    (r"(?i)\b1[:\-]1\b", "Stakeholder", None),
    (r"(?i)\b(skip.?level|exec.?sync|leadership)\b", "Stakeholder", None),
    # Standup/retro -> InternalOps
    (r"(?i)\b(standup|stand.up|retro|retrospective|team.sync|all.hands)\b", "InternalOps", None),
    # User research / interview -> Discovery
    (r"(?i)\b(user.research|interview|usability|discovery|prototype.review)\b", "Discovery", None),
    # Roadmap / strategy -> Strategy
    (r"(?i)\b(roadmap|strategy|vision|OKR|quarterly.planning|PRD)\b", "Strategy", None),
    # 1:1 with <> notation -> Stakeholder
    (r"<>", "Stakeholder", None),
    # Program Review / Leads Sync -> InternalOps
    (r"(?i)\b(program.review|leads.sync|OpMech)\b", "InternalOps", None),

    # ── Pillar 2: Advanced Analytics & AI-Powered Insights (40%) ─────────
    (r"(?i)\b(analytics.agent|insights.agent|deliverability.agent|GenUX|Omni.UX|holdout|beta.v2|freddie|mc_insights_skill|scaled.ai)\b",
     None, "Advanced Analytics & AI-Powered Insights"),
    (r"(?i)\b(DSB|digital.seller|ecomm|product.analytics|discount.analytics|purchase.pattern|reviews|loyalty|growth.agent|benchmarks)\b",
     None, "Advanced Analytics & AI-Powered Insights"),
    (r"(?i)\b(WhatsApp|cross.channel|channel.affinity|messaging.ROI|purchase.propensity|omnichannel|SMS.insight)\b",
     None, "Advanced Analytics & AI-Powered Insights"),
    (r"(?i)\b(contextual.insight|onboarding|activation|cancellation|churn|retention|campaign.creation|real.time.insights)\b",
     None, "Advanced Analytics & AI-Powered Insights"),
    (r"(?i)\b(funnel.performance|discoverability|GTM|bounce.reason|repeat.engagement|entry.point|feature.flag|S2S.event|shopify.analytics)\b",
     None, "Advanced Analytics & AI-Powered Insights"),

    # ── Pillar 3: Platform Intelligence Across MC & QBO (35%) ────────────
    (r"(?i)\b(GBSG|BI.platform|QB.BI|marketing.performance|QBO|KPI.dashboard|mailchimp.into.bi|plan.type.distribution)\b",
     None, "Platform Intelligence Across MC & QBO"),
    (r"(?i)\b(L2C|funnel.chart|website.analytics|data.well|campaign.L2|SKU|testjam)\b",
     None, "Platform Intelligence Across MC & QBO"),
    (r"(?i)\b(Omni|Intuit.Intelligence|orchestration|StarRocks|MCP.server|guardrails|QA.agent|regression.testing)\b",
     None, "Platform Intelligence Across MC & QBO"),
    (r"(?i)\b(MPR|marketing.ROI|email.reporting|SMS.reporting|Klaviyo.parity|automation.reporting|A/B.testing|comparative.reporting)\b",
     None, "Platform Intelligence Across MC & QBO"),

    # ── Pillar 1: Trusted Data Foundation & Quality at Scale (25%) ───────
    (r"(?i)\b(modernization|monolith|CDP|bot.filter|attribution.service|classic.automation)\b",
     None, "Trusted Data Foundation & Quality at Scale"),
    (r"(?i)\b(QA|regression|data.quality|monitoring|alerting|drift.detection|anomaly.detection|code.coverage|flag.management)\b",
     None, "Trusted Data Foundation & Quality at Scale"),
    (r"(?i)\b(CSAT|VOC|data.inaccuracy|data.consistency|CHEQ|IP.feeds|data.retention)\b",
     None, "Trusted Data Foundation & Quality at Scale"),

    # ── Existing report/custom report patterns ───────────────────────────
    (r"(?i)\b(email.report|custom.report|segment.discovery|diagnostics|driver.analysis|tiger|hvc|click.performance|click.map|whatsapp.report|export|recipient.activity|tooltip|DFAD|multivariate|MVT|zero.state|marketing.dashboard)\b",
     None, "Advanced Analytics & AI-Powered Insights"),

    # ── Cross-pillar R&A coordination (maps to highest-weight pillar) ─
    (r"(?i)\b(Q4.PRD.Review|PRD.Review|roadmap.*R&A|R&A.*roadmap)\b", "Strategy", "Advanced Analytics & AI-Powered Insights"),
    (r"(?i)\b(AI.reports|AI.report.*priority|data.issues.*real|data.discrepan)\b", None, "Advanced Analytics & AI-Powered Insights"),
    (r"(?i)\b(Q4.*project.*binder|project.*binder|Q3.*commit|product.*discount.*prompt)\b", None, "Advanced Analytics & AI-Powered Insights"),
    (r"(?i)\b(CRM.platform|L2C.*customer|target.*L2C|L2C.*deep.dive|marketing.*team.*MC)\b", None, "Platform Intelligence Across MC & QBO"),
    (r"(?i)\b(data.quality|data.issue|metric.quality)\b", None, "Trusted Data Foundation & Quality at Scale"),
]

# ── Anomaly thresholds ───────────────────────────────────────────────────────

MEETING_HOURS_THRESHOLD = 20.0  # >20 hrs/week = meeting bloat alert
FRAGMENTATION_THRESHOLD = 5.0   # >5 context switches per hour
PRIORITY_DRIFT_WEEKS = 2        # alert if off-priority for >2 weeks
LOW_VALUE_THRESHOLD = 0.20      # >20% of time on LowValue = alert

# ── Key dates ────────────────────────────────────────────────────────────────

KEY_DATES = {
    "gbsg_bi_phase1": "2026-05-01",  # Early May: Phase 1 GBSG BI platform
    "whatsapp_ga": "2026-07-01",     # July: WhatsApp GA target
}

# ── Server ───────────────────────────────────────────────────────────────────

API_HOST = os.environ.get("API_HOST", "0.0.0.0")
API_PORT = int(os.environ.get("API_PORT", "8001"))
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3002")
