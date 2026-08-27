import uuid
from datetime import datetime
from sqlalchemy import Column, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from app.database import Base


class Exception(Base):
    __tablename__ = "exceptions"

    id             = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    loan_record_id = Column(String(36), ForeignKey("loan_records.id", ondelete="CASCADE"), nullable=False)
    upload_id      = Column(String(36), ForeignKey("uploads.id"))
    loan_id        = Column(String(100), nullable=False, index=True)
    rule_id        = Column(String(20), nullable=False)
    exception_type = Column(String(100), nullable=False)
    severity       = Column(String(20), nullable=False)
    field_name     = Column(String(100))
    actual_value   = Column(Text)
    expected_value = Column(Text)
    message        = Column(Text, nullable=False)
    status         = Column(String(50), default="OPEN", index=True)
    assigned_to    = Column(String(36), )
    created_at     = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at     = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at    = Column(DateTime(timezone=True))

    loan_record       = relationship("LoanRecord", back_populates="exceptions")
    upload            = relationship("Upload", back_populates="exceptions")
    comments          = relationship("ExceptionComment", back_populates="exception", cascade="all, delete-orphan")
    ai_recommendation = relationship("AIRecommendation", back_populates="exception", uselist=False)
    # Full history — one row per decision, never deleted
    review_decisions  = relationship("ReviewDecision", back_populates="exception", order_by="ReviewDecision.created_at")
    audit_events      = relationship("AuditEvent", back_populates="exception")


# Alias so existing imports using LoanException still work
LoanException = Exception


class ExceptionComment(Base):
    __tablename__ = "exception_comments"

    id           = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    exception_id = Column(String(36), ForeignKey("exceptions.id", ondelete="CASCADE"), nullable=False)
    author_id    = Column(String(36), nullable=False)
    comment      = Column(Text, nullable=False)
    created_at   = Column(DateTime(timezone=True), default=datetime.utcnow)

    exception = relationship("Exception", back_populates="comments")
