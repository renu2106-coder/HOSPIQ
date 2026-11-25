from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.models.models import (
    Patient, RegistrationRecord, LaboratoryRecord, PharmacyRecord,
    RadiologyRecord, NursingRecord, AppointmentRecord, InpatientRecord
)
from backend.skills.data_normalization_skill import normalize_date


def detect_patient_conflicts(db: Session, patient_id: str) -> List[Dict[str, Any]]:
    """Analyzes cross-department records for discrepancies, critical labs, and urgent radiology findings."""
    clean_id = patient_id.strip().upper()
    conflicts: List[Dict[str, Any]] = []

    patient = db.query(Patient).filter(Patient.id == clean_id).first()
    if not patient:
        return conflicts

    # 1. Cross-check Registration vs Core Patient Profile
    reg_records = db.query(RegistrationRecord).filter(RegistrationRecord.patient_id == clean_id).all()
    for reg in reg_records:
        if reg.dob and patient.dob:
            norm_reg_dob = normalize_date(reg.dob)
            norm_patient_dob = normalize_date(patient.dob)
            if norm_reg_dob and norm_patient_dob and norm_reg_dob != norm_patient_dob:
                conflicts.append({
                    "category": "Conflicting Patient Details",
                    "department": "Registration",
                    "field": "dob",
                    "patient_id": clean_id,
                    "description": f"Date of Birth conflict: Primary record has '{patient.dob}', whereas Registration source '{reg.source_file}' lists '{reg.dob}'.",
                    "priority": "High",
                    "original_value": patient.dob,
                    "conflicting_value": reg.dob
                })

    # 2. Check Laboratory anomalies, blood group mismatches, and abnormal flags
    lab_records = db.query(LaboratoryRecord).filter(LaboratoryRecord.patient_id == clean_id).all()
    for lab in lab_records:
        # Check blood type test conflict with patient profile if present
        if "blood" in lab.test_name.lower() or "abo" in lab.test_name.lower():
            if patient.blood_group and lab.result_value:
                clean_lab_bg = lab.result_value.strip().upper().replace("POSITIVE", "+").replace("NEGATIVE", "-")
                clean_pat_bg = patient.blood_group.strip().upper().replace("POSITIVE", "+").replace("NEGATIVE", "-")
                if clean_lab_bg != clean_pat_bg:
                    conflicts.append({
                        "category": "Conflicting Patient Details",
                        "department": "Laboratory",
                        "field": "blood_group",
                        "patient_id": clean_id,
                        "description": f"Critical blood group discrepancy: Demographics state '{patient.blood_group}', but Laboratory result lists '{lab.result_value}' (Source: {lab.source_file}).",
                        "priority": "Critical",
                        "original_value": patient.blood_group,
                        "conflicting_value": lab.result_value
                    })

        # Check missing reference ranges for numerical tests
        if not lab.reference_range and lab.test_name.lower() not in ("blood group", "rh factor", "urinalysis color"):
            conflicts.append({
                "category": "Missing Laboratory Information",
                "department": "Laboratory",
                "field": "reference_range",
                "patient_id": clean_id,
                "description": f"Lab test '{lab.test_name}' has result '{lab.result_value}' {lab.unit or ''} without defined reference range.",
                "priority": "Medium",
                "original_value": None,
                "conflicting_value": lab.result_value
            })

        # Highlight abnormal lab values requiring clinician review
        if lab.is_abnormal:
            conflicts.append({
                "category": "Abnormal Laboratory Result",
                "department": "Laboratory",
                "field": lab.test_name,
                "patient_id": clean_id,
                "description": f"Abnormal Lab Finding — {lab.test_name}: '{lab.result_value} {lab.unit or ''}' (Ref: {lab.reference_range or 'N/A'}) from {lab.source_file or 'LIS'}.",
                "priority": "High",
                "original_value": lab.reference_range,
                "conflicting_value": lab.result_value
            })

    # 3. Check Radiology critical / high-priority findings (respecting negations like 'no acute fracture')
    rad_records = db.query(RadiologyRecord).filter(RadiologyRecord.patient_id == clean_id).all()
    for rad in rad_records:
        combined_rad = f"{rad.report_findings or ''} {rad.impression or ''}".lower()
        # Mask common radiology negation clauses before pathology matching
        pos_rad = combined_rad
        for neg_pat in (
            "no acute fracture", "no fracture", "no evidence of fracture", "without fracture",
            "no lytic or sclerotic", "no evidence of lytic", "no evidence of malignancy",
            "no malignancy", "no hemorrhage", "no bony injury", "within normal limits"
        ):
            pos_rad = pos_rad.replace(neg_pat, " [negative] ")

        if any(k in pos_rad for k in ("lytic lesion", "myeloma", "myeloproliferative", "malignancy", "hemorrhage", "fracture", "mass lesion")):
            conflicts.append({
                "category": "Critical Radiology Finding",
                "department": "Radiology",
                "field": rad.imaging_type,
                "patient_id": clean_id,
                "description": f"Urgent Radiology Alert ({rad.imaging_type}): {rad.impression or rad.report_findings}",
                "priority": "Critical",
                "original_value": "Normal Diagnostic Baseline",
                "conflicting_value": rad.impression or rad.report_findings
            })
        elif any(k in pos_rad for k in ("thecal sac indentation", "neural foramina", "disc bulge", "narrowed nasal", "turbinates hypertrophy")):
            conflicts.append({
                "category": "Significant Radiology Finding",
                "department": "Radiology",
                "field": rad.imaging_type,
                "patient_id": clean_id,
                "description": f"Significant Imaging Finding ({rad.imaging_type}): {rad.impression or rad.report_findings}",
                "priority": "High",
                "original_value": "Normal Baseline",
                "conflicting_value": rad.impression or rad.report_findings
            })

    # 4. Check Pharmacy medication consistency
    pharm_records = db.query(PharmacyRecord).filter(PharmacyRecord.patient_id == clean_id).all()
    seen_meds: Dict[str, PharmacyRecord] = {}
    for p in pharm_records:
        base_name = p.medicine_name.strip().lower()
        if base_name in seen_meds:
            prev = seen_meds[base_name]
            if prev.dosage != p.dosage or prev.strength != p.strength:
                conflicts.append({
                    "category": "Inconsistent Medication",
                    "department": "Pharmacy",
                    "field": "dosage",
                    "patient_id": clean_id,
                    "description": f"Concurrent divergent prescriptions for '{p.medicine_name}': '{prev.strength or ''} {prev.dosage or ''}' vs '{p.strength or ''} {p.dosage or ''}'.",
                    "priority": "High",
                    "original_value": f"{prev.strength} {prev.dosage}",
                    "conflicting_value": f"{p.strength} {p.dosage}"
                })
        else:
            seen_meds[base_name] = p

    # 5. Check Allergy vs Medication contraindications if known
    if patient.allergies:
        allergy_text = patient.allergies.lower()
        for p in pharm_records:
            med_l = p.medicine_name.lower()
            if "penicillin" in allergy_text and ("amoxicillin" in med_l or "penicillin" in med_l or "ampicillin" in med_l):
                conflicts.append({
                    "category": "Inconsistent Medication",
                    "department": "Pharmacy",
                    "field": "allergy_contraindication",
                    "patient_id": clean_id,
                    "description": f"Allergy Alert: Patient documented allergy to '{patient.allergies}', but active prescription found for '{p.medicine_name}'.",
                    "priority": "Critical",
                    "original_value": patient.allergies,
                    "conflicting_value": p.medicine_name
                })

    return conflicts
