import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from app.database import Base


class VerifiedLoan(Base):
    __tablename__ = "verified_loans"

    id               = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    loan_id          = Column(String(100), unique=True, nullable=False, index=True)
    loan_record_id   = Column(String(36), ForeignKey("loan_records.id"), nullable=False)
    upload_id        = Column(String(36), ForeignKey("uploads.id"))

    # Module E: canonical data + source file reference
    canonical_data   = Column(JSON, nullable=False)
    source_file      = Column(String(500))
    source_row       = Column(Integer)
    data_lineage     = Column(JSON)   # field-level lineage

    # Module E: validation result
    validation_summary  = Column(JSON)   # per-category quality scores
    exception_count     = Column(Integer, default=0)

    # Module E: reviewer decision + AI recommendation references (stored as JSON arrays)
    ai_recommendation_ids  = Column(JSON, default=list)   # [str(uuid), ...]
    reviewer_decision_ids  = Column(JSON, default=list)   # [str(uuid), ...]

    # Module E: verification stamp
    verified_by      = Column(String(36), nullable=False)
    verified_at      = Column(DateTime(timezone=True), default=datetime.utcnow)
    record_hash      = Column(String(64), nullable=False)
    hash_algorithm   = Column(String(20), default="SHA-256")
    is_hash_valid    = Column(Boolean, default=True)

    status           = Column(String(50), default="VERIFIED")
    notes            = Column(Text)
    exported_at      = Column(DateTime(timezone=True))
    export_count     = Column(Integer, default=0)

    loan_record      = relationship("LoanRecord", back_populates="verified_loan")
