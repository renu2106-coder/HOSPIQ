import os
import json
import re
import shutil
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
from PIL import Image
from pypdf import PdfReader

try:
    import pytesseract
    pytesseract_available = shutil.which("tesseract") is not None
except Exception:
    pytesseract_available = False


def read_csv_file(file_path: str) -> List[Dict[str, Any]]:
    """Reads CSV file and returns list of dict records."""
    df = pd.read_csv(file_path)
    df = df.where(pd.notnull(df), None)
    return df.to_dict(orient="records")


def read_json_file(file_path: str) -> List[Dict[str, Any]]:
    """Reads JSON file (array of records or nested structure)."""
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    elif isinstance(data, dict):
        for key in ["records", "patients", "results", "data", "items"]:
            if key in data and isinstance(data[key], list):
                return data[key]
        return [data]
    return []


def read_excel_file(file_path: str) -> List[Dict[str, Any]]:
    """Reads Excel file (.xlsx, .xls) and returns list of records."""
    df = pd.read_excel(file_path)
    df = df.where(pd.notnull(df), None)
    return df.to_dict(orient="records")


def extract_txt_text(file_path: str) -> str:
    """Reads plain text file."""
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def normalize_document_text(text: str) -> str:
    """Normalizes raw text extracted from PDFs, scanned documents, and text files."""
    if not text:
        return ""

    t = text.replace("\r\n", "\n").replace("\r", "\n")
    t = re.sub(r'[\u2018\u2019\u201A\u201B]', "'", t)
    t = re.sub(r'[\u201C\u201D\u201E\u201F]', '"', t)
    t = re.sub(r'[\u2013\u2014]', '-', t)
    t = re.sub(r'\u2022|\u25CF|\u25CB|\u25AA', '- ', t)

    # Remove markdown stars/hashes and recurring scan footers
    t = re.sub(r'(?m)^\s*#{1,6}\s*', '', t)
    t = t.replace('***', '').replace('**', '')
    t = re.sub(r'(?i)page\s+\d+\s+of\s+\d+', '', t)
    t = re.sub(r'(?i)---\s*page\s+\d+\s*---', '', t)
    t = re.sub(r'(?i)scanned with .*', '', t)
    t = re.sub(r'(?i)confidential\s+medical\s+record', '', t)

    lines = [re.sub(r'[ \t]+', ' ', line).strip() for line in t.split('\n')]
    normalized_lines = []
    blank_counter = 0
    for line in lines:
        if not line:
            blank_counter += 1
            if blank_counter <= 1:
                normalized_lines.append("")
        else:
            blank_counter = 0
            normalized_lines.append(line)

    return "\n".join(normalized_lines).strip()


def _ocr_pil_image(img: Image.Image) -> str:
    """Runs Tesseract OCR on a PIL Image if the tesseract binary is installed."""
    if not pytesseract_available:
        return ""
    try:
        txt = pytesseract.image_to_string(img)
        return txt.strip() if txt else ""
    except Exception:
        return ""


def extract_pdf_text(file_path: str) -> str:
    """Extracts and normalizes text content from a PDF file across all pages, with OCR fallback for scanned PDFs."""
    reader = PdfReader(file_path)
    text_parts = []
    scanned_page_info = []

    for page_idx, page in enumerate(reader.pages):
        txt = page.extract_text()
        if txt and txt.strip():
            text_parts.append(txt.strip())
        else:
            # Scanned PDF page without selectable text layer: inspect embedded images & run OCR if available
            img_ocr_texts = []
            try:
                images = getattr(page, "images", [])
                for img_obj in images:
                    try:
                        from io import BytesIO
                        pil_img = Image.open(BytesIO(img_obj.data))
                        ocr_txt = _ocr_pil_image(pil_img)
                        if ocr_txt:
                            img_ocr_texts.append(ocr_txt)
                    except Exception:
                        continue
            except Exception:
                pass

            if img_ocr_texts:
                text_parts.append("\n".join(img_ocr_texts))
            else:
                scanned_page_info.append(f"Page {page_idx + 1} (image-only scanned scan without text layer)")

    if text_parts:
        return normalize_document_text("\n\n".join(text_parts))

    fname = Path(file_path).name
    return (
        f"[Scanned Image PDF Detected: {fname} | {len(reader.pages)} page(s)]\n"
        f"Pages inspected: {'; '.join(scanned_page_info) or 'Image-based PDF'}.\n"
        f"OCR Engine Status: {'Tesseract Ready' if pytesseract_available else 'Server OCR binary not installed — use Digitalized Report Text Paste or include a text/OCR layer for automatic field extraction.'}"
    )


def extract_image_text(file_path: str) -> str:
    """Performs OCR text extraction on image formats (JPG, PNG, TIFF, WEBP)."""
    try:
        img = Image.open(file_path)
        if pytesseract_available:
            extracted = _ocr_pil_image(img)
            if extracted:
                return normalize_document_text(extracted)

        return (
            f"[Medical Image File: {Path(file_path).name}]\n"
            f"Dimensions: {img.size[0]}x{img.size[1]} | Mode: {img.mode}\n"
            f"OCR Engine Status: {'No text detected in X-Ray/image' if pytesseract_available else 'Server OCR binary not installed — attach text report or use Digitalized Report Text Paste for automatic diagnostic mapping.'}"
        )
    except Exception as e:
        return f"[Image Processing Error: {str(e)}]"


# Clinical laboratory reference patterns:
# (canonical_name, regex_pattern, default_unit, default_ref_range, check_abnormal_fn)
LAB_PATTERNS: List[Tuple[str, str, str, str, Any]] = [
    ("Haemoglobin", r'(?i)\b(?:Ha?emoglobin|HGB|Hb)\b(?:\s*[:\-]\s*|\s+)([0-9]+(?:\.[0-9]+)?)\s*(gm%|g/dL|g/dl)?', "gm%", "11.5 - 16.0 (F) / 14.0 - 17.5 (M)", lambda v, g: (v < 13.5 if g == "Male" else v < 11.5) or v > 18.0),
    ("Total RBC Count", r'(?i)\b(?:Total\s+Erythrocyte\s+count\s*\(?RBC\)?|RBC\s+count|Total\s+RBC)\b[:\s-]*([0-9]+(?:\.[0-9]+)?)\s*(Millions/cumm|mill/cumm|M/uL)?', "Millions/cumm", "4.0 - 5.5", lambda v, g: v < 3.8 or v > 6.0),
    ("Total WBC Count", r'(?i)\b(?:Total\s+Leukocyte\s+count\s*\(?WBC\)?|Total\s+WBC\s+count|WBC\s+count|WBC)\b[:\s-]*([0-9,]+(?:\.[0-9]+)?)\s*(/cumm|cumm|cells/cumm|10\^3/uL)?', "/cumm", "4,000 - 11,000", lambda v, g: v < 4000 or v > 11000),
    ("Platelet Count", r'(?i)\bPlatelet\s+Count\b[:\s-]*([0-9,]+(?:\.[0-9]+)?)\s*(Lakhs/cumm|LAKHS/CUMM|10\^3/uL|/cumm)?', "Lakhs/cumm", "1.50 - 4.50", lambda v, g: (v < 1.50 or v > 4.50) if v < 50 else (v < 150000 or v > 450000)),
    ("HCT / Hematocrit", r'(?i)\b(?:HCT|Hematocrit|PCV)\b[:\s-]*([0-9]+(?:\.[0-9]+)?)\s*%?', "%", "35 - 50", lambda v, g: v < 35 or v > 52),
    ("MCV", r'(?i)\bMCV\b[:\s-]*([0-9]+(?:\.[0-9]+)?)\s*(?:fL|FL)?', "fL", "80 - 100", lambda v, g: v < 80 or v > 100),
    ("MCH", r'(?i)\bMCH\b[:\s-]*([0-9]+(?:\.[0-9]+)?)\s*(?:pg|Pg)?', "Pg", "27 - 32", lambda v, g: v < 27 or v > 33),
    ("MCHC", r'(?i)\bMCHC\b[:\s-]*([0-9]+(?:\.[0-9]+)?)\s*(?:gms?\s*%|g/dL)?', "gms %", "31 - 35", lambda v, g: v < 31 or v > 36),
    ("Neutrophils", r'(?i)\bNeutrophils\b[:\s-]*([0-9]+(?:\.[0-9]+)?)\s*%?', "%", "40 - 75", lambda v, g: v < 35 or v > 78),
    ("Lymphocytes", r'(?i)\bLymphocytes\b[:\s-]*([0-9]+(?:\.[0-9]+)?)\s*%?', "%", "20 - 45", lambda v, g: v < 18 or v > 48),
    ("Monocytes", r'(?i)\bMonocytes\b[:\s-]*([0-9]+(?:\.[0-9]+)?)\s*%?', "%", "1 - 10", lambda v, g: v > 12),
    ("Eosinophils", r'(?i)\bEosinophils\b[:\s-]*([0-9]+(?:\.[0-9]+)?)\s*%?', "%", "1 - 6", lambda v, g: v > 10),
    ("Basophils", r'(?i)\bBasophils\b[:\s-]*([0-9]+(?:\.[0-9]+)?)\s*%?', "%", "0 - 1", lambda v, g: v > 2),
    ("ESR (Erythrocyte Sedimentation Rate)", r'(?i)\b(?:ESR(?:\s*\(Erythrocyte\s*Sedimentation\s*Rate\))?|Erythrocyte\s+Sedimentation\s+Rate)\b[:\s-]*([0-9]+(?:\.[0-9]+)?)\s*(?:mm\s*1st\s*hour|mm/hr)?', "mm 1st hour", "0 - 20", lambda v, g: v > 20),
    ("C-Reactive Protein (CRP)", r'(?i)\b(?:C\s*-?\s*Reactive\s+Protein\s*\(?CRP\)?|CRP)\b[:\s-]*([0-9]+(?:\.[0-9]+)?)\s*(mg/L|mg/dL)?', "mg/L", "Up to 10 mg/L", lambda v, g: v > 10),
    ("Fasting Glucose", r'(?i)\b(?:Fasting\s+(?:Blood\s+)?Glucose|FBS|Glucose)\b[:\s-]*([0-9]+(?:\.[0-9]+)?)\s*(mg/dL)?', "mg/dL", "70 - 100", lambda v, g: v < 65 or v > 125),
    ("HbA1c", r'(?i)\bHbA1c\b[:\s-]*([0-9]+(?:\.[0-9]+)?)\s*%?', "%", "4.0 - 5.6", lambda v, g: v >= 6.5),
    ("Serum Creatinine", r'(?i)\b(?:Serum\s+)?Creatinine\b[:\s-]*([0-9]+(?:\.[0-9]+)?)\s*(mg/dL)?', "mg/dL", "0.6 - 1.3", lambda v, g: v > 1.3),
    ("Serum Calcium", r'(?i)\b(?:Serum\s+)?Calcium\b[:\s-]*([0-9]+(?:\.[0-9]+)?)\s*(mg/dL)?', "mg/dL", "8.5 - 10.5", lambda v, g: v < 8.4 or v > 10.5),
    ("Total Cholesterol", r'(?i)\b(?:Total\s+)?Cholesterol\b[:\s-]*([0-9]+(?:\.[0-9]+)?)\s*(mg/dL)?', "mg/dL", "< 200", lambda v, g: v > 200),
    ("Potassium", r'(?i)\bPotassium\b[:\s-]*([0-9]+(?:\.[0-9]+)?)\s*(mEq/L|mmol/L)?', "mEq/L", "3.5 - 5.1", lambda v, g: v < 3.5 or v > 5.2),
    ("Sodium", r'(?i)\bSodium\b[:\s-]*([0-9]+(?:\.[0-9]+)?)\s*(mEq/L|mmol/L)?', "mEq/L", "135 - 145", lambda v, g: v < 135 or v > 146),
]


def _extract_patient_header_info(text: str) -> Dict[str, Any]:
    """Extracts Patient ID/UHID/OP No, Name, Age, Gender, Referring Doctor, and Dates from real clinical reports."""
    info: Dict[str, Any] = {
        "patient_id": None,
        "external_ids": [],
        "full_name": None,
        "age": None,
        "gender": None,
        "consultant": None,
        "report_date": None,
        "department": None,
        "dob": None
    }

    # Check canonical HOSPIQ Patient ID (P001 - P999) first
    p_code = re.search(r'\b(P\d{3})\b', text)
    if p_code:
        info["patient_id"] = p_code.group(1).upper()

    # Check hospital IDs: Patient Id, UHID No, OP Reg No, Pat. No., Registration ID
    id_patterns = [
        r'(?i)\bPatient\s*Id\s*[:\-]\s*([A-Z0-9-]{3,20})',
        r'(?i)\bUHID(?:\s*(?:No|Number))?\.?\s*[:\-]\s*([A-Z0-9-]{4,20})',
        r'(?i)\bOP\s*Reg\s*No\s*[:\-]\s*([A-Z0-9-]{4,20})',
        r'(?i)\bPat(?:ient)?\.?\s*No\.?\s*[:\-]\s*([A-Z0-9-]{4,20})',
        r'(?i)\bRegistration\s*ID\s*[:\-]\s*([A-Z0-9-]{4,20})',
        r'(?i)\b(?:PID|MRN)\s*[:\-]\s*([A-Z0-9-]{3,20})',
    ]
    for pat in id_patterns:
        m = re.search(pat, text)
        if m:
            candidate = m.group(1).strip().upper()
            if candidate not in info["external_ids"]:
                info["external_ids"].append(candidate)
            if not info["patient_id"]:
                info["patient_id"] = candidate

    # Detect Patient Name (e.g. "Patient Name : MD MEHARUNNIHABUGUM", "Name : Ms. PRAGYA", "Mr. HARISH KANNA")
    name_m = re.search(
        r'(?im)(?:Patient\s*Name|(?<!\w)Name)\s*[:\-]\s*([A-Za-z.\s]{3,55}?)(?=\s+(?:Age|DOB|Gender|UHID|Pat\.|Reg|Patient|Bill|Sample|$)|\r|\n|,)',
        text
    )
    if name_m:
        raw_name = re.sub(r'\s+', ' ', name_m.group(1)).strip(" .:-")
        if raw_name and raw_name.lower() not in ("not documented", "unknown"):
            info["full_name"] = raw_name

    # Detect Age / Gender (e.g. "41 Years / F", "35Y / Male", "038Y / Male", "023Y / Female")
    age_gen = re.search(r'(?i)(?:Age\s*/?\s*(?:Gender|Sex)|Age|Sex)\s*[:\-]?\s*0?(\d{1,3})\s*(?:Y|Years?|Yrs?)?\s*/\s*(Male|Female|M|F|Other)\b', text)
    if age_gen:
        info["age"] = int(age_gen.group(1))
        g_raw = age_gen.group(2).strip().upper()
        info["gender"] = "Male" if g_raw in ("M", "MALE") else ("Female" if g_raw in ("F", "FEMALE") else "Other")
        # Approximate DOB from age if no explicit DOB is stated
        approx_year = datetime.utcnow().year - info["age"]
        info["dob"] = f"{approx_year}-01-01"
    else:
        g_only = re.search(r'(?i)\b(Gender|Sex)\s*[:\-]\s*(Male|Female|Other)\b', text)
        if g_only:
            info["gender"] = g_only.group(2).title()

    # Detect explicit DOB
    dob_m = re.search(r'(?i)\b(?:DOB|Date\s+of\s+Birth)\s*[:\-]\s*(\d{2,4}[-/]\d{1,2}[-/]\d{2,4})', text)
    if dob_m:
        info["dob"] = dob_m.group(1)

    # Detect Consultant / Ref. By
    doc_m = re.search(r'(?im)(?:Consultant|Doctor/Hospital|Doctor|Ref\.?\s*By)\s*[:\-]\s*([^\r\n]+)', text)
    if doc_m:
        info["consultant"] = doc_m.group(1).strip()

    # Detect Date (supports 24/11/2026, 24-Nov-2026, 13-11-2026, 2026-11-24)
    date_m = re.search(
        r'(?i)(?:Report(?:ed)?\s*(?:Date(?:\s*Time)?|On)|Study\s*Date|Printed\s*On|Date)\s*[:\-]?\s*(\d{1,2}[-/][A-Za-z]{3}[-/]\d{4}|\d{1,2}[-/]\d{1,2}[-/]\d{4}|\d{4}[-/]\d{1,2}[-/]\d{1,2})',
        text
    )
    if date_m:
        info["report_date"] = date_m.group(1)
    else:
        any_d = re.search(r'(\d{1,2}[-/][A-Za-z]{3}[-/]\d{4}|\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]\d{4})', text)
        info["report_date"] = any_d.group(1) if any_d else datetime.utcnow().strftime("%Y-%m-%d")

    return info


def parse_unstructured_text(text: str, department: Optional[str] = None) -> List[Dict[str, Any]]:
    """Extracts structured multi-department clinical fields from real digitalized medical reports or normalized OCR text."""
    records: List[Dict[str, Any]] = []
    if not text or not text.strip():
        return records

    # Detect placeholder messages where no actual clinical text exists
    if "OCR Engine Status: Server OCR binary not installed" in text:
        return records

    header = _extract_patient_header_info(text)
    pat_id = header["patient_id"]
    pat_name = header["full_name"]
    date_val = header["report_date"] or datetime.utcnow().strftime("%Y-%m-%d")

    base_patient_meta = {
        "patient_id": pat_id,
        "external_ids": header["external_ids"],
        "full_name": pat_name,
        "age": header["age"],
        "gender": header["gender"],
        "dob": header["dob"],
        "consultant": header["consultant"],
    }

    # 1. Extract Laboratory Results (Numeric & Quantitative)
    seen_lab_tests = set()
    for canonical_name, pattern, unit_default, ref_default, abn_fn in LAB_PATTERNS:
        m = re.search(pattern, text)
        if m:
            raw_num = m.group(1).replace(",", "")
            unit_matched = (m.group(2) if len(m.groups()) >= 2 and m.group(2) else None) or unit_default
            try:
                num_val = float(raw_num)
                is_abn = bool(abn_fn(num_val, header["gender"]))
            except Exception:
                is_abn = False

            seen_lab_tests.add(canonical_name.lower())
            records.append({
                **base_patient_meta,
                "department": "Laboratory",
                "test_name": canonical_name,
                "result_value": m.group(1),
                "unit": unit_matched,
                "reference_range": ref_default,
                "is_abnormal": is_abn,
                "report_date": date_val,
                "ordering_physician": header["consultant"],
                "source_type": "DIGITALIZED_REPORT"
            })

    # Qualitative Serology / Microbiology (Widal, Dengue, Malaria, Blood Group)
    qual_patterns = [
        ("Malaria Ag P.f/p.v", r'(?i)Malaria\s*(?:Ag\s*P\.?f/p\.?v)?\s*[:\s-]+\s*(NEGATIVE|POSITIVE)', "Method: Slide / Rapid Kit"),
        ("Dengue NS1 Antigen", r'(?i)Dengue\s*NS1\s*Antigen\s*[:\s-]+\s*(NON\s*REACTIVE|REACTIVE|POSITIVE|NEGATIVE)', "Non Reactive"),
        ("Dengue IgM", r'(?i)Dengue\s*(?:II\s*)?IgM\s*[:\s-]+\s*(NON\s*REACTIVE|REACTIVE|POSITIVE|NEGATIVE)', "Non Reactive"),
        ("Dengue IgG", r'(?i)Dengue\s*(?:I\s*)?IgG\s*[:\s-]+\s*(NON\s*REACTIVE|REACTIVE|POSITIVE|NEGATIVE)', "Non Reactive"),
        ("Widal S. Typhi O", r'(?i)S\.?\s*TYPHI\s*["\']?O["\']?\s*[:\s-]+\s*(1:\d+\s*(?:Dilutions)?)', "< 1:80"),
        ("Widal S. Typhi H", r'(?i)S\.?\s*TYPHI\s*["\']?H["\']?\s*[:\s-]+\s*(1:\d+\s*(?:Dilutions)?)', "< 1:80"),
        ("Blood Group", r'(?i)Blood\s*Group\s*[:\s-]+\s*(O\+|O-|A\+|A-|B\+|B-|AB\+|AB-)', "ABO/Rh Typing"),
    ]
    for tname, qpat, ref_str in qual_patterns:
        qm = re.search(qpat, text)
        if qm:
            res_str = qm.group(1).strip()
            is_abn = any(k in res_str.upper() for k in ("REACTIVE", "POSITIVE", "1:160", "1:320")) and "NON REACTIVE" not in res_str.upper()
            records.append({
                **base_patient_meta,
                "department": "Laboratory",
                "test_name": tname,
                "result_value": res_str,
                "unit": "",
                "reference_range": ref_str,
                "is_abnormal": is_abn,
                "report_date": date_val,
                "ordering_physician": header["consultant"],
                "source_type": "DIGITALIZED_REPORT"
            })

    # 2. Extract Radiology / Imaging Reports (MRI, X-Ray, CT, Ultrasound, DX)
    rad_header = re.search(
        r'(?im)^\s*((?:MRI|X-RAY|X RAY|CT\s*SCAN|CT|ULTRASOUND|USG|ECHO)\b[^\r\n]{3,85})',
        text
    )
    findings_m = re.search(
        r'(?is)(?:Findings|Observations)\s*:\s*(.*?)(?=\b(?:Impression|Conclusion|Suggested clinical|Radiologist|Dr\.|END OF|$))',
        text
    )
    impression_m = re.search(
        r'(?is)Impression\s*:\s*(.*?)(?=(?:Suggested clinical|Accuracy of|For clinical|For further|\bDR\.|Sign|$))',
        text
    )

    if rad_header or findings_m or impression_m:
        title_str = rad_header.group(1).strip() if rad_header else "Diagnostic Radiology Examination"
        upper_title = title_str.upper()
        modality = "MRI" if "MRI" in upper_title else ("CT Scan" if "CT" in upper_title else ("Ultrasound" if "ULTRASOUND" in upper_title or "USG" in upper_title else "X-Ray"))

        body_part = "General"
        for bp in ["Cervical Spine", "Whole Spine", "Lumbar Spine", "Paranasal Sinuses", "PNS", "Right Hand", "Left Hand", "Skull", "Chest", "Abdomen", "Knee", "Brain"]:
            if bp.lower() in upper_title.lower() or bp.lower() in text.lower():
                body_part = bp
                break

        findings_txt = re.sub(r'\s+', ' ', findings_m.group(1)).strip() if findings_m else title_str
        impression_txt = re.sub(r'\s+', ' ', impression_m.group(1)).strip(" -•\n\r") if impression_m else "See radiology findings for clinical correlation."

        rad_doc_m = re.search(r'(?im)(Dr\.?\s*[A-Z][A-Za-z.\s]{2,35}(?:DNB|MD|FRCR|DMRD)?)', text)
        radiologist_name = rad_doc_m.group(1).strip() if rad_doc_m else (header["consultant"] or "Consultant Radiologist")

        records.append({
            **base_patient_meta,
            "department": "Radiology",
            "imaging_type": f"{modality} - {title_str}"[:100],
            "body_part": body_part,
            "report_findings": findings_txt[:1500],
            "impression": impression_txt[:800],
            "report_date": date_val,
            "radiologist_name": radiologist_name[:100],
            "source_type": "DIGITALIZED_REPORT"
        })

    # 3. Extract Medications / Pharmacy
    med_matches = re.findall(
        r'(?i)\b(Metformin|Lisinopril|Atorvastatin|Amlodipine|Amoxicillin|Levothyroxine|Omeprazole|Losartan|Albuterol|Gabapentin|Pregabalin|Etoricoxib|Methylcobalamin|Paracetamol|Diclofenac|Fluticasone|Levocetirizine|Montelukast|Hydrochlorothiazide|Ciprofloxacin|Cephalexin|Insulin)[:\s-]*([0-9]+\s*(?:mg|mcg|ml|%)?)?\s*(?:[-–,]?\s*(Once\s*daily|Twice\s*daily|BID|TID|QID|Daily|PRN|[0-9]+\s*times?\s*daily))?',
        text
    )
    for med_name, strength, freq in med_matches:
        records.append({
            **base_patient_meta,
            "department": "Pharmacy",
            "medicine_name": med_name.title(),
            "strength": strength.strip() if strength else "Standard",
            "dosage": "1 dose / tablet",
            "frequency": freq.strip() if freq else "Daily",
            "route": "Oral",
            "prescription_date": date_val,
            "prescribing_doctor": header["consultant"] or "Attending Physician",
            "source_type": "DIGITALIZED_REPORT"
        })

    # 4. Extract Vitals / Nursing
    bp_match = re.search(r'(?i)\b(?:BP|Blood\s*Pressure)[:\s-]*([0-9]{2,3}/[0-9]{2,3})\b', text)
    pulse_match = re.search(r'(?i)\b(?:Pulse|Heart\s*Rate|HR)[:\s-]*([0-9]{2,3})\s*(?:bpm)?\b', text)
    temp_match = re.search(r'(?i)\b(?:Temp|Temperature)[:\s-]*([0-9]{2,3}(?:\.[0-9])?)\s*(?:°?[FC])?\b', text)
    spo2_match = re.search(r'(?i)\b(?:SpO2|Oxygen\s*Sat(?:uration)?)[:\s-]*([0-9]{2,3})\s*%?\b', text)

    if bp_match or pulse_match or temp_match or spo2_match:
        records.append({
            **base_patient_meta,
            "department": "Nursing",
            "vital_bp": bp_match.group(1) if bp_match else "120/80",
            "vital_pulse": int(pulse_match.group(1)) if pulse_match else 76,
            "vital_temp": float(temp_match.group(1)) if temp_match else 98.6,
            "vital_spo2": int(spo2_match.group(1)) if spo2_match else 98,
            "recorded_at": date_val,
            "nurse_notes": f"Vitals normalized from digitalized report. Patient: {pat_name or 'Identified'}",
            "source_type": "DIGITALIZED_REPORT"
        })

    # 5. If Patient metadata was found (e.g. Registration / Referral header), add a Registration record so patient profile updates
    if pat_name or pat_id or header["external_ids"]:
        if not records or header["consultant"]:
            records.append({
                **base_patient_meta,
                "department": department or "Registration",
                "registration_date": date_val,
                "department_registered": department or "Outpatient Services",
                "source_type": "DIGITALIZED_REPORT"
            })

    return records


SUPPORTED_EXTENSIONS = {
    ".csv": "csv",
    ".json": "json",
    ".xlsx": "xlsx",
    ".xls": "xlsx",
    ".txt": "txt",
    ".pdf": "pdf",
    ".zip": "zip",
    ".jpg": "image",
    ".jpeg": "image",
    ".png": "image",
    ".tiff": "image",
    ".tif": "image",
    ".webp": "image"
}


def parse_any_file(file_path: str, department: Optional[str] = None) -> Dict[str, Any]:
    """Universal file parser for CSV, JSON, Excel, PDF, Text, Images, and ZIP report bundles."""
    ext = Path(file_path).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        return {
            "success": False,
            "error": f"Unsupported file format '{ext}'. Supported formats: CSV, JSON, XLSX, XLS, TXT, PDF, ZIP, JPG, PNG, TIFF, WEBP.",
            "file_type": ext,
            "records": []
        }

    fmt = SUPPORTED_EXTENSIONS[ext]
    extracted_text = ""
    records: List[Dict[str, Any]] = []

    try:
        if fmt == "csv":
            records = read_csv_file(file_path)
            extracted_text = f"Parsed CSV with {len(records)} row(s)."
        elif fmt == "json":
            records = read_json_file(file_path)
            extracted_text = f"Parsed JSON with {len(records)} record(s)."
        elif fmt == "xlsx":
            records = read_excel_file(file_path)
            extracted_text = f"Parsed Excel sheet with {len(records)} row(s)."
        elif fmt == "txt":
            extracted_text = extract_txt_text(file_path)
            extracted_text = normalize_document_text(extracted_text)
            records = parse_unstructured_text(extracted_text, department=department)
        elif fmt == "pdf":
            extracted_text = extract_pdf_text(file_path)
            records = parse_unstructured_text(extracted_text, department=department)
        elif fmt == "image":
            extracted_text = extract_image_text(file_path)
            records = parse_unstructured_text(extracted_text, department=department)
        elif fmt == "zip":
            sub_texts = []
            with tempfile.TemporaryDirectory() as tmpdir:
                with zipfile.ZipFile(file_path, "r") as zf:
                    for member in zf.namelist():
                        if member.endswith("/") or "__MACOSX" in member:
                            continue
                        sub_ext = Path(member).suffix.lower()
                        if sub_ext in SUPPORTED_EXTENSIONS and sub_ext != ".zip":
                            extracted_path = zf.extract(member, path=tmpdir)
                            sub_res = parse_any_file(extracted_path, department=department)
                            if sub_res.get("success"):
                                records.extend(sub_res.get("records", []))
                                sub_texts.append(f"--- {Path(member).name} ---\n{sub_res.get('extracted_text', '')}")
            extracted_text = "\n\n".join(sub_texts) if sub_texts else f"Archive {Path(file_path).name} extracted (no supported inner records)."

        # Detect patient ID from records if available
        matched_pid = None
        for r in records:
            if isinstance(r, dict):
                for k in ["patient_id", "patientid", "pat_id", "pid", "id"]:
                    if k in r and r[k]:
                        matched_pid = str(r[k]).strip().upper()
                        break
            if matched_pid:
                break

        return {
            "success": True,
            "file_type": fmt,
            "records": records,
            "extracted_text": extracted_text,
            "record_count": len(records),
            "matched_patient_id": matched_pid,
            "department": department or "General"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to parse file: {str(e)}",
            "file_type": fmt,
            "records": []
        }
