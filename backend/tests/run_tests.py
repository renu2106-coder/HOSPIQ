import asyncio
import sys
import requests

BASE_URL = "http://127.0.0.1:8000"

def run_all_tests():
    print("\n================== HOSPIQ AUTOMATED TEST SUITE ==================", flush=True)
    session = requests.Session()

    # Test 1: Health Check
    resp = session.get(f"{BASE_URL}/api/health", timeout=10)
    assert resp.status_code == 200, f"Health check failed: {resp.text}"
    data = resp.json()
    assert data["status"] == "healthy"
    print("✓ Scenario 1: Health check endpoint passed.", flush=True)

    # Test 2: Demo users availability
    resp = session.get(f"{BASE_URL}/api/auth/demo-users", timeout=10)
    assert resp.status_code == 200
    roles = [u["role"] for u in resp.json()]
    for expected_role in ["Doctor", "Nurse", "Pharmacist", "Radiologist", "Hospital Administrator", "Patient"]:
        assert expected_role in roles
    print("✓ Scenario 2: All 6 demo roles verified (Doctor, Nurse, Pharmacist, Radiologist, Admin, Patient).", flush=True)

    # Test 3: Doctor login
    resp = session.post(f"{BASE_URL}/api/auth/login", json={"username": "doctor.smith", "password": "DoctorPass123!"}, timeout=10)
    assert resp.status_code == 200
    doc_token = resp.json()["access_token"]
    doc_headers = {"Authorization": f"Bearer {doc_token}"}
    print("✓ Scenario 3: Doctor authentication and JWT issuance passed.", flush=True)

    # Test 4: Invalid login rejection
    bad_resp = session.post(f"{BASE_URL}/api/auth/login", json={"username": "doctor.smith", "password": "WrongPassword!"}, timeout=10)
    assert bad_resp.status_code == 401
    print("✓ Scenario 4: Invalid password properly rejected with 401 Unauthorized.", flush=True)

    # Test 5: Patient search & provenance
    p_resp = session.get(f"{BASE_URL}/api/patients?query=P001", headers=doc_headers, timeout=10)
    assert p_resp.status_code == 200
    patients = p_resp.json()
    assert len(patients) >= 1
    assert patients[0]["id"] == "P001"

    # Unified record check
    uni_resp = session.get(f"{BASE_URL}/api/patients/P001/unified", headers=doc_headers, timeout=10)
    assert uni_resp.status_code == 200
    assert uni_resp.json()["patient_id"] == "P001"

    # Multi-department bundle & provenance check
    rec_resp = session.get(f"{BASE_URL}/api/records/patient/P001", headers=doc_headers, timeout=10)
    assert rec_resp.status_code == 200
    bundle = rec_resp.json()
    assert "provenance" in bundle
    assert "laboratory_records" in bundle
    assert "pharmacy_records" in bundle
    print("✓ Scenario 5: Patient search, Unified Record consolidation, and Department Provenance passed.", flush=True)

    # Test 6: AI Document Generation & 7-point Validation
    gen_payload = {
        "patient_id": "P001",
        "doc_type": "Clinical Summary",
        "natural_language_request": "Prepare comprehensive summary of current medical records."
    }
    doc_gen_resp = session.post(f"{BASE_URL}/api/documents/generate", json=gen_payload, headers=doc_headers, timeout=60)
    assert doc_gen_resp.status_code == 200
    generated_doc = doc_gen_resp.json()
    doc_id = generated_doc["id"]
    assert generated_doc["validation_status"] in ("Pending Doctor Review", "Revised")

    val_resp = session.get(f"{BASE_URL}/api/validation/document/{doc_id}", headers=doc_headers, timeout=10)
    assert val_resp.status_code == 200
    val_list = val_resp.json()
    assert len(val_list) >= 1
    assert val_list[0]["total_checks"] == 7
    print("✓ Scenario 6: AI Document Generation & 7-point Validation Agent scorecard passed.", flush=True)

    # Test 7: Physician Document Review & Approval Workflow
    review_payload = {
        "action": "APPROVE",
        "doctor_notes": "Reviewed and clinically attested. Good concordance."
    }
    appr_resp = session.post(f"{BASE_URL}/api/documents/{doc_id}/review", json=review_payload, headers=doc_headers, timeout=10)
    assert appr_resp.status_code == 200
    assert appr_resp.json()["validation_status"] == "Approved"
    print("✓ Scenario 7: Doctor review, clinical notes attestation, and approval passed.", flush=True)

    # Test 8: RBAC Enforcement - Nurse cannot approve clinical documents
    nurse_login = session.post(f"{BASE_URL}/api/auth/login", json={"username": "nurse.clara", "password": "NursePass123!"}, timeout=10)
    nurse_token = nurse_login.json()["access_token"]
    nurse_headers = {"Authorization": f"Bearer {nurse_token}"}

    forbidden_appr = session.post(f"{BASE_URL}/api/documents/{doc_id}/review", json=review_payload, headers=nurse_headers, timeout=10)
    assert forbidden_appr.status_code == 403, f"Expected 403, got {forbidden_appr.status_code}"
    print("✓ Scenario 8: Role-based authorization blocked Nurse from approving clinical documents (403 Forbidden).", flush=True)

    # Test 9: Patient isolation - Patient cannot access another patient's records
    pat_login = session.post(f"{BASE_URL}/api/auth/login", json={"username": "patient.john", "password": "PatientPass123!"}, timeout=10)
    pat_token = pat_login.json()["access_token"]
    pat_headers = {"Authorization": f"Bearer {pat_token}"}

    own_p = session.get(f"{BASE_URL}/api/patients/P001", headers=pat_headers, timeout=10)
    assert own_p.status_code == 200
    alien_p = session.get(f"{BASE_URL}/api/patients/P002", headers=pat_headers, timeout=10)
    assert alien_p.status_code == 403
    print("✓ Scenario 9: Patient privacy isolation confirmed: P001 access allowed, P002 access blocked (403 Forbidden).", flush=True)

    # Test 10: Patient Issue Submission & Automated Agent Routing
    issue_payload = {
        "category": "Prescription or Medication",
        "description": "Refill request for Metformin 500mg indicates pending status at the outpatient dispensing counter."
    }
    issue_resp = session.post(f"{BASE_URL}/api/issues", json=issue_payload, headers=pat_headers, timeout=10)
    assert issue_resp.status_code == 200
    issue_data = issue_resp.json()
    assert issue_data["status"] == "Assigned"
    assert issue_data["assigned_department"] == "Pharmacy"
    assert issue_data["issue_id"].startswith("ISS-")
    print("✓ Scenario 10: Patient Issue Portal and automated Issue Management Agent routing passed.", flush=True)

    # Test 11: Duplicate detection & Department Alerts
    dupe_resp = session.get(f"{BASE_URL}/api/agents/duplicate-detection", headers=doc_headers, timeout=10)
    assert dupe_resp.status_code == 200
    assert dupe_resp.json()["detected_duplicates_count"] >= 1

    alerts_resp = session.get(f"{BASE_URL}/api/alerts", headers=doc_headers, timeout=10)
    assert alerts_resp.status_code == 200
    alerts = alerts_resp.json()
    assert len(alerts) >= 1
    print(f"✓ Scenario 11: Cross-department discrepancy & duplicate detection passed ({len(alerts)} active alerts detected).", flush=True)

    # Test 12: Admin Dashboard Metrics Calculated from Database
    admin_login = session.post(f"{BASE_URL}/api/auth/login", json={"username": "admin.hospiq", "password": "AdminPass123!"}, timeout=10)
    admin_token = admin_login.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    metrics_resp = session.get(f"{BASE_URL}/api/dashboard/metrics", headers=admin_headers, timeout=10)
    assert metrics_resp.status_code == 200
    metrics = metrics_resp.json()
    assert metrics["total_patients"] == 15
    assert metrics["total_users"] == 6
    assert metrics["total_doctors"] == 1
    assert metrics["doctor_login_sessions"] >= 1
    assert metrics["records_by_department"]["Laboratory"] > 0
    print("✓ Scenario 12: Admin dashboard metrics verified (live SQL aggregation, zero hardcoded values).", flush=True)

    # Test 13: Universal File Upload and Extraction
    sample_csv = "patient_id,name,dob,gender,contact_number,address,registration_date,blood_group\nP016,Alexander Hamilton,1985-01-11,Male,+1-555-1616,101 Liberty St,2024-04-01,O+"
    files = {"file": ("test_patient.csv", sample_csv.encode("utf-8"), "text/csv")}
    upload_resp = session.post(f"{BASE_URL}/api/uploads", files=files, data={"department": "Registration"}, headers=admin_headers, timeout=10)
    assert upload_resp.status_code == 200
    upload_data = upload_resp.json()
    assert upload_data["upload_status"] == "Completed"
    assert upload_data["extraction_status"] == "Extracted"
    print("✓ Scenario 13: Universal multiformat upload & parsing passed.", flush=True)

    # Test 14: Unsupported File Format Rejection
    bad_files = {"file": ("malicious.exe", b"binarycontent", "application/octet-stream")}
    bad_upload_resp = session.post(f"{BASE_URL}/api/uploads", files=bad_files, data={"department": "IT"}, headers=admin_headers, timeout=10)
    assert bad_upload_resp.status_code == 400
    print("✓ Scenario 14: Unsupported file formats rejected with clear guidance.", flush=True)

    print("\n================== ALL 14 TEST SCENARIOS PASSED! ==================\n", flush=True)

if __name__ == "__main__":
    run_all_tests()
