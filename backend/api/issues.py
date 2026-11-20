import secrets
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.models.models import User, PatientIssue
from backend.schemas.schemas import PatientIssueCreate, PatientIssueUpdate, PatientIssueOut
from backend.security.auth import get_current_user
from backend.skills.audit_logging_skill import log_audit_event
from backend.agents.issue_management_agent import IssueManagementAgent

router = APIRouter(prefix="/api/issues", tags=["Patient Issue Portal"])


@router.post("", response_model=PatientIssueOut)
def submit_patient_issue(
    req: PatientIssueCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submits a patient issue/ticket and triggers the Issue Management Agent for routing."""
    target_patient_id = current_user.patient_id if current_user.role == "Patient" else (req.patient_id or None)
    if target_patient_id:
        target_patient_id = target_patient_id.strip().upper()

    issue_code = f"ISS-{datetime.utcnow().strftime('%Y%m')}-{secrets.token_hex(2).upper()}"

    issue = PatientIssue(
        issue_id=issue_code,
        patient_id=target_patient_id,
        category=req.category,
        description=req.description,
        attachment_filename=req.attachment_filename,
        status="Submitted",
        priority="Medium",
        submitted_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(issue)
    db.commit()
    db.refresh(issue)

    # Invoke Issue Management Agent to classify and route
    agent = IssueManagementAgent(db)
    agent.process_and_route_issue(issue.id)
    db.refresh(issue)

    log_audit_event(
        db=db,
        action="PATIENT_ISSUE_SUBMITTED",
        user_id=current_user.id,
        user_role=current_user.role,
        entity_type="PatientIssue",
        entity_id=issue.issue_id,
        status="SUCCESS",
        details={
            "category": issue.category,
            "assigned_dept": issue.assigned_department,
            "priority": issue.priority
        }
    )

    return issue


@router.get("", response_model=List[PatientIssueOut])
def list_patient_issues(
    status_filter: Optional[str] = None,
    department: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lists issues. Patients see only their own issues. Staff see issues relevant to their role or all."""
    q = db.query(PatientIssue)

    if current_user.role == "Patient":
        q = q.filter(PatientIssue.patient_id == current_user.patient_id)
    else:
        if current_user.role == "Pharmacist":
            q = q.filter(PatientIssue.assigned_department == "Pharmacy")
        elif current_user.role == "Radiologist":
            q = q.filter(PatientIssue.assigned_department == "Radiology")
        elif department:
            q = q.filter(PatientIssue.assigned_department == department)

    if status_filter:
        q = q.filter(PatientIssue.status == status_filter)

    return q.order_by(PatientIssue.submitted_at.desc()).all()


@router.get("/{issue_id}", response_model=PatientIssueOut)
def get_issue(
    issue_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    issue = db.query(PatientIssue).filter(PatientIssue.issue_id == issue_id).first()
    if not issue:
        # Check by integer ID fallback
        if issue_id.isdigit():
            issue = db.query(PatientIssue).filter(PatientIssue.id == int(issue_id)).first()

    if not issue:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Issue not found.")

    if current_user.role == "Patient" and issue.patient_id != current_user.patient_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    return issue


@router.patch("/{issue_id}", response_model=PatientIssueOut)
def update_issue_status(
    issue_id: str,
    payload: PatientIssueUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Updates status, priority, or resolution notes for an issue (Department staff or Admin)."""
    if current_user.role == "Patient":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Patients cannot modify issue management status.")

    issue = db.query(PatientIssue).filter(PatientIssue.issue_id == issue_id).first()
    if not issue and issue_id.isdigit():
        issue = db.query(PatientIssue).filter(PatientIssue.id == int(issue_id)).first()

    if not issue:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Issue not found.")

    issue.status = payload.status
    if payload.priority:
        issue.priority = payload.priority
    if payload.assigned_department:
        issue.assigned_department = payload.assigned_department
    if payload.resolution_notes:
        issue.resolution_notes = payload.resolution_notes

    if payload.status in ("Resolved", "Rejected"):
        issue.resolved_at = datetime.utcnow()

    issue.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(issue)

    log_audit_event(
        db=db,
        action="PATIENT_ISSUE_UPDATED",
        user_id=current_user.id,
        user_role=current_user.role,
        entity_type="PatientIssue",
        entity_id=issue.issue_id,
        status="SUCCESS",
        details={"status": issue.status, "assigned_dept": issue.assigned_department}
    )

    return issue

