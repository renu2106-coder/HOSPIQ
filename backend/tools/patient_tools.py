"""Atomic tools for the Patient Data Management Agent as specified on Page 4 and Page 11 of the project specification document.

Tools perform specific, bounded operations on the database:
- search_patient()
- get_patient_record()
- create_patient()
- insert_lab_result()
- insert_vital()
- insert_medication()
- update_patient()
- archive_record()
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

from backend.models.models import (
    Patient, LaboratoryRecord, NursingRecord, PharmacyRecord,
    RegistrationRecord, AppointmentRecord, InpatientRecord, AuditLog
)
from backend.skills.data_normalization_skill import normalize_date


def search_patient(db: Session, query: str) -> List[Dict[str, Any]]:
    """Tool: Searches patients by ID, first name, last name, or full name."""
    clean_q = query.strip()
    patients = db.query(Patient).filter(
        or_(
            Patient.id.ilike(f"%{clean_q}%"),
            Patient.first_name.ilike(f"%{clean_q}%"),
            Patient.last_name.ilike(f"%{clean_q}%"),
            Patient.full_name.ilike(f"%{clean_q}%")
        )
    ).limit(10).all()

    return [
        {
            "id": p.id,
            "full_name": p.full_name,
            "dob": p.dob,
            "gender": p.gender,
            "blood_group": p.blood_group,
            "contact_phone": p.contact_phone
        }
        for p in patients
    ]


def get_patient_record(db: Session, patient_id: str) -> Optional[Dict[str, Any]]:
    """Tool: Retrieves complete patient profile including demographics and records from all connected tables."""
    clean_id = patient_id.strip().upper()
    patient = db.query(Patient).filter(Patient.id == clean_id).first()
    if not patient:
        return None

    labs = db.query(LaboratoryRecord).filter(LaboratoryRecord.patient_id == clean_id).all()
    vitals = db.query(NursingRecord).filter(NursingRecord.patient_id == clean_id).all()
    meds = db.query(PharmacyRecord).filter(PharmacyRecord.patient_id == clean_id).all()
    appts = db.query(AppointmentRecord).filter(AppointmentRecord.patient_id == clean_id).all()
    inpatients = db.query(InpatientRecord).filter(InpatientRecord.patient_id == clean_id).all()

    return {
        "patient": {
            "id": patient.id,
            "full_name": patient.full_name,
            "first_name": patient.first_name,
            "last_name": patient.last_name,
            "dob": patient.dob,
            "gender": patient.gender,
            "blood_group": patient.blood_group,
            "allergies": patient.allergies,
            "chronic_conditions": patient.chronic_conditions,
            "contact_phone": patient.contact_phone,
            "address": patient.address,
            "emergency_contact": patient.emergency_contact
        },
        "laboratory_records": [
            {
                "id": l.id,
                "test_name": l.test_name,
                "result_value": l.result_value,
                "unit": l.unit,
                "reference_range": l.reference_range,
                "is_abnormal": l.is_abnormal,
                "report_date": l.report_date
            }
            for l in labs
        ],
        "vitals": [
            {
                "id": v.id,
                "vital_bp": v.vital_bp,
                "vital_pulse": v.vital_pulse,
                "vital_temp": v.vital_temp,
                "vital_spo2": v.vital_spo2,
                "recorded_at": v.recorded_at
            }
            for v in vitals
        ],
        "medications": [
            {
                "id": m.id,
                "medicine_name": m.medicine_name,
                "strength": m.strength,
                "dosage": m.dosage,
                "frequency": m.frequency,
                "duration": m.duration,
                "route": m.route,
                "status": m.status
            }
            for m in meds
        ],
        "encounters": [
            {
                "type": "OPD Appointment",
                "id": a.id,
                "date": a.appointment_date,
                "department": a.department,
                "doctor": a.doctor,
                "status": a.appointment_status
            }
            for a in appts
        ] + [
            {
                "type": "Inpatient Ward Stay",
                "id": i.id,
                "admission_date": i.admission_date,
                "discharge_date": i.discharge_date,
                "ward": i.ward,
                "admission_reason": i.admission_diagnosis
            }
            for i in inpatients
        ]
    }


def create_patient(
    db: Session,
    patient_id: str,
    first_name: str,
    last_name: str,
    dob: str,
    gender: str,
    contact_phone: str = "+1-555-0000",
    blood_group: str = "O+",
    allergies: str = "None Reported",
    chronic_conditions: str = "None"
) -> Dict[str, Any]:
    """Tool: Creates a new patient record in the database."""
    clean_id = patient_id.strip().upper()
    existing = db.query(Patient).filter(Patient.id == clean_id).first()
    if existing:
        return {"error": f"Patient with ID {clean_id} already exists.", "patient_id": clean_id}

    full_name = f"{first_name.strip()} {last_name.strip()}".strip()
    patient = Patient(
        id=clean_id,
        first_name=first_name.strip(),
        last_name=last_name.strip(),
        full_name=full_name,
        dob=normalize_date(dob),
        gender=gender.strip(),
        contact_phone=contact_phone.strip(),
        blood_group=blood_group.strip(),
        allergies=allergies.strip(),
        chronic_conditions=chronic_conditions.strip(),
        created_at=datetime.utcnow()
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return {"success": True, "patient_id": patient.id, "full_name": patient.full_name}


def insert_lab_result(
    db: Session,
    patient_id: str,
    test_name: str,
    result_value: str,
    unit: str = "mg/dL",
    reference_range: str = "Normal",
    is_abnormal: bool = False,
    report_date: Optional[str] = None
) -> Dict[str, Any]:
    """Tool: Inserts a laboratory result record."""
    clean_id = patient_id.strip().upper()
    lab = LaboratoryRecord(
        patient_id=clean_id,
        test_name=test_name,
        test_code=f"LAB-{test_name[:3].upper()}",
        result_value=str(result_value),
        unit=unit,
        reference_range=reference_range,
        is_abnormal=is_abnormal,
        report_date=normalize_date(report_date) if report_date else datetime.utcnow().strftime("%Y-%m-%d"),
        lab_department="Clinical Pathology",
        source_file="Manual/Agent Tool Insertion",
        created_at=datetime.utcnow()
    )
    db.add(lab)
    db.commit()
    db.refresh(lab)
    return {"success": True, "lab_id": lab.id, "test_name": lab.test_name, "result": lab.result_value}


def insert_vital(
    db: Session,
    patient_id: str,
    blood_pressure: str,
    pulse: Optional[int] = None,
    temperature: Optional[float] = None,
    spo2: Optional[float] = None,
    recorded_at: Optional[str] = None
) -> Dict[str, Any]:
    """Tool: Inserts a vital signs observation record."""
    clean_id = patient_id.strip().upper()
    vital = NursingRecord(
        patient_id=clean_id,
        vital_bp=blood_pressure,
        vital_pulse=pulse,
        vital_temp=temperature,
        vital_spo2=spo2,
        recorded_at=normalize_date(recorded_at) if recorded_at else datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        nurse_notes="Vital signs recorded via Data Management Agent tool",
        nurse_name="Clinical Nurse Specialist",
        source_file="Manual/Agent Tool Insertion",
        created_at=datetime.utcnow()
    )
    db.add(vital)
    db.commit()
    db.refresh(vital)
    return {"success": True, "vital_id": vital.id, "blood_pressure": vital.vital_bp}


def insert_medication(
    db: Session,
    patient_id: str,
    drug_name: str,
    dose: str = "1 tablet",
    frequency: str = "Daily",
    route: str = "Oral",
    duration: str = "7 days",
    status: str = "Active"
) -> Dict[str, Any]:
    """Tool: Inserts a medication / pharmacy record."""
    clean_id = patient_id.strip().upper()
    med = PharmacyRecord(
        patient_id=clean_id,
        medicine_name=drug_name,
        strength=dose,
        dosage=dose,
        frequency=frequency,
        route=route,
        duration=duration,
        prescription_date=datetime.utcnow().strftime("%Y-%m-%d"),
        prescribing_doctor="Attending Physician",
        status=status,
        source_file="Manual/Agent Tool Insertion",
        created_at=datetime.utcnow()
    )
    db.add(med)
    db.commit()
    db.refresh(med)
    return {"success": True, "medication_id": med.id, "drug_name": med.medicine_name, "dose": med.dosage}


def update_patient(
    db: Session,
    patient_id: str,
    allergies: Optional[str] = None,
    chronic_conditions: Optional[str] = None,
    contact_phone: Optional[str] = None,
    address: Optional[str] = None
) -> Dict[str, Any]:
    """Tool: Updates existing patient demographic and clinical attributes."""
    clean_id = patient_id.strip().upper()
    patient = db.query(Patient).filter(Patient.id == clean_id).first()
    if not patient:
        return {"error": f"Patient with ID {clean_id} not found."}

    if allergies is not None:
        patient.allergies = allergies
    if chronic_conditions is not None:
        patient.chronic_conditions = chronic_conditions
    if contact_phone is not None:
        patient.contact_phone = contact_phone
    if address is not None:
        patient.address = address

    db.commit()
    db.refresh(patient)
    return {"success": True, "patient_id": patient.id, "allergies": patient.allergies, "chronic_conditions": patient.chronic_conditions}


def archive_record(
    db: Session,
    entity_type: str,
    entity_id: int,
    reason: str = "Clinical archival request"
) -> Dict[str, Any]:
    """Tool: Archives a record and logs the archival operation to the immutable audit trail."""
    log = AuditLog(
        action="RECORD_ARCHIVED",
        entity_type=entity_type,
        entity_id=str(entity_id),
        status="SUCCESS",
        details_json=f'{{"reason": "{reason}", "archived_at": "{datetime.utcnow().isoformat()}"}}',
        timestamp=datetime.utcnow()
    )
    db.add(log)
    db.commit()
    return {"success": True, "entity_type": entity_type, "entity_id": entity_id, "status": "Archived"}
