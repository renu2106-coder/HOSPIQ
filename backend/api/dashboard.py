from typing import Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct

from backend.database.session import get_db
from backend.models.models import (
    User, Patient, Document, DepartmentAlert,
    AuditLog, UploadedFile, RegistrationRecord, LaboratoryRecord,
    PharmacyRecord, RadiologyRecord, NursingRecord, AppointmentRecord,
    InpatientRecord, BillingRecord
)
from backend.schemas.schemas import DashboardStatsOut
from backend.security.auth import get_current_user

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard Statistics"])


@router.get("/metrics", response_model=DashboardStatsOut)
def get_live_dashboard_metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Calculates live operational and clinical metrics directly from the database (no hardcoding)."""
    # User counts
    total_users = db.query(User).count()
    total_patients = db.query(Patient).count()
    total_doctors = db.query(User).filter(User.role == "Doctor").count()
    total_paramedics = db.query(User).filter(User.role == "Paramedic").count()

    # Unique doctors who logged in or acted in the system
    unique_doctors_used = db.query(func.count(distinct(AuditLog.user_id))).filter(
        AuditLog.user_role == "Doctor",
        AuditLog.action.in_(["LOGIN_SUCCESS", "DOCUMENT_GENERATED", "DOCUMENT_EDITED", "DOCUMENT_APPROVED"])
    ).scalar() or 0

    # Doctor login sessions
    doctor_login_sessions = db.query(AuditLog).filter(
        AuditLog.user_role == "Doctor",
        AuditLog.action == "LOGIN_SUCCESS"
    ).count()

    # Patient record accesses
    patient_record_accesses = db.query(AuditLog).filter(
        AuditLog.action.in_(["PATIENT_VIEW", "PATIENT_SEARCH"])
    ).count()

    # Document metrics
    documents_generated = db.query(Document).count()
    documents_pending_review = db.query(Document).filter(
        Document.validation_status.in_(["Pending Doctor Review", "Revised", "Generating"])
    ).count()
    documents_approved = db.query(Document).filter(Document.validation_status == "Approved").count()
    documents_rejected = db.query(Document).filter(Document.validation_status == "Rejected").count()
    emergency_documents_issued = db.query(AuditLog).filter(
        AuditLog.action == "EMERGENCY_DOCUMENT_ISSUED"
    ).count()

    # Doctor edits
    doctor_edits = db.query(AuditLog).filter(AuditLog.action == "DOCUMENT_EDITED").count()

    # Department Alerts
    open_alerts = db.query(DepartmentAlert).filter(
        DepartmentAlert.status.in_(["Open", "Under Investigation", "Resolution Pending"])
    ).count()
    open_issues = 0

    # Security metrics
    failed_logins = db.query(AuditLog).filter(AuditLog.action == "LOGIN_FAILED").count()
    unauthorized_attempts = db.query(AuditLog).filter(
        AuditLog.action.in_(["UNAUTHORIZED_ACCESS_ATTEMPT", "UNAUTHORIZED_PATIENT_ACCESS_ATTEMPT"])
    ).count()

    # Ingestion activity
    data_ingestion_files = db.query(UploadedFile).count()

    # Records by department
    records_by_department = {
        "Registration": db.query(RegistrationRecord).count(),
        "Laboratory": db.query(LaboratoryRecord).count(),
        "Pharmacy": db.query(PharmacyRecord).count(),
        "Radiology": db.query(RadiologyRecord).count(),
        "Nursing": db.query(NursingRecord).count(),
        "Inpatient": db.query(InpatientRecord).count(),
        "Appointments": db.query(AppointmentRecord).count(),
        "Billing": db.query(BillingRecord).count()
    }

    # Alerts by priority
    alerts_by_priority = {
        "Critical": db.query(DepartmentAlert).filter(DepartmentAlert.priority == "Critical", DepartmentAlert.status != "Resolved").count(),
        "High": db.query(DepartmentAlert).filter(DepartmentAlert.priority == "High", DepartmentAlert.status != "Resolved").count(),
        "Medium": db.query(DepartmentAlert).filter(DepartmentAlert.priority == "Medium", DepartmentAlert.status != "Resolved").count(),
        "Low": db.query(DepartmentAlert).filter(DepartmentAlert.priority == "Low", DepartmentAlert.status != "Resolved").count()
    }

    return {
        "total_users": total_users,
        "total_patients": total_patients,
        "total_doctors": total_doctors,
        "total_paramedics": total_paramedics,
        "emergency_documents_issued": emergency_documents_issued,
        "unique_doctors_used": unique_doctors_used,
        "doctor_login_sessions": doctor_login_sessions,
        "patient_record_accesses": patient_record_accesses,
        "documents_generated": documents_generated,
        "documents_pending_review": documents_pending_review,
        "documents_approved": documents_approved,
        "documents_rejected": documents_rejected,
        "doctor_edits": doctor_edits,
        "open_alerts": open_alerts,
        "open_issues": open_issues,
        "failed_logins": failed_logins,
        "unauthorized_attempts": unauthorized_attempts,
        "data_ingestion_files": data_ingestion_files,
        "records_by_department": records_by_department,
        "alerts_by_priority": alerts_by_priority
    }

