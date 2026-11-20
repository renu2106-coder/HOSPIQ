import re
from datetime import datetime
from typing import Optional, Dict, Any


def normalize_date(date_str: Optional[str]) -> Optional[str]:
    """Standardizes heterogeneous date formats into ISO 8601 YYYY-MM-DD."""
    if not date_str:
        return None
    date_str = str(date_str).strip()
    if not date_str or date_str.lower() in ("none", "null", "nan", "n/a", ""):
        return None

    # Common date formats
    date_formats = [
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%d-%m-%Y",
        "%m-%d-%Y",
        "%Y/%m/%d",
        "%d.%m.%Y",
        "%Y.%m.%d",
        "%d %b %Y",
        "%d %B %Y",
        "%b %d, %Y",
        "%B %d, %Y",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
    ]

    for fmt in date_formats:
        try:
            parsed = datetime.strptime(date_str, fmt)
            return parsed.strftime("%Y-%m-%d")
        except ValueError:
            continue

    # Try regex extraction for YYYY-MM-DD
    match = re.search(r'(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})', date_str)
    if match:
        y, m, d = match.groups()
        return f"{int(y):04d}-{int(m):02d}-{int(d):02d}"

    # Try regex extraction for DD/MM/YYYY
    match_dmy = re.search(r'(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})', date_str)
    if match_dmy:
        p1, p2, y = match_dmy.groups()
        # Assume DD-MM-YYYY if p1 > 12
        if int(p1) > 12:
            return f"{int(y):04d}-{int(p2):02d}-{int(p1):02d}"
        else:
            return f"{int(y):04d}-{int(p1):02d}-{int(p2):02d}"

    return date_str


def normalize_phone(phone_str: Optional[str]) -> Optional[str]:
    """Standardizes phone numbers by stripping formatting."""
    if not phone_str:
        return None
    phone_clean = re.sub(r'[^\d+]', '', str(phone_str))
    if len(phone_clean) == 10 and not phone_clean.startswith("+"):
        return f"+1-{phone_clean[:3]}-{phone_clean[3:6]}-{phone_clean[6:]}"
    return phone_clean if phone_clean else str(phone_str).strip()


def normalize_gender(gender_str: Optional[str]) -> str:
    """Normalizes gender values to Male, Female, Other, or Unknown."""
    if not gender_str:
        return "Unknown"
    g = str(gender_str).strip().lower()
    if g in ("m", "male", "man"):
        return "Male"
    elif g in ("f", "female", "woman"):
        return "Female"
    elif g in ("o", "other", "non-binary", "transgender"):
        return "Other"
    return "Unknown"


FIELD_SYNONYMS = {
    "patient_id": ["patient_id", "patientid", "pat_id", "pid", "mrn", "id", "patient id", "patient_no", "hospital_id"],
    "first_name": ["first_name", "firstname", "fname", "given_name"],
    "last_name": ["last_name", "lastname", "lname", "surname", "family_name"],
    "full_name": ["full_name", "fullname", "patient_name", "name"],
    "dob": ["dob", "date_of_birth", "birth_date", "birthdate", "born"],
    "gender": ["gender", "sex"],
    "contact_phone": ["contact_phone", "phone", "phone_number", "contact_number", "mobile", "telephone", "cell"],
    "email": ["email", "e-mail", "email_address"],
    "address": ["address", "residence", "residential_address", "home_address"],
    "blood_group": ["blood_group", "bloodgroup", "blood_type", "abo_rh", "blood"],
    "test_name": ["test_name", "lab_test", "test", "investigation"],
    "result_value": ["result_value", "result", "value", "reading", "outcome"],
    "medicine_name": ["medicine_name", "medication", "drug_name", "drug", "medicine"],
    "dosage": ["dosage", "dose"],
    "frequency": ["frequency", "schedule"],
    "duration": ["duration", "days"],
    "imaging_type": ["imaging_type", "modality", "scan_type", "procedure"],
    "report_findings": ["report_findings", "findings", "radiology_findings", "observation"],
    "vital_bp": ["vital_bp", "bp", "blood_pressure"],
    "vital_pulse": ["vital_pulse", "pulse", "heart_rate", "hr"],
    "vital_temp": ["vital_temp", "temperature", "temp"],
    "vital_spo2": ["vital_spo2", "spo2", "oxygen_saturation", "o2_sat"],
    "amount": ["amount", "charge", "fee", "cost", "total_amount"],
    "payment_status": ["payment_status", "status", "bill_status"]
}


def normalize_record_dict(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """Maps varied raw dictionary keys to standard internal schema keys."""
    normalized: Dict[str, Any] = {}
    lower_map = {str(k).strip().lower(): v for k, v in raw_data.items()}

    for canonical, synonyms in FIELD_SYNONYMS.items():
        for syn in synonyms:
            if syn in lower_map:
                normalized[canonical] = lower_map[syn]
                break

    # Retain non-mapped fields under their original cleaned keys
    for k, v in raw_data.items():
        clean_k = str(k).strip().lower().replace(" ", "_")
        if clean_k not in normalized:
            normalized[clean_k] = v

    # Post-process standard types
    if "dob" in normalized:
        normalized["dob"] = normalize_date(str(normalized["dob"]))
    if "gender" in normalized:
        normalized["gender"] = normalize_gender(str(normalized["gender"]))
    if "contact_phone" in normalized:
        normalized["contact_phone"] = normalize_phone(str(normalized["contact_phone"]))
    if "patient_id" in normalized:
        normalized["patient_id"] = str(normalized["patient_id"]).strip().upper()

    return normalized

