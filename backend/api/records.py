from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.models.models import (
    User, RegistrationRecord, LaboratoryRecord, PharmacyRecord,
    RadiologyRecord, NursingRecord, AppointmentRecord, InpatientRecord, BillingRecord
)
from backend.schemas.schemas import (
    RegistrationRecordOut, LaboratoryRecordOut, PharmacyRecordOut,
    RadiologyRecordOut, NursingRecordOut, AppointmentRecordOut,
    InpatientRecordOut, BillingRecordOut
)
from backend.security.auth import get_current_user
from backend.skills.record_retrieval_skill import retrieve_patient_records

router = APIRouter(prefix="/api/records", tags=["Department Records"])


@router.get("/patient/{patient_id}")
def get_all_patient_department_records(
    patient_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves all connected records for a patient across all 8 hospital departments with provenance metadata."""
    clean_id = patient_id.strip().upper()

    if current_user.role == "Patient" and current_user.patient_id != clean_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You may only view your own records."
        )

    bundle = retrieve_patient_records(db, clean_id)
    if "error" in bundle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=bundle["error"])

    # If role is Pharmacist, filter out billing/radiology details if desired, or return bundle with role notice
    return bundle


@router.get("/registration", response_model=List[RegistrationRecordOut])
def list_registration_records(
    patient_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    q = db.query(RegistrationRecord)
    if current_user.role == "Patient":
        q = q.filter(RegistrationRecord.patient_id == current_user.patient_id)
    elif patient_id:
        q = q.filter(RegistrationRecord.patient_id == patient_id.strip().upper())
    return q.all()


@router.get("/laboratory", response_model=List[LaboratoryRecordOut])
def list_laboratory_records(
    patient_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    q = db.query(LaboratoryRecord)
    if current_user.role == "Patient":
        q = q.filter(LaboratoryRecord.patient_id == current_user.patient_id)
    elif patient_id:
        q = q.filter(LaboratoryRecord.patient_id == patient_id.strip().upper())
    return q.all()


@router.get("/pharmacy", response_model=List[PharmacyRecordOut])
def list_pharmacy_records(
    patient_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    q = db.query(PharmacyRecord)
    if current_user.role == "Patient":
        q = q.filter(PharmacyRecord.patient_id == current_user.patient_id)
    elif patient_id:
        q = q.filter(PharmacyRecord.patient_id == patient_id.strip().upper())
    return q.all()


@router.get("/radiology", response_model=List[RadiologyRecordOut])
def list_radiology_records(
    patient_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    q = db.query(RadiologyRecord)
    if current_user.role == "Patient":
        q = q.filter(RadiologyRecord.patient_id == current_user.patient_id)
    elif patient_id:
        q = q.filter(RadiologyRecord.patient_id == patient_id.strip().upper())
    return q.all()


@router.get("/nursing", response_model=List[NursingRecordOut])
def list_nursing_records(
    patient_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    q = db.query(NursingRecord)
    if current_user.role == "Patient":
        q = q.filter(NursingRecord.patient_id == current_user.patient_id)
    elif patient_id:
        q = q.filter(NursingRecord.patient_id == patient_id.strip().upper())
    return q.all()


@router.get("/inpatient", response_model=List[InpatientRecordOut])
def list_inpatient_records(
    patient_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    q = db.query(InpatientRecord)
    if current_user.role == "Patient":
        q = q.filter(InpatientRecord.patient_id == current_user.patient_id)
    elif patient_id:
        q = q.filter(InpatientRecord.patient_id == patient_id.strip().upper())
    return q.all()


@router.get("/appointments", response_model=List[AppointmentRecordOut])
def list_appointment_records(
    patient_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    q = db.query(AppointmentRecord)
    if current_user.role == "Patient":
        q = q.filter(AppointmentRecord.patient_id == current_user.patient_id)
    elif patient_id:
        q = q.filter(AppointmentRecord.patient_id == patient_id.strip().upper())
    return q.all()


@router.get("/billing", response_model=List[BillingRecordOut])
def list_billing_records(
    patient_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Restricted: only Doctor, Admin, or Patient for self
    if current_user.role in ("Nurse", "Pharmacist", "Radiologist"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Role not authorized to access financial billing records.")

    q = db.query(BillingRecord)
    if current_user.role == "Patient":
        q = q.filter(BillingRecord.patient_id == current_user.patient_id)
    elif patient_id:
        q = q.filter(BillingRecord.patient_id == patient_id.strip().upper())
    return q.all()

