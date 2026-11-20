from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.models.models import (
    Patient, RegistrationRecord, LaboratoryRecord, PharmacyRecord,
    RadiologyRecord, NursingRecord, AppointmentRecord, InpatientRecord,
    BillingRecord
)


def retrieve_patient_records(db: Session, patient_id: str) -> Dict[str, Any]:
    """Retrieves all connected records for a patient across all 8 hospital departments."""
    clean_id = patient_id.strip().upper()
    patient = db.query(Patient).filter(Patient.id == clean_id).first()

    if not patient:
        return {"error": f"Patient {clean_id} not found."}

    reg_records = db.query(RegistrationRecord).filter(RegistrationRecord.patient_id == clean_id).all()
    lab_records = db.query(LaboratoryRecord).filter(LaboratoryRecord.patient_id == clean_id).all()
    pharm_records = db.query(PharmacyRecord).filter(PharmacyRecord.patient_id == clean_id).all()
    rad_records = db.query(RadiologyRecord).filter(RadiologyRecord.patient_id == clean_id).all()
    nursing_records = db.query(NursingRecord).filter(NursingRecord.patient_id == clean_id).all()
    appt_records = db.query(AppointmentRecord).filter(AppointmentRecord.patient_id == clean_id).all()
    inpatient_records = db.query(InpatientRecord).filter(InpatientRecord.patient_id == clean_id).all()
    billing_records = db.query(BillingRecord).filter(BillingRecord.patient_id == clean_id).all()

    provenance = {
        "registration": [r.source_file or "EMR Core" for r in reg_records],
        "laboratory": [l.source_file or "LIS System" for l in lab_records],
        "pharmacy": [p.source_file or "Pharmacy MIS" for p in pharm_records],
        "radiology": [r.source_file or "PACS/RIS" for r in rad_records],
        "nursing": [n.source_file or "Ward Station" for n in nursing_records],
        "inpatient": [i.source_file or "ADT System" for i in inpatient_records],
        "appointments": [a.source_file or "Scheduling System" for a in appt_records],
        "billing": [b.source_file or "Financial MIS" for b in billing_records],
    }

    return {
        "patient": {
            "id": patient.id,
            "full_name": patient.full_name,
            "dob": patient.dob,
            "age": patient.age,
            "gender": patient.gender,
            "contact_phone": patient.contact_phone,
            "blood_group": patient.blood_group,
            "allergies": patient.allergies,
            "chronic_conditions": patient.chronic_conditions,
            "address": patient.address,
            "registration_date": patient.registration_date,
        },
        "registration_records": [
            {
                "id": r.id,
                "name": r.name,
                "dob": r.dob,
                "gender": r.gender,
                "contact_number": r.contact_number,
                "address": r.address,
                "registration_date": r.registration_date,
                "source_file": r.source_file
            }
            for r in reg_records
        ],
        "laboratory_records": [
            {
                "id": l.id,
                "test_name": l.test_name,
                "test_code": l.test_code,
                "result_value": l.result_value,
                "unit": l.unit,
                "reference_range": l.reference_range,
                "is_abnormal": l.is_abnormal,
                "report_date": l.report_date,
                "lab_department": l.lab_department,
                "ordering_physician": l.ordering_physician,
                "source_file": l.source_file
            }
            for l in lab_records
        ],
        "pharmacy_records": [
            {
                "id": p.id,
                "medicine_name": p.medicine_name,
                "strength": p.strength,
                "dosage": p.dosage,
                "frequency": p.frequency,
                "duration": p.duration,
                "status": p.status,
                "prescription_date": p.prescription_date,
                "prescribing_doctor": p.prescribing_doctor,
                "source_file": p.source_file
            }
            for p in pharm_records
        ],
        "radiology_records": [
            {
                "id": r.id,
                "imaging_type": r.imaging_type,
                "body_part": r.body_part,
                "report_findings": r.report_findings,
                "impression": r.impression,
                "report_date": r.report_date,
                "radiologist_name": r.radiologist_name,
                "source_file": r.source_file
            }
            for r in rad_records
        ],
        "nursing_records": [
            {
                "id": n.id,
                "vital_bp": n.vital_bp,
                "vital_pulse": n.vital_pulse,
                "vital_temp": n.vital_temp,
                "vital_resp_rate": n.vital_resp_rate,
                "vital_spo2": n.vital_spo2,
                "nurse_notes": n.nurse_notes,
                "recorded_at": n.recorded_at,
                "nurse_name": n.nurse_name,
                "source_file": n.source_file
            }
            for n in nursing_records
        ],
        "inpatient_records": [
            {
                "id": i.id,
                "admission_date": i.admission_date,
                "discharge_date": i.discharge_date,
                "ward": i.ward,
                "bed_number": i.bed_number,
                "admission_diagnosis": i.admission_diagnosis,
                "discharge_diagnosis": i.discharge_diagnosis,
                "attending_physician": i.attending_physician,
                "discharge_status": i.discharge_status,
                "source_file": i.source_file
            }
            for i in inpatient_records
        ],
        "appointment_records": [
            {
                "id": a.id,
                "appointment_date": a.appointment_date,
                "appointment_time": a.appointment_time,
                "department": a.department,
                "doctor": a.doctor,
                "reason_for_visit": a.reason_for_visit,
                "appointment_status": a.appointment_status,
                "source_file": a.source_file
            }
            for a in appt_records
        ],
        "billing_records": [
            {
                "id": b.id,
                "bill_id": b.bill_id,
                "service": b.service,
                "amount": b.amount,
                "payment_status": b.payment_status,
                "billing_date": b.billing_date,
                "source_file": b.source_file
            }
            for b in billing_records
        ],
        "provenance": provenance
    }

