import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Numeric, Boolean, ForeignKey, DateTime, Date, JSON
from sqlalchemy.orm import relationship
from app.database import Base


class LoanRecord(Base):
    __tablename__ = "loan_records"

    id                = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    upload_id         = Column(String(36), ForeignKey("uploads.id", ondelete="CASCADE"), nullable=False)
    source_row        = Column(Integer)

    loan_id           = Column(String(100), nullable=False, index=True)
    borrower_id       = Column(String(100), index=True)
    borrower_name     = Column(String(500))
    co_borrower_name  = Column(String(500))

    loan_type         = Column(String(100))
    loan_purpose      = Column(String(100))
    property_state    = Column(String(10))
    borrower_state    = Column(String(10))
    property_zip      = Column(String(20))
    servicer_name     = Column(String(255))

    original_principal = Column(Numeric(15, 2))
    current_balance    = Column(Numeric(15, 2))
    interest_rate      = Column(Numeric(8, 4))
    monthly_payment    = Column(Numeric(15, 2))
    term_months        = Column(Integer)

    origination_date   = Column(Date)
    maturity_date      = Column(Date)
    last_payment_date  = Column(Date)
    next_payment_date  = Column(Date)
    last_updated_at    = Column(Date)

    payment_status     = Column(String(50))
    days_past_due      = Column(Integer, default=0)
    document_status    = Column(String(50))
    lien_position      = Column(String(20))
    credit_grade       = Column(String(20))
    employment_length  = Column(String(50))
    income_band        = Column(String(50))
    source_system      = Column(String(100))

    raw_data           = Column(JSON)
    parse_errors       = Column(JSON)
    normalized_at      = Column(DateTime(timezone=True), default=datetime.utcnow)
    is_duplicate       = Column(Boolean, default=False)
    duplicate_of       = Column(String(100))

    created_at         = Column(DateTime(timezone=True), default=datetime.utcnow)

    upload              = relationship("Upload", back_populates="loan_records")
    validation_results  = relationship("ValidationResult", back_populates="loan_record", cascade="all, delete-orphan")
    exceptions          = relationship("Exception", back_populates="loan_record", cascade="all, delete-orphan")
    verified_loan       = relationship("VerifiedLoan", back_populates="loan_record", uselist=False)
