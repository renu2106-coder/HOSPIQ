from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.models.models import User, Document, ValidationResult
from backend.schemas.schemas import ValidationResultOut
from backend.security.auth import get_current_user, require_roles
from backend.agents.validation_agent import ValidationAgent
from backend.skills.audit_logging_skill import log_audit_event

router = APIRouter(prefix="/api/validation", tags=["Validation Agent"])


@router.post("/document/{document_id}", response_model=ValidationResultOut)
def run_document_validation(
    document_id: int,
    current_user: User = Depends(require_roles(["Doctor", "Hospital Administrator"])),
    db: Session = Depends(get_db)
):
    """Executes the 7-check validation suite on an existing document."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    agent = ValidationAgent(db)
    result = agent.validate_document(document_id)

    log_audit_event(
        db=db,
        action="VALIDATION_EXECUTED",
        user_id=current_user.id,
        user_role=current_user.role,
        entity_type="ValidationResult",
        entity_id=str(result.id),
        status="SUCCESS",
        details={
            "document_id": document_id,
            "validation_status": result.status,
            "passed": result.passed_checks,
            "total": result.total_checks
        }
    )

    return result


@router.get("/document/{document_id}", response_model=List[ValidationResultOut])
def get_document_validation_results(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves validation scorecard history for a document."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    if current_user.role == "Patient" and doc.patient_id != current_user.patient_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    return db.query(ValidationResult).filter(ValidationResult.document_id == document_id).order_by(ValidationResult.created_at.desc()).all()

