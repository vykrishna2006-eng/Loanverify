import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from app.database import Base


class ReviewDecision(Base):
    __tablename__ = "review_decisions"

    id                   = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    exception_id         = Column(String(36), ForeignKey("exceptions.id", ondelete="CASCADE"), nullable=False)
    ai_recommendation_id = Column(String(36), ForeignKey("ai_recommendations.id"))
    reviewer_id          = Column(String(36), nullable=False)
    decision             = Column(String(50), nullable=False)
    ai_decision_followed = Column(Boolean)
    original_value       = Column(Text)
    corrected_value      = Column(Text)
    reviewer_note        = Column(Text)
    created_at           = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Many decisions per exception (full history preserved)
    exception = relationship("Exception", back_populates="review_decisions")
    ai_rec    = relationship("AIRecommendation")
