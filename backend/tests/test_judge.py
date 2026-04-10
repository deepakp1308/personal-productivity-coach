"""Tests for the judge quality gate."""

import pytest
from backend.agents.judge import judge_recommendation, judge_batch


class TestJudgeRecommendation:
    def test_strong_recommendation_passes(self):
        rec = {
            "kind": "Accelerate",
            "action": "Increase time on 'Advanced Analytics & AI-Powered Insights' — currently at 25% vs. target 40%. Focus on analytics agent GA.",
            "rationale": "This pillar needs more attention to hit Q4 goals per the roadmap alignment.",
            "evidence_ids": [1, 2, 3],
        }
        result = judge_recommendation(rec)
        assert result["status"] == "published"
        assert result["judge_score"] >= 3.0
        assert result["_scores"]["faithfulness"] == 3
        assert result["_scores"]["specificity"] == 3

    def test_no_evidence_blocks(self):
        rec = {
            "kind": "Cut",
            "action": "Stop doing something",
            "rationale": "Just because",
            "evidence_ids": [],
        }
        result = judge_recommendation(rec)
        assert result["status"] == "blocked"
        assert result["_scores"]["faithfulness"] == 1

    def test_vague_action_blocks(self):
        rec = {
            "kind": "Redirect",
            "action": "Do better",
            "rationale": "You should improve your q4 pillar alignment.",
            "evidence_ids": [1, 2],
        }
        result = judge_recommendation(rec)
        assert result["status"] == "blocked"
        assert result["_scores"]["specificity"] == 1

    def test_no_priority_reference_blocks(self):
        rec = {
            "kind": "Accelerate",
            "action": "Spend more time on general tasks and various projects around the office that need attention",
            "rationale": "There are many things to do and you should do more of them",
            "evidence_ids": [1, 2],
        }
        result = judge_recommendation(rec)
        assert result["_scores"]["priority_fit"] == 1
        assert result["status"] == "blocked"

    def test_judge_preserves_original_fields(self):
        rec = {"kind": "Cut", "action": "test", "rationale": "test", "evidence_ids": [1]}
        result = judge_recommendation(rec)
        assert result["kind"] == "Cut"
        assert "judge_score" in result
        assert "judge_reasoning" in result


class TestJudgeBatch:
    def test_batch_judges_all(self):
        recs = [
            {"kind": "Accelerate", "action": f"Do thing {i} with 'analytics agent' priority alignment", "rationale": f"Reason {i} pillar", "evidence_ids": [i, i+1]}
            for i in range(3)
        ]
        results = judge_batch(recs)
        assert len(results) == 3
        for r in results:
            assert "judge_score" in r
