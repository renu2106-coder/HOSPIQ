import json
import re
import secrets
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Body
from sqlalchemy import or_
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.models.models import (
    User, UploadedFile, Patient, RegistrationRecord, LaboratoryRecord,
    PharmacyRecord, RadiologyRecord, NursingRecord, AppointmentRecord,
    InpatientRecord, BillingRecord
)
from backend.schemas.schemas import UploadedFileOut
from backend.security.auth import get_current_user, require_roles
from backend.connectors.file_parser import (
    parse_any_file, SUPPORTED_EXTENSIONS,
    normalize_document_text, parse_unstructured_text
)
from backend.skills.audit_logging_skill import log_audit_event
from backend.skills.data_normalization_skill import normalize_record_dict, normalize_date
from backend.skills.patient_matching_skill import match_patient_identity, compute_name_similarity
from backend.agents.patient_data_agent import PatientDataManagementAgent

router = APIRouter(prefix="/api/uploads", tags=["File Ingestion & Uploads"])

UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB


def _generate_next_canonical_patient_id(db: Session) -> str:
    """Generates next sequential canonical patient ID (e.g. P021, P022)."""
    all_pids = [row[0] for row in db.query(Patient.id).all()]
    max_num = 20
    for pid in all_pids:
        m = re.match(r'^P(\d+)$', str(pid).strip().upper())
        if m:
            max_num = max(max_num, int(m.group(1)))
    return f"P{max_num + 1:03d}"


def _resolve_or_create_patient(rec: Dict[str, Any], db: Session) -> str:
    """Resolves extracted patient metadata against existing patients (canonical ID, UHID, or fuzzy name) or creates a new patient."""
    raw_pid = str(rec.get("patient_id") or "").strip().upper()
    ext_ids = rec.get("external_ids") or []
    full_name = str(rec.get("name") or rec.get("full_name") or "").strip()
    dob = rec.get("dob") or rec.get("date_of_birth")
    gender = rec.get("gender")
    age = rec.get("age")

    # 1. Exact canonical Patient ID check
    if raw_pid:
        exact = db.query(Patient).filter(Patient.id == raw_pid).first()
        if exact:
            return exact.id

    # 2. External hospital ID check (UHID / OP Reg / Patient ID in RegistrationRecord or Patient.address)
    for ext in ([raw_pid] if raw_pid else []) + [str(e).strip().upper() for e in ext_ids if e]:
        if len(ext) >= 4:
            reg_hit = db.query(RegistrationRecord).filter(
                or_(
                    RegistrationRecord.address.ilike(f"%{ext}%"),
                    RegistrationRecord.raw_data_json.ilike(f"%{ext}%")
                )
            ).first()
            if reg_hit:
                return reg_hit.patient_id

    # 3. Multi-factor fuzzy patient matching by name + DOB/gender, plus high-confidence name match
    if full_name and full_name.lower() not in ("unknown", "patient"):
        clean_candidate = re.sub(r'(?i)^(mr|ms|mrs|dr)\.?\s+', '', full_name).strip()
        fuzzy = match_patient_identity(
            db,
            candidate_name=clean_candidate or full_name,
            dob=dob,
            gender=gender
        )
        if fuzzy.get("matched") and fuzzy.get("patient_id"):
            return fuzzy["patient_id"]

        # Exact/near-exact name + compatible gender match (handles reports with Age instead of exact DOB)
        for p in db.query(Patient).all():
            clean_p_name = re.sub(r'(?i)^(mr|ms|mrs|dr)\.?\s+', '', p.full_name or "").strip()
            sim = compute_name_similarity(clean_candidate, clean_p_name)
            gender_ok = (not gender) or (not p.gender) or (gender.lower() == p.gender.lower()) or (p.gender == "Unknown")
            if sim >= 0.88 and gender_ok:
                return p.id

    # 4. Create new patient with canonical P-ID
    if raw_pid and re.match(r'^P\d{3}$', raw_pid):
        new_pid = raw_pid
    else:
        new_pid = _generate_next_canonical_patient_id(db)

    display_name = full_name if full_name else f"Patient {raw_pid or new_pid}"
    clean_name_parts = re.sub(r'(?i)^(mr|ms|mrs|dr)\.?\s+', '', display_name).strip().split()
    fname = clean_name_parts[0] if clean_name_parts else "Patient"
    lname = " ".join(clean_name_parts[1:]) if len(clean_name_parts) > 1 else (raw_pid or new_pid)

    computed_age = int(age) if age and str(age).isdigit() else None
    norm_dob = normalize_date(dob) if dob else None
    if not norm_dob and computed_age:
        norm_dob = f"{datetime.utcnow().year - computed_age}-01-01"

    ext_summary = ", ".join([e for e in ext_ids if e]) if ext_ids else (raw_pid or "")
    patient = Patient(
        id=new_pid,
        first_name=fname[:80],
        last_name=lname[:80],
        full_name=display_name[:150],
        dob=norm_dob or "1985-01-01",
        age=computed_age,
        gender=gender or "Unknown",
        contact_phone=rec.get("contact_phone") or rec.get("phone") or "+91-90000-00000",
        blood_group=rec.get("blood_group") or "Not Documented",
        address=f"Hospital ID Ref: {ext_summary}" if ext_summary else (rec.get("address") or "Hospital Outpatient / Digitalized Record"),
        allergies=rec.get("allergies") or "None Reported",
        chronic_conditions=rec.get("chronic_conditions") or "Under Evaluation",
        registration_date=normalize_date(rec.get("report_date") or rec.get("date")) or datetime.utcnow().strftime("%Y-%m-%d"),
        created_at=datetime.utcnow()
    )
    db.add(patient)
    db.flush()
    return new_pid


def sync_parsed_records_to_database(
    raw_records: List[Dict[str, Any]],
    department: str,
    original_filename: str,
    db: Session
) -> Dict[str, Any]:
    """Automated database update: maps parsed/normalized records into relational department tables

    and triggers PatientDataManagementAgent consolidation + clinical alert detection.
    """
    ingested_count = 0
    affected_patients = set()
    departments_affected = set()
    resolved_cache: Dict[str, str] = {}

    for raw_rec in raw_records:
        if not isinstance(raw_rec, dict):
            continue

        rec = normalize_record_dict(raw_rec)
        # Preserve helper metadata that normalize_record_dict might pass through
        cache_key = f"{rec.get('patient_id') or ''}|{rec.get('full_name') or rec.get('name') or ''}"
        if cache_key in resolved_cache:
            pid = resolved_cache[cache_key]
        else:
            pid = _resolve_or_create_patient(raw_rec, db)
            resolved_cache[cache_key] = pid
        affected_patients.add(pid)

        dept_lower = str(rec.get("department") or department or "General").lower()

        # 1. Laboratory Record
        if "lab" in dept_lower or "test_name" in rec or "result_value" in rec:
            test_name = str(rec.get("test_name") or "Diagnostic Panel")
            res_val = str(rec.get("result_value") or rec.get("result") or "Normal")
            lab_entry = LaboratoryRecord(
                patient_id=pid,
                test_name=test_name[:120],
                test_code=rec.get("test_code") or f"LAB-{re.sub(r'[^A-Z0-9]', '', test_name.upper())[:6] or 'AUTO'}",
                result_value=res_val[:80],
                unit=str(rec.get("unit") or ""),
                reference_range=rec.get("reference_range") or "Standard Clinical Range",
                is_abnormal=bool(rec.get("is_abnormal", False)),
                report_date=normalize_date(rec.get("report_date") or rec.get("date")),
                lab_department=rec.get("lab_department") or "Clinical Pathology & Diagnostics",
                ordering_physician=rec.get("ordering_physician") or rec.get("consultant") or "Attending Physician",
                source_file=original_filename,
                created_at=datetime.utcnow()
            )
            db.add(lab_entry)
            ingested_count += 1
            departments_affected.add("Laboratory")

        # 2. Pharmacy Record
        elif "pharm" in dept_lower or "medicine_name" in rec or "medication" in rec:
            med_name = str(rec.get("medicine_name") or rec.get("medication") or "Medication")
            pharm_entry = PharmacyRecord(
                patient_id=pid,
                medicine_name=med_name[:120],
                strength=str(rec.get("strength") or "Standard"),
                dosage=str(rec.get("dosage") or "1 tablet"),
                frequency=str(rec.get("frequency") or "Daily"),
                duration=str(rec.get("duration") or "7 days"),
                route=str(rec.get("route") or "Oral"),
                prescription_date=normalize_date(rec.get("prescription_date") or rec.get("date")),
                prescribing_doctor=rec.get("prescribing_doctor") or rec.get("consultant") or "Attending Physician",
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
                imaging_type=str(rec.get("imaging_type") or "Diagnostic Imaging")[:120],
                body_part=str(rec.get("body_part") or "Specified Region")[:80],
                report_findings=str(rec.get("report_findings") or rec.get("findings") or "Diagnostic imaging performed."),
                impression=str(rec.get("impression") or "See radiology report for clinical correlation."),
                report_date=normalize_date(rec.get("report_date") or rec.get("date")),
                radiologist_name=str(rec.get("radiologist_name") or rec.get("consultant") or "Consultant Radiologist")[:120],
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
                vital_bp=str(rec.get("vital_bp") or "120/80"),
                vital_pulse=int(rec.get("vital_pulse") or 72),
                vital_temp=float(rec.get("vital_temp") or 98.6),
                vital_resp_rate=int(rec.get("vital_resp_rate") or 16),
                vital_spo2=int(rec.get("vital_spo2") or 98),
                nurse_notes=str(rec.get("nurse_notes") or "Vitals recorded and normalized."),
                recorded_at=normalize_date(rec.get("recorded_at") or rec.get("date")),
                nurse_name=str(rec.get("nurse_name") or "Staff Nurse"),
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
                ward=str(rec.get("ward") or "General Ward"),
                bed_number=str(rec.get("bed_number") or "B-101"),
                admission_diagnosis=str(rec.get("admission_diagnosis") or "Clinical Evaluation"),
                discharge_diagnosis=str(rec.get("discharge_diagnosis") or "Under Review"),
                attending_physician=str(rec.get("attending_physician") or rec.get("consultant") or "Staff Physician"),
                discharge_status=str(rec.get("discharge_status") or "Recovered"),
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
                appointment_time=str(rec.get("appointment_time") or "09:00 AM"),
                department=str(rec.get("department") or "General Medicine"),
                doctor=str(rec.get("doctor") or rec.get("consultant") or "Attending Physician"),
                reason_for_visit=str(rec.get("reason_for_visit") or "Routine consultation"),
                appointment_status=str(rec.get("appointment_status") or "Completed"),
                source_file=original_filename,
                created_at=datetime.utcnow()
            )
            db.add(appt_entry)
            ingested_count += 1
            departments_affected.add("Appointments")

        # 7. Billing
        elif "bill" in dept_lower or "bill_id" in rec:
            bid = str(rec.get("bill_id") or f"BILL-{pid}-{secrets.token_hex(3).upper()}")
            bill_entry = BillingRecord(
                patient_id=pid,
                bill_id=bid,
                service=str(rec.get("service") or "Hospital Service Consultation"),
                amount=float(rec.get("amount") or 150.0),
                payment_status=str(rec.get("payment_status") or "Paid"),
                billing_date=normalize_date(rec.get("billing_date") or rec.get("date")),
                source_file=original_filename,
                created_at=datetime.utcnow()
            )
            db.add(bill_entry)
            ingested_count += 1
            departments_affected.add("Billing")

        # 8. Registration
        elif "reg" in dept_lower or "registration" in dept_lower or raw_rec.get("external_ids"):
            ext_tag = ", ".join([str(x) for x in (raw_rec.get("external_ids") or [])])
            pat_obj = db.query(Patient).filter(Patient.id == pid).first()
            reg_name = str(rec.get("full_name") or rec.get("name") or (pat_obj.full_name if pat_obj else f"Patient {pid}"))
            addr_val = str(rec.get("address") or (f"Hospital Digitalized Intake (Ref ID: {ext_tag})" if ext_tag else "Hospital Digitalized Intake"))
            reg_entry = RegistrationRecord(
                patient_id=pid,
                name=reg_name[:180],
                dob=normalize_date(rec.get("dob")),
                gender=rec.get("gender"),
                registration_date=normalize_date(rec.get("registration_date") or rec.get("date") or rec.get("report_date")),
                contact_number=rec.get("contact_number") or rec.get("phone") or "+91-90000-00000",
                address=addr_val,
                raw_data_json=json.dumps({"external_ids": raw_rec.get("external_ids") or [], "department": department}),
                source_file=original_filename,
                created_at=datetime.utcnow()
            )
            db.add(reg_entry)
            ingested_count += 1
            departments_affected.add("Registration")

    db.commit()

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


def sync_file_records_to_database(file_path: str, department: str, original_filename: str, db: Session) -> Dict[str, Any]:
    """Parses a file on disk and runs automated database synchronization."""
    parse_result = parse_any_file(file_path, department=department)
    if not parse_result.get("success"):
        return {"success": False, "error": parse_result.get("error", "Failed to parse file")}

    records = parse_result.get("records", [])
    if not records:
        return {
            "success": True,
            "records_ingested": 0,
            "patients_affected": [],
            "patients_reconciled": [],
            "departments_affected": [],
            "note": parse_result.get("extracted_text", "No structured entities detected.")
        }

    return sync_parsed_records_to_database(records, department, original_filename, db)


@router.post("/ingest-text")
def ingest_digitalized_report_text(
    payload: Dict[str, Any] = Body(...),
    current_user: User = Depends(require_roles(["Hospital Administrator", "Doctor", "Paramedic", "Nurse", "Radiologist", "Pharmacist"])),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Accepts digitalized or OCR-copied text from any hospital PDF/X-Ray/Lab report, normalizes it,

    auto-matches/creates the patient, populates department tables, and triggers agent reconciliation + alerts.
    """
    raw_text = str(payload.get("text") or "").strip()
    department = str(payload.get("department") or "General")
    filename = str(payload.get("filename") or f"digitalized_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.txt")

    if not raw_text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Report text cannot be empty.")

    normalized_text = normalize_document_text(raw_text)
    extracted_records = parse_unstructured_text(normalized_text, department=department)

    if not extracted_records:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not identify clinical fields or patient info. Include headers like Patient Name, Lab values, or Radiology Findings/Impression."
        )

    sync_summary = sync_parsed_records_to_database(extracted_records, department, filename, db)
    matched_pid = (sync_summary.get("patients_affected") or [None])[0]

    timestamp_prefix = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    safe_token = secrets.token_hex(4)
    stored_filename = f"{timestamp_prefix}_{safe_token}_{Path(filename).name}"
    target_path = UPLOAD_DIR / stored_filename
    with open(target_path, "w", encoding="utf-8") as f:
        f.write(normalized_text)

    uploaded_record = UploadedFile(
        original_filename=filename,
        stored_filename=stored_filename,
        file_type="txt",
        file_size=len(normalized_text.encode("utf-8")),
        source_department=", ".join(sync_summary.get("departments_affected") or [department]),
        upload_status="Completed",
        extraction_status="Extracted",
        validation_status="Synced & Reconciled",
        extracted_text=normalized_text[:4000],
        patient_id_matched=matched_pid,
        record_count=sync_summary.get("records_ingested", 0),
        uploaded_by_user_id=current_user.id,
        uploaded_at=datetime.utcnow()
    )
    db.add(uploaded_record)
    db.commit()
    db.refresh(uploaded_record)

    log_audit_event(
        db=db,
        action="DIGITALIZED_TEXT_INGESTED_AND_SYNCED",
        user_id=current_user.id,
        user_role=current_user.role,
        entity_type="UploadedFile",
        entity_id=str(uploaded_record.id),
        status="SUCCESS",
        details={
            "filename": filename,
            "matched_patient_id": matched_pid,
            "records_ingested": sync_summary.get("records_ingested", 0),
            "departments": sync_summary.get("departments_affected", [])
        }
    )

    return {
        "success": True,
        "uploaded_file_id": uploaded_record.id,
        "matched_patient_id": matched_pid,
        "normalized_text": normalized_text,
        "sync_summary": sync_summary
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

    documents (TXT, PDF, ZIP), and imaging reports (JPG, PNG, TIFF, WEBP).
    """
    original_filename = file.filename or "unknown_file"
    file_ext = Path(original_filename).suffix.lower()

    if file_ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported format '{file_ext}'. Supported formats: CSV, JSON, XLSX, XLS, TXT, PDF, ZIP, JPG, PNG, TIFF, WEBP."
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

    extraction_status = "Extracted" if parse_result["success"] and parse_result.get("record_count", 0) > 0 else ("Scanned / OCR Needed" if parse_result["success"] else "Failed")
    sync_summary = None
    matched_pid = parse_result.get("matched_patient_id")

    if auto_sync and parse_result["success"] and parse_result.get("records"):
        sync_summary = sync_parsed_records_to_database(
            raw_records=parse_result.get("records", []),
            department=department or "General",
            original_filename=original_filename,
            db=db
        )
        if sync_summary.get("patients_affected"):
            matched_pid = sync_summary["patients_affected"][0]

    val_status = "Synced & Reconciled" if (sync_summary and sync_summary.get("records_ingested", 0) > 0) else ("Pending Text / OCR" if parse_result["success"] else "Failed")
    error_msg = parse_result.get("error") if not parse_result["success"] else None

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
        patient_id_matched=matched_pid,
        record_count=(sync_summary.get("records_ingested") if sync_summary else parse_result.get("record_count", 0)) or 0,
        error_message=error_msg,
        uploaded_by_user_id=current_user.id,
        uploaded_at=datetime.utcnow()
    )
    db.add(uploaded_record)
    db.commit()
    db.refresh(uploaded_record)

    log_audit_event(
        db=db,
        action="FILE_UPLOADED_AND_DATABASE_SYNCED" if (sync_summary and sync_summary.get("records_ingested", 0) > 0) else "FILE_UPLOADED",
        user_id=current_user.id,
        user_role=current_user.role,
        entity_type="UploadedFile",
        entity_id=str(uploaded_record.id),
        status="SUCCESS" if parse_result["success"] else "WARNING",
        details={
            "filename": original_filename,
            "department": department,
            "records_found": uploaded_record.record_count,
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

    if sync_result.get("patients_affected"):
        record.patient_id_matched = sync_result["patients_affected"][0]
    record.validation_status = "Synced & Reconciled" if sync_result.get("records_ingested", 0) > 0 else "Pending Text / OCR"
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
            if res.get("success") and res.get("records_ingested", 0) > 0:
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
