"""Module A — Data Ingestion Router"""
import os
import shutil
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, File, UploadFile, Form, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user, require_operator
from app.models.mongo_user import MongoUser as User
from app.schemas.upload import UploadOut, UploadSummary
from app.services import ingestion_service, validation_service, audit_service
from app.config import settings

router = APIRouter()


def _run_validation_background(upload_id: str, db_url: str):
    """Background task: run validation after upload completes."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    engine = create_engine(db_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    try:
        validation_service.run_validation(db, uuid.UUID(upload_id))
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Background validation error: {e}")
    finally:
        db.close()


@router.post("", response_model=UploadSummary, summary="Upload a loan CSV file")
async def upload_csv(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    source_type: str = Form(default="LOAN_TAPE"),
    run_validation: bool = Form(default=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_operator),
):
    """
    **Module A — Data Ingestion**

    Upload a CSV loan tape. The system will:
    1. Validate the file format
    2. Parse and normalize all columns
    3. Bulk insert loan records (preserving raw data)
    4. Optionally run the validation engine immediately

    Returns an import summary with counts of imported and failed rows.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")

    max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    # Save file
    safe_name = f"{uuid.uuid4()}_{file.filename.replace(' ', '_')}"
    file_path = os.path.join(settings.UPLOAD_DIR, safe_name)

    content = await file.read()
    if len(content) > max_size:
        raise HTTPException(status_code=413, detail=f"File exceeds {settings.MAX_UPLOAD_SIZE_MB}MB limit")

    with open(file_path, "wb") as f:
        f.write(content)

    # Ingest
    upload, failed_rows = ingestion_service.ingest_csv(
        db=db,
        file_path=file_path,
        original_filename=file.filename,
        file_size=len(content),
        source_type=source_type,
        uploader=current_user,
    )

    # Audit: file uploaded
    audit_service.log_event(
        db=db,
        event_type=audit_service.AuditEventType.FILE_UPLOADED,
        actor=current_user,
        upload_id=upload.id,
        new_value={
            "filename": file.filename,
            "size": len(content),
            "source_type": source_type,
        },
    )
    audit_service.log_event(
        db=db,
        event_type=audit_service.AuditEventType.RECORDS_IMPORTED,
        actor=current_user,
        upload_id=upload.id,
        new_value={
            "total_rows": upload.total_rows,
            "imported_rows": upload.imported_rows,
            "failed_rows": upload.failed_rows,
        },
    )

    # Run validation inline or background
    exceptions_created = 0
    if run_validation and upload.imported_rows > 0:
        audit_service.log_event(
            db=db,
            event_type=audit_service.AuditEventType.VALIDATION_EXECUTED,
            actor=current_user,
            upload_id=upload.id,
        )
        db.commit()  # commit records before validation

        val_result = validation_service.run_validation(db, upload.id)
        exceptions_created = val_result.get("exceptions", 0)

        audit_service.log_event(
            db=db,
            event_type=audit_service.AuditEventType.EXCEPTION_CREATED,
            actor=current_user,
            upload_id=upload.id,
            new_value=val_result,
        )

    db.commit()

    return UploadSummary(
        upload_id=upload.id,
        filename=upload.original_filename,
        total_rows=upload.total_rows,
        imported_rows=upload.imported_rows,
        failed_rows=upload.failed_rows,
        validation_errors=exceptions_created,
        exceptions_created=exceptions_created,
        status=upload.status,
        failed_row_details=failed_rows[:20],
    )


@router.get("", summary="List all uploads")
def list_uploads(
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.models.upload import Upload
    q = db.query(Upload).order_by(Upload.created_at.desc())
    total = q.count()
    items = q.offset((page - 1) * page_size).limit(page_size).all()
    return {
        "items": [UploadOut.model_validate(u) for u in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{upload_id}", response_model=UploadOut, summary="Get upload by ID")
def get_upload(
    upload_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.models.upload import Upload
    upload = db.query(Upload).filter(Upload.id == upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    return upload


@router.post("/{upload_id}/validate", summary="Re-run validation on an upload")
def rerun_validation(
    upload_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_operator),
):
    result = validation_service.run_validation(db, uuid.UUID(upload_id))
    audit_service.log_event(
        db=db,
        event_type=audit_service.AuditEventType.VALIDATION_EXECUTED,
        actor=current_user,
        upload_id=uuid.UUID(upload_id),
        new_value=result,
    )
    db.commit()
    return result


@router.get("/{upload_id}/quality-score", summary="Get data quality score for an upload")
def get_quality_score(
    upload_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return validation_service.compute_data_quality_score(db, uuid.UUID(upload_id))
