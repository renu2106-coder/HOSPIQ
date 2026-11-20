from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.models.models import User, AuditLog
from backend.schemas.schemas import AuditLogOut
from backend.security.auth import get_current_user, require_roles

router = APIRouter(prefix="/api/audit", tags=["Audit Trail"])


@router.get("", response_model=List[AuditLogOut])
def list_audit_logs(
    action: Optional[str] = None,
    user_id: Optional[int] = None,
    entity_type: Optional[str] = None,
    status_filter: Optional[str] = None,
    limit: int = 150,
    current_user: User = Depends(require_roles(["Hospital Administrator", "Doctor", "Nurse", "Paramedic"])),
    db: Session = Depends(get_db)
):
    """
    Retrieves immutable, append-only security and operational audit trail logs.
    Personalized Access Control:
    - Doctors, Nurses, and Paramedics can ONLY see their own personal audit records (cannot manipulate).
    - Hospital Administrators can view the complete master audit trail across all staff.
    """
    q = db.query(AuditLog)

    # Personalization enforcement: Non-administrators can only see their own audit trails
    if current_user.role != "Hospital Administrator":
        q = q.filter(AuditLog.user_id == current_user.id)
    else:
        if user_id:
            q = q.filter(AuditLog.user_id == user_id)

    if action:
        q = q.filter(AuditLog.action.ilike(f"%{action}%"))
    if entity_type:
        q = q.filter(AuditLog.entity_type == entity_type)
    if status_filter:
        q = q.filter(AuditLog.status == status_filter)

    return q.order_by(AuditLog.timestamp.desc()).limit(limit).all()


@router.get("/scope")
def get_audit_scope(
    current_user: User = Depends(require_roles(["Hospital Administrator", "Doctor", "Nurse", "Paramedic"]))
) -> Dict[str, Any]:
    """Returns the current user's personalized audit scope details."""
    is_admin = current_user.role == "Hospital Administrator"
    return {
        "user_id": current_user.id,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "is_master_admin": is_admin,
        "scope_description": (
            "Master Hospital System Audit Log (All Personnel)"
            if is_admin
            else f"Personalized Immutable Audit Trail for {current_user.full_name} ({current_user.role})"
        )
    }


