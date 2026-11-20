from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.models.models import User, DepartmentAlert
from backend.schemas.schemas import DepartmentAlertOut, AlertStatusUpdate
from backend.security.auth import get_current_user, require_roles
from backend.skills.audit_logging_skill import log_audit_event

router = APIRouter(prefix="/api/alerts", tags=["Department Alerts"])


@router.get("", response_model=List[DepartmentAlertOut])
def list_department_alerts(
    department: Optional[str] = None,
    priority: Optional[str] = None,
    status_filter: Optional[str] = None,
    patient_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lists department alerts with role and filter scoping."""
    if current_user.role == "Patient":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Patients cannot access internal clinical alerts.")

    q = db.query(DepartmentAlert)

    # Scoping by role if department specific
    if current_user.role == "Pharmacist":
        q = q.filter(DepartmentAlert.department == "Pharmacy")
    elif current_user.role == "Radiologist":
        q = q.filter(DepartmentAlert.department == "Radiology")
    elif current_user.role == "Nurse":
        q = q.filter(DepartmentAlert.department.in_(["Nursing", "Inpatient", "Registration"]))

    if department:
        q = q.filter(DepartmentAlert.department == department)
    if priority:
        q = q.filter(DepartmentAlert.priority == priority)
    if status_filter:
        q = q.filter(DepartmentAlert.status == status_filter)
    if patient_id:
        q = q.filter(DepartmentAlert.patient_id == patient_id.strip().upper())

    return q.order_by(DepartmentAlert.created_at.desc()).all()


@router.get("/{alert_id}", response_model=DepartmentAlertOut)
def get_alert_detail(
    alert_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role == "Patient":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized")

    alert = db.query(DepartmentAlert).filter(DepartmentAlert.alert_id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found.")
    return alert


@router.patch("/{alert_id}", response_model=DepartmentAlertOut)
def update_alert_status(
    alert_id: str,
    payload: AlertStatusUpdate,
    current_user: User = Depends(require_roles(["Doctor", "Hospital Administrator", "Nurse", "Pharmacist", "Radiologist"])),
    db: Session = Depends(get_db)
):
    """Updates investigation notes, assigned personnel, or status of an alert."""
    alert = db.query(DepartmentAlert).filter(DepartmentAlert.alert_id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found.")

    alert.status = payload.status
    if payload.investigation_notes:
        existing = alert.investigation_notes or ""
        timestamp_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
        new_entry = f"[{timestamp_str} - {current_user.full_name} ({current_user.role})]: {payload.investigation_notes}"
        alert.investigation_notes = f"{existing}\n{new_entry}".strip()

    if payload.assigned_to:
        alert.assigned_to = payload.assigned_to

    if payload.status in ("Resolved", "Dismissed"):
        alert.resolved_at = datetime.utcnow()

    db.commit()
    db.refresh(alert)

    log_audit_event(
        db=db,
        action="ALERT_STATUS_UPDATED",
        user_id=current_user.id,
        user_role=current_user.role,
        entity_type="DepartmentAlert",
        entity_id=alert.alert_id,
        status="SUCCESS",
        details={"new_status": payload.status, "notes": payload.investigation_notes}
    )

    return alert

