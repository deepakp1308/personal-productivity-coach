"""Pydantic models for structured LLM output and API schemas."""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class ActivityType(str, Enum):
    Strategy = "Strategy"
    Discovery = "Discovery"
    Execution = "Execution"
    Stakeholder = "Stakeholder"
    InternalOps = "InternalOps"
    Reactive = "Reactive"
    LowValue = "LowValue"


class Leverage(str, Enum):
    High = "High"
    Medium = "Medium"
    Low = "Low"


class ClassifierOutput(BaseModel):
    type: ActivityType
    priority: str
    leverage: Leverage
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str


class RecKind(str, Enum):
    Accelerate = "Accelerate"
    Cut = "Cut"
    Redirect = "Redirect"


class RecommendationItem(BaseModel):
    kind: RecKind
    action: str
    rationale: str
    evidence_ids: list[int] = []


class BriefingOutput(BaseModel):
    summary: str
    alignment_pct: float = Field(ge=0.0, le=100.0)
    recommendations: list[RecommendationItem]
    uncertainty_flags: list[str] = []


class JudgeScores(BaseModel):
    faithfulness: int = Field(ge=1, le=3)
    priority_fit: int = Field(ge=1, le=3)
    specificity: int = Field(ge=1, le=3)
    harm_risk: bool = False
    privacy_compliance: bool = True
    reasoning: str


class Urgency(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"


class QuestionStatus(str, Enum):
    open = "open"
    resolved = "resolved"
    stale = "stale"
