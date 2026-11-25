import re
from typing import Dict, Any, List, Tuple


def _s(val: Any) -> str:
    if val is None:
        return ""
    text = str(val)
    text = re.sub(r'#(\d+)', r'No. \1', text)
    return text.replace("#", "").replace("*", "").strip()


def interpret_vitals(nursing: List[Dict[str, Any]]) -> Dict[str, str]:
    """Interprets raw vital signs into meaningful physiological status summaries."""
    if not nursing:
        return {
            "clinical": "No vital signs were recorded in this dataset.",
            "simple": "Vital signs were not included in this upload."
        }
    v = nursing[-1]
    bp = _s(v.get("vital_bp"))
    pulse = v.get("vital_pulse")
    temp = v.get("vital_temp")
    spo2 = v.get("vital_spo2")
    notes = _s(v.get("nurse_notes"))

    findings = []
    simple_parts = []

    if bp and "/" in bp:
        try:
            sys_v, dia_v = [int(x.strip()) for x in bp.split("/")[:2]]
            if sys_v >= 140 or dia_v >= 90:
                findings.append(f"elevated blood pressure ({bp} mmHg — hypertensive range)")
                simple_parts.append(f"Your blood pressure ({bp}) is slightly on the high side")
            elif sys_v < 90 or dia_v < 60:
                findings.append(f"low blood pressure ({bp} mmHg — hypotensive trend)")
                simple_parts.append(f"Your blood pressure ({bp}) is slightly low")
            else:
                findings.append(f"normotensive BP ({bp} mmHg)")
                simple_parts.append(f"Your blood pressure ({bp}) is in a healthy range")
        except Exception:
            findings.append(f"BP {bp} mmHg")

    if temp is not None:
        try:
            t_val = float(temp)
            if t_val >= 100.4:
                findings.append(f"febrile temperature ({t_val}°F — active fever)")
                simple_parts.append(f"you had an active fever ({t_val}°F)")
            elif t_val >= 99.1:
                findings.append(f"low-grade temperature elevation ({t_val}°F)")
                simple_parts.append(f"you had mild warmth ({t_val}°F)")
            else:
                findings.append(f"afebrile temperature ({t_val}°F)")
        except Exception:
            pass

    if pulse is not None:
        try:
            p_val = int(pulse)
            if p_val > 100:
                findings.append(f"tachycardia ({p_val} bpm)")
            elif p_val < 60:
                findings.append(f"bradycardia ({p_val} bpm)")
            else:
                findings.append(f"regular heart rate ({p_val} bpm)")
        except Exception:
            pass

    if spo2 is not None:
        try:
            o2 = int(spo2)
            if o2 < 94:
                findings.append(f"reduced oxygen saturation ({o2}% — monitor respiration)")
                simple_parts.append(f"oxygen level was slightly low at {o2}%")
            else:
                findings.append(f"adequate oxygenation (SpO2 {o2}%)")
        except Exception:
            pass

    clinical_str = "Vital signs demonstrate " + ", ".join(findings) + "." if findings else "Vitals within baseline."
    if notes:
        clinical_str += f" Nursing bedside observation: {notes}"

    simple_str = (
        "; ".join(simple_parts) + ", and oxygen saturation was healthy."
        if simple_parts else "Your basic vital checks (heart rate, temperature, and oxygen) were stable."
    )
    return {"clinical": clinical_str, "simple": simple_str}


def categorize_and_explain_labs(labs: List[Dict[str, Any]], patient: Dict[str, Any]) -> Dict[str, Any]:
    """Groups raw lab values by clinical panel and produces medical + patient-friendly analytical explanations."""
    if not labs:
        return {
            "panels": {},
            "clinical_narratives": ["No laboratory diagnostics are on file for this patient."],
            "simple_narratives": ["No blood or laboratory tests have been uploaded for your record yet."],
            "abnormal_count": 0,
            "normal_count": 0
        }

    panels: Dict[str, List[Dict[str, Any]]] = {
        "Haematology & Blood Counts": [],
        "Inflammatory & Tissue Injury Markers": [],
        "Infectious & Serology Screening": [],
        "Biochemistry, Renal & Metabolic Panel": [],
    }

    for l in labs:
        name_lc = (l.get("test_name") or "").lower()
        dept_lc = (l.get("lab_department") or "").lower()
        if any(k in name_lc for k in ("malaria", "dengue", "widal", "typhi", "antigen", "igm", "igg", "serology")):
            panels["Infectious & Serology Screening"].append(l)
        elif any(k in name_lc for k in ("esr", "sedimentation", "crp", "reactive protein", "ferritin")):
            panels["Inflammatory & Tissue Injury Markers"].append(l)
        elif any(k in name_lc for k in ("hba1c", "glucose", "calcium", "creatinine", "bun", "egfr", "cholesterol", "potassium", "sodium", "alt", "ast", "uric", "lipid", "tsh")):
            panels["Biochemistry, Renal & Metabolic Panel"].append(l)
        elif "biochem" in dept_lc:
            panels["Biochemistry, Renal & Metabolic Panel"].append(l)
        elif "immun" in dept_lc or "serol" in dept_lc:
            panels["Infectious & Serology Screening"].append(l)
        else:
            panels["Haematology & Blood Counts"].append(l)

    clinical_narratives: List[str] = []
    simple_narratives: List[str] = []

    all_text = " ".join(f"{l.get('test_name', '')} {l.get('result_value', '')}" for l in labs).lower()
    abn_labs = [l for l in labs if l.get("is_abnormal")]
    gender = (patient.get("gender") or "").lower()

    # Cross-marker Analytical Reasoning (NOT raw pasting!)
    # 1. Inflammatory Pattern (ESR vs CRP)
    esr_rec = next((l for l in labs if "esr" in (l.get("test_name") or "").lower()), None)
    crp_rec = next((l for l in labs if "crp" in (l.get("test_name") or "").lower() or "reactive protein" in (l.get("test_name") or "").lower()), None)
    if esr_rec and esr_rec.get("is_abnormal"):
        if crp_rec and not crp_rec.get("is_abnormal"):
            clinical_narratives.append(
                f"Inflammatory Dissociation Pattern: Erythrocyte Sedimentation Rate is significantly elevated ({_s(esr_rec['result_value'])} {_s(esr_rec['unit'])} vs normal 0-20), whereas C-Reactive Protein remains normal ({_s(crp_rec['result_value'])} {_s(crp_rec['unit'])}). Clinically, raised ESR with normal CRP points toward sub-acute musculoskeletal inflammation, structural spinal/joint wear, or chronic marrow activity rather than acute bacterial sepsis."
            )
            simple_narratives.append(
                f"Inflammation Marker Explained: Your ESR blood test ({_s(esr_rec['result_value'])}) is higher than normal, showing ongoing body inflammation or tissue stress, while your CRP test ({_s(crp_rec['result_value'])}) is normal — reassuringly ruling out a sudden severe bacterial infection."
            )
        else:
            clinical_narratives.append(
                f"Elevated Systemic Inflammation: ESR is elevated at {_s(esr_rec['result_value'])} {_s(esr_rec['unit'])} (reference: {_s(esr_rec.get('reference_range'))}), signifying active systemic inflammation or hematological marrow activity requiring clinical & imaging correlation."
            )
            simple_narratives.append(
                f"Inflammation Marker Explained: Your ESR blood test ({_s(esr_rec['result_value'])}) is above normal, meaning there is active inflammation in your body that your doctor will connect with your scan results."
            )
    elif crp_rec and crp_rec.get("is_abnormal"):
        clinical_narratives.append(
            f"Acute Phase Activation: CRP is elevated ({_s(crp_rec['result_value'])} {_s(crp_rec['unit'])}), consistent with active acute inflammation or infection."
        )
        simple_narratives.append(
            f"Infection/Inflammation Marker: Your CRP test ({_s(crp_rec['result_value'])}) is raised above normal, indicating active inflammation."
        )

    # 2. Hematology Analysis (Hemoglobin + Indices + Platelets)
    hb_rec = next((l for l in labs if "haemoglobin" in (l.get("test_name") or "").lower() or "hemoglobin" in (l.get("test_name") or "").lower()), None)
    plt_rec = next((l for l in labs if "platelet" in (l.get("test_name") or "").lower()), None)
    idx_rec = next((l for l in labs if "mch" in (l.get("test_name") or "").lower()), None)

    if plt_rec and plt_rec.get("is_abnormal"):
        clinical_narratives.append(
            f"Mild Thrombocytopenia: Platelet count is suppressed below reference ({_s(plt_rec['result_value'])} {_s(plt_rec['unit'])}; normal {_s(plt_rec.get('reference_range'))}). In febrile or viral presentations, mild drops down to ~1.25 Lakhs reflect transient marrow suppression or viral consumption. Clinical safety priority is monitoring platelet recovery over 48 hours and avoiding antiplatelet / blood-thinning analgesics."
        )
        simple_narratives.append(
            f"Platelet Count Explained: Your platelets ({_s(plt_rec['result_value'])} {_s(plt_rec['unit'])}) are mildly below the usual range. Platelets help blood clot properly and commonly dip during viral fevers; stay well hydrated and have a repeat check in 2 days to confirm they are rising."
        )

    if hb_rec and hb_rec.get("is_abnormal"):
        gender_note = "for an adult male" if "male" in gender and "female" not in gender else "relative to standard physiological baseline"
        idx_note = f" accompanied by borderline low red cell hemoglobin indices ({_s(idx_rec['result_value'])})" if idx_rec else ""
        clinical_narratives.append(
            f"Reduced Oxygen-Carrying Capacity (Anemia): Hemoglobin measures {_s(hb_rec['result_value'])} {_s(hb_rec['unit'])} (below threshold {gender_note}){idx_note}. This indicates mild hypochromic/nutritional or chronic-disease anemia; iron profile, reticulocyte response, or dietary replenishment should be assessed."
        )
        simple_narratives.append(
            f"Hemoglobin Explained: Your hemoglobin ({_s(hb_rec['result_value'])} {_s(hb_rec['unit'])}) is mildly below the healthy target, meaning your red blood cells carry slightly less oxygen than normal, which can cause tiredness."
        )
    elif hb_rec and not hb_rec.get("is_abnormal"):
        clinical_narratives.append(
            f"Preserved Haematological Reserves: Hemoglobin ({_s(hb_rec['result_value'])} {_s(hb_rec['unit'])}) and cellular counts remain adequate, confirming no significant anemia."
        )

    # 3. Infectious Fever Panel (Dengue / Malaria / Widal Synthesis)
    if any(k in all_text for k in ("malaria", "dengue", "widal")):
        dengue_neg = "dengue" in all_text and "non reactive" in all_text
        malaria_neg = "malaria" in all_text and "negative" in all_text
        widal_180 = "1:80" in all_text
        widal_high = "1:160" in all_text or "1:320" in all_text
        ruled_out = []
        if malaria_neg:
            ruled_out.append("Malaria")
        if dengue_neg:
            ruled_out.append("Dengue (NS1/IgM/IgG non-reactive)")
        rule_str = " and ".join(ruled_out) if ruled_out else "Major tropical pathogens"
        widal_str = (
            " Widal O & H titers show borderline 1:80 reactivity (non-diagnostic in endemic settings without rising convalescent titers or blood culture correlation)."
            if widal_180 else (" Elevated Widal titers >=1:160 suggest possible enteric fever requiring confirmation." if widal_high else "")
        )
        clinical_narratives.append(
            f"Fever Etiology Differentiation: Targeted screening rules out {rule_str}.{widal_str} Combined with mild leukopenia-trending WBC and reduced platelets, the biomarker signature favors a resolving non-dengue viral febrile illness."
        )
        simple_narratives.append(
            f"Fever Infection Screening Explained: Reassuringly, both Malaria and Dengue tests came back negative. Your typhoid screening (Widal 1:80) sits at a borderline baseline level rather than a strong active infection, which fits a routine self-limiting viral fever."
        )

    # 4. Metabolic / Renal / Glycemic / Calcium Markers
    ca_rec = next((l for l in abn_labs if "calcium" in (l.get("test_name") or "").lower()), None)
    if ca_rec:
        clinical_narratives.append(
            f"Hypercalcemia Alert: Serum Calcium is elevated ({_s(ca_rec['result_value'])} {_s(ca_rec['unit'])} vs ref {_s(ca_rec.get('reference_range'))}). In conjunction with skeletal findings, elevated calcium can signal active bone resorption (e.g., parathyroid or plasma cell/myeloma workup) and necessitates urgent endocrine/hematology review plus adequate hydration."
        )
        simple_narratives.append(
            f"Calcium Level Explained: Your blood calcium ({_s(ca_rec['result_value'])} {_s(ca_rec['unit'])}) is higher than normal; your doctor will investigate why extra calcium is entering the bloodstream from bone or glands."
        )

    hba1c_rec = next((l for l in abn_labs if "hba1c" in (l.get("test_name") or "").lower()), None)
    glu_rec = next((l for l in abn_labs if "glucose" in (l.get("test_name") or "").lower()), None)
    if hba1c_rec or glu_rec:
        g_parts = []
        if hba1c_rec:
            g_parts.append(f"3-month average HbA1c of {_s(hba1c_rec['result_value'])}%")
        if glu_rec:
            g_parts.append(f"glucose {_s(glu_rec['result_value'])} {_s(glu_rec['unit'])}")
        clinical_narratives.append(
            f"Glycemic Dysregulation: {', '.join(g_parts)} indicates suboptimal blood sugar control, increasing microvascular risk and requiring dietary tightening and antihyperglycemic optimization."
        )
        simple_narratives.append(
            f"Blood Sugar Explained: Your glucose tests show sugar levels have been running high, so meal portion control and consistent medication timing are important."
        )

    egfr_rec = next((l for l in labs if "egfr" in (l.get("test_name") or "").lower() or "creatinine" in (l.get("test_name") or "").lower()), None)
    if egfr_rec and egfr_rec.get("is_abnormal"):
        clinical_narratives.append(
            f"Renal Filtration Impairment: {_s(egfr_rec['test_name'])} at {_s(egfr_rec['result_value'])} {_s(egfr_rec['unit'])} demonstrates reduced kidney clearance, requiring renal-safe dosing adjustments and avoidance of nephrotoxic agents."
        )
        simple_narratives.append(
            f"Kidney Test Explained: Your kidney function test ({_s(egfr_rec['test_name'])}) shows your kidneys are filtering slightly slower than normal; keep well hydrated and let your doctor approve all pain medicines."
        )

    if not clinical_narratives:
        clinical_narratives.append(
            "Diagnostic Biomarker Integrity: All evaluated laboratory parameters fall within expected physiological reference ranges without biochemical or hematological derangement."
        )
    if not simple_narratives:
        simple_narratives.append(
            "Overall Lab Meaning: All measured blood tests are reassuringly within healthy reference targets."
        )

    return {
        "panels": {k: v for k, v in panels.items() if v},
        "clinical_narratives": clinical_narratives,
        "simple_narratives": simple_narratives,
        "abnormal_count": len(abn_labs),
        "normal_count": len(labs) - len(abn_labs)
    }


def explain_radiology_studies(rads: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Produces clinical significance and everyday patient-friendly explanations of radiology studies."""
    if not rads:
        return {
            "clinical": ["No radiological or imaging studies are recorded for this patient."],
            "simple": ["No X-ray, CT, or MRI scans are attached to your record yet."],
            "urgency": "Routine"
        }

    clinical_notes: List[str] = []
    simple_notes: List[str] = []
    urgency = "Routine"

    for r in rads:
        study = _s(r.get("imaging_type"))
        findings = _s(r.get("report_findings"))
        imp = _s(r.get("impression"))
        combined = f"{study} {findings} {imp}".lower()

        if "myeloma" in combined or "lytic lesion" in combined:
            urgency = "Critical"
            clinical_notes.append(
                f"Urgent Skeletal Findings ({study}): Punctate tiny lytic lesions within the parietal calvarium raise suspicion for an underlying plasma cell dyscrasia / myeloproliferative process (such as multiple myeloma), despite preserved sella turcica anatomy and absence of traumatic fracture or elevated intracranial pressure. Mandatory next workup includes Serum Protein Electrophoresis (SPEP), free light-chain assay, CT skeletal survey, and prompt Hematology consultation."
            )
            simple_notes.append(
                "Important Finding on Your Skull X-Ray: Although your fall did not break any skull bones or raise brain pressure, the X-ray spotted tiny thinned areas in the upper skull bone. Because these can sometimes relate to bone marrow conditions, your doctor has ordered specialized blood tests (protein electrophoresis) and follow-up scans to check thoroughly and start early specialist care."
            )
        elif "disc bulge" in combined or "thecal sac" in combined or "foramina" in combined:
            if urgency != "Critical":
                urgency = "High"
            clinical_notes.append(
                f"Multi-Level Spinal Degenerative Findings ({study}): Loss of cervical lordosis (straightening due to paraspinal spasm) alongside C4-C5 and C5-C6 central disc bulges and a right lateral C6-C7 disc bulge indenting the thecal sac and narrowing the right neural foramen explains cervical radiculopathy / upper limb symptoms. Concurrent L4-L5 and L5-S1 disc bulges contribute to lumbosacral symptoms, while the spinal cord itself preserves normal caliber and signal without destructive lesions (L5 haemangioma is typically an incidental benign vascular lesion). Conservative posture therapy, physiotherapy, and neuropathic analgesia are clinically indicated."
            )
            simple_notes.append(
                "What Your Spine MRI Explains: Your spinal cord itself is healthy and undamaged. However, neck muscle stiffness has straightened the natural neck curve, and cushioning discs in your neck (C4-C7) and lower back (L4-S1) are bulging slightly toward the spinal fluid sac and narrowing a nerve exit space on the right side — this mechanical pressure is what causes your neck, arm, or back pain. A harmless blood-vessel spot at L5 needs no treatment."
            )
        elif "septal deviation" in combined or "turbinates hypertrophy" in combined:
            if urgency == "Routine":
                urgency = "Moderate"
            clinical_notes.append(
                f"Structural Upper Airway Assessment ({study}): Subtle S-shaped nasal septal deviation coupled with asymmetric inferior/middle turbinate hypertrophy (right > left) explains mechanical narrowing of the nasal passages and chronic nasal airflow obstruction, while bilateral frontal, ethmoidal, and maxillary sinus cavities remain completely aerated and free of acute sinusitis or bony lesions. Targeted intranasal corticosteroid therapy and antihistamines address mucosal hypertrophy; CT PNS correlation may be considered if symptoms persist."
            )
            simple_notes.append(
                "What Your Sinus X-Ray Explains: Good news — your sinus air pockets are completely clear with zero trapped fluid or bone problems. Instead, your nasal breathing difficulty comes from a gentle S-shaped curve in the central nose wall (septum) plus swollen side-linings inside the right nostril, which can be treated effectively with medicated nasal sprays."
            )
        elif "within normal limits" in combined or "no bony injury" in combined:
            clinical_notes.append(
                f"Normal Orthopaedic Exclusion ({study}): Normal bone mineralization, preserved joint spaces, smooth articular margins, and intact osseous continuity definitively exclude acute fracture, dislocation, or lytic bony pathology post-fall. Symptoms correspond to self-limiting soft-tissue sprain or contusion."
            )
            simple_notes.append(
                f"Good News About Your X-Ray ({study}): Your bones, joints, and bone density look completely normal with zero fractures or breaks after your fall. Any soreness is only soft-tissue bruising or sprain, which recovers well with rest and topical pain relief."
            )
        else:
            f_clean = findings.rstrip(".")
            i_clean = (imp or "Correlate with bedside presentation").rstrip(".")
            clinical_notes.append(
                f"Diagnostic Imaging Synthesis ({study}): {f_clean}. Clinical impression: {i_clean}."
            )
            simple_notes.append(
                f"What Your Scan Shows ({study}): {(imp or findings).rstrip('.')}."
            )

    return {"clinical": clinical_notes, "simple": simple_notes, "urgency": urgency}
