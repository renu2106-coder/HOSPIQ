from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
from backend.models.models import Patient, RegistrationRecord


def search_patients(db: Session, query: Optional[str] = None, limit: int = 50) -> List[Patient]:
    """Search patients by canonical ID, hospital UHID/OP/Reg ID, full name, phone number, or email."""
    q = db.query(Patient)
    if query:
        clean_q = query.strip()
        ext_pids = [
            r.patient_id for r in db.query(RegistrationRecord).filter(
                or_(
                    RegistrationRecord.address.ilike(f"%{clean_q}%"),
                    RegistrationRecord.raw_data_json.ilike(f"%{clean_q}%")
                )
            ).all()
        ]
        filters = [
            Patient.id.ilike(f"%{clean_q}%"),
            Patient.full_name.ilike(f"%{clean_q}%"),
            Patient.first_name.ilike(f"%{clean_q}%"),
            Patient.last_name.ilike(f"%{clean_q}%"),
            Patient.contact_phone.ilike(f"%{clean_q}%"),
            Patient.email.ilike(f"%{clean_q}%"),
            Patient.address.ilike(f"%{clean_q}%")
        ]
        if ext_pids:
            filters.append(Patient.id.in_(ext_pids))
        q = q.filter(or_(*filters))
    return q.order_by(Patient.id.asc()).limit(limit).all()


def get_patient_by_id(db: Session, patient_id: str) -> Optional[Patient]:
    """Retrieve a single patient by ID."""
    clean_id = patient_id.strip().upper()
    return db.query(Patient).filter(Patient.id == clean_id).first()
