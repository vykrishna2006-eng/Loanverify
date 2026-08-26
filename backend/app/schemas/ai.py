from pydantic import BaseModel
from typing import Optional, Any, Dict
from uuid import UUID
from datetime import datetime
from decimal import Decimal


class AIRecommendationOut(BaseModel):
    id: UUID
    exception_id: UUID
    loan_id: str
    explanation: Optional[str] = None
    suggested_value: Optional[str] = None
    suggested_action: Optional[str] = None
    confidence_score: Optional[Decimal] = None
    severity_reason: Optional[str] = None
    source_comparison: Optional[Dict[str, Any]] = None
    generated_note: Optional[str] = None
    model_used: Optional[str] = None
    prompt_text: Optional[str] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    latency_ms: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class GenerateRuleRequest(BaseModel):
    description: str   # Natural language rule description


class GeneratedRuleOut(BaseModel):
    rule_expression: str
    rule_name: str
    description: str
    suggested_severity: str
    explanation: str
    ai_generated: bool = True
    status: str = "PENDING_REVIEW"


class BatchSummaryOut(BaseModel):
    total_exceptions: int
    high_severity: int
    medium_severity: int
    low_severity: int
    summary_text: str
    most_common_issue: str
    recommendations: list
