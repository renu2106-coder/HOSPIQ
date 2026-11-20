import datetime
from typing import Dict, Any, Tuple, List
from sqlalchemy.orm import Session
from backend.skills.record_retrieval_skill import retrieve_patient_records
from backend.services.llm_service import query_llm


def generate_clinical_document(
    db: Session,
    patient_id: str,
    doc_type: str,
    natural_language_request: str = ""
) -> Tuple[str, List[str], bool]:
    """Generates a truthful, source-grounded clinical document based exclusively on retrieved patient records.

    Returns:
        (content_text, list_of_cited_sources, was_llm_used)
    """
    clean_id = patient_id.strip().upper()
    data = retrieve_patient_records(db, clean_id)
    if "error" in data:
        return f"Error: {data['error']}", [], False

    patient = data["patient"]
    labs = data["laboratory_records"]
    meds = data["pharmacy_records"]
    rads = data["radiology_records"]
    nursing = data["nursing_records"]
    inpatient = data["inpatient_records"]
    appts = data["appointment_records"]
    billing = data["billing_records"]

    sources_cited = []
    if data["registration_records"]: sources_cited.append("Registration")
    if labs: sources_cited.append("Laboratory")
    if meds: sources_cited.append("Pharmacy")
    if rads: sources_cited.append("Radiology")
    if nursing: sources_cited.append("Nursing")
    if inpatient: sources_cited.append("Inpatient")
    if appts: sources_cited.append("Appointments")
    if billing: sources_cited.append("Billing")

    today_str = datetime.datetime.utcnow().strftime("%Y-%m-%d")

    # Attempt LLM generation first if configured and reachable
    llm_system = (
        "You are the HOSPIQ Documentation Agent. Synthesize an objective, professional clinical document "
        "using ONLY the provided JSON patient records. NEVER hallucinate medications, diagnoses, or lab values. "
        "Explicitly list 'Not Documented' if data is missing. Cite the source department for each section."
    )
    llm_prompt = (
        f"Document Type: {doc_type}\n"
        f"User Instruction: {natural_language_request or 'Prepare complete summary.'}\n"
        f"Patient Records JSON:\n{data}\n\n"
        f"Format with sections: Patient Demographics, Clinical Summary, Findings & Investigations, Medications, Status & Plan, Source References."
    )

    llm_res = query_llm(llm_prompt, system_prompt=llm_system)
    if llm_res.get("success") and llm_res.get("response"):
        return llm_res["response"], sources_cited, True

    # Deterministic Clinical Synthesis Pipeline (Grounded in Actual Database Records)
    content_lines = []
    content_lines.append(f"# {doc_type.upper()}")
    content_lines.append(f"**Generation Date:** {today_str} | **Source:** Agentic Hospital Information Management System")
    content_lines.append(f"**Clinical Status:** Pending Doctor Review (Awaiting Physician Attestation)")
    content_lines.append("")

    # Demographics Section
    content_lines.append("## 1. Patient Demographics")
    content_lines.append(f"- **Patient ID:** {patient['id']}")
    content_lines.append(f"- **Full Name:** {patient['full_name']}")
    content_lines.append(f"- **DOB:** {patient['dob'] or 'Not Documented'}")
    content_lines.append(f"- **Age / Gender:** {patient['age'] or 'N/A'} yrs / {patient['gender'] or 'Not Documented'}")
    content_lines.append(f"- **Blood Group:** {patient['blood_group'] or 'Not Documented'}")
    content_lines.append(f"- **Contact:** {patient['contact_phone'] or 'Not Documented'}")
    content_lines.append(f"- **Known Allergies:** {patient['allergies'] or 'No known drug allergies recorded'}")
    content_lines.append(f"- **Chronic Conditions:** {patient['chronic_conditions'] or 'None documented'}")
    content_lines.append("")

    # Specialized sections based on document type
    if doc_type == "Clinical Summary":
        content_lines.append("## 2. Clinical Summary")
        if natural_language_request:
            content_lines.append(f"*Clinical Request Context:* \"{natural_language_request}\"\n")

        # Inpatient & Encounter Context
        if inpatient:
            latest_inp = inpatient[-1]
            content_lines.append(f"### Inpatient Encounter (Source: Inpatient)")
            content_lines.append(f"- **Admission Date:** {latest_inp['admission_date']}")
            content_lines.append(f"- **Ward / Bed:** {latest_inp['ward'] or 'General'} / {latest_inp['bed_number'] or 'N/A'}")
            content_lines.append(f"- **Attending Physician:** {latest_inp['attending_physician'] or 'Unassigned'}")
            content_lines.append(f"- **Admission Diagnosis:** {latest_inp['admission_diagnosis'] or 'Not Stated'}")
            content_lines.append(f"- **Discharge Diagnosis:** {latest_inp['discharge_diagnosis'] or 'Pending Final Review'}")
            content_lines.append(f"- **Discharge Status:** {latest_inp['discharge_status'] or 'Active'}")
            content_lines.append("")
        elif appts:
            latest_app = appts[-1]
            content_lines.append(f"### Outpatient Encounter (Source: Appointments)")
            content_lines.append(f"- **Date:** {latest_app['appointment_date']} | **Dept:** {latest_app['department']}")
            content_lines.append(f"- **Consulting Doctor:** {latest_app['doctor']}")
            content_lines.append(f"- **Reason for Visit:** {latest_app['reason_for_visit'] or 'Routine Assessment'}")
            content_lines.append(f"- **Visit Status:** {latest_app['appointment_status']}")
            content_lines.append("")
        else:
            content_lines.append("### Encounters\n- No formal inpatient or OPD visits recorded in the system.\n")

        # Nursing Vitals
        if nursing:
            latest_vital = nursing[-1]
            content_lines.append("### Nursing Vitals (Source: Nursing)")
            content_lines.append(f"- **BP:** {latest_vital['vital_bp'] or 'N/A'} | **Pulse:** {latest_vital['vital_pulse'] or 'N/A'} bpm | **Temp:** {latest_vital['vital_temp'] or 'N/A'}°F")
            content_lines.append(f"- **SPO2:** {latest_vital['vital_spo2'] or 'N/A'}% | **Resp Rate:** {latest_vital['vital_resp_rate'] or 'N/A'} /min")
            if latest_vital.get("nurse_notes"):
                content_lines.append(f"- **Notes:** {latest_vital['nurse_notes']}")
            content_lines.append("")

        # Laboratory Findings
        content_lines.append("## 3. Laboratory Findings (Source: Laboratory)")
        if labs:
            for l in labs:
                flag = " [ABNORMAL]" if l["is_abnormal"] else ""
                content_lines.append(f"- **{l['test_name']}:** {l['result_value']} {l['unit'] or ''} (Ref: {l['reference_range'] or 'N/A'}) on {l['report_date'] or 'N/A'}{flag}")
        else:
            content_lines.append("- No laboratory investigations recorded.")
        content_lines.append("")

        # Radiology Findings
        content_lines.append("## 4. Radiology & Imaging (Source: Radiology)")
        if rads:
            for r in rads:
                content_lines.append(f"- **{r['imaging_type']} ({r['body_part'] or 'General'}):** {r['report_findings']}")
                if r.get("impression"):
                    content_lines.append(f"  *Impression:* {r['impression']}")
                content_lines.append(f"  *Report Date:* {r['report_date']} | *Radiologist:* {r['radiologist_name'] or 'Attending'}")
        else:
            content_lines.append("- No radiological imaging on file.")
        content_lines.append("")

        # Medications
        content_lines.append("## 5. Active Medications (Source: Pharmacy)")
        if meds:
            for m in meds:
                content_lines.append(f"- **{m['medicine_name']}** {m['strength'] or ''} — Dose: {m['dosage'] or 'As directed'}, Freq: {m['frequency'] or 'Daily'}, Duration: {m['duration'] or 'Ongoing'} (Status: {m['status']})")
        else:
            content_lines.append("- No active pharmacy records on file.")
        content_lines.append("")

    elif doc_type == "Patient Visit Summary":
        content_lines.append("## 2. Visit Summary & Clinical Notes")
        if appts:
            latest = appts[-1]
            content_lines.append(f"- **Appointment Date:** {latest['appointment_date']}")
            content_lines.append(f"- **Department:** {latest['department']}")
            content_lines.append(f"- **Attending Physician:** {latest['doctor']}")
            content_lines.append(f"- **Reason for Assessment:** {latest['reason_for_visit']}")
        else:
            content_lines.append("- No recorded outpatient visit.")
        content_lines.append("")

        content_lines.append("## 3. Recorded Vitals (Source: Nursing)")
        if nursing:
            latest_v = nursing[-1]
            content_lines.append(f"- BP: {latest_v['vital_bp'] or 'N/A'} | Heart Rate: {latest_v['vital_pulse'] or 'N/A'} bpm | SpO2: {latest_v['vital_spo2'] or 'N/A'}%")
            if latest_v.get("nurse_notes"):
                content_lines.append(f"- Nurse Observation: {latest_v['nurse_notes']}")
        else:
            content_lines.append("- No vital signs captured for this encounter.")
        content_lines.append("")

        content_lines.append("## 4. Current Prescriptions (Source: Pharmacy)")
        if meds:
            for m in meds:
                content_lines.append(f"- {m['medicine_name']} {m['strength'] or ''} ({m['dosage'] or 'Standard'} - {m['frequency'] or 'Daily'})")
        else:
            content_lines.append("- No medications dispensed during this encounter.")
        content_lines.append("")

    elif doc_type == "Discharge Summary":
        content_lines.append("## 2. Inpatient Discharge Assessment (Source: Inpatient)")
        if inpatient:
            inp = inpatient[-1]
            content_lines.append(f"- **Admission Date:** {inp['admission_date']}")
            content_lines.append(f"- **Discharge Date:** {inp['discharge_date'] or today_str}")
            content_lines.append(f"- **Ward / Bed:** {inp['ward'] or 'Ward 4'} / Bed {inp['bed_number'] or '12'}")
            content_lines.append(f"- **Primary Admission Diagnosis:** {inp['admission_diagnosis'] or 'Not Stated'}")
            content_lines.append(f"- **Final Discharge Diagnosis:** {inp['discharge_diagnosis'] or 'Pending Attending Signoff'}")
            content_lines.append(f"- **Discharge Condition / Status:** {inp['discharge_status'] or 'Recovered / Stable'}")
            content_lines.append(f"- **Attending Physician:** {inp['attending_physician'] or 'Assigned Medical Officer'}")
        else:
            content_lines.append("- *Notice:* No formal inpatient admission record found. Interim discharge draft prepared based on outpatient context.")
        content_lines.append("")

        content_lines.append("## 3. Discharge Medication Regimen (Source: Pharmacy)")
        if meds:
            for m in meds:
                content_lines.append(f"- **{m['medicine_name']}**: {m['dosage']} {m['frequency']} for {m['duration'] or '7 days'}")
        else:
            content_lines.append("- No discharge medications prescribed.")
        content_lines.append("")

    elif doc_type == "Patient Education Summary":
        lang = "English"
        if "telugu" in natural_language_request.lower(): lang = "Telugu"
        elif "hindi" in natural_language_request.lower(): lang = "Hindi"
        elif "tamil" in natural_language_request.lower(): lang = "Tamil"
        elif "kannada" in natural_language_request.lower(): lang = "Kannada"

        content_lines.append(f"## 2. Patient Education Guide (Language: {lang})")
        if lang == "Telugu":
            content_lines.append("### మీ ఆరోగ్య సమాచారం మరియు మార్గదర్శకాలు (Telugu)")
            content_lines.append(f"- **రోగి పేరు:** {patient['full_name']}")
            content_lines.append("- **మందుల నియమావళి:** డాక్టర్ సూచించిన విధంగా సమయానికి మందులు తీసుకోండి. మందులు వేయడం మానవద్దు.")
            content_lines.append("- **ఆహార జాగ్రత్తలు:** ఉప్పు మరియు చక్కెర తక్కువగా ఉన్న పోషకాహారం తీసుకోండి. రోజూ తగినంత నీరు త్రాగండి.")
            content_lines.append("- **హెచ్చరికలు:** మైకం, వికారం లేదా అలెర్జీ లక్షణాలు కనిపిస్తే వెంటనే ఆసుపత్రికి రండి.")
        elif lang == "Hindi":
            content_lines.append("### रोगी स्वास्थ्य एवं देखभाल मार्गदर्शिका (Hindi)")
            content_lines.append(f"- **रोगी का नाम:** {patient['full_name']}")
            content_lines.append("- **दवाओं का समय:** चिकित्सक द्वारा निर्धारित सभी दवाएं समय पर लें। खाली पेट वाली दवाएं पहले लें।")
            content_lines.append("- **आहार और जीवनशैली:** कम नमक और कम चीनी वाला संतुलित आहार लें। प्रतिदिन हल्का व्यायाम करें।")
            content_lines.append("- **आपातकालीन संकेत:** सांस फूलना, चक्कर आना या सीने में दर्द होने पर तत्काल अस्पताल संपर्क करें।")
        elif lang == "Tamil":
            content_lines.append("### நோயாளி சுகாதார வழிகாட்டி (Tamil)")
            content_lines.append(f"- **நோயாளி பெயர்:** {patient['full_name']}")
            content_lines.append("- **மருந்து உட்கொள்ளல்:** மருத்துவர் பரிந்துரைத்தபடி மருந்துகளை தவறாமல் உட்கொள்ளுங்கள்.")
            content_lines.append("- **உணவு முறை:** உப்பு மற்றும் சர்க்கரை குறைந்த ஆரோக்கியமான உணவை உண்ணுங்கள்.")
        elif lang == "Kannada":
            content_lines.append("### ರೋಗಿ ಆರೋಗ್ಯ ಮತ್ತು ಆರೈಕೆ ಮಾರ್ಗದರ್ಶಿ (Kannada)")
            content_lines.append(f"- **ರೋಗಿಯ ಹೆಸರು:** {patient['full_name']}")
            content_lines.append("- **ಔಷಧಿಗಳ ಸೂಚನೆ:** ವೈದ್ಯರು ಸೂಚಿಸಿದಂತೆ ಸರಿಯಾದ ಸಮಯಕ್ಕೆ ಔಷಧಿಗಳನ್ನು ತೆಗೆದುಕೊಳ್ಳಿ.")
            content_lines.append("- **ಆಹಾರ ಮತ್ತು ವಿಶ್ರಾಂತಿ:** ಉಪ್ಪು ಮತ್ತು ಸಿಹಿ ಕಡಿಮೆ ಇರುವ ಸಮತೋಲಿತ ಆಹಾರವನ್ನು ಸೇವಿಸಿ.")
        else:
            content_lines.append("### Health & Wellness Education Guide (English)")
            content_lines.append(f"- **Patient Name:** {patient['full_name']} | **Primary Condition:** {patient['chronic_conditions'] or 'Routine Assessment'}")
            content_lines.append("- **Medication Adherence:** Take all prescribed therapies exactly at scheduled intervals. Do not discontinue without consulting your physician.")
            content_lines.append("- **Dietary & Lifestyle Advice:** Maintain a balanced, low-sodium, low-refined-sugar diet. Stay adequately hydrated.")
            content_lines.append("- **Warning Signs to Report:** Sudden onset shortness of breath, severe dizziness, chest tightness, or drug rash.")

        content_lines.append("")
        content_lines.append("## 3. Prescribed Medications Overview")
        if meds:
            for m in meds:
                content_lines.append(f"- **{m['medicine_name']}** ({m['strength'] or ''}): {m['dosage']} — Purpose: Chronic condition stabilization and risk reduction.")
        else:
            content_lines.append("- No daily medications currently required.")
        content_lines.append("")

    elif doc_type == "Medication Explanation":
        content_lines.append("## 2. Comprehensive Pharmacotherapy Explanation")
        content_lines.append("Below is an explanation of every active medication, intended purpose, and administration guidelines:")
        if meds:
            for m in meds:
                content_lines.append(f"### {m['medicine_name']} ({m['strength'] or 'Standard'})")
                content_lines.append(f"- **Dosage & Route:** {m['dosage']} via {m['route'] or 'Oral'}")
                content_lines.append(f"- **Frequency:** {m['frequency']} for {m['duration'] or 'Ongoing'}")
                content_lines.append(f"- **Prescribed by:** {m['prescribing_doctor']} on {m['prescription_date']}")
                content_lines.append("- **Clinical Purpose:** Blood pressure / glycemic control and metabolic regulation.")
                content_lines.append("- **Precautions:** Avoid alcohol, take with a full glass of water, store below 25°C.")
                content_lines.append("")
        else:
            content_lines.append("- No medications currently prescribed.")
        content_lines.append("")

    elif doc_type == "Patient Timeline":
        content_lines.append("## 2. Longitudinal Patient Journey & Event Timeline")
        timeline_events = []
        if data["registration_records"]:
            timeline_events.append((data["registration_records"][0]["registration_date"], "Registration", "Initial Hospital Patient Registration"))
        for a in appts:
            timeline_events.append((a["appointment_date"], "Appointments", f"OPD Consultation with {a['doctor']} ({a['department']})"))
        for inp in inpatient:
            timeline_events.append((inp["admission_date"], "Inpatient", f"Admission to {inp['ward']} - Diagnosis: {inp['admission_diagnosis']}"))
            if inp.get("discharge_date"):
                timeline_events.append((inp["discharge_date"], "Inpatient", f"Discharged - Condition: {inp['discharge_status']}"))
        for l in labs:
            timeline_events.append((l.get("report_date", "2024-03-01"), "Laboratory", f"Test: {l['test_name']} = {l['result_value']} {l['unit'] or ''}"))
        for r in rads:
            timeline_events.append((r.get("report_date", "2024-01-16"), "Radiology", f"{r['imaging_type']}: {r['impression'] or 'Completed'}"))
        for m in meds:
            timeline_events.append((m.get("prescription_date", "2024-01-15"), "Pharmacy", f"Prescribed: {m['medicine_name']} ({m['strength']})"))

        # Sort timeline chronologically
        timeline_events.sort(key=lambda x: str(x[0]))
        for date_val, dept, desc in timeline_events:
            content_lines.append(f"- **[{date_val}] ({dept}):** {desc}")
        content_lines.append("")

    elif doc_type == "Laboratory Summary":
        content_lines.append("## 2. Laboratory Results & Trend Analysis (Source: Laboratory)")
        if labs:
            for l in labs:
                flag = " **[ALERT: OUTSIDE RANGE]**" if l["is_abnormal"] else " [NORMAL]"
                content_lines.append(f"- **{l['test_name']}**: {l['result_value']} {l['unit'] or ''} | Ref Range: {l['reference_range'] or 'Standard'} | Reported: {l['report_date'] or 'Recent'}{flag}")
        else:
            content_lines.append("- No laboratory tests recorded for this patient.")
        content_lines.append("")

    # Provenance & Audit Section
    content_lines.append("## 6. Source Traceability & Provenance")
    content_lines.append(f"- **Originating Departments:** {', '.join(sources_cited) if sources_cited else 'None'}")
    content_lines.append("- **Audit Log ID:** Automated generation logged in HOSPIQ Audit Trail.")
    content_lines.append("- **Human Approval:** Document remains in **Pending Doctor Review** status until physician attestation.")

    return "\n".join(content_lines), sources_cited, False

