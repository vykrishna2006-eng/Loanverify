"""
Module A — Data Ingestion Service
CSV upload → parse → normalize → bulk insert → lineage
"""
import os
import uuid
import hashlib
from datetime import datetime, date
from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal, InvalidOperation

import pandas as pd
from sqlalchemy.orm import Session

from app.models.upload import Upload
from app.models.loan import LoanRecord
from app.models.mongo_user import MongoUser as User
from app.config import settings

# ─── Canonical column mapping ────────────────────────────────────────────────
# Maps many possible column name variants → our internal field names

COLUMN_ALIASES: Dict[str, str] = {
    # Loan ID
    "loan_id": "loan_id", "loanid": "loan_id", "loan id": "loan_id",
    "loan_number": "loan_id", "loan number": "loan_id",

    # Borrower
    "borrower_id": "borrower_id", "borrowerid": "borrower_id",
    "borrower_name": "borrower_name", "borrower name": "borrower_name",
    "co_borrower_name": "co_borrower_name", "coborrower": "co_borrower_name",

    # Financial
    "original_principal": "original_principal", "originalprincipal": "original_principal",
    "original_balance": "original_principal", "loan_amount": "original_principal",
    "current_balance": "current_balance", "currentbalance": "current_balance",
    "balance": "current_balance", "outstanding_balance": "current_balance",
    "interest_rate": "interest_rate", "interestrate": "interest_rate",
    "rate": "interest_rate", "note_rate": "interest_rate",
    "monthly_payment": "monthly_payment", "monthlypayment": "monthly_payment",
    "payment": "monthly_payment",

    # Dates
    "origination_date": "origination_date", "originationdate": "origination_date",
    "loan_date": "origination_date", "close_date": "origination_date",
    "maturity_date": "maturity_date", "maturitydate": "maturity_date",
    "last_payment_date": "last_payment_date", "lastpaymentdate": "last_payment_date",
    "next_payment_date": "next_payment_date", "nextpaymentdate": "next_payment_date",

    # Status
    "payment_status": "payment_status", "paymentstatus": "payment_status",
    "status": "payment_status", "loan_status": "payment_status",
    "days_past_due": "days_past_due", "dayspastdue": "days_past_due", "dpd": "days_past_due",
    "document_status": "document_status", "documentstatus": "document_status",
    "doc_status": "document_status",

    # Loan details
    "loan_type": "loan_type", "loantype": "loan_type",
    "loan_purpose": "loan_purpose", "purpose": "loan_purpose",
    "property_state": "property_state", "state": "property_state", "prop_state": "property_state",
    "borrower_state": "borrower_state",
    "property_zip": "property_zip", "zip": "property_zip", "zip_code": "property_zip",
    "servicer_name": "servicer_name", "servicer": "servicer_name",
    "lien_position": "lien_position", "lien": "lien_position",
    "term_months": "term_months", "term": "term_months", "loan_term": "term_months",
    "credit_grade": "credit_grade", "credit_score_band": "credit_grade",
    "employment_length": "employment_length",
    "income_band": "income_band",
    "last_updated_at": "last_updated_at", "last_updated": "last_updated_at", "updated_at": "last_updated_at",
    "source_system": "source_system",
}

VALID_US_STATES = {
    "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL","IN","IA",
    "KS","KY","LA","ME","MD","MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ",
    "NM","NY","NC","ND","OH","OK","OR","PA","RI","SC","SD","TN","TX","UT","VT",
    "VA","WA","WV","WI","WY","DC","PR","GU","VI","AS","MP",
}

VALID_PAYMENT_STATUSES = {"CURRENT", "DELINQUENT", "DEFAULT", "PAID_OFF", "CLOSED", "FORECLOSURE"}


def normalize_column_name(col: str) -> str:
    """Lower + strip + replace spaces/hyphens."""
    return col.strip().lower().replace(" ", "_").replace("-", "_")


def parse_date(val: Any) -> Tuple[Optional[date], Optional[str]]:
    """Return (parsed_date, error). Empty is (None, None); unparseable is (None, raw)."""
    if pd.isna(val) or val == "" or val is None:
        return None, None
    if isinstance(val, (date, datetime)):
        return (val.date() if isinstance(val, datetime) else val), None
    raw = str(val).strip()
    try:
        parsed = pd.to_datetime(raw, dayfirst=False, errors="raise")
        return parsed.date(), None
    except Exception:
        return None, raw


def parse_decimal(val: Any) -> Optional[Decimal]:
    if pd.isna(val) or val == "" or val is None:
        return None
    try:
        clean = str(val).replace(",", "").replace("$", "").replace("₹", "").strip()
        return Decimal(clean)
    except (InvalidOperation, ValueError):
        return None


def parse_int(val: Any) -> Optional[int]:
    if pd.isna(val) or val == "" or val is None:
        return None
    try:
        return int(float(str(val)))
    except (ValueError, TypeError):
        return None


def normalize_payment_status(val: Any) -> Optional[str]:
    if pd.isna(val) or val is None:
        return None
    mapping = {
        "current": "CURRENT", "cur": "CURRENT", "ok": "CURRENT",
        "delinquent": "DELINQUENT", "del": "DELINQUENT", "late": "DELINQUENT",
        "default": "DEFAULT", "def": "DEFAULT",
        "paid_off": "PAID_OFF", "paidoff": "PAID_OFF", "paid off": "PAID_OFF", "paid": "PAID_OFF",
        "closed": "CLOSED",
        "foreclosure": "FORECLOSURE", "fc": "FORECLOSURE",
    }
    return mapping.get(str(val).strip().lower(), str(val).strip().upper())


def normalize_state(val: Any) -> Optional[str]:
    if pd.isna(val) or val is None:
        return None
    s = str(val).strip().upper()
    return s if s in VALID_US_STATES else s


def map_row_to_loan(row: pd.Series, raw: Dict, source_row: int, upload_id) -> Dict[str, Any]:
    """Convert a normalized DataFrame row to a LoanRecord-compatible dict."""
    orig_date, orig_err = parse_date(row.get("origination_date"))
    mat_date, mat_err = parse_date(row.get("maturity_date"))
    last_pay, last_pay_err = parse_date(row.get("last_payment_date"))
    next_pay, next_pay_err = parse_date(row.get("next_payment_date"))
    last_upd, last_upd_err = parse_date(row.get("last_updated_at"))

    parse_errors = {}
    if orig_err:
        parse_errors["origination_date"] = orig_err
    if mat_err:
        parse_errors["maturity_date"] = mat_err
    if last_pay_err:
        parse_errors["last_payment_date"] = last_pay_err
    if next_pay_err:
        parse_errors["next_payment_date"] = next_pay_err
    if last_upd_err:
        parse_errors["last_updated_at"] = last_upd_err

    borrower_state = normalize_state(row.get("borrower_state"))
    property_state = normalize_state(row.get("property_state")) or borrower_state

    return {
        "id": str(uuid.uuid4()),
        "upload_id": upload_id,
        "source_row": source_row,
        "loan_id": str(row.get("loan_id", "")).strip() or None,
        "borrower_id": str(row.get("borrower_id", "")).strip() or None if row.get("borrower_id") else None,
        "borrower_name": str(row.get("borrower_name", "")).strip() or None if row.get("borrower_name") else None,
        "co_borrower_name": str(row.get("co_borrower_name", "")).strip() or None if row.get("co_borrower_name") else None,
        "loan_type": str(row.get("loan_type", "")).strip() or None if row.get("loan_type") else None,
        "loan_purpose": str(row.get("loan_purpose", "")).strip() or None if row.get("loan_purpose") else None,
        "property_state": property_state,
        "borrower_state": borrower_state or property_state,
        "property_zip": str(row.get("property_zip", "")).strip() or None if row.get("property_zip") else None,
        "servicer_name": str(row.get("servicer_name", "")).strip() or None if row.get("servicer_name") else None,
        "original_principal": parse_decimal(row.get("original_principal")),
        "current_balance": parse_decimal(row.get("current_balance")),
        "interest_rate": parse_decimal(row.get("interest_rate")),
        "monthly_payment": parse_decimal(row.get("monthly_payment")),
        "term_months": parse_int(row.get("term_months")),
        "origination_date": orig_date,
        "maturity_date": mat_date,
        "last_payment_date": last_pay,
        "next_payment_date": next_pay,
        "last_updated_at": last_upd,
        "payment_status": normalize_payment_status(row.get("payment_status")),
        "days_past_due": parse_int(row.get("days_past_due")) or 0,
        "document_status": str(row.get("document_status", "")).strip().upper() or None if row.get("document_status") else None,
        "lien_position": str(row.get("lien_position", "")).strip() or None if row.get("lien_position") else None,
        "credit_grade": str(row.get("credit_grade", "")).strip() or None if row.get("credit_grade") else None,
        "employment_length": str(row.get("employment_length", "")).strip() or None if row.get("employment_length") else None,
        "income_band": str(row.get("income_band", "")).strip() or None if row.get("income_band") else None,
        "source_system": str(row.get("source_system", "")).strip() or None if row.get("source_system") else None,
        "raw_data": raw,
        "parse_errors": parse_errors or None,
        "is_duplicate": False,
    }


def ingest_csv(
    db: Session,
    file_path: str,
    original_filename: str,
    file_size: int,
    source_type: str,
    uploader: User,
) -> Tuple[Upload, List[Dict]]:
    """
    Full ingestion pipeline:
    1. Create upload record
    2. Parse CSV with pandas
    3. Normalize column names
    4. Map rows to LoanRecord dicts
    5. Detect duplicates within batch
    6. Bulk insert
    7. Update upload summary
    Returns (upload, failed_rows)
    """
    upload = Upload(
        filename=os.path.basename(file_path),
        original_filename=original_filename,
        file_size=file_size,
        file_path=file_path,
        source_type=source_type,
        status="PROCESSING",
        uploaded_by=uploader.id,
    )
    db.add(upload)
    db.flush()  # get upload.id

    failed_rows: List[Dict] = []
    records_to_insert: List[Dict] = []

    # ── Parse CSV ──────────────────────────────────────────────────────────
    try:
        df = pd.read_csv(
            file_path,
            dtype=str,            # read everything as string first
            keep_default_na=False,
            na_values=["", "N/A", "n/a", "NULL", "null", "None", "none", "#N/A"],
        )
    except Exception as e:
        upload.status = "FAILED"
        upload.error_summary = {"error": str(e)}
        upload.completed_at = datetime.utcnow()
        db.flush()
        return upload, []

    upload.total_rows = len(df)

    # ── Normalize column names ─────────────────────────────────────────────
    df.columns = [normalize_column_name(c) for c in df.columns]
    # Remap aliases
    rename_map = {}
    for col in df.columns:
        canonical = COLUMN_ALIASES.get(col)
        if canonical and canonical != col:
            rename_map[col] = canonical
    if rename_map:
        df = df.rename(columns=rename_map)

    if source_type == "DOCUMENT_MANIFEST":
        return _ingest_document_manifest(db, upload, df)

    # ── Detect duplicates within the batch ────────────────────────────────
    seen_loan_ids: Dict[str, int] = {}

    for idx, row in df.iterrows():
        row_num = int(idx) + 2  # 1-indexed, +1 for header
        row_dict = row.to_dict()

        # Basic required-field check at parse time
        loan_id_raw = str(row.get("loan_id", "")).strip()
        if not loan_id_raw or loan_id_raw.lower() in ("nan", "none", ""):
            failed_rows.append({
                "row": row_num,
                "error": "Missing loan_id",
                "data": row_dict,
            })
            continue

        mapped = map_row_to_loan(row, row_dict, row_num, upload.id)

        # Mark duplicates
        if loan_id_raw in seen_loan_ids:
            mapped["is_duplicate"] = True
            mapped["duplicate_of"] = loan_id_raw
        else:
            seen_loan_ids[loan_id_raw] = row_num

        records_to_insert.append(mapped)

    # ── Bulk insert ────────────────────────────────────────────────────────
    if records_to_insert:
        db.bulk_insert_mappings(LoanRecord, records_to_insert)

    # ── Update upload summary ──────────────────────────────────────────────
    upload.imported_rows = len(records_to_insert)
    upload.failed_rows = len(failed_rows)
    upload.error_summary = {"failed_rows": failed_rows[:50]} if failed_rows else None
    upload.status = "COMPLETED"
    upload.completed_at = datetime.utcnow()
    db.flush()

    return upload, failed_rows


def _ingest_document_manifest(db: Session, upload: Upload, df: pd.DataFrame) -> Tuple[Upload, List[Dict]]:
    """Merge mock document availability onto existing loan records by loan_id."""
    failed_rows: List[Dict] = []
    updated = 0
    for idx, row in df.iterrows():
        row_num = int(idx) + 2
        loan_id_raw = str(row.get("loan_id", "")).strip()
        if not loan_id_raw:
            failed_rows.append({"row": row_num, "error": "Missing loan_id", "data": row.to_dict()})
            continue
        doc_status = str(row.get("document_status", "")).strip().upper() or None
        loans = db.query(LoanRecord).filter(LoanRecord.loan_id == loan_id_raw).all()
        if not loans:
            failed_rows.append({"row": row_num, "error": f"No loan found for {loan_id_raw}", "data": row.to_dict()})
            continue
        for loan in loans:
            if doc_status:
                loan.document_status = doc_status
            raw = dict(loan.raw_data or {})
            raw["document_manifest"] = row.to_dict()
            loan.raw_data = raw
            updated += 1

    upload.imported_rows = updated
    upload.failed_rows = len(failed_rows)
    upload.error_summary = {"failed_rows": failed_rows[:50], "merged_document_status": True} if failed_rows else {"merged_document_status": True}
    upload.status = "COMPLETED"
    upload.completed_at = datetime.utcnow()
    db.flush()
    return upload, failed_rows
