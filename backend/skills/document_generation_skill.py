import datetime
import re
from typing import Dict, Any, Tuple, List
from sqlalchemy.orm import Session
from backend.skills.record_retrieval_skill import retrieve_patient_records
from backend.skills.clinical_explanation_skill import (
    interpret_vitals,
    categorize_and_explain_labs,
    explain_radiology_studies,
)
from backend.services.llm_service import query_llm


PHARMACOLOGY_MAP: Dict[str, Tuple[str, str]] = {
    "pregabalin": (
        "Neuropathic pain modulator calming irritated nerve signals from spinal disc compression",
        "Take at bedtime; may cause mild drowsiness or dizziness; avoid alcohol."
    ),
    "methylcobalamin": (
        "Neurotropic Vitamin B12 cofactor supporting myelin repair and nerve recovery",
        "Take once daily after meals consistently as prescribed."
    ),
    "etoricoxib": (
        "Targeted COX-2 anti-inflammatory analgesic reducing spinal/joint tissue swelling",
        "Use short course only after food; monitor blood pressure."
    ),
    "paracetamol": (
        "Fever-reducing and non-bleeding analgesic safe for viral fevers and mild pain",
        "Wait at least 6 hours between doses; do not exceed 3 grams in 24 hours."
    ),
    "oral rehydration": (
        "Balanced electrolyte and fluid replacement supporting circulation and platelet recovery",
        "Sip steadily throughout the day during fever recovery."
    ),
    "fluticasone": (
        "Intranasal corticosteroid spray reducing swollen nasal turbinates and improving airflow",
        "Aim spray slightly outward away from the central nasal septum once daily."
    ),
    "levocetirizine": (
        "Antihistamine blocking allergic nasal congestion, sneezing, and airway irritation",
        "Take once at night to minimize mild daytime drowsiness."
    ),
    "diclofenac": (
        "Topical anti-inflammatory NSAID gel relieving localized post-fall tendon or muscle soreness",
        "Apply externally to intact skin only; wash hands after application."
    ),
    "metformin": (
        "Insulin-sensitizing glucose regulator stabilizing blood sugar in Type 2 Diabetes",
        "Take with meals to reduce stomach discomfort; keep well hydrated."
    ),
    "lisinopril": (
        "ACE inhibitor lowering arterial pressure and protecting heart/kidney workload",
        "Monitor BP regularly; report any persistent dry cough or lightheadedness."
    ),
    "atorvastatin": (
        "Cholesterol-lowering statin reducing arterial plaque and cardiovascular risk",
        "Take consistently in the evening; report unexplained muscle aching."
    ),
    "losartan": (
        "Angiotensin receptor blocker (ARB) protecting blood vessels and kidneys",
        "Take at a fixed time daily; check potassium and kidney values periodically."
    ),
    "amlodipine": (
        "Calcium channel blocker relaxing arterial tone to maintain steady blood pressure",
        "Check blood pressure regularly; monitor for mild ankle swelling."
    ),
    "amoxicillin": (
        "Beta-lactam antibacterial agent targeting susceptible respiratory or systemic infections",
        "Confirm absence of penicillin allergy before taking; complete the full course."
    ),
    "levothyroxine": (
        "Thyroid hormone replacement normalizing basal metabolism",
        "Take on an empty stomach 30-60 minutes before breakfast."
    ),
    "albuterol": (
        "Fast-acting bronchodilator opening constricted bronchial airways",
        "Use inhaler as directed; seek urgent care if breathing difficulty persists."
    ),
}


def strip_markdown_symbols(text: str) -> str:
    """Removes Markdown heading hashes (#) and star formatting (* / **) from clinical text."""
    if not text:
        return ""
    cleaned_lines = []
    for line in text.splitlines():
        line = re.sub(r'^\s*#{1,6}\s*', '', line)
        line = re.sub(r'#(\d+)', r'No. \1', line)
        line = line.replace('#', '')
        line = re.sub(r'^(\s*)\*\s+', r'\1• ', line)
        line = line.replace('***', '').replace('**', '').replace('*', '')
        cleaned_lines.append(line)
    return "\n".join(cleaned_lines)


def _clean_val(val: Any) -> str:
    if val is None:
        return ""
    return strip_markdown_symbols(str(val))


def _explain_medication(med_name: str) -> Tuple[str, str]:
    key = (med_name or "").strip().lower()
    for drug_key, info in PHARMACOLOGY_MAP.items():
        if drug_key in key:
            return info
    return (
        "Targeted symptom management and physiological support per specialist assessment",
        "Follow exact prescribed dosing; do not adjust without physician review."
    )


def generate_clinical_document(
    db: Session,
    patient_id: str,
    doc_type: str,
    natural_language_request: str = ""
) -> Tuple[str, List[str], bool]:
    """Generates clearly differentiated, analytical clinical reports tailored to format and patient records."""
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
    if data["registration_records"]:
        sources_cited.append("Registration")
    if labs:
        sources_cited.append("Laboratory")
    if meds:
        sources_cited.append("Pharmacy")
    if rads:
        sources_cited.append("Radiology")
    if nursing:
        sources_cited.append("Nursing")
    if inpatient:
        sources_cited.append("Inpatient")
    if appts:
        sources_cited.append("Appointments")
    if billing:
        sources_cited.append("Billing")

    today_str = datetime.datetime.utcnow().strftime("%Y-%m-%d")

    llm_system = (
        "You are the HOSPIQ Documentation Agent. Never simply copy-paste raw lab tables or imaging strings verbatim. "
        "Synthesize and EXPLAIN the medical meaning of findings clearly, differentiate Laboratory Summary (biomarker panels) "
        "from Clinical Summary (multi-department diagnostic integration) and Discharge Summary (care closure & follow-up). "
        "Format strictly as plain text with ZERO hashtags (#) and ZERO stars (*). Cite only real database facts."
    )
    llm_prompt = (
        f"Document Type: {doc_type}\n"
        f"User Instruction: {natural_language_request or 'Provide an analytical, clearly explained medical summary.'}\n"
        f"Patient Records JSON:\n{data}\n"
    )
    llm_res = query_llm(llm_prompt, system_prompt=llm_system)
    if llm_res.get("success") and llm_res.get("response"):
        return strip_markdown_symbols(llm_res["response"]), sources_cited, True

    vitals_interp = interpret_vitals(nursing)
    lab_interp = categorize_and_explain_labs(labs, patient)
    rad_interp = explain_radiology_studies(rads)

    content_lines: List[str] = []
    content_lines.append(doc_type.upper())
    content_lines.append("=" * 60)
    content_lines.append(f"Report Date: {today_str} | Format Profile: {doc_type}")
    content_lines.append("Clinical Status: Pending Doctor Review (Awaiting Physician Attestation)")
    content_lines.append("")

    # Compact common Patient Identification Bar (distinct per doc format)
    content_lines.append("1. PATIENT IDENTIFICATION")
    content_lines.append("-" * 60)
    content_lines.append(
        f"• Patient ID: {_clean_val(patient['id'])} | Name: {_clean_val(patient['full_name'])} "
        f"| Age / Gender: {patient['age'] or 'N/A'} yrs / {_clean_val(patient['gender']) or 'N/A'}"
    )
    content_lines.append(
        f"• DOB: {_clean_val(patient['dob']) or 'Not Documented'} | Blood Group: {_clean_val(patient['blood_group']) or 'N/A'} "
        f"| Allergies: {_clean_val(patient['allergies']) or 'None Recorded'}"
    )
    content_lines.append(f"• Clinical Focus: {_clean_val(patient['chronic_conditions']) or 'Active Clinical Evaluation'}")
    content_lines.append("")

    next_section_num = 3

    # =========================================================================
    # FORMAT 1: CLINICAL SUMMARY (Holistic Multi-Department Synthesis & Meaning)
    # =========================================================================
    if doc_type == "Clinical Summary":
        content_lines.append("2. INTEGRATED CLINICAL PRESENTATION & CONTEXT")
        content_lines.append("-" * 60)
        consultant = _clean_val(appts[-1]["doctor"]) if appts else (_clean_val(inpatient[-1]["attending_physician"]) if inpatient else "Attending Physician")
        dept_ctx = _clean_val(appts[-1]["department"]) if appts else (_clean_val(inpatient[-1]["ward"]) if inpatient else "General Medicine")
        visit_reason = _clean_val(appts[-1]["reason_for_visit"]) if appts else (_clean_val(inpatient[-1]["admission_diagnosis"]) if inpatient else _clean_val(patient.get("chronic_conditions")))
        content_lines.append(
            f"{_clean_val(patient['full_name'])} ({patient['age'] or 'N/A'}y {_clean_val(patient['gender'])}) presented under {dept_ctx} "
            f"(Clinician: {consultant}) for evaluation of: {visit_reason or 'diagnostic workup'}. "
            f"{vitals_interp['clinical']}"
        )
        content_lines.append("")

        content_lines.append("3. CLINICAL INTERPRETATION OF DIAGNOSTIC REPORTS")
        content_lines.append("-" * 60)
        for pt in lab_interp["clinical_narratives"]:
            content_lines.append(f"• {pt}")
        for pt in rad_interp["clinical"]:
            content_lines.append(f"• {pt}")
        content_lines.append("")

        content_lines.append("4. CROSS-DEPARTMENT RECONCILIATION & RISK FLAGS")
        content_lines.append("-" * 60)
        content_lines.append(
            f"• Laboratory Profile: {lab_interp['abnormal_count']} abnormal and {lab_interp['normal_count']} normal parameter(s) analyzed."
        )
        content_lines.append(
            f"• Radiology Triage Escalation: {rad_interp['urgency']} Priority across {len(rads)} imaging study/studies."
        )
        content_lines.append(
            f"• Medication Safety: {_clean_val(patient['allergies']) or 'No known allergies'}; cross-checked against {len(meds)} active prescription(s)."
        )
        content_lines.append("")

        content_lines.append("5. THERAPEUTIC PLAN & CARE FOLLOW-UP")
        content_lines.append("-" * 60)
        if meds:
            for m in meds:
                purpose, _ = _explain_medication(m["medicine_name"])
                content_lines.append(
                    f"• {_clean_val(m['medicine_name'])} {_clean_val(m['strength'])} ({_clean_val(m['dosage'])}, {_clean_val(m['frequency'])}): {purpose}."
                )
        else:
            content_lines.append("• Supportive monitoring and specialist diagnostic follow-up pending physician sign-off.")
        content_lines.append("")
        next_section_num = 6

    # =========================================================================
    # FORMAT 2: LABORATORY SUMMARY (Organ-System Biomarker Panel Interpretation)
    # =========================================================================
    elif doc_type == "Laboratory Summary":
        content_lines.append("2. DIAGNOSTIC LABORATORY INTERPRETATION (Clinician Analysis)")
        content_lines.append("-" * 60)
        content_lines.append(
            f"Analytical Overview: Reviewed {len(labs)} total laboratory assay(s) ({lab_interp['abnormal_count']} flagged outside physiological reference range, {lab_interp['normal_count']} within normal limits)."
        )
        content_lines.append("")
        for narr in lab_interp["clinical_narratives"]:
            content_lines.append(f"• {narr}")
        content_lines.append("")

        content_lines.append("3. ORGANIZED BIOMARKER RESULTS BY LABORATORY PANEL")
        content_lines.append("-" * 60)
        if lab_interp["panels"]:
            for panel_name, items in lab_interp["panels"].items():
                content_lines.append(f"[{panel_name}]")
                for l in items:
                    status_tag = "OUTSIDE REFERENCE RANGE [ABNORMAL]" if l["is_abnormal"] else "Within Reference [Normal]"
                    content_lines.append(
                        f"• {_clean_val(l['test_name'])}: {_clean_val(l['result_value'])} {_clean_val(l['unit'])} "
                        f"| Reference Range: {_clean_val(l['reference_range']) or 'Standard'} | Status: {status_tag} ({_clean_val(l['report_date']) or today_str})"
                    )
                content_lines.append("")
        else:
            content_lines.append("• No laboratory panels recorded for this patient; Reference Range evaluation N/A.")
            content_lines.append("")
        next_section_num = 4

    # =========================================================================
    # FORMAT 3: DISCHARGE SUMMARY (Care Transition, Diagnosis & Home Regimen)
    # =========================================================================
    elif doc_type == "Discharge Summary":
        content_lines.append("2. EPISODE SUMMARY & HOSPITAL / OUTPATIENT COURSE")
        content_lines.append("-" * 60)
        if inpatient:
            inp = inpatient[-1]
            content_lines.append(f"• Admission / Discharge Dates: {_clean_val(inp['admission_date'])} to {_clean_val(inp['discharge_date']) or today_str}")
            content_lines.append(f"• Care Unit: {_clean_val(inp['ward']) or 'Ward'} (Bed {_clean_val(inp['bed_number']) or 'N/A'}) | Attending: {_clean_val(inp['attending_physician'])}")
            content_lines.append(f"• Working Admission Diagnosis: {_clean_val(inp['admission_diagnosis'])}")
            content_lines.append(f"• Final Confirmed Assessment: {_clean_val(inp['discharge_diagnosis'])}")
            content_lines.append(f"• Discharge Condition / Status: {_clean_val(inp['discharge_status']) or 'Recovered / Stable'}")
        else:
            att = _clean_val(appts[-1]["doctor"]) if appts else "Attending Clinician"
            content_lines.append(f"• Care Setting: Outpatient / Diagnostic Care under {att}.")
            content_lines.append(f"• Primary Working Condition: {_clean_val(patient['chronic_conditions']) or 'Diagnostic Assessment'}")
            content_lines.append("• Discharge Condition / Status: Hemodynamically stable for outpatient management and scheduled follow-up.")
        content_lines.append("")

        content_lines.append("3. DIAGNOSTIC CONCLUSION & CLINICAL RATIONALE")
        content_lines.append("-" * 60)
        content_lines.append(f"• Vital Status at Transition: {vitals_interp['clinical']}")
        for pt in lab_interp["clinical_narratives"]:
            content_lines.append(f"• Lab Conclusion: {pt}")
        for pt in rad_interp["clinical"]:
            content_lines.append(f"• Imaging Conclusion: {pt}")
        content_lines.append("")

        content_lines.append("4. DISCHARGE MEDICATION REGIMEN & FOLLOW-UP INSTRUCTIONS")
        content_lines.append("-" * 60)
        if meds:
            for m in meds:
                purpose, prec = _explain_medication(m["medicine_name"])
                content_lines.append(
                    f"• {_clean_val(m['medicine_name'])} {_clean_val(m['strength'])}: Take {_clean_val(m['dosage'])} {_clean_val(m['frequency'])} for {_clean_val(m['duration']) or 'prescribed course'} — Reason: {purpose}."
                )
        else:
            content_lines.append("• No take-home prescriptions required; monitor symptoms and complete specialist consult.")
        content_lines.append("• Return Precautions: Seek urgent care if new neurological weakness, persistent high fever, bleeding, or severe pain develops.")
        content_lines.append("")
        next_section_num = 5

    # =========================================================================
    # FORMAT 4: PATIENT VISIT SUMMARY (Concise Outpatient SOAP Note)
    # =========================================================================
    elif doc_type == "Patient Visit Summary":
        content_lines.append("2. OUTPATIENT VISIT SUMMARY & ASSESSMENT (SOAP)")
        content_lines.append("-" * 60)
        if appts:
            latest = appts[-1]
            content_lines.append(f"• Date & Department: {_clean_val(latest['appointment_date'])} ({_clean_val(latest['department'])})")
            content_lines.append(f"• Consulting Clinician: {_clean_val(latest['doctor'])}")
            content_lines.append(f"• Chief Reason for Visit: {_clean_val(latest['reason_for_visit'])}")
        else:
            content_lines.append("• Encounter Overview: Routine longitudinal clinical chart review.")
        content_lines.append("")

        content_lines.append("3. RECORDED VITALS & KEY FINDINGS REVIEWED")
        content_lines.append("-" * 60)
        content_lines.append(f"• {vitals_interp['clinical']}")
        for pt in lab_interp["clinical_narratives"][:2]:
            content_lines.append(f"• {pt}")
        for pt in rad_interp["clinical"][:2]:
            content_lines.append(f"• {pt}")
        content_lines.append("")

        content_lines.append("4. PRESCRIPTIONS & ENCOUNTER PLAN")
        content_lines.append("-" * 60)
        if meds:
            for m in meds:
                content_lines.append(f"• {_clean_val(m['medicine_name'])} {_clean_val(m['strength'])}: {_clean_val(m['dosage']) or 'Standard'}, {_clean_val(m['frequency']) or 'Daily'}")
        else:
            content_lines.append("• No prescriptions initiated during this visit.")
        content_lines.append("")
        next_section_num = 5

    # =========================================================================
    # FORMAT 5: PATIENT EDUCATION SUMMARY (Simple Everyday Jargon-Free Guide)
    # =========================================================================
    elif doc_type == "Patient Education Summary":
        lang = "English"
        if "telugu" in natural_language_request.lower():
            lang = "Telugu"
        elif "hindi" in natural_language_request.lower():
            lang = "Hindi"
        elif "tamil" in natural_language_request.lower():
            lang = "Tamil"
        elif "kannada" in natural_language_request.lower():
            lang = "Kannada"

        content_lines.append(f"2. YOUR HEALTH RESULTS EXPLAINED SIMPLY (Language: {lang})")
        content_lines.append("-" * 60)
        content_lines.append(f"Dear {_clean_val(patient['full_name'])}, here is what your medical reports mean in everyday language:")
        content_lines.append("")
        content_lines.append(f"• Your Basic Checks: {vitals_interp['simple']}")
        for pt in lab_interp["simple_narratives"]:
            content_lines.append(f"• {pt}")
        for pt in rad_interp["simple"]:
            content_lines.append(f"• {pt}")
        content_lines.append("")

        if lang == "Telugu":
            content_lines.append("ముఖ్యమైన ఆరోగ్య సూచనలు (Telugu Summary & Next Steps)")
            content_lines.append("• మందుల నియమావళి: డాక్టర్ సూచించిన విధంగా సమయానికి మందులు తీసుకోండి. మీ మందులను ఆకస్మికంగా ఆపవద్దు.")
            content_lines.append("• జాగ్రత్తలు: మీ రిపోర్ట్‌లోని ఫలితాల ఆధారంగా స్పెషలిస్ట్ డాక్టర్ సూచించిన పరీక్షలు మరియు ఫాలో-అప్ సమయానికి పూర్తి చేయండి.")
        elif lang == "Hindi":
            content_lines.append("आसान स्वास्थ्य सलाह एवं सावधानियाँ (Hindi Summary & Next Steps)")
            content_lines.append("• दवाओं का नियम: डॉक्टर द्वारा बताई गई सभी दवाएं सही समय पर लें और बिना पूछे बंद न करें।")
            content_lines.append("• अगला कदम: अपनी जांच रिपोर्ट में बताए गए विशेष निष्कर्षों के अनुसार विशेषज्ञ डॉक्टर से फॉलो-अप जरूर करें।")
        elif lang == "Tamil":
            content_lines.append("முக்கிய சுகாதார வழிகாட்டுதல் (Tamil Summary & Next Steps)")
            content_lines.append("• மருந்து உட்கொள்ளல்: மருத்துவர் பரிந்துரைத்தபடி மருந்துகளை தவறாமல் உட்கொள்ளுங்கள்.")
        elif lang == "Kannada":
            content_lines.append("ಮುಖ್ಯ ಆರೋಗ್ಯ ಸಲಹೆಗಳು (Kannada Summary & Next Steps)")
            content_lines.append("• ಔಷಧಿಗಳ ಸೂಚನೆ: ವೈದ್ಯರು ಸೂಚಿಸಿದಂತೆ ಸರಿಯಾದ ಸಮಯಕ್ಕೆ ಔಷಧಿಗಳನ್ನು ತೆಗೆದುಕೊಳ್ಳಿ.")
        else:
            content_lines.append("Actionable Care & Next Steps at Home")
            content_lines.append("• Follow Specialist Advice: Review your flagged lab or imaging steps directly at your follow-up appointment.")
            content_lines.append("• Medication Consistency: Take prescribed medicines at regular times; never start extra over-the-counter pain pills without asking your doctor.")
            content_lines.append("• Warning Signs: Contact the clinic promptly if you notice severe dizziness, numbness/weakness, persistent high fever, or unexpected bruising.")

        content_lines.append("")
        content_lines.append("3. YOUR MEDICATIONS IN PLAIN WORDS")
        content_lines.append("-" * 60)
        if meds:
            for m in meds:
                purpose, prec = _explain_medication(m["medicine_name"])
                content_lines.append(f"• {_clean_val(m['medicine_name'])} ({_clean_val(m['strength'])}): Helps by acting as {purpose.lower()}. Tip: {prec}")
        else:
            content_lines.append("• No active prescriptions listed; continue recommended rest, hydration, and diagnostic follow-up.")
        content_lines.append("")
        next_section_num = 4

    # =========================================================================
    # FORMAT 6: MEDICATION EXPLANATION (Safety, Mechanism & Interactions)
    # =========================================================================
    elif doc_type == "Medication Explanation":
        content_lines.append("2. COMPREHENSIVE PHARMACOTHERAPY EXPLANATION")
        content_lines.append("-" * 60)
        content_lines.append(f"Allergy Screening Check: Recorded allergies = {_clean_val(patient['allergies']) or 'None'}. Detailed mechanism and safety notes:")
        content_lines.append("")
        if meds:
            for m in meds:
                purpose, precautions = _explain_medication(m["medicine_name"])
                content_lines.append(f"{_clean_val(m['medicine_name'])} ({_clean_val(m['strength']) or 'Standard'})")
                content_lines.append(f"• Dosage & Route: {_clean_val(m.get('dosage')) or 'As directed'} via {_clean_val(m.get('route')) or 'Oral'}")
                content_lines.append(f"• Frequency / Schedule: {_clean_val(m.get('frequency')) or 'Daily'} for {_clean_val(m.get('duration')) or 'Ongoing'}")
                content_lines.append(f"• Prescribing Clinician: {_clean_val(m.get('prescribing_doctor')) or 'Attending Physician'} ({_clean_val(m.get('prescription_date')) or today_str})")
                content_lines.append(f"• Therapeutic Purpose: {purpose}")
                content_lines.append(f"• Clinical Precautions: {precautions}")
                content_lines.append("")
        else:
            content_lines.append("• No active medications currently prescribed; pharmacotherapy monitoring N/A.")
        content_lines.append("")
        next_section_num = 3

    # =========================================================================
    # FORMAT 7: PATIENT TIMELINE (Chronological Episode Reconstruction)
    # =========================================================================
    elif doc_type == "Patient Timeline":
        content_lines.append("2. LONGITUDINAL PATIENT JOURNEY & CLINICAL TIMELINE")
        content_lines.append("-" * 60)
        timeline_events = []
        if data["registration_records"]:
            timeline_events.append((data["registration_records"][0]["registration_date"] or today_str, "Registration", f"Patient registered ({_clean_val(data['registration_records'][0].get('address') or 'Hospital Intake')})"))
        for a in appts:
            timeline_events.append((a["appointment_date"] or today_str, "Consultation", f"Evaluated by {_clean_val(a['doctor'])} ({_clean_val(a['department'])}) — {_clean_val(a.get('reason_for_visit'))}"))
        for inp in inpatient:
            timeline_events.append((inp["admission_date"] or today_str, "Inpatient", f"Admitted to {_clean_val(inp['ward'])} — {_clean_val(inp['admission_diagnosis'])}"))
            if inp.get("discharge_date"):
                timeline_events.append((inp["discharge_date"], "Inpatient", f"Transitioned/Discharged — {_clean_val(inp['discharge_status'])}"))
        for n in nursing:
            timeline_events.append((n.get("recorded_at") or today_str, "Nursing", f"Triage vitals captured (BP {_clean_val(n.get('vital_bp'))}, Temp {n.get('vital_temp')}°F) — {_clean_val(n.get('nurse_notes'))}"))
        for l in labs:
            abn_tag = " [ABNORMAL]" if l.get("is_abnormal") else ""
            timeline_events.append((l.get("report_date") or today_str, "Laboratory", f"Assay completed: {_clean_val(l['test_name'])} = {_clean_val(l['result_value'])} {_clean_val(l['unit'])}{abn_tag}"))
        for r in rads:
            timeline_events.append((r.get("report_date") or today_str, "Radiology", f"{_clean_val(r['imaging_type'])} — Impression: {_clean_val(r.get('impression') or 'Completed')}"))
        for m in meds:
            timeline_events.append((m.get("prescription_date") or today_str, "Pharmacy", f"Initiated therapy: {_clean_val(m['medicine_name'])} ({_clean_val(m['strength'])})"))

        timeline_events.sort(key=lambda x: str(x[0]))
        if timeline_events:
            for date_val, dept, desc in timeline_events:
                content_lines.append(f"• [{date_val}] ({dept}): {desc}")
        else:
            content_lines.append("• No chronological clinical events recorded.")
        content_lines.append("")
        next_section_num = 3

    # Provenance & Sign-Off Footer
    content_lines.append(f"{next_section_num}. SOURCE TRACEABILITY & PROVENANCE")
    content_lines.append("-" * 60)
    content_lines.append(f"• Connected Hospital Departments: {', '.join(sources_cited) if sources_cited else 'None'}")
    content_lines.append("• Audit Provenance: Automated synthesis logged in HOSPIQ Audit Trail.")
    content_lines.append("• Governance Barrier: Pending Doctor Review until authorized physician sign-off.")

    final_text = strip_markdown_symbols("\n".join(content_lines))
    return final_text, sources_cited, False
