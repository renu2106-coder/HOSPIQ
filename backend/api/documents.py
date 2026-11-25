from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.models.models import User, Document, DocumentVersion
from backend.schemas.schemas import (
    DocumentOut, DocumentGenerateRequest, DocumentUpdate,
    DocumentReviewRequest, DocumentVersionOut
)
from backend.security.auth import get_current_user, require_roles
from backend.skills.audit_logging_skill import log_audit_event
from backend.skills.document_generation_skill import strip_markdown_symbols
from backend.agents.orchestrator_agent import OrchestratorAgent

router = APIRouter(prefix="/api/documents", tags=["AI Documentation"])


@router.post("/generate", response_model=DocumentOut)
def generate_document_workflow(
    req: DocumentGenerateRequest,
    current_user: User = Depends(require_roles(["Doctor", "Paramedic", "Hospital Administrator"])),
    db: Session = Depends(get_db)
):
    """Initiates multi-agent document generation pipeline:

    Consolidates data -> Documentation Agent synthesizes draft -> Validation Agent executes checks -> Stages for Doctor Review.
    """
    clean_id = req.patient_id.strip().upper()

    orchestrator = OrchestratorAgent(db)
    pipeline_res = orchestrator.execute_document_generation_pipeline(
        patient_id=clean_id,
        doc_type=req.doc_type,
        natural_language_request=req.natural_language_request,
        user_id=current_user.id
    )

    if "error" in pipeline_res:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=pipeline_res["error"])

    doc = db.query(Document).filter(Document.id == pipeline_res["document_id"]).first()

    log_audit_event(
        db=db,
        action="DOCUMENT_GENERATED",
        user_id=current_user.id,
        user_role=current_user.role,
        entity_type="Document",
        entity_id=str(doc.id),
        status="SUCCESS",
        details={
            "patient_id": clean_id,
            "doc_type": req.doc_type,
            "validation_status": doc.validation_status
        }
    )

    return doc


@router.get("", response_model=List[DocumentOut])
def list_documents(
    patient_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lists clinical documents with role-based filtering."""
    q = db.query(Document)

    # Patients can only view APPROVED documents belonging to themselves
    if current_user.role == "Patient":
        q = q.filter(
            Document.patient_id == current_user.patient_id,
            Document.validation_status == "Approved"
        )
    elif current_user.role in ("Nurse", "Pharmacist", "Radiologist"):
        # Department staff can view Approved or Pending documents for permitted patients
        if patient_id:
            q = q.filter(Document.patient_id == patient_id.strip().upper())
    elif patient_id:
        q = q.filter(Document.patient_id == patient_id.strip().upper())

    return q.order_by(Document.created_at.desc()).all()


@router.get("/{document_id}", response_model=DocumentOut)
def get_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves document detail including its version history and validation results."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    if current_user.role == "Patient":
        if doc.patient_id != current_user.patient_id or doc.validation_status != "Approved":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You are not authorized to view this document."
            )

    log_audit_event(
        db=db,
        action="DOCUMENT_VIEW",
        user_id=current_user.id,
        user_role=current_user.role,
        entity_type="Document",
        entity_id=str(doc.id),
        status="SUCCESS"
    )

    return doc


@router.put("/{document_id}", response_model=DocumentOut)
def edit_document(
    document_id: int,
    payload: DocumentUpdate,
    current_user: User = Depends(require_roles(["Doctor", "Paramedic"])),
    db: Session = Depends(get_db)
):
    """Allows an authorized Doctor or Paramedic to edit and revise the document text, saving a new version."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    # Determine next version number
    current_versions = db.query(DocumentVersion).filter(DocumentVersion.document_id == doc.id).count()
    next_ver = current_versions + 1

    clean_content = strip_markdown_symbols(payload.content)
    doc.content = clean_content
    doc.validation_status = "Revised"
    doc.updated_at = datetime.utcnow()

    editor_title = "Paramedic Revision" if current_user.role == "Paramedic" else "Physician Revision"
    new_ver = DocumentVersion(
        document_id=doc.id,
        version_number=next_ver,
        content=clean_content,
        changed_by_user_id=current_user.id,
        change_summary=payload.change_summary or f"{editor_title} by {current_user.full_name}",
        created_at=datetime.utcnow()
    )
    db.add(new_ver)
    db.commit()
    db.refresh(doc)

    log_audit_event(
        db=db,
        action="DOCUMENT_EDITED",
        user_id=current_user.id,
        user_role=current_user.role,
        entity_type="Document",
        entity_id=str(doc.id),
        status="SUCCESS",
        details={"version": next_ver, "change_summary": payload.change_summary, "role": current_user.role}
    )

    return doc


@router.post("/{document_id}/review", response_model=DocumentOut)
def review_document(
    document_id: int,
    review: DocumentReviewRequest,
    current_user: User = Depends(require_roles(["Doctor", "Paramedic"])),
    db: Session = Depends(get_db)
):
    """Enforces clinical approval: Doctors approve/reject. Paramedics can directly issue in extreme emergency conditions."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    if current_user.role == "Paramedic":
        if not review.is_emergency:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Paramedics can only directly issue documents in extreme emergency conditions. Routine reviews require an authorized Doctor."
            )
        act = "APPROVE"
        new_status = "Approved"
        override_reason = review.emergency_override_reason or "Field Triage Emergency Direct Issuance"
        doc.doctor_notes = f"[EMERGENCY DIRECT ISSUE - {current_user.full_name} ({current_user.role})]: {override_reason}. {review.doctor_notes or ''}"
        doc.validation_status = new_status
        doc.reviewed_by_doctor_id = current_user.id
        doc.reviewed_at = datetime.utcnow()
        doc.updated_at = datetime.utcnow()

        current_versions = db.query(DocumentVersion).filter(DocumentVersion.document_id == doc.id).count()
        new_ver = DocumentVersion(
            document_id=doc.id,
            version_number=current_versions + 1,
            content=doc.content,
            changed_by_user_id=current_user.id,
            change_summary=f"Emergency Direct Issue by Paramedic: {override_reason}",
            created_at=datetime.utcnow()
        )
        db.add(new_ver)
        db.commit()
        db.refresh(doc)

        log_audit_event(
            db=db,
            action="EMERGENCY_DOCUMENT_ISSUED",
            user_id=current_user.id,
            user_role=current_user.role,
            entity_type="Document",
            entity_id=str(doc.id),
            status="SUCCESS",
            details={"emergency_override": override_reason, "notes": doc.doctor_notes}
        )
        return doc

    # Standard Doctor review
    act = review.action.strip().upper()
    if act not in ("APPROVE", "REJECT"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Action must be APPROVE or REJECT.")

    new_status = "Approved" if act == "APPROVE" else "Rejected"
    doc.validation_status = new_status
    doc.doctor_notes = review.doctor_notes
    doc.reviewed_by_doctor_id = current_user.id
    doc.reviewed_at = datetime.utcnow()
    doc.updated_at = datetime.utcnow()

    # Track decision in version history
    current_versions = db.query(DocumentVersion).filter(DocumentVersion.document_id == doc.id).count()
    new_ver = DocumentVersion(
        document_id=doc.id,
        version_number=current_versions + 1,
        content=doc.content,
        changed_by_user_id=current_user.id,
        change_summary=f"Physician {new_status}: {review.doctor_notes or 'No notes provided'}",
        created_at=datetime.utcnow()
    )
    db.add(new_ver)

    db.commit()
    db.refresh(doc)

    log_audit_event(
        db=db,
        action=f"DOCUMENT_{new_status.upper()}",
        user_id=current_user.id,
        user_role=current_user.role,
        entity_type="Document",
        entity_id=str(doc.id),
        status="SUCCESS",
        details={"doctor_notes": review.doctor_notes, "final_status": new_status}
    )

    return doc


@router.get("/{document_id}/versions", response_model=List[DocumentVersionOut])
def get_document_versions(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves immutable version history for the specified document."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    if current_user.role == "Patient" and doc.patient_id != current_user.patient_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    return db.query(DocumentVersion).filter(DocumentVersion.document_id == document_id).order_by(DocumentVersion.version_number.asc()).all()

