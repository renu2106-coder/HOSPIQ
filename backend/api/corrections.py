from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.models.models import User, CorrectionRequest, Patient, DepartmentAlert
from backend.schemas.schemas import (
    CorrectionRequestCreate, CorrectionRequestReview, CorrectionRequestOut
)
from backend.security.auth import get_current_user, require_roles
from backend.skills.audit_logging_skill import log_audit_event
from backend.agents.patient_data_agent import PatientDataManagementAgent

router = APIRouter(prefix="/api/corrections", tags=["Correction Requests"])


@router.post("", response_model=CorrectionRequestOut)
def create_correction_request(
    req: CorrectionRequestCreate,
    current_user: User = Depends(require_roles(["Doctor", "Hospital Administrator", "Nurse", "Pharmacist", "Radiologist"])),
    db: Session = Depends(get_db)
):
    """Submits a formal request to correct discrepant patient or department data."""
    clean_id = req.patient_id.strip().upper()
    patient = db.query(Patient).filter(Patient.id == clean_id).first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found.")

    correction = CorrectionRequest(
        alert_id=req.alert_id,
        patient_id=clean_id,
        department=req.department,
        field_name=req.field_name,
        original_value=req.original_value,
        proposed_value=req.proposed_value,
        justification=req.justification,
        requested_by_user_id=current_user.id,
        status="Pending Review",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(correction)
    db.commit()
    db.refresh(correction)

    log_audit_event(
        db=db,
        action="CORRECTION_REQUEST_SUBMITTED",
        user_id=current_user.id,
        user_role=current_user.role,
        entity_type="CorrectionRequest",
        entity_id=str(correction.id),
        status="SUCCESS",
        details={
            "patient_id": clean_id,
            "field": req.field_name,
            "original": req.original_value,
            "proposed": req.proposed_value
        }
    )

    return correction


@router.get("", response_model=List[CorrectionRequestOut])
def list_corrections(
    status_filter: Optional[str] = None,
    patient_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role == "Patient":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized")

    q = db.query(CorrectionRequest)
    if status_filter:
        q = q.filter(CorrectionRequest.status == status_filter)
    if patient_id:
        q = q.filter(CorrectionRequest.patient_id == patient_id.strip().upper())
    return q.order_by(CorrectionRequest.created_at.desc()).all()


@router.post("/{correction_id}/review", response_model=CorrectionRequestOut)
def review_correction(
    correction_id: int,
    payload: CorrectionRequestReview,
    current_user: User = Depends(require_roles(["Doctor", "Hospital Administrator"])),
    db: Session = Depends(get_db)
):
    """Approves or rejects a data correction request. When approved, applies controlled database update."""
    correction = db.query(CorrectionRequest).filter(CorrectionRequest.id == correction_id).first()
    if not correction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Correction request not found.")

    decision = payload.action.strip().upper()
    if decision not in ("APPROVE", "REJECT"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Action must be APPROVE or REJECT.")

    new_status = "Approved" if decision == "APPROVE" else "Rejected"
    correction.status = new_status
    correction.reviewed_by_user_id = current_user.id
    correction.review_notes = payload.review_notes
    correction.updated_at = datetime.utcnow()

    # If approved, perform controlled update on the Patient model if applicable
    if decision == "APPROVE":
        patient = db.query(Patient).filter(Patient.id == correction.patient_id).first()
        if patient and hasattr(patient, correction.field_name):
            setattr(patient, correction.field_name, correction.proposed_value)
            patient.updated_at = datetime.utcnow()

        # If linked to an alert, mark alert as resolved
        if correction.alert_id:
            alert = db.query(DepartmentAlert).filter(DepartmentAlert.id == correction.alert_id).first()
            if alert:
                alert.status = "Resolved"
                alert.resolved_at = datetime.utcnow()

        # Re-consolidate unified record via agent
        agent = PatientDataManagementAgent(db)
        agent.consolidate_unified_record(correction.patient_id)

    db.commit()
    db.refresh(correction)

    log_audit_event(
        db=db,
        action=f"CORRECTION_{new_status.upper()}",
        user_id=current_user.id,
        user_role=current_user.role,
        entity_type="CorrectionRequest",
        entity_id=str(correction.id),
        status="SUCCESS",
        details={
            "field": correction.field_name,
            "original_value": correction.original_value,
            "approved_value": correction.proposed_value if decision == "APPROVE" else None,
            "review_notes": payload.review_notes
        }
    )

    return correction

