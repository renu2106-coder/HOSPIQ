from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.models.models import User, Patient, UnifiedPatientRecord
from backend.schemas.schemas import PatientOut, UnifiedPatientRecordOut
from backend.security.auth import get_current_user
from backend.skills.patient_search_skill import search_patients, get_patient_by_id
from backend.skills.audit_logging_skill import log_audit_event
from backend.agents.patient_data_agent import PatientDataManagementAgent

router = APIRouter(prefix="/api/patients", tags=["Patients"])


@router.get("", response_model=List[PatientOut])
def list_or_search_patients(
    query: Optional[str] = Query(None, description="Search by ID, Name, Phone, or Email"),
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Searches patient database. Patients are restricted strictly to viewing their own record."""
    # If current user is a patient, restrict strictly to their linked record
    if current_user.role == "Patient":
        if not current_user.patient_id:
            return []
        pat = get_patient_by_id(db, current_user.patient_id)
        return [pat] if pat else []

    results = search_patients(db, query=query, limit=limit)

    # Log record access event in audit trail
    log_audit_event(
        db=db,
        action="PATIENT_SEARCH",
        user_id=current_user.id,
        user_role=current_user.role,
        entity_type="Patient",
        entity_id=query or "ALL",
        status="SUCCESS",
        details={"query": query, "results_count": len(results)}
    )

    return results


@router.get("/{patient_id}", response_model=PatientOut)
def get_patient(
    patient_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves patient demographics. Restricts patients to their own ID."""
    clean_id = patient_id.strip().upper()

    if current_user.role == "Patient" and current_user.patient_id != clean_id:
        log_audit_event(
            db=db,
            action="UNAUTHORIZED_PATIENT_ACCESS_ATTEMPT",
            user_id=current_user.id,
            user_role=current_user.role,
            entity_type="Patient",
            entity_id=clean_id,
            status="UNAUTHORIZED"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You are only authorized to view your own patient profile."
        )

    patient = get_patient_by_id(db, clean_id)
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Patient {clean_id} not found.")

    log_audit_event(
        db=db,
        action="PATIENT_VIEW",
        user_id=current_user.id,
        user_role=current_user.role,
        entity_type="Patient",
        entity_id=clean_id,
        status="SUCCESS"
    )

    return patient


@router.get("/{patient_id}/unified", response_model=UnifiedPatientRecordOut)
def get_unified_patient_record(
    patient_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves the consolidated unified patient record with provenance and data quality metrics."""
    clean_id = patient_id.strip().upper()

    if current_user.role == "Patient" and current_user.patient_id != clean_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You are only authorized to view your own record."
        )

    unified = db.query(UnifiedPatientRecord).filter(UnifiedPatientRecord.patient_id == clean_id).first()
    if not unified:
        # Generate on demand if missing
        agent = PatientDataManagementAgent(db)
        agent.consolidate_unified_record(clean_id)
        unified = db.query(UnifiedPatientRecord).filter(UnifiedPatientRecord.patient_id == clean_id).first()

    if not unified:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Unified record for {clean_id} not found.")

    return unified


@router.post("/{patient_id}/reconsolidate")
def reconsolidate_unified_record(
    patient_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Triggers the Patient Data Management Agent to recalculate the unified record and detect discrepancies."""
    if current_user.role not in ("Doctor", "Hospital Administrator", "Nurse"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized to trigger data consolidation.")

    clean_id = patient_id.strip().upper()
    agent = PatientDataManagementAgent(db)
    result = agent.consolidate_unified_record(clean_id)

    log_audit_event(
        db=db,
        action="PATIENT_DATA_RECONSOLIDATION",
        user_id=current_user.id,
        user_role=current_user.role,
        entity_type="UnifiedPatientRecord",
        entity_id=clean_id,
        status="SUCCESS",
        details=result
    )

    return results


@router.get("/{patient_id}/fhir")
def export_patient_fhir(
    patient_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Challenge A — FHIR Interoperability Export: Returns patient records formatted as a simplified FHIR-like resource bundle (Patient, Encounter, Observation, DiagnosticReport, MedicationRequest)."""
    from datetime import datetime
    from backend.skills.record_retrieval_skill import retrieve_patient_records
    clean_id = patient_id.strip().upper()
    data = retrieve_patient_records(db, clean_id)
    if "error" in data:
        raise HTTPException(status_code=404, detail="Patient not found")

    p = data["patient"]
    entries = []

    # 1. FHIR Patient Resource
    entries.append({
        "fullUrl": f"urn:uuid:patient-{p['id']}",
        "resource": {
            "resourceType": "Patient",
            "id": p["id"],
            "name": [{"text": p.get("full_name")}],
            "gender": p["gender"].lower() if p.get("gender") else "unknown",
            "birthDate": p.get("dob"),
            "telecom": [{"system": "phone", "value": p["contact_phone"]}] if p.get("contact_phone") else []
        }
    })

    # 2. FHIR Encounter Resources
    for a in data.get("appointment_records", []):
        entries.append({
            "fullUrl": f"urn:uuid:encounter-{a['id']}",
            "resource": {
                "resourceType": "Encounter",
                "id": f"ENC-{a['id']}",
                "status": "finished" if a.get("appointment_status") == "Completed" else "planned",
                "class": {"code": "AMB", "display": "Ambulatory OPD"},
                "subject": {"reference": f"Patient/{p['id']}"},
                "participant": [{"individual": {"display": a.get("doctor")}}],
                "period": {"start": a.get("appointment_date")}
            }
        })

    # 3. FHIR Observation Resources (Lab)
    for l in data.get("laboratory_records", []):
        entries.append({
            "fullUrl": f"urn:uuid:observation-lab-{l['id']}",
            "resource": {
                "resourceType": "Observation",
                "id": f"OBS-LAB-{l['id']}",
                "status": "final",
                "category": [{"coding": [{"code": "laboratory", "display": "Laboratory"}]}],
                "code": {"text": l.get("test_name")},
                "subject": {"reference": f"Patient/{p['id']}"},
                "valueQuantity": {"value": l.get("result_value"), "unit": l.get("unit")},
                "interpretation": [{"text": "Abnormal" if l.get("is_abnormal") else "Normal"}]
            }
        })

    # 4. FHIR DiagnosticReport (Radiology)
    for r in data.get("radiology_records", []):
        entries.append({
            "fullUrl": f"urn:uuid:diagnosticreport-{r['id']}",
            "resource": {
                "resourceType": "DiagnosticReport",
                "id": f"RAD-{r['id']}",
                "status": "final",
                "code": {"text": r.get("imaging_type")},
                "subject": {"reference": f"Patient/{p['id']}"},
                "conclusion": r.get("impression") or r.get("report_findings")
            }
        })

    # 5. FHIR MedicationRequest (Pharmacy)
    for m in data.get("pharmacy_records", []):
        entries.append({
            "fullUrl": f"urn:uuid:medicationrequest-{m['id']}",
            "resource": {
                "resourceType": "MedicationRequest",
                "id": f"MED-{m['id']}",
                "status": "active" if m.get("status") == "Active" else "stopped",
                "intent": "order",
                "medicationCodeableConcept": {"text": f"{m.get('medicine_name')} {m.get('strength') or ''}"},
                "subject": {"reference": f"Patient/{p['id']}"},
                "dosageInstruction": [{"text": m.get("dosage")}]
            }
        })

    return {
        "resourceType": "Bundle",
        "type": "collection",
        "timestamp": datetime.utcnow().isoformat(),
        "total": len(entries),
        "entry": entries
    }

