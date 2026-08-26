import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, JSON
from app.database import Base


class Export(Base):
    __tablename__ = "exports"

    id           = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    export_type  = Column(String(50), nullable=False)
    file_path    = Column(String)
    record_count = Column(Integer)
    exported_by  = Column(String(36), ForeignKey("users.id"))
    filters_used = Column(JSON)
    created_at   = Column(DateTime(timezone=True), default=datetime.utcnow)
