from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.models.models import User
from backend.schemas.schemas import UserOut, UserCreate
from backend.security.auth import get_current_user, require_roles, hash_password
from backend.skills.audit_logging_skill import log_audit_event

router = APIRouter(prefix="/api/users", tags=["User Management"])


@router.get("", response_model=List[UserOut])
def list_users(
    current_user: User = Depends(require_roles(["Hospital Administrator"])),
    db: Session = Depends(get_db)
):
    """Lists all registered system users (Hospital Administrator only)."""
    return db.query(User).all()


@router.post("", response_model=UserOut)
def create_new_user(
    req: UserCreate,
    current_user: User = Depends(require_roles(["Hospital Administrator"])),
    db: Session = Depends(get_db)
):
    """Creates a new role-based system user (Hospital Administrator only)."""
    existing = db.query(User).filter(User.username == req.username).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered.")

    existing_email = db.query(User).filter(User.email == req.email).first()
    if existing_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered.")

    user = User(
        username=req.username,
        hashed_password=hash_password(req.password),
        full_name=req.full_name,
        email=req.email,
        role=req.role,
        department=req.department,
        patient_id=req.patient_id,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    log_audit_event(
        db=db,
        action="USER_CREATED",
        user_id=current_user.id,
        user_role=current_user.role,
        entity_type="User",
        entity_id=str(user.id),
        status="SUCCESS",
        details={"username": user.username, "role": user.role}
    )

    return user

