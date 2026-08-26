import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, BigInteger, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from app.database import Base


class Upload(Base):
    __tablename__ = "uploads"

    id                = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    filename          = Column(String(500), nullable=False)
    original_filename = Column(String(500), nullable=False)
    file_size         = Column(BigInteger)
    file_path         = Column(String)
    source_type       = Column(String(50), default="LOAN_TAPE")
    total_rows        = Column(Integer, default=0)
    imported_rows     = Column(Integer, default=0)
    failed_rows       = Column(Integer, default=0)
    status            = Column(String(50), default="PROCESSING")
    error_summary     = Column(JSON)
    uploaded_by       = Column(String(36), ForeignKey("users.id"))
    created_at        = Column(DateTime(timezone=True), default=datetime.utcnow)
    completed_at      = Column(DateTime(timezone=True))
    loan_records     = relationship("LoanRecord", back_populates="upload", cascade="all, delete-orphan")
    exceptions       = relationship("Exception", back_populates="upload")
    audit_events     = relationship("AuditEvent", back_populates="upload")
