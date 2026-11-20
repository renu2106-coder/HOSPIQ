import datetime
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, Index
)
from sqlalchemy.orm import relationship
from backend.database.session import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(80), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(150), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    role = Column(String(50), nullable=False)  # Doctor, Nurse, Pharmacist, Radiologist, Hospital Administrator, Patient
    department = Column(String(100), nullable=True)
    patient_id = Column(String(50), ForeignKey("patients.id", ondelete="SET NULL"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    patient = relationship("Patient", back_populates="user_account", foreign_keys=[patient_id])
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")


class Patient(Base):
    __tablename__ = "patients"

    id = Column(String(50), primary_key=True, index=True)  # e.g. P001, P002
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    full_name = Column(String(200), nullable=False, index=True)
    dob = Column(String(20), nullable=True)  # YYYY-MM-DD
    age = Column(Integer, nullable=True)
    gender = Column(String(20), nullable=True)
    contact_phone = Column(String(50), nullable=True, index=True)
    email = Column(String(150), nullable=True)
    address = Column(Text, nullable=True)
    blood_group = Column(String(10), nullable=True)
    emergency_contact = Column(String(150), nullable=True)
    allergies = Column(Text, nullable=True)
    chronic_conditions = Column(Text, nullable=True)
    registration_date = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    user_account = relationship("User", back_populates="patient", uselist=False)
    registration_records = relationship("RegistrationRecord", back_populates="patient", cascade="all, delete-orphan")
    laboratory_records = relationship("LaboratoryRecord", back_populates="patient", cascade="all, delete-orphan")
    pharmacy_records = relationship("PharmacyRecord", back_populates="patient", cascade="all, delete-orphan")
    radiology_records = relationship("RadiologyRecord", back_populates="patient", cascade="all, delete-orphan")
    nursing_records = relationship("NursingRecord", back_populates="patient", cascade="all, delete-orphan")
    appointment_records = relationship("AppointmentRecord", back_populates="patient", cascade="all, delete-orphan")
    inpatient_records = relationship("InpatientRecord", back_populates="patient", cascade="all, delete-orphan")
    billing_records = relationship("BillingRecord", back_populates="patient", cascade="all, delete-orphan")
    unified_record = relationship("UnifiedPatientRecord", back_populates="patient", uselist=False, cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="patient", cascade="all, delete-orphan")
    alerts = relationship("DepartmentAlert", back_populates="patient", cascade="all, delete-orphan")
    issues = relationship("PatientIssue", back_populates="patient", cascade="all, delete-orphan")


class RegistrationRecord(Base):
    __tablename__ = "registration_records"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String(50), ForeignKey("patients.id", ondelete="CASCADE"), index=True, nullable=False)
    name = Column(String(200), nullable=False)
    dob = Column(String(30), nullable=True)
    gender = Column(String(20), nullable=True)
    contact_number = Column(String(50), nullable=True)
    address = Column(Text, nullable=True)
    registration_date = Column(String(30), nullable=True)
    source_file = Column(String(255), nullable=True)
    raw_data_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    patient = relationship("Patient", back_populates="registration_records")


class LaboratoryRecord(Base):
    __tablename__ = "laboratory_records"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String(50), ForeignKey("patients.id", ondelete="CASCADE"), index=True, nullable=False)
    test_name = Column(String(150), nullable=False, index=True)
    test_code = Column(String(50), nullable=True)
    result_value = Column(String(100), nullable=False)
    unit = Column(String(50), nullable=True)
    reference_range = Column(String(100), nullable=True)
    is_abnormal = Column(Boolean, default=False)
    report_date = Column(String(30), nullable=True)
    lab_department = Column(String(100), nullable=True)
    ordering_physician = Column(String(150), nullable=True)
    source_file = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    patient = relationship("Patient", back_populates="laboratory_records")


class PharmacyRecord(Base):
    __tablename__ = "pharmacy_records"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String(50), ForeignKey("patients.id", ondelete="CASCADE"), index=True, nullable=False)
    medicine_name = Column(String(150), nullable=False, index=True)
    strength = Column(String(50), nullable=True)
    dosage = Column(String(100), nullable=True)
    frequency = Column(String(100), nullable=True)
    duration = Column(String(50), nullable=True)
    route = Column(String(50), nullable=True, default="Oral")
    prescription_date = Column(String(30), nullable=True)
    prescribing_doctor = Column(String(150), nullable=True)
    status = Column(String(50), default="Active")  # Active, Completed, Discontinued
    source_file = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    patient = relationship("Patient", back_populates="pharmacy_records")


class RadiologyRecord(Base):
    __tablename__ = "radiology_records"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String(50), ForeignKey("patients.id", ondelete="CASCADE"), index=True, nullable=False)
    imaging_type = Column(String(100), nullable=False)  # X-Ray, CT Scan, MRI, Ultrasound
    body_part = Column(String(100), nullable=True)
    report_findings = Column(Text, nullable=False)
    impression = Column(Text, nullable=True)
    report_date = Column(String(30), nullable=True)
    radiologist_name = Column(String(150), nullable=True)
    source_file = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    patient = relationship("Patient", back_populates="radiology_records")


class NursingRecord(Base):
    __tablename__ = "nursing_records"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String(50), ForeignKey("patients.id", ondelete="CASCADE"), index=True, nullable=False)
    vital_bp = Column(String(30), nullable=True)       # e.g. 120/80 mmHg
    vital_pulse = Column(Integer, nullable=True)       # bpm
    vital_temp = Column(Float, nullable=True)          # Fahrenheit or Celsius
    vital_resp_rate = Column(Integer, nullable=True)   # breaths/min
    vital_spo2 = Column(Integer, nullable=True)        # %
    nurse_notes = Column(Text, nullable=True)
    recorded_at = Column(String(30), nullable=True)
    nurse_name = Column(String(150), nullable=True)
    source_file = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    patient = relationship("Patient", back_populates="nursing_records")


class AppointmentRecord(Base):
    __tablename__ = "appointment_records"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String(50), ForeignKey("patients.id", ondelete="CASCADE"), index=True, nullable=False)
    appointment_date = Column(String(30), nullable=False)
    appointment_time = Column(String(20), nullable=True)
    department = Column(String(100), nullable=False)
    doctor = Column(String(150), nullable=False)
    reason_for_visit = Column(String(255), nullable=True)
    appointment_status = Column(String(50), default="Scheduled")  # Scheduled, Completed, Cancelled, No-Show
    source_file = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    patient = relationship("Patient", back_populates="appointment_records")


class InpatientRecord(Base):
    __tablename__ = "inpatient_records"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String(50), ForeignKey("patients.id", ondelete="CASCADE"), index=True, nullable=False)
    admission_date = Column(String(30), nullable=False)
    discharge_date = Column(String(30), nullable=True)
    ward = Column(String(100), nullable=True)
    bed_number = Column(String(50), nullable=True)
    admission_diagnosis = Column(Text, nullable=True)
    discharge_diagnosis = Column(Text, nullable=True)
    attending_physician = Column(String(150), nullable=True)
    discharge_status = Column(String(50), nullable=True)  # Recovered, Transferred, Home Care, Deceased
    source_file = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    patient = relationship("Patient", back_populates="inpatient_records")


class BillingRecord(Base):
    __tablename__ = "billing_records"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String(50), ForeignKey("patients.id", ondelete="CASCADE"), index=True, nullable=False)
    bill_id = Column(String(50), nullable=False, unique=True, index=True)
    service = Column(String(200), nullable=False)
    amount = Column(Float, nullable=False)
    payment_status = Column(String(50), default="Pending")  # Paid, Pending, Partially Paid, Insured
    billing_date = Column(String(30), nullable=True)
    source_file = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    patient = relationship("Patient", back_populates="billing_records")


class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id = Column(Integer, primary_key=True, index=True)
    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)  # csv, json, xlsx, pdf, png, etc.
    file_size = Column(Integer, nullable=False)     # in bytes
    source_department = Column(String(100), nullable=True)
    upload_status = Column(String(50), default="Uploaded")  # Uploaded, Processing, Completed, Failed
    extraction_status = Column(String(50), default="Pending")  # Extracted, Partial, Failed, Skipped
    validation_status = Column(String(50), default="Pending")  # Validated, Discrepancies Detected, Pending
    extracted_text = Column(Text, nullable=True)
    patient_id_matched = Column(String(50), nullable=True)
    record_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    uploaded_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    uploaded_at = Column(DateTime, default=datetime.datetime.utcnow)


class UnifiedPatientRecord(Base):
    __tablename__ = "unified_patient_records"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String(50), ForeignKey("patients.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    completeness_score = Column(Float, default=0.0)  # Percentage 0-100%
    summary_json = Column(Text, nullable=True)       # JSON summary of all departments
    missing_fields_json = Column(Text, nullable=True) # JSON list of missing fields
    conflict_fields_json = Column(Text, nullable=True)# JSON list of detected discrepancies
    validation_status = Column(String(50), default="Validated") # Validated, Requires Attention, Incomplete
    provenance_json = Column(Text, nullable=True)     # JSON tracking origins of each field
    last_consolidated_at = Column(DateTime, default=datetime.datetime.utcnow)

    patient = relationship("Patient", back_populates="unified_record")


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String(50), ForeignKey("patients.id", ondelete="CASCADE"), index=True, nullable=False)
    doc_type = Column(String(100), nullable=False)  # Clinical Summary, Patient Visit Summary, Discharge Summary, Laboratory Summary
    title = Column(String(255), nullable=False)
    natural_language_request = Column(Text, nullable=True)
    content = Column(Text, nullable=False)
    validation_status = Column(String(50), default="Pending Doctor Review")
    # Statuses: Generating, Validation Failed, Pending Doctor Review, Approved, Rejected, Revised
    doctor_notes = Column(Text, nullable=True)
    reviewed_by_doctor_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    source_references_json = Column(Text, nullable=True)  # JSON array of department records cited
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    patient = relationship("Patient", back_populates="documents")
    versions = relationship("DocumentVersion", back_populates="document", cascade="all, delete-orphan")
    validation_results = relationship("ValidationResult", back_populates="document", cascade="all, delete-orphan")


class DocumentVersion(Base):
    __tablename__ = "document_versions"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), index=True, nullable=False)
    version_number = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    changed_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    change_summary = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    document = relationship("Document", back_populates="versions")


class ValidationResult(Base):
    __tablename__ = "validation_results"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), index=True, nullable=False)
    total_checks = Column(Integer, default=0)
    passed_checks = Column(Integer, default=0)
    failed_checks = Column(Integer, default=0)
    warnings_count = Column(Integer, default=0)
    status = Column(String(50), nullable=False)  # Passed, Warning, Failed
    details_json = Column(Text, nullable=False)  # JSON array of individual check items
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    document = relationship("Document", back_populates="validation_results")


class DepartmentAlert(Base):
    __tablename__ = "department_alerts"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(String(50), unique=True, index=True, nullable=False)  # e.g. ALT-1001
    patient_id = Column(String(50), ForeignKey("patients.id", ondelete="CASCADE"), index=True, nullable=True)
    department = Column(String(100), nullable=False)
    alert_category = Column(String(100), nullable=False)
    # Duplicate Record, Conflicting Patient Details, Missing Laboratory Information,
    # Inconsistent Medication, Incorrect Appointment, Data Sync Error
    description = Column(Text, nullable=False)
    priority = Column(String(30), default="Medium")  # Low, Medium, High, Critical
    status = Column(String(50), default="Open")      # Open, Under Investigation, Resolution Pending, Resolved, Dismissed
    assigned_to = Column(String(100), nullable=True)
    investigation_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    patient = relationship("Patient", back_populates="alerts")
    corrections = relationship("CorrectionRequest", back_populates="alert", cascade="all, delete-orphan")


class CorrectionRequest(Base):
    __tablename__ = "correction_requests"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, ForeignKey("department_alerts.id", ondelete="CASCADE"), index=True, nullable=True)
    patient_id = Column(String(50), ForeignKey("patients.id", ondelete="CASCADE"), index=True, nullable=False)
    department = Column(String(100), nullable=False)
    field_name = Column(String(100), nullable=False)
    original_value = Column(Text, nullable=True)
    proposed_value = Column(Text, nullable=False)
    justification = Column(Text, nullable=False)
    requested_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(50), default="Pending Review")  # Pending Review, Approved, Rejected
    reviewed_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    review_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    alert = relationship("DepartmentAlert", back_populates="corrections")


class PatientIssue(Base):
    __tablename__ = "patient_issues"

    id = Column(Integer, primary_key=True, index=True)
    issue_id = Column(String(50), unique=True, index=True, nullable=False)  # e.g. ISS-2001
    patient_id = Column(String(50), ForeignKey("patients.id", ondelete="CASCADE"), index=True, nullable=True)
    category = Column(String(100), nullable=False)
    # Personal Information, Appointment, Laboratory Report, Prescription or Medication,
    # Radiology Report, Billing, Hospital Service, Website or Technical Issue, Other
    description = Column(Text, nullable=False)
    attachment_filename = Column(String(255), nullable=True)
    status = Column(String(50), default="Submitted")
    # Submitted, Assigned, In Progress, Awaiting Patient Information, Resolved, Rejected
    priority = Column(String(30), default="Medium")
    assigned_department = Column(String(100), nullable=True)
    routing_reason = Column(Text, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    submitted_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    patient = relationship("Patient", back_populates="issues")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(50), unique=True, index=True, nullable=False)  # e.g. EVT-3001
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    user_role = Column(String(50), nullable=True)
    action = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(100), nullable=True)  # Patient, Document, Alert, Issue, Upload, User, Auth
    entity_id = Column(String(100), nullable=True)
    status = Column(String(50), default="SUCCESS")    # SUCCESS, FAILED, UNAUTHORIZED, WARNING
    details_json = Column(Text, nullable=True)
    ip_address = Column(String(50), nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)

    user = relationship("User", back_populates="audit_logs")


class AgentExecution(Base):
    __tablename__ = "agent_executions"

    id = Column(Integer, primary_key=True, index=True)
    agent_name = Column(String(100), nullable=False, index=True)
    # Patient Data Management Agent, Documentation Agent, Validation Agent, Issue Management Agent, Orchestrator Agent
    task = Column(String(255), nullable=False)
    patient_id = Column(String(50), nullable=True, index=True)
    tools_invoked_json = Column(Text, nullable=True)  # JSON list of tools called
    execution_status = Column(String(50), default="Success")  # Success, Failed, Running
    result_summary = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    latency_ms = Column(Integer, default=0)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)

