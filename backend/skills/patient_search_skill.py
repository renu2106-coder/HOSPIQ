from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_
from backend.models.models import Patient


def search_patients(db: Session, query: Optional[str] = None, limit: int = 50) -> List[Patient]:
    """Search patients by ID, full name, phone number, or email."""
    q = db.query(Patient)
    if query:
        clean_q = query.strip()
        search_filter = or_(
            Patient.id.ilike(f"%{clean_q}%"),
            Patient.full_name.ilike(f"%{clean_q}%"),
            Patient.first_name.ilike(f"%{clean_q}%"),
            Patient.last_name.ilike(f"%{clean_q}%"),
            Patient.contact_phone.ilike(f"%{clean_q}%"),
            Patient.email.ilike(f"%{clean_q}%")
        )
        q = q.filter(search_filter)
    return q.order_by(Patient.id.asc()).limit(limit).all()


def get_patient_by_id(db: Session, patient_id: str) -> Optional[Patient]:
    """Retrieve a single patient by ID."""
    clean_id = patient_id.strip().upper()
    return db.query(Patient).filter(Patient.id == clean_id).first()

