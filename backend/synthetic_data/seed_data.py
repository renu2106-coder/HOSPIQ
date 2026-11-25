import os
import json
from pathlib import Path
from datetime import datetime
import pandas as pd
from sqlalchemy.orm import Session

from backend.database.session import SessionLocal, Base, engine
from backend.models.models import (
    User, Patient, RegistrationRecord, LaboratoryRecord, PharmacyRecord,
    RadiologyRecord, NursingRecord, AppointmentRecord, InpatientRecord,
    BillingRecord, UnifiedPatientRecord, DepartmentAlert, PatientIssue,
    AuditLog, AgentExecution
)
from backend.security.auth import hash_password
from backend.agents.patient_data_agent import PatientDataManagementAgent

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"

PATIENT_SEEDS = [
    {
        "id": "P001", "first_name": "Ravi", "last_name": "Kumar", "dob": "1998-03-12", "age": 26,
        "gender": "Male", "contact_phone": "+1-555-0101", "email": "ravi.kumar@example.com",
        "address": "42 MG Road, Sector 4", "blood_group": "O+", "emergency_contact": "Priya Kumar (Spouse) +1-555-0102",
        "allergies": "Penicillin (rash)", "chronic_conditions": "Essential Hypertension, Type 2 Diabetes", "registration_date": "2023-01-15"
    },
    {
        "id": "P002", "first_name": "Sarah", "last_name": "Jenkins", "dob": "1992-11-23", "age": 32,
        "gender": "Female", "contact_phone": "+1-555-0202", "email": "s.jenkins@example.com",
        "address": "1204 Elm Street, Riverdale", "blood_group": "A+", "emergency_contact": "Tom Jenkins +1-555-0203",
        "allergies": "None known", "chronic_conditions": "Mild Asthma", "registration_date": "2023-02-10"
    },
    {
        "id": "P003", "first_name": "Michael", "last_name": "Chang", "dob": "1975-08-30", "age": 49,
        "gender": "Male", "contact_phone": "+1-555-0303", "email": "m.chang@example.com",
        "address": "88 Lotus Boulevard, Metro City", "blood_group": "B+", "emergency_contact": "Grace Chang +1-555-0304",
        "allergies": "Sulfa drugs", "chronic_conditions": "Hyperlipidemia, CAD", "registration_date": "2023-03-05"
    },
    {
        "id": "P004", "first_name": "Emily", "last_name": "Rodriguez", "dob": "1988-04-12", "age": 36,
        "gender": "Female", "contact_phone": "+1-555-0404", "email": "e.rodriguez@example.com",
        "address": "45 Ocean View Road, Baytown", "blood_group": "AB+", "emergency_contact": "Carlos Rodriguez +1-555-0405",
        "allergies": "None", "chronic_conditions": "Migraine", "registration_date": "2023-04-18"
    },
    {
        "id": "P005", "first_name": "David", "last_name": "Thompson", "dob": "1965-12-03", "age": 59,
        "gender": "Male", "contact_phone": "+1-555-0505", "email": "d.thompson@example.com",
        "address": "300 Pine Grove, Oak Ridge", "blood_group": "O-", "emergency_contact": "Linda Thompson +1-555-0506",
        "allergies": "Latex, Codeine", "chronic_conditions": "Chronic Kidney Disease Stage 3, Hypertension", "registration_date": "2023-05-22"
    },
    {
        "id": "P006", "first_name": "Amanda", "last_name": "White", "dob": "1995-07-19", "age": 29,
        "gender": "Female", "contact_phone": "+1-555-0606", "email": "a.white@example.com",
        "address": "55 Maple Avenue, Cedar Falls", "blood_group": "A-", "emergency_contact": "Paul White +1-555-0607",
        "allergies": "Peanuts", "chronic_conditions": "None", "registration_date": "2023-06-11"
    },
    {
        "id": "P007", "first_name": "Robert", "last_name": "Lewis", "dob": "1958-03-27", "age": 66,
        "gender": "Male", "contact_phone": "+1-555-0707", "email": "r.lewis@example.com",
        "address": "910 Birch Lane, High Point", "blood_group": "O+", "emergency_contact": "Martha Lewis +1-555-0708",
        "allergies": "Aspirin", "chronic_conditions": "Osteoarthritis, Atrial Fibrillation", "registration_date": "2023-07-04"
    },
    {
        "id": "P008", "first_name": "Lisa", "last_name": "Patel", "dob": "1983-09-15", "age": 41,
        "gender": "Female", "contact_phone": "+1-555-0808", "email": "l.patel@example.com",
        "address": "12 Willow Creek, Brookside", "blood_group": "B-", "emergency_contact": "Sanjay Patel +1-555-0809",
        "allergies": "None", "chronic_conditions": "Hypothyroidism", "registration_date": "2023-08-19"
    },
    {
        "id": "P009", "first_name": "James", "last_name": "Wilson", "dob": "1972-01-08", "age": 52,
        "gender": "Male", "contact_phone": "+1-555-0909", "email": "j.wilson@example.com",
        "address": "77 Sunset Drive, Hillcrest", "blood_group": "AB-", "emergency_contact": "Karen Wilson +1-555-0910",
        "allergies": "Shellfish", "chronic_conditions": "GERD, Sleep Apnea", "registration_date": "2023-09-14"
    },
    {
        "id": "P010", "first_name": "Maria", "last_name": "Garcia", "dob": "1990-10-25", "age": 34,
        "gender": "Female", "contact_phone": "+1-555-1010", "email": "m.garcia@example.com",
        "address": "104 Meadow View, Sunnydale", "blood_group": "O+", "emergency_contact": "Juan Garcia +1-555-1011",
        "allergies": "None", "chronic_conditions": "Iron Deficiency Anemia", "registration_date": "2023-10-02"
    },
    {
        "id": "P011", "first_name": "Brian", "last_name": "O'Connor", "dob": "1984-06-18", "age": 40,
        "gender": "Male", "contact_phone": "+1-555-1111", "email": "b.oconnor@example.com",
        "address": "402 Chestnut Court, Highland", "blood_group": "A+", "emergency_contact": "Claire O'Connor +1-555-1112",
        "allergies": "Ibuprofen", "chronic_conditions": "Mild Psoriasis", "registration_date": "2023-11-12"
    },
    {
        "id": "P012", "first_name": "Jessica", "last_name": "Taylor", "dob": "1999-02-14", "age": 25,
        "gender": "Female", "contact_phone": "+1-555-1212", "email": "j.taylor@example.com",
        "address": "610 University Way, College Park", "blood_group": "B+", "emergency_contact": "Mark Taylor +1-555-1213",
        "allergies": "None", "chronic_conditions": "None", "registration_date": "2023-12-01"
    },
    {
        "id": "P013", "first_name": "Daniel", "last_name": "Martinez", "dob": "1968-11-11", "age": 56,
        "gender": "Male", "contact_phone": "+1-555-1313", "email": "d.martinez@example.com",
        "address": "815 Cedar Ridge, Greenfield", "blood_group": "O+", "emergency_contact": "Elena Martinez +1-555-1314",
        "allergies": "Ciprofloxacin", "chronic_conditions": "Peripheral Neuropathy, Type 2 Diabetes", "registration_date": "2024-01-10"
    },
    {
        "id": "P014", "first_name": "Rachel", "last_name": "Adams", "dob": "1993-05-29", "age": 31,
        "gender": "Female", "contact_phone": "+1-555-1414", "email": "r.adams@example.com",
        "address": "220 Lakeview Drive, Lakeside", "blood_group": "A-", "emergency_contact": "Steven Adams +1-555-1415",
        "allergies": "None", "chronic_conditions": "Generalized Anxiety Disorder", "registration_date": "2024-02-15"
    },
    {
        "id": "P015", "first_name": "Christopher", "last_name": "Hall", "dob": "1978-07-07", "age": 46,
        "gender": "Male", "contact_phone": "+1-555-1515", "email": "c.hall@example.com",
        "address": "33 Heritage Circle, Old Town", "blood_group": "AB+", "emergency_contact": "Sarah Hall +1-555-1516",
        "allergies": "Penicillin", "chronic_conditions": "Gout, Hyperuricemia", "registration_date": "2024-03-20"
    }
]

DEMO_USERS = [
    {
        "username": "doctor.smith",
        "password": "DoctorPass123!",
        "full_name": "Dr. Sarah Smith, MD",
        "email": "dr.smith@hospiq.local",
        "role": "Doctor",
        "department": "Internal Medicine",
        "patient_id": None
    },
    {
        "username": "paramedic.alex",
        "password": "ParamedicPass123!",
        "full_name": "Alex Rivera, EMT-P",
        "email": "alex.rivera@hospiq.local",
        "role": "Paramedic",
        "department": "Emergency Medical Services",
        "patient_id": None
    },
    {
        "username": "nurse.clara",
        "password": "NursePass123!",
        "full_name": "Nurse Clara Barton, RN",
        "email": "clara.barton@hospiq.local",
        "role": "Nurse",
        "department": "Inpatient Ward A",
        "patient_id": None
    },
    {
        "username": "pharm.david",
        "password": "PharmPass123!",
        "full_name": "David Vance, PharmD",
        "email": "david.vance@hospiq.local",
        "role": "Pharmacist",
        "department": "Central Pharmacy",
        "patient_id": None
    },
    {
        "username": "rad.elena",
        "password": "RadPass123!",
        "full_name": "Dr. Elena Rostova, MD",
        "email": "elena.rostova@hospiq.local",
        "role": "Radiologist",
        "department": "Diagnostic Imaging",
        "patient_id": None
    },
    {
        "username": "admin.hospiq",
        "password": "AdminPass123!",
        "full_name": "Executive Administrator",
        "email": "admin@hospiq.local",
        "role": "Hospital Administrator",
        "department": "Health Informatics & Operations",
        "patient_id": None
    },
    {
        "username": "patient.ravi",
        "password": "PatientPass123!",
        "full_name": "Ravi Kumar",
        "email": "ravi.kumar@example.com",
        "role": "Patient",
        "department": None,
        "patient_id": "P001"
    },
    {
        "username": "patient.john",
        "password": "PatientPass123!",
        "full_name": "Johnathan Miller",
        "email": "patient.john@hospiq.local",
        "role": "Patient",
        "department": None,
        "patient_id": "P001"
    }
]


def generate_department_files():
    """Generates synthetic department data files in CSV, JSON, XLSX formats on disk."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Registration CSV (contains deliberate anomalies: duplicate record for P002, mixed date formats, missing fields)
    reg_rows = []
    for p in PATIENT_SEEDS:
        reg_rows.append({
            "patient_id": p["id"],
            "name": f"{p['first_name']} {p['last_name']}",
            "dob": p["dob"],
            "gender": p["gender"],
            "contact_number": p["contact_phone"],
            "address": p["address"],
            "registration_date": p["registration_date"],
            "blood_group": p["blood_group"]
        })
    # Add duplicate record for P002 with alternative date format and slight address update
    reg_rows.append({
        "patient_id": "P002",
        "name": "Sarah Jenkins",
        "dob": "23/11/1992",  # DD/MM/YYYY variant
        "gender": "Female",
        "contact_number": "+1-555-0202",
        "address": "1204 Elm Street, Apt 3B, Riverdale",
        "registration_date": "10/02/2023",
        "blood_group": "A+"
    })
    # Add record with conflicting DOB for P003
    reg_rows.append({
        "patient_id": "P003",
        "name": "Michael Chang",
        "dob": "1975-09-02",  # Conflict with core DOB 1975-08-30
        "gender": "Male",
        "contact_number": "+1-555-0303",
        "address": "88 Lotus Boulevard, Metro City",
        "registration_date": "2023-03-05",
        "blood_group": "B+"
    })

    reg_path = DATA_DIR / "registration" / "patients_registration.csv"
    pd.DataFrame(reg_rows).to_csv(reg_path, index=False)

    # 2. Laboratory JSON (contains normal & abnormal results, and deliberate blood group conflict for P003)
    lab_records = [
        # P001 (Diabetic/Hypertensive)
        {"patient_id": "P001", "test_name": "Fasting Blood Glucose", "test_code": "GLU-F", "result_value": "142", "unit": "mg/dL", "reference_range": "70-99", "is_abnormal": True, "report_date": "2024-03-10", "lab_department": "Clinical Biochemistry", "ordering_physician": "Dr. Sarah Smith"},
        {"patient_id": "P001", "test_name": "Hemoglobin A1c", "test_code": "HBA1C", "result_value": "7.8", "unit": "%", "reference_range": "< 5.7", "is_abnormal": True, "report_date": "2024-03-10", "lab_department": "Clinical Biochemistry", "ordering_physician": "Dr. Sarah Smith"},
        {"patient_id": "P001", "test_name": "Serum Creatinine", "test_code": "CREAT", "result_value": "1.1", "unit": "mg/dL", "reference_range": "0.7-1.3", "is_abnormal": False, "report_date": "2024-03-10", "lab_department": "Clinical Biochemistry", "ordering_physician": "Dr. Sarah Smith"},
        {"patient_id": "P001", "test_name": "Lipid Panel - Total Cholesterol", "test_code": "CHOL", "result_value": "210", "unit": "mg/dL", "reference_range": "< 200", "is_abnormal": True, "report_date": "2024-03-10", "lab_department": "Clinical Biochemistry", "ordering_physician": "Dr. Sarah Smith"},

        # P002 (Asthma)
        {"patient_id": "P002", "test_name": "Complete Blood Count - WBC", "test_code": "WBC", "result_value": "6.8", "unit": "x10^3/uL", "reference_range": "4.5-11.0", "is_abnormal": False, "report_date": "2024-02-14", "lab_department": "Hematology", "ordering_physician": "Dr. John Adams"},
        {"patient_id": "P002", "test_name": "Total IgE", "test_code": "IGE", "result_value": "180", "unit": "IU/mL", "reference_range": "< 100", "is_abnormal": True, "report_date": "2024-02-14", "lab_department": "Immunology", "ordering_physician": "Dr. John Adams"},

        # P003 (CAD / Conflicting Blood Group test)
        {"patient_id": "P003", "test_name": "Blood Group & Rh Typing", "test_code": "BG-RH", "result_value": "O+", "unit": "", "reference_range": "ABO/Rh", "is_abnormal": False, "report_date": "2024-01-20", "lab_department": "Blood Bank", "ordering_physician": "Dr. Robert Vance"},
        {"patient_id": "P003", "test_name": "High-Sensitivity Troponin I", "test_code": "TROP-I", "result_value": "0.02", "unit": "ng/mL", "reference_range": "< 0.04", "is_abnormal": False, "report_date": "2024-01-20", "lab_department": "Cardiac Chemistry", "ordering_physician": "Dr. Robert Vance"},

        # P004 (Missing Reference Range test)
        {"patient_id": "P004", "test_name": "Serum Ferritin", "test_code": "FERR", "result_value": "35", "unit": "ng/mL", "reference_range": "", "is_abnormal": False, "report_date": "2024-04-05", "lab_department": "Clinical Biochemistry", "ordering_physician": "Dr. Sarah Smith"},

        # P005 (CKD Stage 3)
        {"patient_id": "P005", "test_name": "Estimated GFR", "test_code": "EGFR", "result_value": "48", "unit": "mL/min/1.73m2", "reference_range": "> 60", "is_abnormal": True, "report_date": "2024-03-18", "lab_department": "Nephrology Lab", "ordering_physician": "Dr. Alice Wong"},
        {"patient_id": "P005", "test_name": "Serum Potassium", "test_code": "K+", "result_value": "4.9", "unit": "mmol/L", "reference_range": "3.5-5.0", "is_abnormal": False, "report_date": "2024-03-18", "lab_department": "Clinical Biochemistry", "ordering_physician": "Dr. Alice Wong"},

        # P007 (AFib)
        {"patient_id": "P007", "test_name": "Prothrombin Time / INR", "test_code": "INR", "result_value": "2.4", "unit": "", "reference_range": "2.0-3.0", "is_abnormal": False, "report_date": "2024-02-28", "lab_department": "Hematology", "ordering_physician": "Dr. Robert Vance"},

        # P010 (Anemia)
        {"patient_id": "P010", "test_name": "Hemoglobin", "test_code": "HGB", "result_value": "9.4", "unit": "g/dL", "reference_range": "12.0-15.5", "is_abnormal": True, "report_date": "2024-03-01", "lab_department": "Hematology", "ordering_physician": "Dr. Sarah Smith"},

        # P015 (Gout)
        {"patient_id": "P015", "test_name": "Serum Uric Acid", "test_code": "URIC", "result_value": "8.9", "unit": "mg/dL", "reference_range": "3.5-7.2", "is_abnormal": True, "report_date": "2024-03-12", "lab_department": "Clinical Biochemistry", "ordering_physician": "Dr. John Adams"}
    ]
    lab_path = DATA_DIR / "laboratory" / "lab_results.json"
    with open(lab_path, "w", encoding="utf-8") as f:
        json.dump(lab_records, f, indent=2)

    # 3. Pharmacy Excel (.xlsx) (contains active/discontinued meds, conflicting dosage for P005)
    pharm_records = [
        {"patient_id": "P001", "medicine_name": "Metformin Hydrochloride", "strength": "500 mg", "dosage": "1 tablet twice daily with meals", "frequency": "BID", "duration": "90 days", "route": "Oral", "prescription_date": "2024-01-15", "prescribing_doctor": "Dr. Sarah Smith", "status": "Active"},
        {"patient_id": "P001", "medicine_name": "Lisinopril", "strength": "10 mg", "dosage": "1 tablet daily in the morning", "frequency": "OD", "duration": "90 days", "route": "Oral", "prescription_date": "2024-01-15", "prescribing_doctor": "Dr. Sarah Smith", "status": "Active"},
        {"patient_id": "P001", "medicine_name": "Atorvastatin Calcium", "strength": "20 mg", "dosage": "1 tablet at bedtime", "frequency": "QHS", "duration": "90 days", "route": "Oral", "prescription_date": "2024-01-15", "prescribing_doctor": "Dr. Sarah Smith", "status": "Active"},

        {"patient_id": "P002", "medicine_name": "Albuterol Inhaler", "strength": "90 mcg", "dosage": "2 puffs every 4-6 hours PRN wheezing", "frequency": "PRN", "duration": "30 days", "route": "Inhalation", "prescription_date": "2024-02-14", "prescribing_doctor": "Dr. John Adams", "status": "Active"},
        {"patient_id": "P002", "medicine_name": "Fluticasone Propionate Inhaler", "strength": "110 mcg", "dosage": "1 puff twice daily", "frequency": "BID", "duration": "60 days", "route": "Inhalation", "prescription_date": "2024-02-14", "prescribing_doctor": "Dr. John Adams", "status": "Active"},

        {"patient_id": "P003", "medicine_name": "Amlodipine Besylate", "strength": "5 mg", "dosage": "1 tablet daily", "frequency": "OD", "duration": "90 days", "route": "Oral", "prescription_date": "2024-01-20", "prescribing_doctor": "Dr. Robert Vance", "status": "Active"},
        {"patient_id": "P003", "medicine_name": "Rosuvastatin", "strength": "10 mg", "dosage": "1 tablet daily", "frequency": "OD", "duration": "90 days", "route": "Oral", "prescription_date": "2024-01-20", "prescribing_doctor": "Dr. Robert Vance", "status": "Active"},

        # P005 (Conflicting dosages of Losartan entered)
        {"patient_id": "P005", "medicine_name": "Losartan Potassium", "strength": "50 mg", "dosage": "1 tablet daily", "frequency": "OD", "duration": "60 days", "route": "Oral", "prescription_date": "2024-03-01", "prescribing_doctor": "Dr. Alice Wong", "status": "Active"},
        {"patient_id": "P005", "medicine_name": "Losartan Potassium", "strength": "100 mg", "dosage": "1 tablet twice daily", "frequency": "BID", "duration": "30 days", "route": "Oral", "prescription_date": "2024-03-10", "prescribing_doctor": "Dr. Emergency Cover", "status": "Active"},

        {"patient_id": "P007", "medicine_name": "Warfarin Sodium", "strength": "5 mg", "dosage": "1 tablet in evening per INR titration", "frequency": "OD", "duration": "30 days", "route": "Oral", "prescription_date": "2024-02-28", "prescribing_doctor": "Dr. Robert Vance", "status": "Active"},
        {"patient_id": "P008", "medicine_name": "Levothyroxine Sodium", "strength": "75 mcg", "dosage": "1 tablet daily on empty stomach", "frequency": "OD", "duration": "90 days", "route": "Oral", "prescription_date": "2024-01-10", "prescribing_doctor": "Dr. Sarah Smith", "status": "Active"},
        {"patient_id": "P010", "medicine_name": "Ferrous Sulfate", "strength": "325 mg", "dosage": "1 tablet daily with vitamin C", "frequency": "OD", "duration": "60 days", "route": "Oral", "prescription_date": "2024-03-01", "prescribing_doctor": "Dr. Sarah Smith", "status": "Active"},
        {"patient_id": "P015", "medicine_name": "Allopurinol", "strength": "100 mg", "dosage": "1 tablet daily after food", "frequency": "OD", "duration": "60 days", "route": "Oral", "prescription_date": "2024-03-15", "prescribing_doctor": "Dr. John Adams", "status": "Active"}
    ]
    pharm_path = DATA_DIR / "pharmacy" / "prescriptions.xlsx"
    pd.DataFrame(pharm_records).to_excel(pharm_path, index=False)

    # 4. Radiology JSON
    rad_records = [
        {"patient_id": "P001", "imaging_type": "Chest X-Ray (PA View)", "body_part": "Chest", "report_findings": "Cardiothoracic ratio normal at 48%. Normal vascularity. Clear lung fields bilaterally without focal consolidation, pneumothorax, or pleural effusion. Osseous thoracic cage intact.", "impression": "No acute cardiopulmonary disease.", "report_date": "2024-01-16", "radiologist_name": "Dr. Elena Rostova"},
        {"patient_id": "P002", "imaging_type": "Chest X-Ray (PA View)", "body_part": "Chest", "report_findings": "Mild bronchial wall thickening consistent with reactive airway disease / mild asthma. No parenchymal infiltrates or pulmonary edema.", "impression": "Reactive airway changes without consolidation.", "report_date": "2024-02-14", "radiologist_name": "Dr. Elena Rostova"},
        {"patient_id": "P003", "imaging_type": "Echocardiogram (Transthoracic)", "body_part": "Heart", "report_findings": "Left ventricular ejection fraction preserved at 58%. Mild concentric left ventricular hypertrophy. Grade 1 diastolic dysfunction.", "impression": "Hypertensive heart remodeling with preserved systolic function.", "report_date": "2024-01-22", "radiologist_name": "Dr. Elena Rostova"},
        {"patient_id": "P005", "imaging_type": "Renal Ultrasound", "body_part": "Kidneys", "report_findings": "Right kidney measures 9.8 cm, left measures 10.1 cm. Increased bilateral cortical echogenicity consistent with medical renal disease. No hydronephrosis or renal calculi.", "impression": "Bilateral renal parenchymal disease consistent with clinical CKD.", "report_date": "2024-03-19", "radiologist_name": "Dr. Elena Rostova"},
        {"patient_id": "P007", "imaging_type": "X-Ray Right Knee", "body_part": "Right Knee", "report_findings": "Moderate joint space narrowing of the medial compartment. Marginal osteophyte formation along the tibial plateau. No acute fracture or dislocation.", "impression": "Moderate tricompartmental osteoarthritis, predominant medially.", "report_date": "2024-02-28", "radiologist_name": "Dr. Elena Rostova"}
    ]
    rad_path = DATA_DIR / "radiology" / "radiology_reports.json"
    with open(rad_path, "w", encoding="utf-8") as f:
        json.dump(rad_records, f, indent=2)

    # 5. Nursing Vitals CSV
    nursing_rows = [
        {"patient_id": "P001", "vital_bp": "138/84 mmHg", "vital_pulse": 76, "vital_temp": 98.4, "vital_resp_rate": 16, "vital_spo2": 98, "nurse_notes": "Patient calm, compliant with oral antidiabetic therapy. Mild headache reported.", "recorded_at": "2024-03-10 09:30", "nurse_name": "Clara Barton, RN"},
        {"patient_id": "P002", "vital_bp": "118/74 mmHg", "vital_pulse": 82, "vital_temp": 98.6, "vital_resp_rate": 18, "vital_spo2": 99, "nurse_notes": "Mild expiratory wheeze heard on forced exhalation. Inhaler technique reviewed.", "recorded_at": "2024-02-14 11:15", "nurse_name": "Clara Barton, RN"},
        {"patient_id": "P003", "vital_bp": "144/88 mmHg", "vital_pulse": 70, "vital_temp": 98.1, "vital_resp_rate": 15, "vital_spo2": 97, "nurse_notes": "BP slightly elevated above baseline. Advised low sodium intake.", "recorded_at": "2024-01-20 14:00", "nurse_name": "Clara Barton, RN"},
        {"patient_id": "P004", "vital_bp": "120/78 mmHg", "vital_pulse": 74, "vital_temp": 98.2, "vital_resp_rate": 16, "vital_spo2": 99, "nurse_notes": "Routine vitals normal. No complaints of dizziness.", "recorded_at": "2024-04-05 10:20", "nurse_name": "Sarah Connor, RN"},
        {"patient_id": "P005", "vital_bp": "152/92 mmHg", "vital_pulse": 68, "vital_temp": 98.0, "vital_resp_rate": 17, "vital_spo2": 96, "nurse_notes": "Mild pedal edema noted (1+ pitting). Physician informed.", "recorded_at": "2024-03-18 08:45", "nurse_name": "Clara Barton, RN"}
    ]
    nurs_path = DATA_DIR / "nursing" / "nursing_vitals.csv"
    pd.DataFrame(nursing_rows).to_csv(nurs_path, index=False)

    # 6. Inpatient Admissions JSON
    inpatient_records = [
        {"patient_id": "P001", "admission_date": "2024-01-14", "discharge_date": "2024-01-17", "ward": "Medical Ward 3", "bed_number": "304-B", "admission_diagnosis": "Uncontrolled Type 2 Diabetes with symptomatic hyperglycemia", "discharge_diagnosis": "Type 2 Diabetes mellitus, stabilized on Metformin; Essential Hypertension", "attending_physician": "Dr. Sarah Smith", "discharge_status": "Recovered / Discharged Home"},
        {"patient_id": "P005", "admission_date": "2024-03-17", "discharge_date": "2024-03-21", "ward": "Renal Ward 2", "bed_number": "212-A", "admission_diagnosis": "Hypertensive urgency with Stage 3 Chronic Kidney Disease exacerbation", "discharge_diagnosis": "Hypertensive nephropathy, stabilized volume status", "attending_physician": "Dr. Alice Wong", "discharge_status": "Transferred to Outpatient Nephrology Follow-up"}
    ]
    inp_path = DATA_DIR / "inpatient" / "admissions.json"
    with open(inp_path, "w", encoding="utf-8") as f:
        json.dump(inpatient_records, f, indent=2)

    # 7. Appointments CSV
    appt_rows = [
        {"patient_id": "P001", "appointment_date": "2024-01-14", "appointment_time": "09:00 AM", "department": "Internal Medicine", "doctor": "Dr. Sarah Smith", "reason_for_visit": "High morning fasting sugar readings and fatigue", "appointment_status": "Completed"},
        {"patient_id": "P001", "appointment_date": "2024-04-15", "appointment_time": "10:30 AM", "department": "Internal Medicine", "doctor": "Dr. Sarah Smith", "reason_for_visit": "Quarterly diabetic check-up & HbA1c review", "appointment_status": "Scheduled"},
        {"patient_id": "P002", "appointment_date": "2024-02-14", "appointment_time": "11:00 AM", "department": "Pulmonology", "doctor": "Dr. John Adams", "reason_for_visit": "Cold weather asthma exacerbation", "appointment_status": "Completed"},
        {"patient_id": "P003", "appointment_date": "2024-01-20", "appointment_time": "02:00 PM", "department": "Cardiology", "doctor": "Dr. Robert Vance", "reason_for_visit": "Routine hypertension & ECG follow-up", "appointment_status": "Completed"},
        {"patient_id": "P004", "appointment_date": "2024-04-05", "appointment_time": "03:30 PM", "department": "Neurology", "doctor": "Dr. Sarah Smith", "reason_for_visit": "Persistent unilateral tension headache", "appointment_status": "Completed"},
        {"patient_id": "P005", "appointment_date": "2024-03-17", "appointment_time": "08:30 AM", "department": "Nephrology", "doctor": "Dr. Alice Wong", "reason_for_visit": "Renal function lab review & blood pressure check", "appointment_status": "Completed"}
    ]
    appt_path = DATA_DIR / "appointments" / "clinic_appointments.csv"
    pd.DataFrame(appt_rows).to_csv(appt_path, index=False)

    # 8. Billing JSON
    billing_records = [
        {"patient_id": "P001", "bill_id": "INV-2024-00101", "service": "Inpatient 3-Day Medical Stay & Nursing Care", "amount": 1450.00, "payment_status": "Insured", "billing_date": "2024-01-17"},
        {"patient_id": "P001", "bill_id": "INV-2024-00102", "service": "Comprehensive Metabolic Panel & HbA1c", "amount": 185.00, "payment_status": "Paid", "billing_date": "2024-03-10"},
        {"patient_id": "P002", "bill_id": "INV-2024-00201", "service": "Specialist Consultation & Spirometry", "amount": 220.00, "payment_status": "Paid", "billing_date": "2024-02-14"},
        {"patient_id": "P003", "bill_id": "INV-2024-00301", "service": "Transthoracic Echocardiogram & ECG", "amount": 450.00, "payment_status": "Paid", "billing_date": "2024-01-22"},
        {"patient_id": "P004", "bill_id": "INV-2024-00401", "service": "Neurological Consultation & Lab Evaluation", "amount": 275.00, "payment_status": "Pending", "billing_date": "2024-04-05"},
        {"patient_id": "P005", "bill_id": "INV-2024-00501", "service": "Renal Ultrasound & Emergency Admission Co-pay", "amount": 890.00, "payment_status": "Pending", "billing_date": "2024-03-21"}
    ]
    bill_path = DATA_DIR / "billing" / "hospital_bills.json"
    with open(bill_path, "w", encoding="utf-8") as f:
        json.dump(billing_records, f, indent=2)


def seed_database(db: Session):
    """Initializes tables, seeds demo users, patients, department records, and runs consolidation."""
    Base.metadata.create_all(bind=engine)

    # 1. Seed Demo Users if not present
    for u in DEMO_USERS:
        existing = db.query(User).filter(
            (User.username == u["username"]) | (User.email == u["email"])
        ).first()
        if not existing:
            try:
                user = User(
                    username=u["username"],
                    hashed_password=hash_password(u["password"]),
                    full_name=u["full_name"],
                    email=u["email"],
                    role=u["role"],
                    department=u["department"],
                    patient_id=u["patient_id"],
                    is_active=True,
                    created_at=datetime.utcnow()
                )
                db.add(user)
                db.commit()
            except Exception as e:
                db.rollback()
                print(f"[Seed Warning] Skipping user {u.get('username')}: {e}")

    # 2. Seed Patients
    for p in PATIENT_SEEDS:
        existing = db.query(Patient).filter(Patient.id == p["id"]).first()
        if not existing:
            patient = Patient(
                id=p["id"],
                first_name=p["first_name"],
                last_name=p["last_name"],
                full_name=f"{p['first_name']} {p['last_name']}",
                dob=p["dob"],
                age=p["age"],
                gender=p["gender"],
                contact_phone=p["contact_phone"],
                email=p["email"],
                address=p["address"],
                blood_group=p["blood_group"],
                emergency_contact=p["emergency_contact"],
                allergies=p["allergies"],
                chronic_conditions=p["chronic_conditions"],
                registration_date=p["registration_date"],
                created_at=datetime.utcnow()
            )
            db.add(patient)
    db.commit()

    # 3. Seed Registration Records
    reg_path = DATA_DIR / "registration" / "patients_registration.csv"
    if reg_path.exists():
        df = pd.read_csv(reg_path)
        for _, row in df.iterrows():
            rec = RegistrationRecord(
                patient_id=str(row["patient_id"]).strip().upper(),
                name=str(row["name"]),
                dob=str(row["dob"]) if pd.notnull(row["dob"]) else None,
                gender=str(row["gender"]) if pd.notnull(row["gender"]) else None,
                contact_number=str(row["contact_number"]) if pd.notnull(row["contact_number"]) else None,
                address=str(row["address"]) if pd.notnull(row["address"]) else None,
                registration_date=str(row["registration_date"]) if pd.notnull(row["registration_date"]) else None,
                source_file="patients_registration.csv",
                created_at=datetime.utcnow()
            )
            db.add(rec)
        db.commit()

    # 4. Seed Lab Records
    lab_path = DATA_DIR / "laboratory" / "lab_results.json"
    if lab_path.exists():
        with open(lab_path, "r", encoding="utf-8") as f:
            labs = json.load(f)
        for l in labs:
            rec = LaboratoryRecord(
                patient_id=l["patient_id"],
                test_name=l["test_name"],
                test_code=l.get("test_code"),
                result_value=str(l["result_value"]),
                unit=l.get("unit"),
                reference_range=l.get("reference_range"),
                is_abnormal=bool(l.get("is_abnormal", False)),
                report_date=l.get("report_date"),
                lab_department=l.get("lab_department"),
                ordering_physician=l.get("ordering_physician"),
                source_file="lab_results.json",
                created_at=datetime.utcnow()
            )
            db.add(rec)
        db.commit()

    # 5. Seed Pharmacy Records
    pharm_path = DATA_DIR / "pharmacy" / "prescriptions.xlsx"
    if pharm_path.exists():
        df = pd.read_excel(pharm_path)
        for _, row in df.iterrows():
            rec = PharmacyRecord(
                patient_id=str(row["patient_id"]).strip().upper(),
                medicine_name=str(row["medicine_name"]),
                strength=str(row["strength"]) if pd.notnull(row["strength"]) else None,
                dosage=str(row["dosage"]) if pd.notnull(row["dosage"]) else None,
                frequency=str(row["frequency"]) if pd.notnull(row["frequency"]) else None,
                duration=str(row["duration"]) if pd.notnull(row["duration"]) else None,
                route=str(row["route"]) if pd.notnull(row["route"]) else "Oral",
                prescription_date=str(row["prescription_date"]) if pd.notnull(row["prescription_date"]) else None,
                prescribing_doctor=str(row["prescribing_doctor"]) if pd.notnull(row["prescribing_doctor"]) else None,
                status=str(row["status"]) if pd.notnull(row["status"]) else "Active",
                source_file="prescriptions.xlsx",
                created_at=datetime.utcnow()
            )
            db.add(rec)
        db.commit()

    # 6. Seed Radiology Records
    rad_path = DATA_DIR / "radiology" / "radiology_reports.json"
    if rad_path.exists():
        with open(rad_path, "r", encoding="utf-8") as f:
            rads = json.load(f)
        for r in rads:
            rec = RadiologyRecord(
                patient_id=r["patient_id"],
                imaging_type=r["imaging_type"],
                body_part=r.get("body_part"),
                report_findings=r["report_findings"],
                impression=r.get("impression"),
                report_date=r.get("report_date"),
                radiologist_name=r.get("radiologist_name"),
                source_file="radiology_reports.json",
                created_at=datetime.utcnow()
            )
            db.add(rec)
        db.commit()

    # 7. Seed Nursing Records
    nurs_path = DATA_DIR / "nursing" / "nursing_vitals.csv"
    if nurs_path.exists():
        df = pd.read_csv(nurs_path)
        for _, row in df.iterrows():
            rec = NursingRecord(
                patient_id=str(row["patient_id"]).strip().upper(),
                vital_bp=str(row["vital_bp"]) if pd.notnull(row["vital_bp"]) else None,
                vital_pulse=int(row["vital_pulse"]) if pd.notnull(row["vital_pulse"]) else None,
                vital_temp=float(row["vital_temp"]) if pd.notnull(row["vital_temp"]) else None,
                vital_resp_rate=int(row["vital_resp_rate"]) if pd.notnull(row["vital_resp_rate"]) else None,
                vital_spo2=int(row["vital_spo2"]) if pd.notnull(row["vital_spo2"]) else None,
                nurse_notes=str(row["nurse_notes"]) if pd.notnull(row["nurse_notes"]) else None,
                recorded_at=str(row["recorded_at"]) if pd.notnull(row["recorded_at"]) else None,
                nurse_name=str(row["nurse_name"]) if pd.notnull(row["nurse_name"]) else None,
                source_file="nursing_vitals.csv",
                created_at=datetime.utcnow()
            )
            db.add(rec)
        db.commit()

    # 8. Seed Inpatient Records
    inp_path = DATA_DIR / "inpatient" / "admissions.json"
    if inp_path.exists():
        with open(inp_path, "r", encoding="utf-8") as f:
            inps = json.load(f)
        for i in inps:
            rec = InpatientRecord(
                patient_id=i["patient_id"],
                admission_date=i["admission_date"],
                discharge_date=i.get("discharge_date"),
                ward=i.get("ward"),
                bed_number=i.get("bed_number"),
                admission_diagnosis=i.get("admission_diagnosis"),
                discharge_diagnosis=i.get("discharge_diagnosis"),
                attending_physician=i.get("attending_physician"),
                discharge_status=i.get("discharge_status"),
                source_file="admissions.json",
                created_at=datetime.utcnow()
            )
            db.add(rec)
        db.commit()

    # 9. Seed Appointments Records
    appt_path = DATA_DIR / "appointments" / "clinic_appointments.csv"
    if appt_path.exists():
        df = pd.read_csv(appt_path)
        for _, row in df.iterrows():
            rec = AppointmentRecord(
                patient_id=str(row["patient_id"]).strip().upper(),
                appointment_date=str(row["appointment_date"]),
                appointment_time=str(row["appointment_time"]) if pd.notnull(row["appointment_time"]) else None,
                department=str(row["department"]),
                doctor=str(row["doctor"]),
                reason_for_visit=str(row["reason_for_visit"]) if pd.notnull(row["reason_for_visit"]) else None,
                appointment_status=str(row["appointment_status"]) if pd.notnull(row["appointment_status"]) else "Scheduled",
                source_file="clinic_appointments.csv",
                created_at=datetime.utcnow()
            )
            db.add(rec)
        db.commit()

    # 10. Seed Billing Records
    bill_path = DATA_DIR / "billing" / "hospital_bills.json"
    if bill_path.exists():
        with open(bill_path, "r", encoding="utf-8") as f:
            bills = json.load(f)
        for b in bills:
            rec = BillingRecord(
                patient_id=b["patient_id"],
                bill_id=b["bill_id"],
                service=b["service"],
                amount=float(b["amount"]),
                payment_status=b.get("payment_status", "Pending"),
                billing_date=b.get("billing_date"),
                source_file="hospital_bills.json",
                created_at=datetime.utcnow()
            )
            db.add(rec)
        db.commit()

    # 11. Run Patient Data Management Agent to build Unified Records for all 15 baseline patients
    data_agent = PatientDataManagementAgent(db)
    for p in PATIENT_SEEDS:
        data_agent.consolidate_unified_record(p["id"])

    # 12. Seed Real-Time Integrated Patient Cases (P016 - P020)
    seed_real_time_clinical_cases(db)

    # 13. Initial Audit Log
    init_audit = AuditLog(
        event_id=f"EVT-INIT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        user_id=1,
        user_role="Hospital Administrator",
        action="DATABASE_INITIALIZATION_AND_SEEDING",
        entity_type="System",
        entity_id="HOSPIQ_CORE",
        status="SUCCESS",
        details_json='{"message": "Synthetic and real-time clinical dataset seeded across 8 departments for 20 patients."}',
        ip_address="127.0.0.1",
        timestamp=datetime.utcnow()
    )
    db.add(init_audit)
    db.commit()


def seed_real_time_clinical_cases(db: Session):
    """Idempotently integrates the 5 real-time hospital diagnostic cases (P016 - P020) with full 8-department records."""
    real_cases = [
        # P016: MD Meharunnihabugum (Prathima Relief MRI Cervical & Whole Spine + CBP/ESR/CRP PDF)
        {
            "patient": {
                "id": "P016", "first_name": "MD", "last_name": "Meharunnihabugum", "full_name": "MD Meharunnihabugum",
                "dob": "1985-05-15", "age": 41, "gender": "Female", "contact_phone": "+91-98480-14876",
                "email": "meharunnihabugum@patient.hospiq.local",
                "address": "UHID: 26014876 | OP: OP2611030190 | Warangal, Telangana",
                "blood_group": "O+", "emergency_contact": "Family Guardian +91-98480-14877",
                "allergies": "No known drug allergies",
                "chronic_conditions": "Cervical & Lumbar Disc Bulge, Neural Foraminal Narrowing, Elevated Inflammatory Marker (ESR)",
                "registration_date": "2026-11-24"
            },
            "reg": {
                "name": "MD Meharunnihabugum", "dob": "1985-05-15", "gender": "Female",
                "registration_date": "2026-11-24",
                "raw_data_json": json.dumps({"department": "Orthopaedics", "uhid": "26014876", "op_no": "OP2611030190"}),
                "contact_number": "+91-98480-14876",
                "address": "Prathima Relief Institute of Medical Sciences, Warangal (UHID: 26014876)",
                "source_file": "Prathima_Relief_MRI_Lab_Report_P016.pdf"
            },
            "labs": [
                {"test_name": "Haemoglobin", "test_code": "HGB", "result_value": "11.8", "unit": "gm%", "reference_range": "11.5 - 16.0 (Female)", "is_abnormal": False, "report_date": "2026-11-24", "lab_department": "Haematology", "ordering_physician": "Dr. Mythilee Vadlamudi", "source_file": "Prathima_Relief_Lab_CBP_P016.pdf"},
                {"test_name": "Total RBC Count", "test_code": "RBC", "result_value": "4.80", "unit": "Millions/cumm", "reference_range": "4.0 - 5.0", "is_abnormal": False, "report_date": "2026-11-24", "lab_department": "Haematology", "ordering_physician": "Dr. Mythilee Vadlamudi", "source_file": "Prathima_Relief_Lab_CBP_P016.pdf"},
                {"test_name": "Total Leukocyte Count (WBC)", "test_code": "WBC", "result_value": "7600", "unit": "/cumm", "reference_range": "4,000 - 11,000", "is_abnormal": False, "report_date": "2026-11-24", "lab_department": "Haematology", "ordering_physician": "Dr. Mythilee Vadlamudi", "source_file": "Prathima_Relief_Lab_CBP_P016.pdf"},
                {"test_name": "Platelet Count", "test_code": "PLT", "result_value": "3.63", "unit": "Lakhs/cumm", "reference_range": "1.4 - 4.5 Lakhs/cumm", "is_abnormal": False, "report_date": "2026-11-24", "lab_department": "Haematology", "ordering_physician": "Dr. Mythilee Vadlamudi", "source_file": "Prathima_Relief_Lab_CBP_P016.pdf"},
                {"test_name": "Neutrophils / Lymphocytes", "test_code": "DIFF", "result_value": "64% / 29% (Normocytic RBC)", "unit": "%", "reference_range": "N:35-75% / L:20-40%", "is_abnormal": False, "report_date": "2026-11-24", "lab_department": "Haematology", "ordering_physician": "Dr. Mythilee Vadlamudi", "source_file": "Prathima_Relief_Lab_CBP_P016.pdf"},
                {"test_name": "ESR (Erythrocyte Sedimentation Rate)", "test_code": "ESR", "result_value": "52", "unit": "mm 1st hour", "reference_range": "0 - 20", "is_abnormal": True, "report_date": "2026-11-24", "lab_department": "Haematology / Pathology", "ordering_physician": "Dr. Mythilee Vadlamudi", "source_file": "Prathima_Relief_Lab_ESR_P016.pdf"},
                {"test_name": "C-Reactive Protein (CRP)", "test_code": "CRP", "result_value": "4.5", "unit": "mg/L", "reference_range": "Up to 10 mg/L", "is_abnormal": False, "report_date": "2026-11-24", "lab_department": "Microbiology / Serology", "ordering_physician": "Dr. Mythilee Vadlamudi", "source_file": "Prathima_Relief_Lab_CRP_P016.pdf"},
            ],
            "rads": [
                {
                    "imaging_type": "MRI Cervical Spine with Whole Spine Screening",
                    "body_part": "Cervical & Whole Spine",
                    "report_findings": "Straightening of cervical spine. Central disc bulges at C4-C5 & C5-C6 causing thecal sac indentation. Right lateral disc bulge at C6-C7 causing thecal sac indentation and narrowing of right neural foramina. Whole sagittal spine screening: Disc bulges noted at L4-L5 & L5-S1 causing thecal sac indentation; Haemangioma at L5. Spinal cord shows normal caliber and signal intensity.",
                    "impression": "1) Central disc bulges at C4-C5 & C5-C6 causing thecal sac indentation. 2) Right lateral disc bulge at C6-C7 causing thecal sac indentation and narrowing of right neural foramina. 3) L4-L5 & L5-S1 disc bulges and benign L5 vertebral haemangioma.",
                    "report_date": "2026-11-24",
                    "radiologist_name": "Dr. T. Ramesh MD.DMRD / Dr. P. Keerthi Bharathi MD.RD",
                    "source_file": "Prathima_Relief_MRI_Spine_P016.pdf"
                }
            ],
            "nursing": [
                {"vital_bp": "126/82", "vital_pulse": 78, "vital_temp": 98.4, "vital_resp_rate": 16, "vital_spo2": 99, "nurse_notes": "Patient reports neck stiffness radiating to right upper limb and lower back discomfort; advised cervical collar & physiotherapy review.", "recorded_at": "2026-11-24", "nurse_name": "Nurse Deepika, RN", "source_file": "Ortho_Triage_P016.csv"}
            ],
            "meds": [
                {"medicine_name": "Pregabalin", "strength": "75 mg", "dosage": "1 capsule", "frequency": "Once nightly", "duration": "14 days", "prescription_date": "2026-11-24", "prescribing_doctor": "Dr. Mythilee Vadlamudi", "status": "Active", "source_file": "Prathima_Ortho_Rx.xlsx"},
                {"medicine_name": "Methylcobalamin", "strength": "1500 mcg", "dosage": "1 tablet", "frequency": "Once daily", "duration": "30 days", "prescription_date": "2026-11-24", "prescribing_doctor": "Dr. Mythilee Vadlamudi", "status": "Active", "source_file": "Prathima_Ortho_Rx.xlsx"},
                {"medicine_name": "Etoricoxib", "strength": "90 mg", "dosage": "1 tablet", "frequency": "Once daily after food", "duration": "5 days", "prescription_date": "2026-11-24", "prescribing_doctor": "Dr. Mythilee Vadlamudi", "status": "Active", "source_file": "Prathima_Ortho_Rx.xlsx"},
            ],
            "appts": [
                {"appointment_date": "2026-11-24", "appointment_time": "04:30 PM", "department": "Orthopaedics", "doctor": "Dr. Mythilee Vadlamudi", "reason_for_visit": "MRI Spine, CBP, ESR, CRP evaluation for cervical radiculopathy & low back pain", "appointment_status": "Completed", "source_file": "Prathima_OPD.csv"}
            ],
            "inpatient": [
                {"admission_date": "2026-11-24", "discharge_date": "2026-11-24", "ward": "Orthopaedics Daycare Unit", "bed_number": "DC-04", "admission_diagnosis": "Cervical spondylotic radiculopathy (C4-C7 disc bulges) with L4-S1 disc bulge", "discharge_diagnosis": "Multi-level cervical (C4-C7) & lumbar (L4-S1) disc disease, conservative neuro-rehab initiated", "attending_physician": "Dr. Mythilee Vadlamudi", "discharge_status": "Discharged Home — Physiotherapy & Ortho Follow-up", "source_file": "Prathima_ADT.json"}
            ],
            "billing": [
                {"bill_id": "OB26012812", "service": "MRI Cervical + Whole Spine Screening & Haematology Panel (CBP, ESR, CRP)", "amount": 8950.0, "payment_status": "Paid", "billing_date": "2026-11-24", "source_file": "Prathima_Billing.json"}
            ]
        },

        # P017: Harish Kanna (Mahesh Clinical Laboratory CBP + Widal + Dengue + Malaria)
        {
            "patient": {
                "id": "P017", "first_name": "Harish", "last_name": "Kanna", "full_name": "Harish Kanna",
                "dob": "1991-06-10", "age": 35, "gender": "Male", "contact_phone": "+91-94937-34072",
                "email": "harish.kanna@patient.hospiq.local",
                "address": "OP Reg No: OP6780019340 | Order: 20261113-282 | Pedanandipadu, Guntur",
                "blood_group": "B+", "emergency_contact": "Kanna Family +91-94937-34073",
                "allergies": "No known drug allergies",
                "chronic_conditions": "Febrile Viral Illness Workup, Mild Thrombocytopenia (Platelets 1.25 Lakhs), Mild Anemia (Hb 12.1 gm%)",
                "registration_date": "2026-11-13"
            },
            "reg": {
                "name": "Harish Kanna", "dob": "1991-06-10", "gender": "Male",
                "registration_date": "2026-11-13",
                "raw_data_json": json.dumps({"department": "Laboratory / Gen Med", "op_reg_no": "OP6780019340", "lab_order": "20261113-282"}),
                "contact_number": "+91-94937-34072",
                "address": "Pedanandipadu, Bapatla / Guntur Dist, AP (OP6780019340)",
                "source_file": "CH.HARISH.zip"
            },
            "labs": [
                {"test_name": "Hemoglobin", "test_code": "HGB", "result_value": "12.1", "unit": "gm%", "reference_range": "Male: 14.0 - 17.5 gm%", "is_abnormal": True, "report_date": "2026-11-13", "lab_department": "Haematology", "ordering_physician": "Self / Gen Med", "source_file": "Mahesh_Lab_HARISH_1.png"},
                {"test_name": "Platelet Count", "test_code": "PLT", "result_value": "1.25", "unit": "LAKHS/CUMM", "reference_range": "1.50 - 4.50 LAKHS/CUMM", "is_abnormal": True, "report_date": "2026-11-13", "lab_department": "Haematology", "ordering_physician": "Self / Gen Med", "source_file": "Mahesh_Lab_HARISH_1.png"},
                {"test_name": "Total WBC Count", "test_code": "WBC", "result_value": "4500", "unit": "/cumm", "reference_range": "4,000 - 11,000/cumm", "is_abnormal": False, "report_date": "2026-11-13", "lab_department": "Haematology", "ordering_physician": "Self / Gen Med", "source_file": "Mahesh_Lab_HARISH_1.png"},
                {"test_name": "RBC Count", "test_code": "RBC", "result_value": "4.50", "unit": "mill/cumm", "reference_range": "4.0 - 6.0 mill/cumm", "is_abnormal": False, "report_date": "2026-11-13", "lab_department": "Haematology", "ordering_physician": "Self / Gen Med", "source_file": "Mahesh_Lab_HARISH_1.png"},
                {"test_name": "MCH / MCHC", "test_code": "INDICES", "result_value": "26.8 Pg / 30.8 gms%", "unit": "Pg / gms%", "reference_range": "MCH: 27-32 / MCHC: 31-35", "is_abnormal": True, "report_date": "2026-11-13", "lab_department": "Haematology", "ordering_physician": "Self / Gen Med", "source_file": "Mahesh_Lab_HARISH_1.png"},
                {"test_name": "Malaria Ag P.f/p.v (Smear for MP)", "test_code": "MP-AG", "result_value": "NEGATIVE", "unit": "", "reference_range": "Negative", "is_abnormal": False, "report_date": "2026-11-13", "lab_department": "Immunology", "ordering_physician": "Self / Gen Med", "source_file": "Mahesh_Lab_HARISH_1.png"},
                {"test_name": "Widal (S. Typhi O & H)", "test_code": "WIDAL", "result_value": "S. Typhi O: 1:80 / H: 1:80 (AH/BH: 1:20)", "unit": "Dilutions", "reference_range": "Borderline (< 1:160)", "is_abnormal": False, "report_date": "2026-11-13", "lab_department": "Immunology", "ordering_physician": "Self / Gen Med", "source_file": "Mahesh_Lab_HARISH_1.png"},
                {"test_name": "Dengue Serology (NS1 / IgM / IgG)", "test_code": "DENGUE", "result_value": "NS1: NON REACTIVE | IgM: NON REACTIVE | IgG: NON REACTIVE", "unit": "", "reference_range": "Non Reactive", "is_abnormal": False, "report_date": "2026-11-13", "lab_department": "Serology", "ordering_physician": "Self / Gen Med", "source_file": "Mahesh_Lab_HARISH_1.png"},
            ],
            "rads": [
                {"imaging_type": "Ultrasound Abdomen Screening (Baseline)", "body_part": "Abdomen", "report_findings": "Liver, spleen, and gallbladder normal in size and echotexture. No free fluid / ascites noted.", "impression": "Normal abdominal screening; no organomegaly or capillary leak.", "report_date": "2026-11-13", "radiologist_name": "Dr. Sudheer, MD", "source_file": "GenMed_USG_P017.json"}
            ],
            "nursing": [
                {"vital_bp": "116/74", "vital_pulse": 88, "vital_temp": 100.6, "vital_resp_rate": 18, "vital_spo2": 98, "nurse_notes": "Low-grade fever evaluation; platelets slightly low at 1.25 Lakhs/cumm; oral hydration and platelet repeat monitoring in 48 hrs advised.", "recorded_at": "2026-11-13", "nurse_name": "Nurse Clara Barton, RN", "source_file": "OPD_Vitals_P017.csv"}
            ],
            "meds": [
                {"medicine_name": "Paracetamol", "strength": "650 mg", "dosage": "1 tablet", "frequency": "Every 6-8 hours if fever > 100°F", "duration": "5 days", "prescription_date": "2026-11-13", "prescribing_doctor": "Dr. Sarah Smith", "status": "Active", "source_file": "GenMed_Rx_P017.xlsx"},
                {"medicine_name": "Oral Rehydration Salts (ORS)", "strength": "21.8 g sachet", "dosage": "1 sachet in 1L water", "frequency": "Sip throughout day", "duration": "5 days", "prescription_date": "2026-11-13", "prescribing_doctor": "Dr. Sarah Smith", "status": "Active", "source_file": "GenMed_Rx_P017.xlsx"},
            ],
            "appts": [
                {"appointment_date": "2026-11-13", "appointment_time": "08:30 PM", "department": "General Medicine", "doctor": "Dr. Sarah Smith", "reason_for_visit": "Fever profile follow-up: CBP (Hb 12.1, Platelets 1.25L), Widal 1:80, Dengue/Malaria negative", "appointment_status": "Completed", "source_file": "GenMed_OPD.csv"}
            ],
            "inpatient": [],
            "billing": [
                {"bill_id": "BILL-20261113-282", "service": "Complete Fever Lab Panel (CBP, Malaria, Widal, Dengue NS1/IgM/IgG)", "amount": 1850.0, "payment_status": "Paid", "billing_date": "2026-11-13", "source_file": "Mahesh_Lab_Bill.json"}
            ]
        },

        # P018: Mr. B Krishna Rao (X-Ray PNS - Subtle S-shaped deviation + turbinate hypertrophy)
        {
            "patient": {
                "id": "P018", "first_name": "B Krishna", "last_name": "Rao", "full_name": "B Krishna Rao",
                "dob": "1988-08-20", "age": 38, "gender": "Male", "contact_phone": "+91-98490-46422",
                "email": "b.krishnarao@patient.hospiq.local",
                "address": "Patient ID: 4646422 | Reg: 265120001020 | Dwaraka Nagar, Visakhapatnam, AP",
                "blood_group": "A+", "emergency_contact": "Rao Family +91-98490-46423",
                "allergies": "No known drug allergies",
                "chronic_conditions": "Deviated Nasal Septum (S-Shaped), Bilateral Turbinate Hypertrophy (Right > Left)",
                "registration_date": "2026-11-24"
            },
            "reg": {
                "name": "B Krishna Rao", "dob": "1988-08-20", "gender": "Male",
                "registration_date": "2026-11-24",
                "raw_data_json": json.dumps({"department": "ENT / Radiology", "external_patient_id": "4646422", "reg_id": "265120001020"}),
                "contact_number": "+91-98490-46422",
                "address": "Dwaraka Nagar, Visakhapatnam, AP-530016 (Patient ID: 4646422)",
                "source_file": "DX_PNS_4646422.jpg"
            },
            "labs": [
                {"test_name": "Absolute Eosinophil Count (AEC)", "test_code": "AEC", "result_value": "340", "unit": "cells/cumm", "reference_range": "40 - 440", "is_abnormal": False, "report_date": "2026-11-24", "lab_department": "Haematology", "ordering_physician": "Dr. Dakshina Murthy D", "source_file": "ENT_Lab_P018.json"}
            ],
            "rads": [
                {
                    "imaging_type": "X-RAY PARANASAL SINUSES (PNS) [DX]",
                    "body_part": "Paranasal Sinuses (PNS)",
                    "report_findings": "Nasal septum shows subtle 'S' shaped deviation. Visualized turbinates hypertrophy noted (right > left) with narrowed nasal cavities. Bilateral frontal and ethmoidal sinuses are normal. Bilateral maxillary sinuses are normal. No lytic or sclerotic bony lesions. Soft tissues appear normal.",
                    "impression": "Subtle S-shaped nasal septal deviation and turbinate hypertrophy (right > left) causing narrowed nasal cavities; paranasal sinuses clear. For clinical correlation and CT if clinically indicated.",
                    "report_date": "2026-11-24",
                    "radiologist_name": "Dr. Sudheer (DNB, FRCR, Reg: 84190)",
                    "source_file": "XRay_PNS_63156855.pdf"
                }
            ],
            "nursing": [
                {"vital_bp": "122/78", "vital_pulse": 74, "vital_temp": 98.6, "vital_resp_rate": 16, "vital_spo2": 99, "nurse_notes": "Referred by Dr. Dakshina Murthy D for chronic nasal stuffiness and recurrent frontal headache.", "recorded_at": "2026-11-24", "nurse_name": "Nurse Deepika, RN", "source_file": "ENT_Vitals_P018.csv"}
            ],
            "meds": [
                {"medicine_name": "Fluticasone Furoate Nasal Spray", "strength": "27.5 mcg/spray", "dosage": "2 sprays each nostril", "frequency": "Once daily", "duration": "30 days", "prescription_date": "2026-11-24", "prescribing_doctor": "Dr. Dakshina Murthy D", "status": "Active", "source_file": "ENT_Rx_P018.xlsx"},
                {"medicine_name": "Levocetirizine", "strength": "5 mg", "dosage": "1 tablet", "frequency": "Once nightly", "duration": "10 days", "prescription_date": "2026-11-24", "prescribing_doctor": "Dr. Dakshina Murthy D", "status": "Active", "source_file": "ENT_Rx_P018.xlsx"},
            ],
            "appts": [
                {"appointment_date": "2026-11-24", "appointment_time": "06:30 PM", "department": "ENT (Otorhinolaryngology)", "doctor": "Dr. Dakshina Murthy D", "reason_for_visit": "Nasal obstruction assessment & X-Ray PNS Accn No. 63156855", "appointment_status": "Completed", "source_file": "ENT_OPD.csv"}
            ],
            "inpatient": [],
            "billing": [
                {"bill_id": "ACCN-63156855", "service": "DX X-Ray Paranasal Sinuses (PNS) & ENT Consultation", "amount": 950.0, "payment_status": "Paid", "billing_date": "2026-11-24", "source_file": "DX_Billing_P018.json"}
            ]
        },

        # P019: Ms. Pragya (X-Ray Right Hand PA & Oblique Views - Normal after fall)
        {
            "patient": {
                "id": "P019", "first_name": "Pragya", "last_name": "Ms.", "full_name": "Ms. Pragya",
                "dob": "2003-04-12", "age": 23, "gender": "Female", "contact_phone": "+91-97010-25795",
                "email": "pragya.9625795@patient.hospiq.local",
                "address": "Patient ID: 9625795 | Reg: 260060032652 | Dwaraka Nagar, Visakhapatnam",
                "blood_group": "O+", "emergency_contact": "Guardian +91-97010-25796",
                "allergies": "No known drug allergies",
                "chronic_conditions": "Post-Fall Right Hand Soft Tissue Pain (X-Ray Normal — No Fracture)",
                "registration_date": "2026-11-24"
            },
            "reg": {
                "name": "Ms. Pragya", "dob": "2003-04-12", "gender": "Female",
                "registration_date": "2026-11-24",
                "raw_data_json": json.dumps({"department": "Orthopaedics / Radiology", "external_patient_id": "9625795", "reg_id": "260060032652"}),
                "contact_number": "+91-97010-25795",
                "address": "Dwaraka Nagar, Visakhapatnam, AP (Patient ID: 9625795)",
                "source_file": "DX_RightHand_9625795.pdf"
            },
            "labs": [
                {"test_name": "Serum Calcium (Bone Health Baseline)", "test_code": "CA", "result_value": "9.4", "unit": "mg/dL", "reference_range": "8.5 - 10.5", "is_abnormal": False, "report_date": "2026-11-24", "lab_department": "Biochemistry", "ordering_physician": "Duty Medical Officer", "source_file": "Ortho_Baseline_P019.json"}
            ],
            "rads": [
                {
                    "imaging_type": "X-RAY RIGHT HAND PA & OBLIQUE VIEWS [DX]",
                    "body_part": "Right Hand",
                    "report_findings": "History: Fall and pain. Bone density is normal. Alignment is normal. Joint spaces are normal. Articular margins are normal. No evidence of lytic / sclerotic bone lesions. No bony injury noted. Soft tissues are normal.",
                    "impression": "Within normal limits (No acute fracture or dislocation detected).",
                    "report_date": "2026-11-24",
                    "radiologist_name": "Dr. Sudheer (DNB, FRCR)",
                    "source_file": "XRay_RightHand_63158383.pdf"
                }
            ],
            "nursing": [
                {"vital_bp": "112/72", "vital_pulse": 76, "vital_temp": 98.4, "vital_resp_rate": 16, "vital_spo2": 99, "nurse_notes": "Walk-in post minor fall with right hand soreness; ice pack applied, zero visible deformity, intact neurovascular status.", "recorded_at": "2026-11-24", "nurse_name": "Nurse Clara Barton, RN", "source_file": "ER_Vitals_P019.csv"}
            ],
            "meds": [
                {"medicine_name": "Diclofenac Diethylamine Gel", "strength": "1.16% Topical", "dosage": "Apply thinly to painful area", "frequency": "Twice daily", "duration": "7 days", "prescription_date": "2026-11-24", "prescribing_doctor": "Dr. Sarah Smith", "status": "Active", "source_file": "Ortho_Rx_P019.xlsx"},
                {"medicine_name": "Paracetamol", "strength": "500 mg", "dosage": "1 tablet", "frequency": "As needed for pain (max 3/day)", "duration": "3 days", "prescription_date": "2026-11-24", "prescribing_doctor": "Dr. Sarah Smith", "status": "Active", "source_file": "Ortho_Rx_P019.xlsx"},
            ],
            "appts": [
                {"appointment_date": "2026-11-24", "appointment_time": "08:40 PM", "department": "Orthopaedics / Diagnostic DX", "doctor": "Self-Referred / Duty Ortho", "reason_for_visit": "Right hand fall injury screening — X-Ray Right Hand PA & Oblique Accn No. 63158383", "appointment_status": "Completed", "source_file": "Ortho_OPD.csv"}
            ],
            "inpatient": [],
            "billing": [
                {"bill_id": "ACCN-63158383", "service": "DX X-Ray Right Hand (PA & Oblique Views)", "amount": 600.0, "payment_status": "Paid", "billing_date": "2026-11-24", "source_file": "DX_Billing_P019.json"}
            ]
        },

        # P020: Patient 9624735 (Port Trust - Skull Lateral View: Multiple tiny parietal lytic lesions -> consider myeloma)
        {
            "patient": {
                "id": "P020", "first_name": "Port Trust", "last_name": "Case 9624735", "full_name": "Patient 9624735 (Visakhapatnam Port Trust)",
                "dob": "1968-01-15", "age": 58, "gender": "Male", "contact_phone": "+91-891-2879624",
                "email": "case.9624735@patient.hospiq.local",
                "address": "Patient ID: 9624735 | Reg: 260060032641 | Ref: Visakhapatnam Port Trust - Port Service",
                "blood_group": "O+", "emergency_contact": "Port Trust Medical Desk +91-891-2879000",
                "allergies": "No known drug allergies",
                "chronic_conditions": "Multiple Parietal Lytic Skull Lesions (Suspected Myeloproliferative Disorder / Myeloma Evaluation)",
                "registration_date": "2026-11-25"
            },
            "reg": {
                "name": "Patient 9624735 (Visakhapatnam Port Trust)", "dob": "1968-01-15", "gender": "Male",
                "registration_date": "2026-11-25",
                "raw_data_json": json.dumps({"department": "Haematology / Port Trust Referral", "external_patient_id": "9624735", "reg_id": "260060032641"}),
                "contact_number": "+91-891-2879624",
                "address": "Visakhapatnam Port Trust - Port Service, AP (Patient ID: 9624735)",
                "source_file": "DX_Skull_9624735.pdf"
            },
            "labs": [
                {"test_name": "Hemoglobin", "test_code": "HGB", "result_value": "10.4", "unit": "gm%", "reference_range": "14.0 - 17.5 gm% (Male)", "is_abnormal": True, "report_date": "2026-11-25", "lab_department": "Haematology", "ordering_physician": "Port Trust Medical Officer", "source_file": "PortTrust_Workup_P020.json"},
                {"test_name": "ESR (Erythrocyte Sedimentation Rate)", "test_code": "ESR", "result_value": "68", "unit": "mm 1st hour", "reference_range": "0 - 20", "is_abnormal": True, "report_date": "2026-11-25", "lab_department": "Haematology", "ordering_physician": "Port Trust Medical Officer", "source_file": "PortTrust_Workup_P020.json"},
                {"test_name": "Serum Calcium", "test_code": "CA", "result_value": "10.8", "unit": "mg/dL", "reference_range": "8.5 - 10.5", "is_abnormal": True, "report_date": "2026-11-25", "lab_department": "Biochemistry", "ordering_physician": "Port Trust Medical Officer", "source_file": "PortTrust_Workup_P020.json"},
                {"test_name": "Serum Creatinine", "test_code": "CREAT", "result_value": "1.3", "unit": "mg/dL", "reference_range": "0.6 - 1.3", "is_abnormal": False, "report_date": "2026-11-25", "lab_department": "Biochemistry", "ordering_physician": "Port Trust Medical Officer", "source_file": "PortTrust_Workup_P020.json"},
            ],
            "rads": [
                {
                    "imaging_type": "X-RAY SKULL LATERAL & AP VIEWS [DX]",
                    "body_part": "Skull (Parietal Bone / Sella)",
                    "report_findings": "History: Fall. Multiple tiny lytic lesions noted in parietal bone. Sella size, contour, floor of the sella, anterior & posterior clinoid processes are normal. No evidence of raised intracranial tension. No evidence of abnormal calcification. No evidence of bony injury noted.",
                    "impression": "Multiple tiny lytic lesions noted in parietal bone - to consider myeloproliferative disorder such as myeloma. Advise serum electrophoresis for further evaluation. Advise CT / x-ray lateral view of nasal bone for further evaluation. For clinical correlation.",
                    "report_date": "2026-11-25",
                    "radiologist_name": "Dr. Sudheer (DNB, FRCR)",
                    "source_file": "XRay_Skull_63155053.pdf"
                }
            ],
            "nursing": [
                {"vital_bp": "134/84", "vital_pulse": 82, "vital_temp": 98.5, "vital_resp_rate": 16, "vital_spo2": 98, "nurse_notes": "Port Trust referral post fall; alert and oriented (GCS 15/15). Urgent Hematology referral flagged for parietal bone lytic lesions.", "recorded_at": "2026-11-25", "nurse_name": "Nurse Clara Barton, RN", "source_file": "Triage_Vitals_P020.csv"}
            ],
            "meds": [
                {"medicine_name": "Paracetamol", "strength": "500 mg", "dosage": "1 tablet", "frequency": "As needed for mild scalp tenderness", "duration": "3 days", "prescription_date": "2026-11-25", "prescribing_doctor": "Dr. Sarah Smith", "status": "Active", "source_file": "Heme_Supportive_P020.xlsx"},
            ],
            "appts": [
                {"appointment_date": "2026-11-25", "appointment_time": "10:30 AM", "department": "Haematology / Internal Medicine", "doctor": "Dr. Sarah Smith", "reason_for_visit": "Urgent workup: skull parietal lytic lesions -> Serum Protein Electrophoresis & CT correlation", "appointment_status": "Scheduled", "source_file": "PortTrust_Referral.csv"}
            ],
            "inpatient": [
                {"admission_date": "2026-11-25", "discharge_date": None, "ward": "Internal Medicine Observation", "bed_number": "OBS-02", "admission_diagnosis": "Parietal skull lytic lesions under evaluation for suspected myeloproliferative disorder / myeloma", "discharge_diagnosis": "Pending Serum Protein Electrophoresis & Hematology Consult", "attending_physician": "Dr. Sarah Smith", "discharge_status": "Under Active Evaluation", "source_file": "Admission_Obs_P020.json"}
            ],
            "billing": [
                {"bill_id": "ACCN-63155053", "service": "DX X-Ray Skull Lateral & AP + Hematology Screening Workup", "amount": 2450.0, "payment_status": "Pending", "billing_date": "2026-11-25", "source_file": "PortTrust_Billing_P020.json"}
            ]
        },
    ]

    data_agent = PatientDataManagementAgent(db)
    for case in real_cases:
        p_info = case["patient"]
        pid = p_info["id"]
        if not db.query(Patient).filter(Patient.id == pid).first():
            pat = Patient(
                id=pid,
                first_name=p_info["first_name"],
                last_name=p_info["last_name"],
                full_name=p_info["full_name"],
                dob=p_info["dob"],
                age=p_info["age"],
                gender=p_info["gender"],
                contact_phone=p_info["contact_phone"],
                email=p_info["email"],
                address=p_info["address"],
                blood_group=p_info["blood_group"],
                emergency_contact=p_info["emergency_contact"],
                allergies=p_info["allergies"],
                chronic_conditions=p_info["chronic_conditions"],
                registration_date=p_info["registration_date"],
                created_at=datetime.utcnow()
            )
            db.add(pat)
            db.flush()

            reg = case["reg"]
            db.add(RegistrationRecord(patient_id=pid, created_at=datetime.utcnow(), **reg))

            for lab in case["labs"]:
                db.add(LaboratoryRecord(patient_id=pid, created_at=datetime.utcnow(), **lab))

            for rad in case["rads"]:
                db.add(RadiologyRecord(patient_id=pid, created_at=datetime.utcnow(), **rad))

            for nurs in case["nursing"]:
                db.add(NursingRecord(patient_id=pid, created_at=datetime.utcnow(), **nurs))

            for med in case["meds"]:
                db.add(PharmacyRecord(
                    patient_id=pid, medicine_name=med["medicine_name"], strength=med["strength"],
                    dosage=med["dosage"], frequency=med["frequency"], duration=med["duration"],
                    route="Topical" if "Gel" in med["medicine_name"] else ("Nasal Spray" if "Spray" in med["medicine_name"] else "Oral"),
                    prescription_date=med["prescription_date"], prescribing_doctor=med["prescribing_doctor"],
                    status=med["status"], source_file=med["source_file"], created_at=datetime.utcnow()
                ))

            for appt in case["appts"]:
                db.add(AppointmentRecord(patient_id=pid, created_at=datetime.utcnow(), **appt))

            for inp in case["inpatient"]:
                db.add(InpatientRecord(patient_id=pid, created_at=datetime.utcnow(), **inp))

            for bill in case["billing"]:
                db.add(BillingRecord(patient_id=pid, created_at=datetime.utcnow(), **bill))

            db.commit()

        if not db.query(UnifiedPatientRecord).filter(UnifiedPatientRecord.patient_id == pid).first():
            data_agent.consolidate_unified_record(pid)


if __name__ == "__main__":
    generate_department_files()
    db = SessionLocal()
    try:
        seed_database(db)
        print("HOSPIQ synthetic data generated and seeded successfully!")
    finally:
        db.close()

