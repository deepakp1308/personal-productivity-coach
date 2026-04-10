"""Seed data generator for the Personal Productivity Coach.

Generates sample activities across Slack and Email for 2 weeks,
covering the three Q4 pillars.
"""

import json
import random
from datetime import datetime, timedelta

from backend.storage import db
from backend.agents.classifier import classify_batch


SLACK_TEMPLATES = [
    # Pillar 2: Advanced Analytics & AI-Powered Insights
    {"title": "Reviewed analytics agent beta metrics with Stephen", "source": "slack", "channel": "r-and-a-leads", "duration_minutes": 5},
    {"title": "Discussed GenUX to Omni UX transition timeline", "source": "slack", "channel": "insights-agent", "duration_minutes": 10},
    {"title": "DSB actionable intelligence PRD feedback for Nicole", "source": "slack", "channel": "dsb-intelligence", "duration_minutes": 8},
    {"title": "WhatsApp analytics requirements review", "source": "slack", "channel": "omnichannel", "duration_minutes": 5},
    {"title": "Contextual insights in campaign creation — design review", "source": "slack", "channel": "insights-agent", "duration_minutes": 15},
    {"title": "Growth agent POC scope discussion", "source": "slack", "channel": "dsb-intelligence", "duration_minutes": 10},
    {"title": "Cross-channel benchmarks data validation", "source": "slack", "channel": "omnichannel", "duration_minutes": 5},
    {"title": "LLM-powered onboarding insights experiment results", "source": "slack", "channel": "insights-agent", "duration_minutes": 10},

    # Pillar 3: Platform Intelligence Across MC & QBO
    {"title": "GBSG BI platform Phase 1 launch checklist review", "source": "slack", "channel": "bi-platform", "duration_minutes": 10},
    {"title": "L2C funnel chart requirements with Nicole", "source": "slack", "channel": "l2c-reporting", "duration_minutes": 8},
    {"title": "Marketing ROI report QBO integration discussion", "source": "slack", "channel": "bi-platform", "duration_minutes": 10},
    {"title": "Omni orchestration layer — data access strategy debate", "source": "slack", "channel": "project-omni", "duration_minutes": 15},
    {"title": "StarRocks to BI pipeline architecture review", "source": "slack", "channel": "bi-platform", "duration_minutes": 10},
    {"title": "L2C website analytics funnel scope", "source": "slack", "channel": "l2c-reporting", "duration_minutes": 5},

    # Pillar 1: Trusted Data Foundation
    {"title": "QA regression test coverage plan review with Nicole", "source": "slack", "channel": "qa-and-quality", "duration_minutes": 10},
    {"title": "Data quality monitoring dashboard requirements", "source": "slack", "channel": "qa-and-quality", "duration_minutes": 8},
    {"title": "Classic automation modernization status update", "source": "slack", "channel": "modernization", "duration_minutes": 5},
    {"title": "CDP upstream data quality handoff to Dan", "source": "slack", "channel": "data-quality", "duration_minutes": 10},

    # InternalOps / Stakeholder
    {"title": "R&A team standup", "source": "slack", "channel": "r-and-a-team", "duration_minutes": 15},
    {"title": "1:1 with Stephen Yu — analytics agent roadmap", "source": "slack", "channel": "dm", "duration_minutes": 30},
    {"title": "1:1 with Nicole Jayne — DSB + L2C priorities", "source": "slack", "channel": "dm", "duration_minutes": 30},
    {"title": "Skip-level with VP Product", "source": "slack", "channel": "dm", "duration_minutes": 30},
    {"title": "Leads sync — cross-team alignment", "source": "slack", "channel": "ra-leads", "duration_minutes": 15},

    # Low-value / Reactive
    {"title": "Forwarded escalation about email report data mismatch", "source": "slack", "channel": "escalations", "duration_minutes": 5},
    {"title": "Status update thread for all-hands prep", "source": "slack", "channel": "general", "duration_minutes": 5},
]

EMAIL_TEMPLATES = [
    {"title": "Re: Analytics Agent GA timeline and holdout design", "source": "email", "duration_minutes": 10},
    {"title": "GBSG BI Platform — Phase 1 launch coordination", "source": "email", "duration_minutes": 15},
    {"title": "L2C Reporting PRD review comments", "source": "email", "duration_minutes": 10},
    {"title": "Marketing KPI via QBO BI_DPV1.3 stakeholder alignment", "source": "email", "duration_minutes": 10},
    {"title": "WhatsApp Public Beta Q4 — design review notes", "source": "email", "duration_minutes": 8},
    {"title": "QA automation PRD review — Stephen's draft", "source": "email", "duration_minutes": 10},
    {"title": "Re: Modernization sprint planning", "source": "email", "duration_minutes": 5},
    {"title": "Weekly R&A team status digest", "source": "email", "duration_minutes": 5},
    {"title": "Contextual insights experiment metrics follow-up", "source": "email", "duration_minutes": 8},
    {"title": "DSB conversion analytics — ecomm benchmarks data", "source": "email", "duration_minutes": 10},
]

SAMPLE_DECISIONS = [
    {"description": "Decided to keep analytics agent on GenUX for Q4, defer Omni UX transition to FY27", "channel": "insights-agent", "related_priority": "Advanced Analytics & AI-Powered Insights"},
    {"description": "Approved Nicole's plan to release segments in custom reports before DSB benchmarks", "channel": "dsb-intelligence", "related_priority": "Advanced Analytics & AI-Powered Insights"},
    {"description": "Aligned with GBSG team on Phase 1 scope: email + SMS + marketing ROI reports only", "channel": "bi-platform", "related_priority": "Platform Intelligence Across MC & QBO"},
    {"description": "Agreed to prioritize L2C funnel chart over website analytics funnel for early May", "channel": "l2c-reporting", "related_priority": "Platform Intelligence Across MC & QBO"},
    {"description": "Committed to zero data inaccuracy VOCs target within 30 days", "channel": "qa-and-quality", "related_priority": "Trusted Data Foundation & Quality at Scale"},
]

SAMPLE_QUESTIONS = [
    {"description": "Should deliverability agent be merged into insights agent or remain standalone?", "urgency": "high", "owner": "Stephen Yu", "related_priority": "Advanced Analytics & AI-Powered Insights"},
    {"description": "What's the data access strategy for Omni: StarRocks vs. MCP server vs. API?", "urgency": "high", "owner": "Stephen Yu", "related_priority": "Platform Intelligence Across MC & QBO"},
    {"description": "Who will own the broader QA improvements beyond Nicole and Stephen's scope?", "urgency": "medium", "owner": "Saikat Mukherjee", "related_priority": "Trusted Data Foundation & Quality at Scale"},
    {"description": "How do we support L2C customers beyond the existing 60K overlapping QBO+MC users?", "urgency": "medium", "owner": "Nicole Jayne", "related_priority": "Platform Intelligence Across MC & QBO"},
]


def seed():
    """Seed the database with sample data."""
    db.reset_db()

    # Seed priorities
    for p in [
        {"name": "Advanced Analytics & AI-Powered Insights", "description": "Analytics Agent GA, DSB intelligence, omnichannel, contextual insights.", "weight": 0.40, "pillar": 2},
        {"name": "Platform Intelligence Across MC & QBO", "description": "GBSG BI platform, L2C reporting, Omni integration.", "weight": 0.35, "pillar": 3},
        {"name": "Trusted Data Foundation & Quality at Scale", "description": "Modernization, QA practices, data quality.", "weight": 0.25, "pillar": 1},
    ]:
        db.insert_priority(p["name"], p["description"], p["weight"], p["pillar"])

    # Generate 2 weeks of activities
    now = datetime.now()
    activities = []

    for week_offset in range(2):
        base_date = now - timedelta(weeks=week_offset)
        for day_offset in range(5):  # Mon-Fri
            day = base_date - timedelta(days=base_date.weekday()) + timedelta(days=day_offset)

            # 4-6 Slack messages per day
            for template in random.sample(SLACK_TEMPLATES, min(random.randint(4, 6), len(SLACK_TEMPLATES))):
                hour = random.randint(8, 17)
                minute = random.randint(0, 59)
                occurred = day.replace(hour=hour, minute=minute, second=0)
                activities.append({
                    "source": template["source"],
                    "source_id": f"slack-{occurred.isoformat()}-{random.randint(1000, 9999)}",
                    "title": template["title"],
                    "summary": template["title"],
                    "duration_minutes": template.get("duration_minutes", 5),
                    "channel": template.get("channel", ""),
                    "occurred_at": occurred.isoformat(),
                })

            # 1-2 emails per day
            for template in random.sample(EMAIL_TEMPLATES, min(random.randint(1, 2), len(EMAIL_TEMPLATES))):
                hour = random.randint(8, 17)
                minute = random.randint(0, 59)
                occurred = day.replace(hour=hour, minute=minute, second=0)
                activities.append({
                    "source": template["source"],
                    "source_id": f"email-{occurred.isoformat()}-{random.randint(1000, 9999)}",
                    "title": template["title"],
                    "summary": template["title"],
                    "duration_minutes": template.get("duration_minutes", 10),
                    "occurred_at": occurred.isoformat(),
                })

    count = db.insert_activities_bulk(activities)

    # Classify all activities
    all_activities = db.get_activities(limit=5000)
    classifications = classify_batch(all_activities, use_llm=False)
    db.insert_classifications_bulk(classifications)

    # Seed decisions
    for d in SAMPLE_DECISIONS:
        db.insert_decision(
            description=d["description"],
            channel=d.get("channel", ""),
            related_priority=d.get("related_priority"),
        )

    # Seed open questions
    for q in SAMPLE_QUESTIONS:
        db.insert_open_question(
            description=q["description"],
            urgency=q.get("urgency", "medium"),
            owner=q.get("owner", ""),
            related_priority=q.get("related_priority"),
        )

    print(f"Seeded {count} activities, {len(classifications)} classified, {len(SAMPLE_DECISIONS)} decisions, {len(SAMPLE_QUESTIONS)} questions")
