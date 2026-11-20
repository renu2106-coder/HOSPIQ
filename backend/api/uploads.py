import os
import secrets
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.models.models import (
    User, UploadedFile, Patient, RegistrationRecord, LaboratoryRecord,
    PharmacyRecord, RadiologyRecord, NursingRecord, AppointmentRecord,
    InpatientRecord, BillingRecord
)
from backend.schemas.schemas import UploadedFileOut
from backend.security.auth import get_current_user, require_roles
from backend.connectors.file_parser import parse_any_file, SUPPORTED_EXTENSIONS
from backend.skills.audit_logging_skill import log_audit_event
from backend.skills.data_normalization_skill import normalize_record_dict, normalize_date
from backend.agents.patient_data_agent import PatientDataManagementAgent

router = APIRouter(prefix="/api/uploads", tags=["File Ingestion & Uploads"])

UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB


def sync_file_records_to_database(file_path: str, department: str, original_filename: str, db: Session) -> Dict[str, Any]:
    """Automated database update: converts parsed/normalized records into relational department tables

    and recalculates Unified Patient Records, completeness, and clinical conflict checks.
    """
    parse_result = parse_any_file(file_path, department=department)
    if not parse_result.get("success"):
        return {"success": False, "error": parse_result.get("error", "Failed to parse file")}

    records = parse_result.get("records", [])
    default_pid = parse_result.get("matched_patient_id") or "P001"
    ingested_count = 0
    affected_patients = set()
    departments_affected = set()

    for raw_rec in records:
        if not isinstance(raw_rec, dict):
            continue

        rec = normalize_record_dict(raw_rec)
        pid = rec.get("patient_id") or default_pid
        pid = str(pid).strip().upper()
        affected_patients.add(pid)

        # Ensure Patient exists
        patient = db.query(Patient).filter(Patient.id == pid).first()
        if not patient:
            full_name = str(rec.get("name") or rec.get("full_name") or f"Patient {pid}").strip()
            parts = full_name.split()
            fname = parts[0] if parts else f"Patient"
            lname = " ".join(parts[1:]) if len(parts) > 1 else pid
            patient = Patient(
                id=pid,
                first_name=fname,
                last_name=lname,
                full_name=full_name,
                dob=normalize_date(rec.get("dob") or rec.get("date_of_birth") or "1980-01-01"),
                gender=rec.get("gender") or "Unknown",
                contact_phone=rec.get("contact_phone") or rec.get("phone") or "+1-555-0000",
                blood_group=rec.get("blood_group") or "O+",
                allergies=rec.get("allergies") or "None Reported",
                chronic_conditions=rec.get("chronic_conditions") or "None",
                created_at=datetime.utcnow()
            )
            db.add(patient)
            db.flush()

        dept_lower = (rec.get("department") or department or "General").lower()

        # 1. Laboratory Record
        if "lab" in dept_lower or "test_name" in rec or "result_value" in rec:
            test_name = rec.get("test_name") or "Diagnostic Panel"
            res_val = str(rec.get("result_value") or rec.get("result") or "Normal")
            lab_entry = LaboratoryRecord(
                patient_id=pid,
                test_name=test_name,
                test_code=rec.get("test_code") or "LAB-AUTO",
                result_value=res_val,
                unit=rec.get("unit") or "mg/dL",
                reference_range=rec.get("reference_range") or "Standard Clinical Range",
                is_abnormal=bool(rec.get("is_abnormal", False)),
                report_date=normalize_date(rec.get("report_date") or rec.get("date")),
                lab_department=rec.get("lab_department") or "Clinical Chemistry",
                source_file=original_filename,
                created_at=datetime.utcnow()
            )
            db.add(lab_entry)
            ingested_count += 1
            departments_affected.add("Laboratory")

        # 2. Pharmacy Record
        elif "pharm" in dept_lower or "medicine_name" in rec or "medication" in rec:
            med_name = rec.get("medicine_name") or rec.get("medication") or "Medication"
            pharm_entry = PharmacyRecord(
                patient_id=pid,
                medicine_name=med_name,
                strength=rec.get("strength") or "Standard",
                dosage=rec.get("dosage") or "1 tablet",
                frequency=rec.get("frequency") or "Daily",
                duration=rec.get("duration") or "7 days",
                route=rec.get("route") or "Oral",
                prescription_date=normalize_date(rec.get("prescription_date") or rec.get("date")),
                prescribing_doctor=rec.get("prescribing_doctor") or "Attending Physician",
                status="Active",
                source_file=original_filename,
                created_at=datetime.utcnow()
            )
            db.add(pharm_entry)
            ingested_count += 1
            departments_affected.add("Pharmacy")

        # 3. Radiology Record
        elif "rad" in dept_lower or "imaging_type" in rec or "report_findings" in rec:
            rad_entry = RadiologyRecord(
                patient_id=pid,
                imaging_type=rec.get("imaging_type") or "Diagnostic Imaging",
                body_part=rec.get("body_part") or "Chest",
                report_findings=rec.get("report_findings") or rec.get("findings") or "No acute findings.",
                impression=rec.get("impression") or "Stable clinical examination.",
                report_date=normalize_date(rec.get("report_date") or rec.get("date")),
                radiologist_name=rec.get("radiologist_name") or "Diagnostic Specialist",
                source_file=original_filename,
                created_at=datetime.utcnow()
            )
            db.add(rad_entry)
            ingested_count += 1
            departments_affected.add("Radiology")

        # 4. Nursing Record
        elif "nurs" in dept_lower or "vital_bp" in rec or "vital_pulse" in rec:
            nurse_entry = NursingRecord(
                patient_id=pid,
                vital_bp=rec.get("vital_bp") or "120/80",
                vital_pulse=int(rec.get("vital_pulse") or 72),
                vital_temp=float(rec.get("vital_temp") or 98.6),
                vital_resp_rate=int(rec.get("vital_resp_rate") or 16),
                vital_spo2=int(rec.get("vital_spo2") or 98),
                nurse_notes=rec.get("nurse_notes") or "Vitals recorded and normalized.",
                recorded_at=normalize_date(rec.get("recorded_at") or rec.get("date")),
                nurse_name=rec.get("nurse_name") or "Staff Nurse",
                source_file=original_filename,
                created_at=datetime.utcnow()
            )
            db.add(nurse_entry)
            ingested_count += 1
            departments_affected.add("Nursing")

        # 5. Inpatient Record
        elif "inpatient" in dept_lower or "admission_date" in rec:
            inp_entry = InpatientRecord(
                patient_id=pid,
                admission_date=normalize_date(rec.get("admission_date") or rec.get("date")),
                discharge_date=normalize_date(rec.get("discharge_date")),
                ward=rec.get("ward") or "General Ward",
                bed_number=str(rec.get("bed_number") or "B-101"),
                admission_diagnosis=rec.get("admission_diagnosis") or "Clinical Evaluation",
                discharge_diagnosis=rec.get("discharge_diagnosis") or "Resolved",
                attending_physician=rec.get("attending_physician") or "Staff Physician",
                discharge_status=rec.get("discharge_status") or "Recovered",
                source_file=original_filename,
                created_at=datetime.utcnow()
            )
            db.add(inp_entry)
            ingested_count += 1
            departments_affected.add("Inpatient")

        # 6. Appointments
        elif "appoint" in dept_lower or "appointment_date" in rec:
            appt_entry = AppointmentRecord(
                patient_id=pid,
                appointment_date=normalize_date(rec.get("appointment_date") or rec.get("date")),
                appointment_time=rec.get("appointment_time") or "09:00 AM",
                department=rec.get("department") or "General Medicine",
                doctor=rec.get("doctor") or "Attending Physician",
                reason_for_visit=rec.get("reason_for_visit") or "Routine consultation",
                appointment_status=rec.get("appointment_status") or "Completed",
                source_file=original_filename,
                created_at=datetime.utcnow()
            )
            db.add(appt_entry)
            ingested_count += 1
            departments_affected.add("Appointments")

        # 7. Billing
        elif "bill" in dept_lower or "bill_id" in rec:
            bid = str(rec.get("bill_id") or f"BILL-{pid}-{int(datetime.utcnow().timestamp())}")
            bill_entry = BillingRecord(
                patient_id=pid,
                bill_id=bid,
                service=rec.get("service") or "Hospital Service Consultation",
                amount=float(rec.get("amount") or 150.0),
                payment_status=rec.get("payment_status") or "Paid",
                billing_date=normalize_date(rec.get("billing_date") or rec.get("date")),
                source_file=original_filename,
                created_at=datetime.utcnow()
            )
            db.add(bill_entry)
            ingested_count += 1
            departments_affected.add("Billing")

        # 8. Registration
        elif "reg" in dept_lower or "registration" in dept_lower:
            reg_entry = RegistrationRecord(
                patient_id=pid,
                registration_date=normalize_date(rec.get("registration_date") or rec.get("date")),
                department_registered=rec.get("department_registered") or "Outpatient Registration",
                contact_number=rec.get("contact_number") or rec.get("phone") or "+1-555-0000",
                address=rec.get("address") or "Standard Address",
                source_file=original_filename,
                created_at=datetime.utcnow()
            )
            db.add(reg_entry)
            ingested_count += 1
            departments_affected.add("Registration")

    db.commit()

    # Automate multi-agent patient reconciliation and unified record consolidation
    agent = PatientDataManagementAgent(db)
    reconciled_patients = []
    for pat_id in affected_patients:
        res = agent.consolidate_unified_record(pat_id)
        if "error" not in res:
            reconciled_patients.append(pat_id)

    return {
        "success": True,
        "records_ingested": ingested_count,
        "patients_affected": list(affected_patients),
        "patients_reconciled": reconciled_patients,
        "departments_affected": list(departments_affected)
    }


@router.post("", response_model=UploadedFileOut)
async def upload_and_process_file(
    file: UploadFile = File(...),
    department: Optional[str] = Form("General"),
    auto_sync: Optional[bool] = Form(True),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Universal hospital file upload endpoint supporting structured data (CSV, JSON, XLSX),

    documents (TXT, PDF), and imaging reports (JPG, PNG, TIFF, WEBP).
    Automates text normalization and database ingestion.
    """
    original_filename = file.filename or "unknown_file"
    file_ext = Path(original_filename).suffix.lower()

    if file_ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported format '{file_ext}'. Supported formats: CSV, JSON, XLSX, XLS, TXT, PDF, JPG, PNG, TIFF, WEBP."
        )

    contents = await file.read()
    file_size = len(contents)
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of 25MB (Size: {file_size / (1024*1024):.1f} MB)."
        )

    timestamp_prefix = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    safe_token = secrets.token_hex(4)
    stored_filename = f"{timestamp_prefix}_{safe_token}_{Path(original_filename).name}"
    target_path = UPLOAD_DIR / stored_filename

    with open(target_path, "wb") as f:
        f.write(contents)

    parse_result = parse_any_file(str(target_path), department=department)

    extraction_status = "Extracted" if parse_result["success"] else "Failed"
    val_status = "Validated" if parse_result["success"] and parse_result.get("matched_patient_id") else "Pending"
    error_msg = parse_result.get("error") if not parse_result["success"] else None

    # Persist record in database
    uploaded_record = UploadedFile(
        original_filename=original_filename,
        stored_filename=stored_filename,
        file_type=file_ext.replace(".", ""),
        file_size=file_size,
        source_department=department,
        upload_status="Completed",
        extraction_status=extraction_status,
        validation_status=val_status,
        extracted_text=parse_result.get("extracted_text", "")[:4000],
        patient_id_matched=parse_result.get("matched_patient_id"),
        record_count=parse_result.get("record_count", 0),
        error_message=error_msg,
        uploaded_by_user_id=current_user.id,
        uploaded_at=datetime.utcnow()
    )
    db.add(uploaded_record)
    db.commit()
    db.refresh(uploaded_record)

    # Automated database synchronization if requested
    sync_summary = None
    if auto_sync and parse_result["success"]:
        sync_summary = sync_file_records_to_database(
            file_path=str(target_path),
            department=department or "General",
            original_filename=original_filename,
            db=db
        )

    log_audit_event(
        db=db,
        action="FILE_UPLOADED_AND_DATABASE_SYNCED" if (auto_sync and parse_result["success"]) else "FILE_UPLOADED",
        user_id=current_user.id,
        user_role=current_user.role,
        entity_type="UploadedFile",
        entity_id=str(uploaded_record.id),
        status="SUCCESS" if parse_result["success"] else "WARNING",
        details={
            "filename": original_filename,
            "department": department,
            "records_found": parse_result.get("record_count", 0),
            "auto_synced": bool(auto_sync),
            "sync_summary": sync_summary
        }
    )

    return uploaded_record


@router.post("/{file_id}/auto-sync")
def auto_sync_uploaded_file(
    file_id: int,
    current_user: User = Depends(require_roles(["Hospital Administrator", "Doctor", "Paramedic"])),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Automates normalization, database insertion, and unified patient reconciliation for an uploaded file."""
    record = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Uploaded file record not found.")

    file_path = UPLOAD_DIR / record.stored_filename
    if not file_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Underlying file not found on disk.")

    sync_result = sync_file_records_to_database(
        file_path=str(file_path),
        department=record.source_department or "General",
        original_filename=record.original_filename,
        db=db
    )

    record.validation_status = "Synced & Reconciled"
    db.commit()

    log_audit_event(
        db=db,
        action="DATABASE_AUTOMATED_SYNC",
        user_id=current_user.id,
        user_role=current_user.role,
        entity_type="UploadedFile",
        entity_id=str(record.id),
        status="SUCCESS" if sync_result.get("success") else "FAILED",
        details=sync_result
    )

    return sync_result


@router.post("/auto-sync-all")
def auto_sync_all_files(
    current_user: User = Depends(require_roles(["Hospital Administrator", "Doctor"])),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Automates full hospital database update across all uploaded department files."""
    files = db.query(UploadedFile).all()
    total_records = 0
    synced_files = 0
    all_affected_patients = set()

    for f in files:
        fpath = UPLOAD_DIR / f.stored_filename
        if fpath.exists():
            res = sync_file_records_to_database(
                file_path=str(fpath),
                department=f.source_department or "General",
                original_filename=f.original_filename,
                db=db
            )
            if res.get("success"):
                synced_files += 1
                total_records += res.get("records_ingested", 0)
                all_affected_patients.update(res.get("patients_affected", []))
                f.validation_status = "Synced & Reconciled"

    db.commit()

    log_audit_event(
        db=db,
        action="DATABASE_FULL_AUTOMATED_SYNC",
        user_id=current_user.id,
        user_role=current_user.role,
        entity_type="HospitalDatabase",
        entity_id="ALL",
        status="SUCCESS",
        details={
            "synced_files": synced_files,
            "total_records_ingested": total_records,
            "patients_reconciled": list(all_affected_patients)
        }
    )

    return {
        "success": True,
        "files_synced": synced_files,
        "total_records_ingested": total_records,
        "patients_reconciled": list(all_affected_patients)
    }


@router.get("/{file_id}/normalized-text")
def get_file_normalized_text(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Returns the clean normalized text and extracted clinical entities from any uploaded PDF/file."""
    record = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found.")

    file_path = UPLOAD_DIR / record.stored_filename
    if not file_path.exists():
        return {
            "file_id": file_id,
            "filename": record.original_filename,
            "normalized_text": record.extracted_text or "No text available.",
            "records": []
        }

    parsed = parse_any_file(str(file_path), department=record.source_department)
    return {
        "file_id": file_id,
        "filename": record.original_filename,
        "file_type": record.file_type,
        "department": record.source_department,
        "matched_patient_id": parsed.get("matched_patient_id") or record.patient_id_matched,
        "normalized_text": parsed.get("extracted_text") or record.extracted_text or "",
        "structured_records": parsed.get("records", [])
    }


@router.get("", response_model=List[UploadedFileOut])
def list_uploaded_files(
    department: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lists files ingested into the platform."""
    if current_user.role == "Patient":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Patients cannot view raw file uploads.")

    q = db.query(UploadedFile)
    if department:
        q = q.filter(UploadedFile.source_department == department)
    return q.order_by(UploadedFile.uploaded_at.desc()).all()

