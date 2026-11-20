import time
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from backend.models.models import (
    Patient, UnifiedPatientRecord, RegistrationRecord, LaboratoryRecord,
    PharmacyRecord, RadiologyRecord, NursingRecord, AppointmentRecord,
    InpatientRecord, BillingRecord, DepartmentAlert, AgentExecution
)
from backend.skills.data_normalization_skill import normalize_record_dict, normalize_date
from backend.skills.duplicate_detection_skill import detect_duplicate_records
from backend.skills.conflict_detection_skill import detect_patient_conflicts


class PatientDataManagementAgent:
    """Agent 1: Handles data ingestion, normalization, patient matching,

    duplicate detection, discrepancy detection, and unified record consolidation.
    """

    def __init__(self, db: Session):
        self.db = db

    def consolidate_unified_record(self, patient_id: str) -> Dict[str, Any]:
        """Consolidates reliable records from all 8 departments into a UnifiedPatientRecord."""
        start_time = time.time()
        clean_id = patient_id.strip().upper()
        tools_called = ["retrieve_patient_records", "detect_patient_conflicts", "calculate_completeness"]

        patient = self.db.query(Patient).filter(Patient.id == clean_id).first()
        if not patient:
            self._log_execution(
                task=f"Consolidate Unified Record for {clean_id}",
                patient_id=clean_id,
                tools=tools_called,
                status="Failed",
                summary="Patient not found",
                error=f"No patient with ID {clean_id}",
                latency_ms=int((time.time() - start_time) * 1000)
            )
            return {"error": "Patient not found"}

        # Gather records
        reg_count = self.db.query(RegistrationRecord).filter(RegistrationRecord.patient_id == clean_id).count()
        lab_count = self.db.query(LaboratoryRecord).filter(LaboratoryRecord.patient_id == clean_id).count()
        pharm_count = self.db.query(PharmacyRecord).filter(PharmacyRecord.patient_id == clean_id).count()
        rad_count = self.db.query(RadiologyRecord).filter(RadiologyRecord.patient_id == clean_id).count()
        nurs_count = self.db.query(NursingRecord).filter(NursingRecord.patient_id == clean_id).count()
        appt_count = self.db.query(AppointmentRecord).filter(AppointmentRecord.patient_id == clean_id).count()
        inp_count = self.db.query(InpatientRecord).filter(InpatientRecord.patient_id == clean_id).count()
        bill_count = self.db.query(BillingRecord).filter(BillingRecord.patient_id == clean_id).count()

        # Completeness calculation
        total_depts = 8
        active_depts = sum(1 for c in [reg_count, lab_count, pharm_count, rad_count, nurs_count, appt_count, inp_count, bill_count] if c > 0)
        completeness_pct = round((active_depts / total_depts) * 100.0, 1)

        missing_fields = []
        if not patient.dob: missing_fields.append("Date of Birth")
        if not patient.contact_phone: missing_fields.append("Contact Phone")
        if not patient.blood_group: missing_fields.append("Blood Group")
        if not patient.address: missing_fields.append("Residential Address")
        if not patient.emergency_contact: missing_fields.append("Emergency Contact")

        conflicts = detect_patient_conflicts(self.db, clean_id)

        # Check existing alerts or create alerts for critical conflicts
        for conf in conflicts:
            existing_alert = self.db.query(DepartmentAlert).filter(
                DepartmentAlert.patient_id == clean_id,
                DepartmentAlert.alert_category == conf["category"],
                DepartmentAlert.status == "Open"
            ).first()
            if not existing_alert:
                alert = DepartmentAlert(
                    alert_id=f"ALT-{clean_id}-{int(time.time() * 1000) % 100000}",
                    patient_id=clean_id,
                    department=conf["department"],
                    alert_category=conf["category"],
                    description=conf["description"],
                    priority=conf["priority"],
                    status="Open",
                    created_at=datetime.utcnow()
                )
                self.db.add(alert)

        validation_status = "Requires Attention" if conflicts else ("Incomplete" if completeness_pct < 60 else "Validated")

        summary_payload = {
            "patient_demographics": {
                "name": patient.full_name,
                "dob": patient.dob,
                "gender": patient.gender,
                "blood_group": patient.blood_group,
                "allergies": patient.allergies,
                "chronic_conditions": patient.chronic_conditions
            },
            "connected_departments": {
                "registration": reg_count,
                "laboratory": lab_count,
                "pharmacy": pharm_count,
                "radiology": rad_count,
                "nursing": nurs_count,
                "inpatient": inp_count,
                "appointments": appt_count,
                "billing": bill_count
            }
        }

        provenance_payload = {
            "registration": "Registration CSV/Portal Data Ingestion",
            "laboratory": "Laboratory Information System (LIS) Interface",
            "pharmacy": "Pharmacy MIS / Prescription Ingestion",
            "radiology": "Radiology PACS Findings Engine",
            "nursing": "Ward Nurse Station Station Input",
            "inpatient": "ADT Admission-Discharge Inpatient Database",
            "appointments": "Central OPD Booking System",
            "billing": "Hospital Financial Accounts Gateway"
        }

        # Update or create UnifiedPatientRecord
        unified_rec = self.db.query(UnifiedPatientRecord).filter(UnifiedPatientRecord.patient_id == clean_id).first()
        if not unified_rec:
            unified_rec = UnifiedPatientRecord(
                patient_id=clean_id,
                completeness_score=completeness_pct,
                summary_json=json.dumps(summary_payload),
                missing_fields_json=json.dumps(missing_fields),
                conflict_fields_json=json.dumps(conflicts),
                validation_status=validation_status,
                provenance_json=json.dumps(provenance_payload),
                last_consolidated_at=datetime.utcnow()
            )
            self.db.add(unified_rec)
        else:
            unified_rec.completeness_score = completeness_pct
            unified_rec.summary_json = json.dumps(summary_payload)
            unified_rec.missing_fields_json = json.dumps(missing_fields)
            unified_rec.conflict_fields_json = json.dumps(conflicts)
            unified_rec.validation_status = validation_status
            unified_rec.provenance_json = json.dumps(provenance_payload)
            unified_rec.last_consolidated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(unified_rec)

        latency = int((time.time() - start_time) * 1000)
        self._log_execution(
            task=f"Consolidated Unified Record for {clean_id}",
            patient_id=clean_id,
            tools=tools_called,
            status="Success",
            summary=f"Unified record consolidated ({completeness_pct}% completeness, {len(conflicts)} discrepancies detected).",
            error=None,
            latency_ms=latency
        )

        return {
            "patient_id": clean_id,
            "completeness_score": completeness_pct,
            "validation_status": validation_status,
            "conflicts_count": len(conflicts),
            "missing_fields": missing_fields
        }

    def _log_execution(self, task: str, patient_id: Optional[str], tools: List[str], status: str, summary: str, error: Optional[str], latency_ms: int):
        exec_entry = AgentExecution(
            agent_name="Patient Data Management Agent",
            task=task,
            patient_id=patient_id,
            tools_invoked_json=json.dumps(tools),
            execution_status=status,
            result_summary=summary,
            error_message=error,
            latency_ms=latency_ms,
            timestamp=datetime.utcnow()
        )
        self.db.add(exec_entry)
        self.db.commit()

