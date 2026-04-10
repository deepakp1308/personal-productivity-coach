"""Ingest real Slack + Gmail data into the Personal Productivity Coach."""

from backend.storage import db
from backend.agents.classifier import classify_batch


# ── Real Slack messages (from:<@W8FL6URHQ> + to:<@W8FL6URHQ>) ───────────────

SLACK_ACTIVITIES = [
    # Deepak's messages
    {"source": "slack", "source_id": "slack-hvc-vivian-plan", "title": "Working on HVC plan with Vivian Wang", "summary": "Let's work on the plan for HVC feedback", "channel": "hvc_feedback", "duration_minutes": 5, "occurred_at": "2026-04-10T15:00:00", "participants": ["Vivian Wang"]},
    {"source": "slack", "source_id": "slack-hvc-fix-c1", "title": "HVC fix for C1 customers — mollify affected users", "summary": "Once fixed, we should mollify handful of C1s who have raised this in last week or 2", "channel": "hvc_feedback", "duration_minutes": 5, "occurred_at": "2026-04-10T14:30:00", "participants": ["Nicole Jayne"]},
    {"source": "slack", "source_id": "slack-hvc-eta", "title": "Asking Nicole and Nakib for ETA on HVC fix", "summary": "What is the ETA on this?", "channel": "hvc_feedback", "duration_minutes": 5, "occurred_at": "2026-04-09T11:00:00", "participants": ["Nicole Jayne", "Nakib Khandaker"]},
    {"source": "slack", "source_id": "slack-hvc-ticket-tracking", "title": "Asking Nicole and Vivian to post HVC ticket for tracking closure", "summary": "Post the ticket here for tracking closure", "channel": "hvc_feedback", "duration_minutes": 5, "occurred_at": "2026-04-08T10:00:00", "participants": ["Nicole Jayne", "Vivian Wang"]},
    {"source": "slack", "source_id": "slack-gdm-debrief-nj-sy", "title": "Debrief with Nicole and Stephen", "summary": "Quick debrief after meeting", "channel": "group-dm-nicole-stephen", "duration_minutes": 15, "occurred_at": "2026-04-10T13:00:00", "participants": ["Nicole Jayne", "Stephen Yu"]},
    {"source": "slack", "source_id": "slack-gdm-q3-commitments", "title": "Checking Q3 product and discount prompt commitments still on track", "summary": "Can we make sure our committed product and discount related prompts we committed for q3 is still delivered along with this work?", "channel": "group-dm-nicole-stephen", "duration_minutes": 10, "occurred_at": "2026-04-09T16:00:00", "participants": ["Nicole Jayne", "Stephen Yu"]},
    {"source": "slack", "source_id": "slack-dm-saikat-wellbeing", "title": "DM with Saikat — feeling under the weather", "summary": "Feeling under the weather, will check slack later", "channel": "dm-saikat", "duration_minutes": 2, "occurred_at": "2026-04-09T08:30:00", "participants": ["Saikat Mukherjee"]},
    {"source": "slack", "source_id": "slack-leadership-ooo", "title": "Posted OOO to marketing data platforms leadership", "summary": "Feeling under the weather this morning, will check slack later", "channel": "marketing-data-platforms-leadership", "duration_minutes": 2, "occurred_at": "2026-04-09T08:25:00", "participants": ["Nathan Snell"]},
    {"source": "slack", "source_id": "slack-dm-michael-followup", "title": "DM with Michael Walton — CRM platform role discussion", "summary": "Follow-up on role opportunity: maintaining title/comp, clear path to lead team, direct reporting preference", "channel": "dm-michael-walton", "duration_minutes": 20, "occurred_at": "2026-04-08T14:00:00", "participants": ["Michael Walton"]},
    {"source": "slack", "source_id": "slack-dm-michael-crm-eng", "title": "DM with Michael Walton — CRM platform engineering team question", "summary": "Who is durable engineering team for CRM platform - jack/jing or Nandu/Push?", "channel": "dm-michael-walton", "duration_minutes": 10, "occurred_at": "2026-04-08T13:00:00", "participants": ["Michael Walton"]},
    {"source": "slack", "source_id": "slack-dm-michael-kashi", "title": "DM with Michael Walton — Kashi org involvement question", "summary": "Is there a reason why Kashi org is getting involved when Matt and Jack own get and grow charter?", "channel": "dm-michael-walton", "duration_minutes": 10, "occurred_at": "2026-04-08T12:30:00", "participants": ["Michael Walton"]},
    {"source": "slack", "source_id": "slack-dm-nathan-org", "title": "DM with Nathan Snell — creative org structure discussion", "summary": "Spoke to him, asked for some creative org structure, one more round before making decision", "channel": "dm-nathan-snell", "duration_minutes": 10, "occurred_at": "2026-04-07T16:00:00", "participants": ["Nathan Snell"]},
    {"source": "slack", "source_id": "slack-pm-agent-report", "title": "Sent PM Productivity Agent weekly report to self", "summary": "Weekly report: Stephen on Insights Agent, Nicole on Email Report, Vivian on Tiger Team VoC", "channel": "dm-self", "duration_minutes": 5, "occurred_at": "2026-04-10T09:00:00", "participants": []},

    # Messages TO Deepak (mentions/replies)
    {"source": "slack", "source_id": "slack-nj-contextual-help", "title": "Nicole asking Stephen for help on contextual insights and Omni sub-agent", "summary": "Need help from Stephen with specifics on contextual insights, integrate Mailchimp Analytics Agent as a sub-agent", "channel": "group-dm-nicole-stephen", "duration_minutes": 5, "occurred_at": "2026-04-10T16:00:00", "participants": ["Nicole Jayne", "Stephen Yu"]},
    {"source": "slack", "source_id": "slack-nj-binder-projects", "title": "Nicole sharing Q4 project binder with all projects in rows", "summary": "I have nearly all of the projects in rows in the binder spreadsheet", "channel": "group-dm-nicole-stephen", "duration_minutes": 5, "occurred_at": "2026-04-10T15:45:00", "participants": ["Nicole Jayne"]},
    {"source": "slack", "source_id": "slack-sy-chat-available", "title": "Stephen Yu available to chat", "summary": "I can chat if free", "channel": "group-dm-nicole-stephen", "duration_minutes": 5, "occurred_at": "2026-04-10T14:00:00", "participants": ["Stephen Yu"]},
    {"source": "slack", "source_id": "slack-sy-ai-reports-priority", "title": "Stephen confirming AI reports are still #1 priority", "summary": "AI reports are still number 1 priority", "channel": "group-dm-agent-team", "duration_minutes": 5, "occurred_at": "2026-04-09T15:00:00", "participants": ["Stephen Yu", "Ben Leathers", "Sid Kumar", "Nick Boyle", "Nithali Sridhar"]},
    {"source": "slack", "source_id": "slack-sy-data-issues-analysis", "title": "Stephen analyzing real data issues vs user misunderstanding", "summary": "Curious on whether these are real data issues or user misunderstanding. Looks like majority are indeed real data issues", "channel": "group-dm-agent-team", "duration_minutes": 10, "occurred_at": "2026-04-09T14:00:00", "participants": ["Stephen Yu"]},
    {"source": "slack", "source_id": "slack-nithali-deliverability-outage", "title": "Nithali reporting deliverability agent outage", "summary": "Ongoing deliverability agent outage, looking into MVT discrepancies", "channel": "group-dm-agent-team", "duration_minutes": 5, "occurred_at": "2026-04-09T10:00:00", "participants": ["Nithali Sridhar"]},
    {"source": "slack", "source_id": "slack-michael-crm-response", "title": "Michael Walton response on CRM platform role — Jing's team, 150 engineers", "summary": "Jing's team, 150 engineers total. Path to lead team possible but not guaranteed. Working with HR on title/comp.", "channel": "dm-michael-walton", "duration_minutes": 15, "occurred_at": "2026-04-09T12:00:00", "participants": ["Michael Walton"]},
    {"source": "slack", "source_id": "slack-michael-platform-context", "title": "Michael Walton explaining Intuit platform evolution context", "summary": "Kashi org involved because Intuit becoming a platform vs two apps. Central teams thinking about common good.", "channel": "dm-michael-walton", "duration_minutes": 10, "occurred_at": "2026-04-08T16:00:00", "participants": ["Michael Walton"]},
    {"source": "slack", "source_id": "slack-saikat-apology", "title": "DM with Saikat — resolving interpersonal friction", "summary": "Saikat apologized for being edgy, Deepak accepted — no hard feelings, all good", "channel": "dm-saikat", "duration_minutes": 5, "occurred_at": "2026-04-09T09:00:00", "participants": ["Saikat Mukherjee"]},
]

# ── Real Gmail data (calendar invites + emails) ──────────────────────────────

EMAIL_ACTIVITIES = [
    # Calendar events (extracted from invitations)
    {"source": "calendar", "source_id": "cal-prd-review-1", "title": "R&A: Q4 PRD Review 1", "summary": "Q4 planning PRD review with Nakib, Saikat, Stephen, Nicole, Vivian, Eddie, Sahana, Sid, Dmitri, Jane, Sarvesh, Lorraine", "duration_minutes": 60, "occurred_at": "2026-04-10T12:15:00", "participants": ["Nakib Khandaker", "Saikat Mukherjee", "Stephen Yu", "Nicole Jayne", "Vivian Wang", "Eddie Shrake", "Lorraine Lim"]},
    {"source": "calendar", "source_id": "cal-prd-review-2", "title": "R&A: Q4 PRD Review 2", "summary": "Q4 PRD review session 2 — align on scope before moving forward", "duration_minutes": 60, "occurred_at": "2026-04-14T08:00:00", "participants": ["Nakib Khandaker", "Stephen Yu", "Nicole Jayne", "Saikat Mukherjee", "Vivian Wang"]},
    {"source": "calendar", "source_id": "cal-prd-review-3", "title": "R&A: Q4 PRD Review 3", "summary": "Q4 PRD review session 3 — final alignment", "duration_minutes": 60, "occurred_at": "2026-04-17T08:00:00", "participants": ["Nakib Khandaker", "Stephen Yu", "Nicole Jayne", "Saikat Mukherjee", "Vivian Wang"]},
    {"source": "calendar", "source_id": "cal-hvc-escalations", "title": "[Weekly] Top Customer Health: HVC Escalations Review", "summary": "HVC escalation review with Melina Iacovou, Bonnie Watkins, Saikat, Nicole, Vivian, Zack, Nathan, Matt Cimino", "duration_minutes": 30, "occurred_at": "2026-04-15T13:00:00", "participants": ["Melina Iacovou", "Saikat Mukherjee", "Nicole Jayne", "Vivian Wang", "Nathan Snell"]},
    {"source": "calendar", "source_id": "cal-mc-program-review", "title": "Weekly MC Program Review — MC Leadership Execution Tracker", "summary": "MC program review with Jack Tam, Nathan Bullock, Shani Boston, Andrew Firstenberger", "duration_minutes": 60, "occurred_at": "2026-04-10T15:45:00", "participants": ["Jack Tam", "Nathan Bullock", "Shani Boston", "Saikat Mukherjee"]},
    {"source": "calendar", "source_id": "cal-l2c-deep-dive", "title": "Deep Dive Session on Target L2C Customers", "summary": "Deep dive on L2C target customers with Diana Williams, AllMailChimpPMs, Nathan Bullock, Jack Tam, Matt Idema", "duration_minutes": 60, "occurred_at": "2026-04-10T14:39:00", "participants": ["Diana Williams", "Nathan Bullock", "Jack Tam", "Matt Idema", "Michael Walton"]},
    {"source": "calendar", "source_id": "cal-web-deep-dive-cancelled", "title": "Mailchimp.com Web Deep Dive Weekly (CANCELLED)", "summary": "Cancelled — no baked experiment results or special topics this week", "duration_minutes": 0, "occurred_at": "2026-04-10T12:05:00", "participants": []},
    {"source": "calendar", "source_id": "cal-zoom-stephen", "title": "Zoom Meeting with Stephen Yu", "summary": "Stephen Yu joined your meeting", "duration_minutes": 30, "occurred_at": "2026-04-10T13:20:00", "participants": ["Stephen Yu"]},

    # Emails
    {"source": "email", "source_id": "email-aman-thankyou", "title": "Thank you from Aman Bansal — interview follow-up", "summary": "Aman excited about the opportunity, reflecting on conversation last week about Mailchimp evolution", "duration_minutes": 5, "occurred_at": "2026-04-10T12:56:00", "participants": ["Aman Bansal"]},
    {"source": "email", "source_id": "email-compliance-overdue", "title": "Workers overdue on compliance courses", "summary": "Team members overdue on compliance training — remind workers to complete", "duration_minutes": 5, "occurred_at": "2026-04-10T11:15:00", "participants": []},
    {"source": "email", "source_id": "email-nakib-roadmap-suggestion", "title": "Nakib Khandaker added suggestion to R&A Q4 Roadmap_DPV1.3", "summary": "Nakib added a suggestion to the Q4 roadmap document", "duration_minutes": 10, "occurred_at": "2026-04-10T07:12:00", "participants": ["Nakib Khandaker"]},
    {"source": "email", "source_id": "email-michelle-web-cancelled", "title": "Michelle Parekh — Web Deep Dive cancelled", "summary": "Cancelling today's meeting, no baked experiment results this week", "duration_minutes": 2, "occurred_at": "2026-04-10T09:12:00", "participants": ["Michelle Parekh"]},
]

# ── Real decisions extracted from conversations ──────────────────────────────

REAL_DECISIONS = [
    {"description": "Asked for creative org structure for CRM platform role — one more round before deciding", "channel": "dm-nathan-snell", "related_priority": "Platform Intelligence Across MC & QBO", "stakeholders": ["Nathan Snell", "Michael Walton"]},
    {"description": "Confirmed Q3 product and discount prompt commitments must still be delivered alongside Q4 work", "channel": "group-dm-nicole-stephen", "related_priority": "Advanced Analytics & AI-Powered Insights", "stakeholders": ["Nicole Jayne", "Stephen Yu"]},
    {"description": "Directed Nicole and Vivian to post HVC ticket for tracking closure", "channel": "hvc_feedback", "related_priority": "Trusted Data Foundation & Quality at Scale", "stakeholders": ["Nicole Jayne", "Vivian Wang"]},
    {"description": "Requested ETA from Nicole and Nakib on HVC fix — committed to mollifying affected C1 customers once fixed", "channel": "hvc_feedback", "related_priority": "Trusted Data Foundation & Quality at Scale", "stakeholders": ["Nicole Jayne", "Nakib Khandaker"]},
]

# ── Real open questions from conversations ───────────────────────────────────

REAL_QUESTIONS = [
    {"description": "Should I take the CRM platform PM role under Michael Walton? Title/comp needs HR confirmation, reporting structure under discussion", "urgency": "high", "owner": "Deepak Prabhakaran", "related_priority": "Platform Intelligence Across MC & QBO"},
    {"description": "Are the data discrepancies in analytics agent real data issues or user misunderstanding? Stephen says majority are real", "urgency": "high", "owner": "Stephen Yu", "related_priority": "Advanced Analytics & AI-Powered Insights"},
    {"description": "Is the deliverability agent outage resolved? Nithali was investigating MVT discrepancies", "urgency": "high", "owner": "Nithali Sridhar", "related_priority": "Advanced Analytics & AI-Powered Insights"},
    {"description": "Who will Jing's 150-engineer CRM team be dedicated to? How does that affect R&A scope?", "urgency": "medium", "owner": "Michael Walton", "related_priority": "Platform Intelligence Across MC & QBO"},
    {"description": "Team members overdue on compliance training — who needs to complete?", "urgency": "medium", "owner": "Deepak Prabhakaran", "related_priority": None},
    {"description": "What specifics does Stephen need from Nicole on contextual insights and Omni sub-agent integration?", "urgency": "medium", "owner": "Stephen Yu", "related_priority": "Advanced Analytics & AI-Powered Insights"},
]


def ingest_real_data():
    """Replace seed data with real Slack + Gmail data."""
    db.reset_db()

    # Seed priorities
    for p in [
        {"name": "Advanced Analytics & AI-Powered Insights", "description": "Analytics Agent GA, DSB intelligence, omnichannel, contextual insights.", "weight": 0.40, "pillar": 2},
        {"name": "Platform Intelligence Across MC & QBO", "description": "GBSG BI platform, L2C reporting, Omni integration.", "weight": 0.35, "pillar": 3},
        {"name": "Trusted Data Foundation & Quality at Scale", "description": "Modernization, QA practices, data quality.", "weight": 0.25, "pillar": 1},
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
