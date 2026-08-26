import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Numeric, ForeignKey, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from app.database import Base


class AIRecommendation(Base):
    __tablename__ = "ai_recommendations"

    id                = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    exception_id      = Column(String(36), ForeignKey("exceptions.id", ondelete="CASCADE"), nullable=False)
    loan_id           = Column(String(100), nullable=False, index=True)

    explanation       = Column(Text)
    suggested_value   = Column(Text)
    suggested_action  = Column(String(100))
    confidence_score  = Column(Numeric(5, 2))
    severity_reason   = Column(Text)
    source_comparison = Column(JSON)
    generated_note    = Column(Text)
    batch_summary     = Column(Text)

    model_used        = Column(String(100))
    prompt_text       = Column(Text)
    prompt_tokens     = Column(Integer)
    completion_tokens = Column(Integer)
    latency_ms        = Column(Integer)
    created_at        = Column(DateTime(timezone=True), default=datetime.utcnow)

    exception = relationship("Exception", back_populates="ai_recommendation")
