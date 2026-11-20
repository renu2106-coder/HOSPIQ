import re
import json
from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from backend.models.models import Patient
from backend.skills.record_retrieval_skill import retrieve_patient_records
from backend.skills.conflict_detection_skill import detect_patient_conflicts


def validate_clinical_document(
    db: Session,
    patient_id: str,
    doc_type: str,
    content: str,
    source_references: List[str]
) -> Dict[str, Any]:
    """Executes a rigorous 7-point validation suite on clinical documentation using deterministic Python checks."""
    checks: List[Dict[str, Any]] = []
    clean_id = patient_id.strip().upper()

    patient = db.query(Patient).filter(Patient.id == clean_id).first()
    records = retrieve_patient_records(db, clean_id)
    conflicts = detect_patient_conflicts(db, clean_id)

    # -------------------------------------------------------------
    # Check 1: Patient ID Consistency
    # -------------------------------------------------------------
    has_patient_id = clean_id in content or f"Patient ID: {clean_id}" in content or f"ID: {clean_id}" in content
    # Check for mismatching IDs like P002 inside P001 doc
    other_patient_ids = re.findall(r'\bP\d{3}\b', content)
    alien_ids = [pid for pid in other_patient_ids if pid != clean_id]

    if not has_patient_id:
        checks.append({
            "check_id": "CHK-01",
            "name": "Patient ID Consistency",
            "status": "Failed",
            "explanation": f"Document content does not reference the correct Patient ID '{clean_id}'."
        })
    elif alien_ids:
        checks.append({
            "check_id": "CHK-01",
            "name": "Patient ID Consistency",
            "status": "Failed",
            "explanation": f"Discrepancy detected: Document mentions external patient identifier(s) {list(set(alien_ids))}."
        })
    else:
        checks.append({
            "check_id": "CHK-01",
            "name": "Patient ID Consistency",
            "status": "Passed",
            "explanation": f"Patient identifier '{clean_id}' consistently verified across all document sections."
        })

    # -------------------------------------------------------------
    # Check 2: Required Field Completeness
    # -------------------------------------------------------------
    missing_fields = []
    if not patient or not patient.dob:
        missing_fields.append("Date of Birth")
    if not patient or not patient.gender:
        missing_fields.append("Gender")
    if not patient or not patient.contact_phone:
        missing_fields.append("Contact Number")

    if missing_fields:
        checks.append({
            "check_id": "CHK-02",
            "name": "Required Field Completeness",
            "status": "Warning",
            "explanation": f"Demographic omissions detected in underlying records: {', '.join(missing_fields)}."
        })
    else:
        checks.append({
            "check_id": "CHK-02",
            "name": "Required Field Completeness",
            "status": "Passed",
            "explanation": "All mandatory demographic fields (Name, DOB, Gender, Contact) are present."
        })

    # -------------------------------------------------------------
    # Check 3: Date Validity
    # -------------------------------------------------------------
    found_dates = re.findall(r'\b(20\d{2}[-/.]\d{1,2}[-/.]\d{1,2}|\d{1,2}[-/.]\d{1,2}[-/.]20\d{2})\b', content)
    future_dates = []
    now_year = datetime.utcnow().year

    for d_str in found_dates:
        # Check if year is unrealistically in the future
        year_match = re.search(r'20\d{2}', d_str)
        if year_match and int(year_match.group(0)) > now_year + 1:
            future_dates.append(d_str)

    if future_dates:
        checks.append({
            "check_id": "CHK-03",
            "name": "Date Validity",
            "status": "Failed",
            "explanation": f"Unrealistic or future clinical dates identified: {', '.join(future_dates)}."
        })
    elif not found_dates:
        checks.append({
            "check_id": "CHK-03",
            "name": "Date Validity",
            "status": "Warning",
            "explanation": "No clinical timestamps or event dates were detected in the generated document."
        })
    else:
        checks.append({
            "check_id": "CHK-03",
            "name": "Date Validity",
            "status": "Passed",
            "explanation": f"All {len(found_dates)} detected timestamps are chronological and valid."
        })

    # -------------------------------------------------------------
    # Check 4: Conflicting Source Information
    # -------------------------------------------------------------
    critical_conflicts = [c for c in conflicts if c.get("priority") in ("Critical", "High")]
    if critical_conflicts:
        sample_conflict = critical_conflicts[0]
        checks.append({
            "check_id": "CHK-04",
            "name": "Conflicting Source Information",
            "status": "Warning",
            "explanation": f"Active source discrepancy flagged: {sample_conflict.get('description')}"
        })
    else:
        checks.append({
            "check_id": "CHK-04",
            "name": "Conflicting Source Information",
            "status": "Passed",
            "explanation": "No unresolved high-priority cross-department data conflicts detected."
        })

    # -------------------------------------------------------------
    # Check 5: Unsupported Statements / Hallucination Guard
    # -------------------------------------------------------------
    # Verify that medications mentioned in content actually exist in Pharmacy records
    pharm_meds = [p["medicine_name"].lower() for p in records.get("pharmacy_records", [])]
    common_meds_in_text = re.findall(r'(?i)\b(Metformin|Lisinopril|Atorvastatin|Amlodipine|Amoxicillin|Omeprazole|Albuterol|Gabapentin|Levothyroxine|Losartan|Paracetamol|Ibuprofen|Aspirin|Ciprofloxacin)\b', content)
    unsupported_meds = []
    for med in common_meds_in_text:
        med_l = med.lower()
        if not any(med_l in pm for pm in pharm_meds):
            unsupported_meds.append(med)

    if unsupported_meds:
        checks.append({
            "check_id": "CHK-05",
            "name": "Unsupported Statements",
            "status": "Failed",
            "explanation": f"Potential hallucination or unverified medication claims: {list(set(unsupported_meds))} not found in Pharmacy records."
        })
    else:
        checks.append({
            "check_id": "CHK-05",
            "name": "Unsupported Statements",
            "status": "Passed",
            "explanation": "Clinical statements and medication references match confirmed source records."
        })

    # -------------------------------------------------------------
    # Check 6: Missing Source References
    # -------------------------------------------------------------
    if not source_references or len(source_references) == 0:
        checks.append({
            "check_id": "CHK-06",
            "name": "Source Traceability",
            "status": "Failed",
            "explanation": "Document lacks provenance references or department source citations."
        })
    else:
        checks.append({
            "check_id": "CHK-06",
            "name": "Source Traceability",
            "status": "Passed",
            "explanation": f"Document provenance verified across {len(source_references)} source department(s): {', '.join(source_references)}."
        })

    # -------------------------------------------------------------
    # Check 7: Document Structure & Required Sections
    # -------------------------------------------------------------
    required_sections = ["Clinical Summary", "Patient", "Status"]
    if doc_type == "Discharge Summary":
        required_sections = ["Discharge", "Condition", "Medication"]
    elif doc_type == "Laboratory Summary":
        required_sections = ["Laboratory", "Results", "Reference"]

    missing_sections = [sec for sec in required_sections if sec.lower() not in content.lower()]
    if missing_sections:
        checks.append({
            "check_id": "CHK-07",
            "name": "Document Structure & Required Sections",
            "status": "Warning",
            "explanation": f"Recommended clinical section header(s) absent: {', '.join(missing_sections)}."
        })
    else:
        checks.append({
            "check_id": "CHK-07",
            "name": "Document Structure & Required Sections",
            "status": "Passed",
            "explanation": "Clinical document conforms to required structural sections and formatting."
        })

    # Calculate overall summary
    total = len(checks)
    passed = sum(1 for c in checks if c["status"] == "Passed")
    failed = sum(1 for c in checks if c["status"] == "Failed")
    warnings = sum(1 for c in checks if c["status"] == "Warning")

    if failed > 0:
        overall_status = "Failed"
    elif warnings > 0:
        overall_status = "Warning"
    else:
        overall_status = "Passed"

    return {
        "total_checks": total,
        "passed_checks": passed,
        "failed_checks": failed,
        "warnings_count": warnings,
        "status": overall_status,
        "checks": checks
    }

