import json
import secrets
from datetime import datetime
from typing import Optional, Any, Dict
from sqlalchemy.orm import Session
from backend.models.models import AuditLog


def log_audit_event(
    db: Session,
    action: str,
    user_id: Optional[int] = None,
    user_role: Optional[str] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    status: str = "SUCCESS",
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = "127.0.0.1"
) -> AuditLog:
    """Creates an append-only audit trail record in the database."""
    event_id = f"EVT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(3).upper()}"
    details_str = json.dumps(details) if details else None

    audit_entry = AuditLog(
        event_id=event_id,
        user_id=user_id,
        user_role=user_role,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id is not None else None,
        status=status,
        details_json=details_str,
        ip_address=ip_address,
        timestamp=datetime.utcnow()
    )
    db.add(audit_entry)
    db.commit()
    db.refresh(audit_entry)
    return audit_entry

