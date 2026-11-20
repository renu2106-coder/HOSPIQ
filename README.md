# Agentic Hospital Management System (HOSPIQ)
### Multi-Agent AI Healthcare Platform • Multi-Layered Architecture
**Tagline:** Connected Departments. Better Hospital Services.  
*An Academic Postgraduate MSc Health Informatics and Analytics Project*

---

## 1. Executive Summary

Modern hospitals manage patient data across fragmented, isolated departmental systems (Registration, Laboratory, Pharmacy, Radiology, Inpatient Ward Nursing, OPD/Appointments, and Billing). This fragmentation causes duplicate records, conflicting medications, lab value discrepancies, missing data, and manual documentation burden.

**HOSPIQ** is an enterprise-grade multi-agent healthcare information management system structured across **5 distinct architectural layers** to ensure data integration, clinical safety, deterministic guardrails, and cryptographic auditability.

---

## 2. Multi-Layered Application Architecture

The platform is designed around 5 coordinated layers:

```
[Layer 1: Security & Identity Gateway]
   ├── Two-Step Verification (2FA / 6-Digit Authenticator)
   └── Session Entry Audit Logging (LOGIN_ENTRY with exact UTC timestamp)
           │
[Layer 2: Role-Adaptive Interface & Guidance]
   ├── Personalized Interactive Tutorial Walkthrough (Doctor, Paramedic, Nurse, etc.)
   └── Strict Role-Based Access Control (RBAC) Portals
           │
[Layer 3: Agentic Clinical Core]
   ├── Deterministic Multi-Agent Orchestration (Patient Data, Documentation, Validation)
   ├── Cross-Department Data Synthesis & Discrepancy Detection
   └── Mandatory Physician Attestation Barrier
           │
[Layer 4: Automated Data Ingestion & Storage Sync]
   ├── Unstructured Document Normalization (PDF-to-Text Clinical Extraction)
   └── 1-Click Automated Database Synchronization (8 Connected Departments)
           │
[Layer 5: Provenance, Governance & Exit Auditing]
   ├── Append-Only Non-Manipulable Audit Trail
   └── Session Exit Audit Logging (LOGOUT_EXIT with elapsed session duration)
```

---

## 3. Key Features & Recent Enhancements

### 1. Two-Step Verification (2FA) & Privacy Gateway
- Enforces a high-security Two-Step Verification workflow during authentication.
- **Step 1:** Primary credentials verification (Username & Password).
- **Step 2:** 6-digit security code challenge sent to user's masked healthcare contact (`+1 (***) ***-XX21`).
- Evaluator-friendly: Includes a **⚡ One-Click Auto-Fill Code** button to instantly populate the active test passcode (`849204` or session code).

### 2. Session Entry & Exit Tracking in Audit Trail
- **Time of Entry (Login):** Automatically recorded as `LOGIN_ENTRY` with UTC timestamp and 2FA verification status.
- **Time of Exit (Logout):** Recorded as `LOGOUT_EXIT`. The backend automatically calculates total elapsed session duration (`Xm Ys`) by cross-referencing the entry timestamp.
- **Audit Trail UI:** Clearly highlights green `🟢 ENTRY (Login)` and purple `🔴 EXIT (Logout)` badges with live duration tags directly in the table.

### 3. Role-Tailored Interactive Tutorial Modal
- Automatically launches upon login, providing a personalized walkthrough tailored to each user's specific role:
  - **Doctor:** Cross-department records, AI document preparation, mandatory physician sign-off, personal audit logs.
  - **Paramedic:** Field triage lookup, clinical summary editing, extreme emergency direct issuance protocol, EMS audit log.
  - **Nurse:** Bedside vitals monitoring, medication conflict alerts, shift duration audits.
  - **Pharmacist:** Cross-department prescription reconciliation and patient medication advisories.
  - **Radiologist:** Diagnostic imaging ingestion and report linking.
  - **Hospital Administrator:** 1-Click database sync, system-wide master audit trail, RBAC boundaries.
  - **Patient:** Reconciled health record and physician-approved discharge instructions.
- Can be re-opened anytime by clicking the **Workflow Tutorial** button in the top navigation bar.

### 4. Interactive Modern Clinical Color Theme
- Revamped design system featuring a high-contrast clinical palette:
  - **Primary Navy:** `#0F172A` (Rich Slate 900)
  - **Clinical Azure:** `#0284C7` (Interactive Sky / Primary Actions)
  - **Emerald Green:** `#059669` (Validated & Approved States)
  - **Clean Background:** `#F8FAFC`
- Interactive card lift hover states, smooth transitions, and distinct badge styling.

### 5. Streamlined Navigation (Removal of Developer Telemetry)
- Removed the developer "Agent Activity" telemetry tab and activity trace grid from the UI.
- Replaced with the clean **Multi-Layered Architecture Workflow Pipeline**.

### 6. Speech & Voice Command Interface (Challenge D, Page 22)
- Added live Web Speech API speech recognition and natural voice command parsing in the **AI Workflow Hub**.
- Allows users to speak clinical requests aloud: e.g. *"Prepare the discharge summary for patient P001"*.
- Automatically resolves target patient ID (`P001` - `P015`), matches document task, and executes agent drafting.

### 7. Interactive Academic Specification Test Suite (Section 19, Page 16)
- One-click live evaluation of all 6 test cases mandated by Page 16 of the reference document via the **Spec Tests (6)** button:
  1. **Test Case 1:** Normal Data (Consistent Sources)
  2. **Test Case 2:** Different Patient Names (Fuzzy Matching across Ravi Kumar, R. Kumar, Ravi K., RAVI KUMAR)
  3. **Test Case 3:** Duplicate Record Detection (Identical lab timestamps / prescriptions)
  4. **Test Case 4:** Missing Information Handling (Omitted medication/demographic flags)
  5. **Test Case 5:** Conflicting Information (BP = 120/80 vs 160/100)
  6. **Test Case 6:** Incorrect Generated Information (Validation Agent catches hallucinated medication e.g. Insulin vs Metformin)

### 8. MSc Viva Defense Guide & Questions (Section 25, Page 22-23)
- Embedded interactive examination guide directly in the top navigation bar via the **Viva Guide** button.
- Comprehensive academic answers to all 21 viva defense questions categorized by architecture, agent design, matching algorithms, safety, and offline LAN operations.

### 9. Document Normalization & 1-Click Automated Database Update
- **PDF Normalization:** Automatically parses unstructured PDF uploads, removes formatting noise, and extracts clinical entities (Vitals, Lab panels, Medications).
- **1-Click Database Synchronization:** Updates central relational tables (`laboratory_records`, `pharmacy_records`, `nursing_records`, `radiology_records`, `inpatient_records`, etc.) with automated patient reconciliation.

---

## 4. Default Demo Accounts

Quick-fill account buttons are available directly on the login screen:

| Role | Username | Password | Full Name & Title | Access & Permissions |
| :--- | :--- | :--- | :--- | :--- |
| **Doctor** | `doctor.smith` | `DoctorPass123!` | Dr. Sarah Smith, MD | Full clinical generation, editing, approval, personal audit |
| **Paramedic** | `paramedic.alex` | `ParamedicPass123!` | Alex Rivera, EMT-P | Summary editing, emergency direct issue, personal audit |
| **Nurse** | `nurse.clara` | `NursePass123!` | Clara Barton, RN | Inpatient vitals, nursing logs, personal audit |
| **Pharmacist** | `pharm.david` | `PharmPass123!` | David Vance, PharmD | Dispensing records, pharmacy alerts |
| **Radiologist** | `rad.elena` | `RadPass123!` | Dr. Elena Rostova, MD | Diagnostic imaging findings, radiology alerts |
| **Administrator** | `admin.hospiq` | `AdminPass123!` | Executive Administrator | Full master audit trail, database sync, system metrics |
| **Patient** | `patient.ravi` | `PatientPass123!` | Ravi Kumar (P001) | Read-only unified health record, personal summaries |

---

## 5. How to Run the Application

The application uses a **single-command unified server** where FastAPI serves both the React production frontend and the API backend simultaneously on port 8000.

### Step 1: Install Dependencies (if not already done)
```bash
pip install -r requirements.txt
npm --prefix frontend install
npm --prefix frontend run build
```

### Step 2: Start the Unified Application
Run either:
```bash
python run.py
```
*Or on Windows, double-click:*
```bash
start_hospiq.bat
```

### Step 3: Access the Application
- **Web Application:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive Swagger Docs:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 6. Verification Walkthrough

1. **Verify Two-Step Verification (2FA):**
   - Navigate to [http://127.0.0.1:8000](http://127.0.0.1:8000).
   - Click `Doctor (Dr. Sarah Smith)` on the quick role switcher, then click **Continue to 2-Step Verification**.
   - Notice Step 2 opens showing masked contact `+1 (***) ***-8921`.
   - Click **⚡ One-Click Auto-Fill Code** (or enter `849204`) and click **Verify & Enter HOSPIQ**.

2. **Verify Personalized Role-Based Tutorial:**
   - Immediately upon login, the **Physician / Doctor Portal Personalized Guide** modal appears.
   - Walk through the 4 steps (`Patient Context` → `Clinical Drafting` → `Clinical Sign-off` → `Security & Provenance`).
   - Close the modal, then click **Workflow Tutorial** in the top navbar to verify it can be reopened anytime.

3. **Verify Entry & Exit Session Tracking in Audit Trail:**
   - Click on the **Audit Trail** tab in the sidebar.
   - Observe the top row: `🟢 ENTRY (Login)` badge showing the exact timestamp of your login.
   - Click **Logout** in the top navbar.
   - Log in again (or as `admin.hospiq` / `AdminPass123!`).
   - In the Audit Trail, observe the `🔴 EXIT (Logout)` event showing the calculated **Total Session Duration** (e.g. `Duration: 1m 24s`) and exact exit timestamp.

4. **Verify Removal of "Agent Activity":**
   - Confirm the sidebar has NO "Agent Activity" tab.
   - In the **AI Workflow Hub**, observe the clean **Multi-Layered System Pipeline** replacing developer telemetry.

---
*Agentic Hospital Management System — Academic Postgraduate MSc Health Informatics and Analytics Project.*
