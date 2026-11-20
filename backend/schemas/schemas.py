from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


# Auth Schemas
class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    username: str
    role: str
    full_name: str
    department: Optional[str] = None
    patient_id: Optional[str] = None


class UserLogin(BaseModel):
    username: str
    password: str


class TwoFactorInitiateRequest(BaseModel):
    username: str
    password: str


class TwoFactorVerifyRequest(BaseModel):
    username: str
    code: str


class TwoFactorChallengeOut(BaseModel):
    requires_2fa: bool
    session_id: str
    username: str
    full_name: str
    role: str
    masked_contact: str
    security_code: str


class UserCreate(BaseModel):
    username: str
    password: str
    full_name: str
    email: str
    role: str
    department: Optional[str] = None
    patient_id: Optional[str] = None


class UserOut(BaseModel):
    id: int
    username: str
    full_name: str
    email: str
    role: str
    department: Optional[str] = None
    patient_id: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Patient Schemas
class PatientOut(BaseModel):
    id: str
    first_name: str
    last_name: str
    full_name: str
    dob: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    contact_phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    blood_group: Optional[str] = None
    emergency_contact: Optional[str] = None
    allergies: Optional[str] = None
    chronic_conditions: Optional[str] = None
    registration_date: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class UnifiedPatientRecordOut(BaseModel):
    id: int
    patient_id: str
    completeness_score: float
    summary_json: Optional[str] = None
    missing_fields_json: Optional[str] = None
    conflict_fields_json: Optional[str] = None
    validation_status: str
    provenance_json: Optional[str] = None
    last_consolidated_at: datetime

    class Config:
        from_attributes = True


# Department Records
class RegistrationRecordOut(BaseModel):
    id: int
    patient_id: str
    name: str
    dob: Optional[str] = None
    gender: Optional[str] = None
    contact_number: Optional[str] = None
    address: Optional[str] = None
    registration_date: Optional[str] = None
    source_file: Optional[str] = None

    class Config:
        from_attributes = True


class LaboratoryRecordOut(BaseModel):
    id: int
    patient_id: str
    test_name: str
    test_code: Optional[str] = None
    result_value: str
    unit: Optional[str] = None
    reference_range: Optional[str] = None
    is_abnormal: bool
    report_date: Optional[str] = None
    lab_department: Optional[str] = None
    ordering_physician: Optional[str] = None
    source_file: Optional[str] = None

    class Config:
        from_attributes = True


class PharmacyRecordOut(BaseModel):
    id: int
    patient_id: str
    medicine_name: str
    strength: Optional[str] = None
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    duration: Optional[str] = None
    route: Optional[str] = None
    prescription_date: Optional[str] = None
    prescribing_doctor: Optional[str] = None
    status: str
    source_file: Optional[str] = None

    class Config:
        from_attributes = True


class RadiologyRecordOut(BaseModel):
    id: int
    patient_id: str
    imaging_type: str
    body_part: Optional[str] = None
    report_findings: str
    impression: Optional[str] = None
    report_date: Optional[str] = None
    radiologist_name: Optional[str] = None
    source_file: Optional[str] = None

    class Config:
        from_attributes = True


class NursingRecordOut(BaseModel):
    id: int
    patient_id: str
    vital_bp: Optional[str] = None
    vital_pulse: Optional[int] = None
    vital_temp: Optional[float] = None
    vital_resp_rate: Optional[int] = None
    vital_spo2: Optional[int] = None
    nurse_notes: Optional[str] = None
    recorded_at: Optional[str] = None
    nurse_name: Optional[str] = None
    source_file: Optional[str] = None

    class Config:
        from_attributes = True


class AppointmentRecordOut(BaseModel):
    id: int
    patient_id: str
    appointment_date: str
    appointment_time: Optional[str] = None
    department: str
    doctor: str
    reason_for_visit: Optional[str] = None
    appointment_status: str
    source_file: Optional[str] = None

    class Config:
        from_attributes = True


class InpatientRecordOut(BaseModel):
    id: int
    patient_id: str
    admission_date: str
    discharge_date: Optional[str] = None
    ward: Optional[str] = None
    bed_number: Optional[str] = None
    admission_diagnosis: Optional[str] = None
    discharge_diagnosis: Optional[str] = None
    attending_physician: Optional[str] = None
    discharge_status: Optional[str] = None
    source_file: Optional[str] = None

    class Config:
        from_attributes = True


class BillingRecordOut(BaseModel):
    id: int
    patient_id: str
    bill_id: str
    service: str
    amount: float
    payment_status: str
    billing_date: Optional[str] = None
    source_file: Optional[str] = None

    class Config:
        from_attributes = True


# Document Schemas
class DocumentGenerateRequest(BaseModel):
    patient_id: str
    doc_type: str  # Clinical Summary, Patient Visit Summary, Discharge Summary, Laboratory Summary
    natural_language_request: Optional[str] = None


class DocumentUpdate(BaseModel):
    content: str
    change_summary: Optional[str] = "Manual physician revision"


class DocumentReviewRequest(BaseModel):
    action: str  # APPROVE, REJECT, or EMERGENCY_DIRECT_ISSUE
    doctor_notes: Optional[str] = None
    is_emergency: Optional[bool] = False
    emergency_override_reason: Optional[str] = None


class DocumentVersionOut(BaseModel):
    id: int
    document_id: int
    version_number: int
    content: str
    changed_by_user_id: Optional[int] = None
    change_summary: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ValidationResultOut(BaseModel):
    id: int
    document_id: int
    total_checks: int
    passed_checks: int
    failed_checks: int
    warnings_count: int
    status: str
    details_json: str
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentOut(BaseModel):
    id: int
    patient_id: str
    doc_type: str
    title: str
    natural_language_request: Optional[str] = None
    content: str
    validation_status: str
    doctor_notes: Optional[str] = None
    reviewed_by_doctor_id: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    created_by_user_id: Optional[int] = None
    source_references_json: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    versions: Optional[List[DocumentVersionOut]] = None
    validation_results: Optional[List[ValidationResultOut]] = None

    class Config:
        from_attributes = True


# Alert & Correction Schemas
class DepartmentAlertOut(BaseModel):
    id: int
    alert_id: str
    patient_id: Optional[str] = None
    department: str
    alert_category: str
    description: str
    priority: str
    status: str
    assigned_to: Optional[str] = None
    investigation_notes: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AlertStatusUpdate(BaseModel):
    status: str
    investigation_notes: Optional[str] = None
    assigned_to: Optional[str] = None


class CorrectionRequestCreate(BaseModel):
    alert_id: Optional[int] = None
    patient_id: str
    department: str
    field_name: str
    original_value: Optional[str] = None
    proposed_value: str
    justification: str


class CorrectionRequestReview(BaseModel):
    action: str  # APPROVE or REJECT
    review_notes: Optional[str] = None


class CorrectionRequestOut(BaseModel):
    id: int
    alert_id: Optional[int] = None
    patient_id: str
    department: str
    field_name: str
    original_value: Optional[str] = None
    proposed_value: str
    justification: str
    requested_by_user_id: Optional[int] = None
    status: str
    reviewed_by_user_id: Optional[int] = None
    review_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Patient Issue Schemas
class PatientIssueCreate(BaseModel):
    patient_id: Optional[str] = None
    category: str
    description: str
    attachment_filename: Optional[str] = None


class PatientIssueUpdate(BaseModel):
    status: str
    priority: Optional[str] = None
    assigned_department: Optional[str] = None
    resolution_notes: Optional[str] = None


class PatientIssueOut(BaseModel):
    id: int
    issue_id: str
    patient_id: Optional[str] = None
    category: str
    description: str
    attachment_filename: Optional[str] = None
    status: str
    priority: str
    assigned_department: Optional[str] = None
    routing_reason: Optional[str] = None
    resolution_notes: Optional[str] = None
    submitted_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Uploaded File Schemas
class UploadedFileOut(BaseModel):
    id: int
    original_filename: str
    stored_filename: str
    file_type: str
    file_size: int
    source_department: Optional[str] = None
    upload_status: str
    extraction_status: str
    validation_status: str
    extracted_text: Optional[str] = None
    patient_id_matched: Optional[str] = None
    record_count: int
    error_message: Optional[str] = None
    uploaded_at: datetime

    class Config:
        from_attributes = True


# Audit Log Schemas
class AuditLogOut(BaseModel):
    id: int
    event_id: str
    user_id: Optional[int] = None
    user_role: Optional[str] = None
    action: str
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    status: str
    details_json: Optional[str] = None
    ip_address: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True


# Agent Execution Schemas
class AgentExecutionOut(BaseModel):
    id: int
    agent_name: str
    task: str
    patient_id: Optional[str] = None
    tools_invoked_json: Optional[str] = None
    execution_status: str
    result_summary: Optional[str] = None
    error_message: Optional[str] = None
    latency_ms: int
    timestamp: datetime

    class Config:
        from_attributes = True


# Dashboard Statistics Schema (Computed from Database)
class DashboardStatsOut(BaseModel):
    total_users: int
    total_patients: int
    total_doctors: int
    total_paramedics: Optional[int] = 0
    emergency_documents_issued: Optional[int] = 0
    unique_doctors_used: int
    doctor_login_sessions: int
    patient_record_accesses: int
    documents_generated: int
    documents_pending_review: int
    documents_approved: int
    documents_rejected: int
    doctor_edits: int
    open_alerts: int
    open_issues: Optional[int] = 0
    failed_logins: int
    unauthorized_attempts: int
    data_ingestion_files: int
    records_by_department: Dict[str, int]
    alerts_by_priority: Dict[str, int]

