"""Ingest real Slack + Gmail data into the Personal Productivity Coach."""

from backend.storage import db
from backend.agents.classifier import classify_batch


# ── Real Slack messages (from:<@W8FL6URHQ> + to:<@W8FL6URHQ>) ───────────────

SLACK_ACTIVITIES = [
    # ── Deepak's sent messages (Apr 13-17, 2026) ──────────────────────────────
    {"source": "slack", "source_id": "slack-tiger-voc-rollout-decision", "title": "Tiger Team rollout decision: continue 50%→75%→100% ramp on recipient activity & click map", "summary": "Moving forward with recipient activity, click performance, and click map as is. Continuing rollout from 50% to 75% then 100%. Custom fields in table not yet confirmed for all live accounts, investigating rollback vs ramp coverage gap.", "channel": "rna-tiger-voc", "duration_minutes": 15, "occurred_at": "2026-04-14T10:00:00", "participants": ["Nicole Jayne", "Vivian Wang"]},
    {"source": "slack", "source_id": "slack-analytics-ai-diffuse", "title": "Asking Stephen and Nicole how fast to diffuse analytics AI use case", "summary": "analytics ai usecase, how fast can we diffuse? Cc: Sid, Nick Boyle", "channel": "mc-reporting-analytics-feedback", "duration_minutes": 5, "occurred_at": "2026-04-14T11:00:00", "participants": ["Stephen Yu", "Nicole Jayne", "Sid Kumar", "Nick Boyle"]},
    {"source": "slack", "source_id": "slack-team-salute", "title": "Team recognition salute in #mc-reporting-analytics-feedback", "summary": "Sent team-wide shoutout tagging all R&A members: Sid, Saikat, Jane, Nakib, NJ, Stephen, Dmitri, SKumar", "channel": "mc-reporting-analytics-feedback", "duration_minutes": 5, "occurred_at": "2026-04-14T10:45:00", "participants": ["Sid Kumar", "Saikat Mukherjee", "Jane Guthrie", "Nakib Khandaker", "Nicole Jayne", "Stephen Yu", "Dmitri"]},
    {"source": "slack", "source_id": "slack-bi-platform-scope", "title": "Confirming BI as platform of reporting and analytics for all Intuit and QBO suites", "summary": "not in the vibe coded prototype - but BI is the platform of reporting and analytics for all Intuit and QBO suites", "channel": "internal-mpr-via-qb-bi", "duration_minutes": 5, "occurred_at": "2026-04-15T14:00:00", "participants": ["Saikat Mukherjee"]},
    {"source": "slack", "source_id": "slack-hvc-receipt-followup", "title": "HVC follow-up: post receipt activity export and other ramp-up details needed", "summary": "should follow up post receipt activity export and other ramp up to get more details", "channel": "hvc_feedback", "duration_minutes": 5, "occurred_at": "2026-04-14T09:30:00", "participants": ["Vivian Wang", "Nicole Jayne"]},
    {"source": "slack", "source_id": "slack-nj-dm-yo", "title": "DM with Nicole Jayne — coordinating demo/sync", "summary": "Coordinating sync: 'yo / lets talk / ok' sequence, Nicole wrapping up prior meeting in 20min", "channel": "dm-nicole", "duration_minutes": 10, "occurred_at": "2026-04-16T10:35:00", "participants": ["Nicole Jayne"]},
    {"source": "slack", "source_id": "slack-sy-dm-omni-monetization", "title": "DM with Stephen Yu — Omni monetization experiments and access", "summary": "Asked for Omni monetization experiment references, access request. Stephen shared AA monetization POV: cost not a concern, competitors monetize at copilot layer, free-to-paid test prototypes created.", "channel": "dm-stephen", "duration_minutes": 20, "occurred_at": "2026-04-17T08:48:00", "participants": ["Stephen Yu"]},
    {"source": "slack", "source_id": "slack-sy-brooks-thread", "title": "DM with Stephen Yu — referencing Brook's thread on user research", "summary": "Shared Brook's thread after Stephen noted he requested user research and testing. Stephen has not seen AI content changes grounded in actual research and data, can defend and escalate if needed.", "channel": "dm-stephen", "duration_minutes": 10, "occurred_at": "2026-04-17T08:55:00", "participants": ["Stephen Yu"]},
    {"source": "slack", "source_id": "slack-gdm-content-tone-validation", "title": "Group DM with Stephen and Nathan: content/framing/tone must be tested before GA", "summary": "Content, framing and tone has impact on how insights and recommendations land. All her changes should be tested/validated for no harm minimum before GA.", "channel": "group-dm-stephen-nathan", "duration_minutes": 15, "occurred_at": "2026-04-15T09:00:00", "participants": ["Stephen Yu", "Nathan Snell"]},
    {"source": "slack", "source_id": "slack-pm-agent-report-0417", "title": "Sent PM Productivity Agent weekly report to self", "summary": "Weekly report Apr 13-16: Stephen on Insights Agent & Scaled AI, Nicole on Email Report Reimagine & Custom Reports & HVC, Vivian on Tiger Team VoC & WhatsApp reporting", "channel": "dm-self", "duration_minutes": 5, "occurred_at": "2026-04-17T09:00:00", "participants": []},
    {"source": "slack", "source_id": "slack-bi-yes-confirm", "title": "Confirming BI platform scope in #internal-mpr-via-qb-bi", "summary": "Yes confirmation on BI platform scope", "channel": "internal-mpr-via-qb-bi", "duration_minutes": 2, "occurred_at": "2026-04-15T13:45:00", "participants": ["Saikat Mukherjee"]},

    # ── Messages TO Deepak (mentions/replies, Apr 13-17) ──────────────────────
    {"source": "slack", "source_id": "slack-nj-clickmap-hvc-escalation", "title": "Nicole escalating missing Click Map → Recipient Activity entry point ($393 MRR at risk)", "summary": "Customers noticed missing entry point from Click Map to Recipient Activity, 2 reports totaling $393 MRR. Asked Vivian to create plan to restore functionality with tiger team.", "channel": "group-dm-nj-vivian", "duration_minutes": 10, "occurred_at": "2026-04-16T09:00:00", "participants": ["Nicole Jayne", "Vivian Wang"]},
    {"source": "slack", "source_id": "slack-nj-email-report-figma-diff", "title": "Nicole requesting Figma diff between launched and previous email report experience", "summary": "Here's a figma of the original experience. Please do a diff between what recently launched and what was previously existing to get ahead of any other missing or not identical experiences.", "channel": "group-dm-nj-vivian", "duration_minutes": 10, "occurred_at": "2026-04-16T09:05:00", "participants": ["Nicole Jayne", "Vivian Wang"]},
    {"source": "slack", "source_id": "slack-nj-whatsapp-ai-report", "title": "Nicole sharing AI-First WhatsApp intelligence report and LLM-powered insights Figma", "summary": "Nicole shared AI-First WhatsApp intelligence prototype (github.intuit.com) and LLM-powered insights Figma design. Demo session coordinated.", "channel": "dm-nicole", "duration_minutes": 20, "occurred_at": "2026-04-16T12:00:00", "participants": ["Nicole Jayne"]},
    {"source": "slack", "source_id": "slack-sy-aa-monetization-pov", "title": "Stephen sharing AA monetization POV doc — free-to-paid test strategy", "summary": "Cost is not a concern, spending very low amounts. Competitors monetize at copilot layer. Can run free to paid tests with prototypes. Document shared for review.", "channel": "dm-stephen", "duration_minutes": 15, "occurred_at": "2026-04-17T07:23:00", "participants": ["Stephen Yu"]},
    {"source": "slack", "source_id": "slack-sy-perf-calibration-onepager", "title": "Stephen sharing one-pager for performance calibration", "summary": "Stephen shared one-pager for performance calibration. Happy to chat more if questions.", "channel": "dm-stephen", "duration_minutes": 10, "occurred_at": "2026-04-16T06:02:00", "participants": ["Stephen Yu"]},
    {"source": "slack", "source_id": "slack-omni-convo-quality-evals", "title": "Large group DM: Omni migration and conversation quality evals ownership", "summary": "Conversation quality evals not started yet. In migration to Omni, how much conversation quality owned by Freddie vs Insights Agent? Omni already has eval framework so should take lead given marketing analysis is more deterministic.", "channel": "group-dm-agents-team", "duration_minutes": 20, "occurred_at": "2026-04-15T14:30:00", "participants": ["Stephen Yu", "Ben Leathers", "Sid Kumar", "Nick Boyle", "Bryan Smith", "Nithali Sridhar", "Jason Dudley"]},
    {"source": "slack", "source_id": "slack-gdm-prd-session-friction", "title": "Group DM with Nicole and Stephen — PRD session friction, design not reading requirements", "summary": "Stephen: Design has not done any reading of what the requirements are, should have been done weeks ago. Nicole: these are like strategy docs, too vague to build workback plans from. Discussion about prompt expansion being the biggest opportunity.", "channel": "group-dm-nicole-stephen", "duration_minutes": 20, "occurred_at": "2026-04-15T11:00:00", "participants": ["Nicole Jayne", "Stephen Yu"]},
    {"source": "slack", "source_id": "slack-gdm-ramp-counting", "title": "Group DM with Nicole and Vivian — counting release date for tiger team ramp", "summary": "Vivian raised: do we count release date as when we ramped to 100% or when we began ramping at all? Manjusha question about CP/CM counting as this or next week.", "channel": "group-dm-nj-vivian", "duration_minutes": 10, "occurred_at": "2026-04-16T08:30:00", "participants": ["Nicole Jayne", "Vivian Wang"]},
    {"source": "slack", "source_id": "slack-jane-sy-response-surprise", "title": "Jane Guthrie surprised by Stephen Yu's response on content changes", "summary": "Jane: Let's discuss this at our 1:1. I'm continuously surprised by SY's response.", "channel": "dm-jane", "duration_minutes": 5, "occurred_at": "2026-04-17T08:51:00", "participants": ["Jane Guthrie"]},
]

# ── Real Gmail data (calendar invites + emails) ──────────────────────────────

EMAIL_ACTIVITIES = [
    # ── Calendar events (Mon-Thu Apr 13-17, inferred from Slack context) ───────
    # Monday Apr 13
    {"source": "calendar", "source_id": "cal-rna-leads-sync-0413", "title": "RNA Leads Sync weekly", "summary": "Weekly leads sync with Sid Kumar, Jane Guthrie, Nicole, Stephen, Tiffany, Sahana, Eddie, Alex, Nakib", "duration_minutes": 30, "occurred_at": "2026-04-13T10:00:00", "participants": ["Sid Kumar", "Jane Guthrie", "Nicole Jayne", "Stephen Yu", "Tiffany Huang", "Sahana Srivatsan", "Nakib Khandaker"]},
    {"source": "calendar", "source_id": "cal-onsite-meeting-0413", "title": "Onsite meeting — team in-person session", "summary": "Deepak in onsite meeting (referenced in Slack: 'In a onsite meeting')", "duration_minutes": 120, "occurred_at": "2026-04-13T13:00:00", "participants": ["Nicole Jayne", "Vivian Wang"]},

    # Tuesday Apr 14
    {"source": "calendar", "source_id": "cal-daily-mpr-sync-0414", "title": "Daily Sync: Marketing Performance Reporting via QB BI Platform", "summary": "Daily sync for 5/11 launch goal — status from Design, Prod, Eng", "duration_minutes": 15, "occurred_at": "2026-04-14T11:00:00", "participants": ["Nakib Khandaker", "Lauren Colwell", "Sid Kumar", "Nicole Jayne", "Stephen Yu", "Eddie Shrake"]},
    {"source": "calendar", "source_id": "cal-tiger-team-sync-0414", "title": "Tiger Team VOC Sync", "summary": "Tiger team sync on recipient activity rollout, click map, and click performance status", "duration_minutes": 30, "occurred_at": "2026-04-14T14:00:00", "participants": ["Vivian Wang", "Nicole Jayne", "Nakib Khandaker"]},

    # Wednesday Apr 15
    {"source": "calendar", "source_id": "cal-prd-session-0415", "title": "R&A Q4 PRD Session", "summary": "PRD session with Nicole, Stephen, Vivian, Nakib — friction noted: PRDs too vague for workback plans, design not reading requirements, prompt expansion as biggest opportunity", "duration_minutes": 60, "occurred_at": "2026-04-15T11:00:00", "participants": ["Nicole Jayne", "Stephen Yu", "Vivian Wang", "Nakib Khandaker", "Dmitri"]},
    {"source": "calendar", "source_id": "cal-daily-mpr-sync-0415", "title": "Daily Sync: Marketing Performance Reporting via QB BI Platform", "summary": "Daily sync for 5/11 launch goal", "duration_minutes": 15, "occurred_at": "2026-04-15T11:00:00", "participants": ["Nakib Khandaker", "Lauren Colwell", "Sid Kumar", "Nicole Jayne", "Stephen Yu"]},
    {"source": "calendar", "source_id": "cal-omni-migration-0415", "title": "Omni Migration Planning — Insights Agent conversation quality evals", "summary": "Discussion on Omni migration: conversation quality evals ownership between Freddie and Insights Agent, Omni eval framework lead", "duration_minutes": 45, "occurred_at": "2026-04-15T14:30:00", "participants": ["Stephen Yu", "Ben Leathers", "Sid Kumar", "Nick Boyle", "Bryan Smith", "Nithali Sridhar", "Jason Dudley"]},

    # Thursday Apr 16
    {"source": "calendar", "source_id": "cal-nj-whatsapp-demo-0416", "title": "Nicole Jayne — WhatsApp Intelligence AI-First Report Demo", "summary": "Demo of AI-First WhatsApp intelligence report and LLM-powered insights Figma design", "duration_minutes": 30, "occurred_at": "2026-04-16T14:00:00", "participants": ["Nicole Jayne"]},
    {"source": "calendar", "source_id": "cal-daily-mpr-sync-0416", "title": "Daily Sync: Marketing Performance Reporting via QB BI Platform", "summary": "Daily sync for 5/11 launch goal", "duration_minutes": 15, "occurred_at": "2026-04-16T11:00:00", "participants": ["Nakib Khandaker", "Lauren Colwell", "Sid Kumar", "Nicole Jayne", "Stephen Yu"]},
    {"source": "calendar", "source_id": "cal-sy-perf-calibration-0416", "title": "Stephen Yu — Performance Calibration 1:1", "summary": "Stephen shared one-pager for performance calibration, reviewed together", "duration_minutes": 30, "occurred_at": "2026-04-16T13:00:00", "participants": ["Stephen Yu"]},
]

# ── Real decisions extracted from conversations ──────────────────────────────

REAL_DECISIONS = [
    {"description": "Decided to continue recipient activity, click performance, and click map rollout from 50%→75%→100% despite custom field gap in some live accounts", "channel": "rna-tiger-voc", "related_priority": "Trusted Data Foundation & Quality at Scale", "stakeholders": ["Nicole Jayne", "Vivian Wang"]},
    {"description": "Mandated that all content/framing/tone changes to insights must be tested and validated for no harm before GA", "channel": "group-dm-stephen-nathan", "related_priority": "Advanced Analytics & AI-Powered Insights", "stakeholders": ["Stephen Yu", "Nathan Snell"]},
    {"description": "Directed Vivian to create plan to restore Click Map → Recipient Activity entry point after Nicole's HVC escalation ($393 MRR at risk)", "channel": "group-dm-nj-vivian", "related_priority": "Trusted Data Foundation & Quality at Scale", "stakeholders": ["Nicole Jayne", "Vivian Wang"]},
    {"description": "Aligned team on BI as the platform of reporting and analytics for all Intuit and QBO suites — not just the vibe coded prototype", "channel": "internal-mpr-via-qb-bi", "related_priority": "Platform Intelligence Across MC & QBO", "stakeholders": ["Saikat Mukherjee"]},
]

# ── Real open questions from conversations ───────────────────────────────────

REAL_QUESTIONS = [
    {"description": "Are custom fields missing in recipient activity table for some live accounts due to a rollback or ramp coverage gap? Must confirm before continuing ramp.", "urgency": "high", "owner": "Vivian Wang", "related_priority": "Trusted Data Foundation & Quality at Scale"},
    {"description": "In the Omni migration, how much of conversation quality will be owned by Freddie vs Insights Agent? This has not been discussed yet.", "urgency": "high", "owner": "Stephen Yu", "related_priority": "Advanced Analytics & AI-Powered Insights"},
    {"description": "How fast can the analytics AI use case be diffused across the product? What is the rollout sequencing for Sid and Nick Boyle?", "urgency": "high", "owner": "Deepak Prabhakaran", "related_priority": "Advanced Analytics & AI-Powered Insights"},
    {"description": "Does the missing Click Map → Recipient Activity entry point affect more than the 2 known reports ($393 MRR)? Needs Figma diff to confirm scope.", "urgency": "high", "owner": "Vivian Wang", "related_priority": "Trusted Data Foundation & Quality at Scale"},
    {"description": "Should release date for tiger team work be counted as ramp-start or ramp-to-100%? Affects Q4 delivery date accounting.", "urgency": "medium", "owner": "Vivian Wang", "related_priority": "Trusted Data Foundation & Quality at Scale"},
    {"description": "Do CP/CM deliverables count as this week or next week for tiger team release tracking?", "urgency": "medium", "owner": "Nicole Jayne", "related_priority": "Advanced Analytics & AI-Powered Insights"},
    {"description": "Can the 8 planned tests for prompt expansion be combined/parallelized? Stephen flagged most tests are on the same surfaces and can't run in parallel.", "urgency": "medium", "owner": "Nicole Jayne", "related_priority": "Advanced Analytics & AI-Powered Insights"},
]


def ingest_real_data():
    """Replace seed data with real Slack + Gmail data."""
    db.reset_db()

    # Seed priorities
    for p in [
        {"name": "Advanced Analytics & AI-Powered Insights", "description": "Analytics Agent GA, DSB intelligence, omnichannel, contextual insights.", "weight": 0.35, "pillar": 2},
        {"name": "Platform Intelligence Across MC & QBO", "description": "GBSG BI platform, L2C reporting, Omni integration.", "weight": 0.30, "pillar": 3},
        {"name": "Trusted Data Foundation & Quality at Scale", "description": "Modernization, QA practices, data quality.", "weight": 0.20, "pillar": 1},
        {"name": "Leadership & Strategic Investments", "description": "Career positioning, org design, people management, team health, hiring, stakeholder alignment.", "weight": 0.15, "pillar": 4},
    ]:
        db.insert_priority(p["name"], p["description"], p["weight"], p["pillar"])

    # Insert all activities
    all_activities = SLACK_ACTIVITIES + EMAIL_ACTIVITIES
    count = db.insert_activities_bulk(all_activities)

    # Classify
    activities = db.get_activities(limit=5000)
    classifications = classify_batch(activities, use_llm=False)
    db.insert_classifications_bulk(classifications)

    # Insert decisions
    for d in REAL_DECISIONS:
        db.insert_decision(
            description=d["description"],
            channel=d.get("channel", ""),
            related_priority=d.get("related_priority"),
            stakeholders=d.get("stakeholders", []),
        )

    # Insert open questions
    for q in REAL_QUESTIONS:
        db.insert_open_question(
            description=q["description"],
            urgency=q.get("urgency", "medium"),
            owner=q.get("owner", ""),
            related_priority=q.get("related_priority"),
        )

    print(f"Ingested {count} real activities, {len(classifications)} classified, {len(REAL_DECISIONS)} decisions, {len(REAL_QUESTIONS)} open questions")


if __name__ == "__main__":
    ingest_real_data()
