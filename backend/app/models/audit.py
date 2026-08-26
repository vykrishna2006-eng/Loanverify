import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, ForeignKey, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from app.database import Base


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id           = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_type   = Column(String(100), nullable=False, index=True)
    actor_id     = Column(String(36), ForeignKey("users.id"))
    actor_email  = Column(String(255))
    loan_id      = Column(String(100), index=True)
    upload_id    = Column(String(36), ForeignKey("uploads.id"))
    exception_id = Column(String(36), ForeignKey("exceptions.id"))

    old_value    = Column(JSON)
    new_value    = Column(JSON)
    reason       = Column(Text)

    ai_involved  = Column(Boolean, default=False)
    ai_metadata  = Column(JSON)

    ip_address   = Column(String(45))
    user_agent   = Column(Text)
    # Named 'metadata' logically — column is metadata to avoid SQLAlchemy reserved-word conflict
    extra_metadata = Column("metadata", JSON)

    created_at   = Column(DateTime(timezone=True), default=datetime.utcnow, index=True)
    upload    = relationship("Upload", back_populates="audit_events")
    exception = relationship("Exception", back_populates="audit_events")
