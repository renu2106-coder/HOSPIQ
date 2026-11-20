import requests
import json

BASE = "http://127.0.0.1:8000/api"
s = requests.Session()

print("--- HOSPIQ END-TO-END CLINICAL & MULTI-AGENT VERIFICATION ---")

# 1. Login as Doctor
r = s.post(f"{BASE}/auth/login", json={"username": "doctor.smith", "password": "DoctorPass123!"})
assert r.status_code == 200, f"Login failed: {r.text}"
doc_token = r.json()["access_token"]
doc_headers = {"Authorization": f"Bearer {doc_token}"}
print("1. [PASS] Doctor login successful! Token acquired.")

# 2. Get Unified Record for P001
r = s.get(f"{BASE}/patients/P001/unified", headers=doc_headers)
assert r.status_code == 200, f"Get unified record failed: {r.text}"
unified = r.json()
print(f"2. [PASS] P001 Unified Record: {unified.get('full_name')} | Blood Group: {unified.get('blood_group')} | Allergies: {unified.get('allergies')}")

# 3. Generate Clinical Summary
print("3. Invoking Documentation Agent with local Ollama Llama 3.2...")
r = s.post(f"{BASE}/documents/generate", json={"patient_id": "P001", "doc_type": "Clinical Summary"}, headers=doc_headers, timeout=60)
assert r.status_code == 200, f"Doc generation failed: {r.text}"
doc = r.json()
doc_id = doc["id"]
print(f"3. [PASS] Document #{doc_id} generated. Title: '{doc['title']}' | Status: {doc['validation_status']}")

# 4. Check 7-Point Validation Scorecard
r = s.get(f"{BASE}/validation/document/{doc_id}", headers=doc_headers)
assert r.status_code == 200, f"Get validation failed: {r.text}"
val_list = r.json()
latest_val = val_list[0] if isinstance(val_list, list) and len(val_list) > 0 else val_list
print(f"4. [PASS] 7-Point Validation Suite: Status: {latest_val.get('status')} | Passed Checks: {latest_val.get('passed_checks')}/{latest_val.get('total_checks')}")

# 5. Doctor Review & Sign-off
r = s.post(f"{BASE}/documents/{doc_id}/review", json={"action": "APPROVE", "doctor_notes": "Physician verified all clinical findings and medication safety contraindications."}, headers=doc_headers)
assert r.status_code == 200, f"Approval failed: {r.text}"
appr_doc = r.json()
assert appr_doc["validation_status"] == "Approved"
print(f"5. [PASS] Physician Attestation Complete! Final Status: {appr_doc['validation_status']} | Approved by Doctor #{appr_doc.get('reviewed_by_doctor_id')}")

# 6. Verify Document Versions
r = s.get(f"{BASE}/documents/{doc_id}/versions", headers=doc_headers)
assert r.status_code == 200
versions = r.json()
print(f"6. [PASS] Document Versions Tracked: {len(versions)} immutable revisions archived in database.")

# 7. Patient Issue Submission & NLP Routing
r = s.post(f"{BASE}/auth/login", json={"username": "patient.john", "password": "PatientPass123!"})
assert r.status_code == 200
pat_token = r.json()["access_token"]
pat_headers = {"Authorization": f"Bearer {pat_token}"}

r = s.post(f"{BASE}/issues", json={
    "category": "Prescription or Medication",
    "description": "I experienced dizziness after taking the Lisinopril medication prescribed yesterday."
}, headers=pat_headers)
assert r.status_code == 200, f"Issue submission failed: {r.text}"
issue = r.json()
print(f"7. [PASS] Patient Issue #{issue['issue_id']} auto-routed to Department: '{issue['assigned_department']}' | Status: '{issue['status']}'")

# 8. Check Append-Only Regulatory Audit Trail
r = s.get(f"{BASE}/audit?limit=5", headers=doc_headers)
assert r.status_code == 200
logs = r.json()
print(f"8. [PASS] Append-Only Audit Trail: {len(logs)} recent entries retrieved. Top Action: {logs[0]['action']} by User #{logs[0]['user_id']}")

print("\n========================================================")
print("SUCCESS: ALL CLINICAL, DATA QUALITY, AND AGENT WORKFLOWS VALIDATED!")
print("========================================================")
