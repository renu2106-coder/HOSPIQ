from typing import List, Dict, Any
from sqlalchemy.orm import Session
from backend.models.models import Patient, RegistrationRecord
from backend.skills.data_normalization_skill import normalize_date


def detect_duplicate_records(db: Session) -> List[Dict[str, Any]]:
    """Identifies potential duplicate patient records across registrations."""
    duplicates = []
    patients = db.query(Patient).all()

    # Track by normalized full name + dob
    name_dob_map: Dict[str, List[Patient]] = {}
    phone_map: Dict[str, List[Patient]] = {}

    for p in patients:
        norm_name = p.full_name.strip().lower()
        norm_dob = normalize_date(p.dob) or ""
        key_nd = f"{norm_name}|{norm_dob}"
        if key_nd not in name_dob_map:
            name_dob_map[key_nd] = []
        name_dob_map[key_nd].append(p)

        if p.contact_phone:
            phone_key = p.contact_phone.strip()
            if phone_key not in phone_map:
                phone_map[phone_key] = []
            phone_map[phone_key].append(p)

    # Check for name + DOB duplicates
    for key, p_list in name_dob_map.items():
        if len(p_list) > 1:
            name, dob = key.split("|", 1)
            duplicates.append({
                "type": "NAME_AND_DOB_DUPLICATE",
                "patient_ids": [p.id for p in p_list],
                "names": [p.full_name for p in p_list],
                "description": f"Multiple patient entries identified with identical name '{name.title()}' and DOB '{dob}'."
            })

    # Check for phone duplicates with different names
    for phone, p_list in phone_map.items():
        if len(p_list) > 1:
            unique_ids = list({p.id for p in p_list})
            if len(unique_ids) > 1:
                duplicates.append({
                    "type": "SHARED_CONTACT_PHONE",
                    "patient_ids": unique_ids,
                    "names": [p.full_name for p in p_list],
                    "description": f"Shared contact phone '{phone}' across distinct patient IDs: {', '.join(unique_ids)}."
                })

    # Check duplicate records within registration_records table (e.g. redundant submissions for same patient)
    reg_records = db.query(RegistrationRecord).all()
    reg_pid_map: Dict[str, List[RegistrationRecord]] = {}
    for r in reg_records:
        pid = r.patient_id.strip().upper()
        if pid not in reg_pid_map:
            reg_pid_map[pid] = []
        reg_pid_map[pid].append(r)

    for pid, r_list in reg_pid_map.items():
        if len(r_list) > 1:
            sources = [r.source_file or "EMR" for r in r_list]
            duplicates.append({
                "type": "REDUNDANT_REGISTRATION_ENTRY",
                "patient_ids": [pid],
                "record_ids": [r.id for r in r_list],
                "description": f"Patient {pid} ({r_list[0].name}) has {len(r_list)} separate registration entries ingested across sources ({', '.join(sources)})."
            })

    return duplicates
