import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.database import Base


class ValidationRule(Base):
    __tablename__ = "validation_rules"

    id              = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    rule_id         = Column(String(20), unique=True, nullable=False, index=True)
    name            = Column(String(255), nullable=False)
    description     = Column(String)
    category        = Column(String(100))
    severity        = Column(String(20), default="MEDIUM")
    is_active       = Column(Boolean, default=True)
    rule_expression = Column(String)
    rule_fn_name    = Column(String(100))
    created_at      = Column(DateTime(timezone=True), default=datetime.utcnow)
    created_by      = Column(String(36), )
    source          = Column(String(50), default="SYSTEM")


class ValidationResult(Base):
    __tablename__ = "validation_results"

    id             = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    loan_record_id = Column(String(36), ForeignKey("loan_records.id", ondelete="CASCADE"), nullable=False)
    upload_id      = Column(String(36), ForeignKey("uploads.id", ondelete="CASCADE"), nullable=False)
    rule_id        = Column(String(20), nullable=False, index=True)
    passed         = Column(Boolean, nullable=False)
    created_at     = Column(DateTime(timezone=True), default=datetime.utcnow)

    loan_record = relationship("LoanRecord", back_populates="validation_results")
