import os
import json
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.main import app
from backend.database.session import Base, get_db
from backend.models.models import User, Patient, Document, DepartmentAlert, CorrectionRequest, PatientIssue
from backend.security.auth import hash_password, create_access_token

client = TestClient(app)


def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["system"] == "HOSPIQ"


def test_demo_users_available():
    response = client.get("/api/auth/demo-users")
    assert response.status_code == 200
    roles = [u["role"] for u in response.json()]
    assert "Doctor" in roles
    assert "Nurse" in roles
    assert "Pharmacist" in roles
    assert "Radiologist" in roles
    assert "Hospital Administrator" in roles
    assert "Patient" in roles


def test_doctor_login_success():
    login_payload = {
        "username": "doctor.smith",
        "password": "DoctorPass123!"
    }
    resp = client.post("/api/auth/login", json=login_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["role"] == "Doctor"


def test_invalid_login_failure():
    bad_payload = {
        "username": "doctor.smith",
        "password": "WrongPassword!"
    }
    resp = client.post("/api/auth/login", json=bad_payload)
    assert resp.status_code == 401


def test_patient_search_and_provenance():
    # Login as doctor
    token_resp = client.post("/api/auth/login", json={"username": "doctor.smith", "password": "DoctorPass123!"})
    token = token_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Search for P001
    search_resp = client.get("/api/patients?query=P001", headers=headers)
    assert search_resp.status_code == 200
    patients = search_resp.json()
    assert len(patients) >= 1
    assert patients[0]["id"] == "P001"

    # Get unified record
    unified_resp = client.get("/api/patients/P001/unified", headers=headers)
    assert unified_resp.status_code == 200
    unified = unified_resp.json()
    assert unified["patient_id"] == "P001"
    assert unified["completeness_score"] > 50

    # Get department records bundle with provenance
    records_resp = client.get("/api/records/patient/P001", headers=headers)
    assert records_resp.status_code == 200
    bundle = records_resp.json()
    assert "provenance" in bundle
    assert "laboratory_records" in bundle
    assert "pharmacy_records" in bundle


def test_document_generation_validation_and_doctor_approval():
    # Login as doctor
    token_resp = client.post("/api/auth/login", json={"username": "doctor.smith", "password": "DoctorPass123!"})
    token = token_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Generate document
    gen_payload = {
        "patient_id": "P001",
        "doc_type": "Clinical Summary",
        "natural_language_request": "Generate a comprehensive clinical summary of current medical records."
    }
    doc_resp = client.post("/api/documents/generate", json=gen_payload, headers=headers)
    assert doc_resp.status_code == 200
    doc = doc_resp.json()
    doc_id = doc["id"]
    # Must be Pending Doctor Review
    assert doc["validation_status"] in ("Pending Doctor Review", "Revised")

    # 2. Check validation results
    val_resp = client.get(f"/api/validation/document/{doc_id}", headers=headers)
    assert val_resp.status_code == 200
    vals = val_resp.json()
    assert len(vals) >= 1
    first_val = vals[0]
    assert first_val["total_checks"] == 7
    assert first_val["status"] in ("Passed", "Warning")

    # 3. Doctor reviews & approves
    review_payload = {
        "action": "APPROVE",
        "doctor_notes": "Reviewed and clinically attested. Good concordance."
    }
    appr_resp = client.post(f"/api/documents/{doc_id}/review", json=review_payload, headers=headers)
    assert appr_resp.status_code == 200
    approved_doc = appr_resp.json()
    assert approved_doc["validation_status"] == "Approved"
    assert approved_doc["doctor_notes"] == "Reviewed and clinically attested. Good concordance."


def test_nurse_cannot_approve_clinical_document():
    # Login as nurse
    nurse_resp = client.post("/api/auth/login", json={"username": "nurse.clara", "password": "NursePass123!"})
    nurse_token = nurse_resp.json()["access_token"]
    nurse_headers = {"Authorization": f"Bearer {nurse_token}"}

    # Attempt to approve a document (should be forbidden: 403)
    review_payload = {
        "action": "APPROVE",
        "doctor_notes": "Nurse attempting approval."
    }
    forbidden_resp = client.post("/api/documents/1/review", json=review_payload, headers=nurse_headers)
    assert forbidden_resp.status_code == 403


def test_patient_portal_isolation():
    # Login as patient (patient.john linked to P001)
    pat_resp = client.post("/api/auth/login", json={"username": "patient.john", "password": "PatientPass123!"})
    pat_token = pat_resp.json()["access_token"]
    pat_headers = {"Authorization": f"Bearer {pat_token}"}

    # Patient accessing own record P001 -> Success
    own_resp = client.get("/api/patients/P001", headers=pat_headers)
    assert own_resp.status_code == 200

    # Patient attempting to access P002 -> Forbidden (403)
    other_resp = client.get("/api/patients/P002", headers=pat_headers)
    assert other_resp.status_code == 403


def test_patient_issue_reporting_and_agent_routing():
    # Patient submits an issue
    pat_resp = client.post("/api/auth/login", json={"username": "patient.john", "password": "PatientPass123!"})
    pat_token = pat_resp.json()["access_token"]
    pat_headers = {"Authorization": f"Bearer {pat_token}"}

    issue_payload = {
        "category": "Laboratory Report",
        "description": "My recent fasting blood glucose test result is missing its reference range interpretation."
    }
    issue_resp = client.post("/api/issues", json=issue_payload, headers=pat_headers)
    assert issue_resp.status_code == 200
    issue_data = issue_resp.json()
    assert issue_data["status"] == "Assigned"
    assert issue_data["assigned_department"] == "Laboratory"
    assert issue_data["issue_id"].startswith("ISS-")


def test_duplicate_detection_skill():
    # Login as doctor
    token_resp = client.post("/api/auth/login", json={"username": "doctor.smith", "password": "DoctorPass123!"})
    token = token_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    dupe_resp = client.get("/api/agents/duplicate-detection", headers=headers)
    assert dupe_resp.status_code == 200
    dupe_data = dupe_resp.json()
    assert dupe_data["detected_duplicates_count"] >= 1


def test_dashboard_metrics_real_database_calculation():
    token_resp = client.post("/api/auth/login", json={"username": "admin.hospiq", "password": "AdminPass123!"})
    token = token_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    dash_resp = client.get("/api/dashboard/metrics", headers=headers)
    assert dash_resp.status_code == 200
    metrics = dash_resp.json()
    assert metrics["total_patients"] >= 15
    assert metrics["total_users"] >= 6
    assert metrics["total_doctors"] >= 1
    assert "records_by_department" in metrics
    assert metrics["records_by_department"]["Laboratory"] > 0

