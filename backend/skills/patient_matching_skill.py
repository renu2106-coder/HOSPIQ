"""Patient Matching Skill as specified on Page 10 and Page 11 of the project document.

Implements multi-factor fuzzy identity resolution across disparate department sources:
- Name similarity (handles abbreviations e.g. 'R. Kumar', 'Ravi K.', 'RAVI KUMAR')
- Normalized Date of Birth (handles format variants '12/03/1998', '1998-03-12', '12-Mar-1998')
- Gender normalization ('M', 'Male', 'male', '1')
- Phone number matching
"""

import difflib
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from backend.models.models import Patient
from backend.skills.data_normalization_skill import normalize_date, normalize_gender, normalize_phone


def compute_name_similarity(name1: str, name2: str) -> float:
    """Computes similarity between two names, handling initials, abbreviations, and case."""
    n1 = name1.strip().lower()
    n2 = name2.strip().lower()

    if n1 == n2:
        return 1.0

    # Token-level matching (e.g. 'r. kumar' vs 'ravi kumar')
    tokens1 = [t.replace('.', '') for t in n1.split()]
    tokens2 = [t.replace('.', '') for t in n2.split()]

    if len(tokens1) > 1 and len(tokens2) > 1:
        # Last name match check
        last_match = tokens1[-1] == tokens2[-1]
        first_init_match = tokens1[0][0] == tokens2[0][0]
        if last_match and first_init_match:
            return 0.92

    # Sequence matcher fallback
    return difflib.SequenceMatcher(None, n1, n2).ratio()


def match_patient_identity(
    db: Session,
    candidate_name: str,
    dob: Optional[str] = None,
    gender: Optional[str] = None,
    phone: Optional[str] = None,
    patient_id: Optional[str] = None
) -> Dict[str, Any]:
    """Matches a candidate demographic profile against authoritative patient records in the database."""
    # 1. Exact ID match if provided
    if patient_id:
        clean_id = patient_id.strip().upper()
        pat = db.query(Patient).filter(Patient.id == clean_id).first()
        if pat:
            return {
                "matched": True,
                "patient_id": pat.id,
                "confidence": 1.0,
                "match_reason": "Exact Patient ID Match",
                "patient_name": pat.full_name
            }

    norm_dob = normalize_date(dob) if dob else None
    norm_gen = normalize_gender(gender) if gender else None
    norm_ph = normalize_phone(phone) if phone else None

    all_patients = db.query(Patient).all()
    best_match: Optional[Patient] = None
    best_score = 0.0
    match_factors = []

    for p in all_patients:
        score = 0.0
        factors = []

        # Name similarity (weight 0.45)
        name_sim = compute_name_similarity(candidate_name, p.full_name)
        score += name_sim * 0.45
        if name_sim >= 0.8:
            factors.append(f"Name similarity {round(name_sim*100)}%")

        # DOB match (weight 0.35)
        if norm_dob and p.dob:
            if norm_dob == p.dob:
                score += 0.35
                factors.append("Normalized DOB Match (100%)")
            else:
                score -= 0.15

        # Gender match (weight 0.10)
        if norm_gen and p.gender:
            if norm_gen.lower() == p.gender.lower():
                score += 0.10
                factors.append("Gender Match")
            elif norm_gen != "Unknown" and p.gender != "Unknown":
                score -= 0.10

        # Phone match (weight 0.10)
        if norm_ph and p.contact_phone:
            clean_cp = normalize_phone(p.contact_phone)
            if clean_cp and (norm_ph in clean_cp or clean_cp in norm_ph):
                score += 0.10
                factors.append("Phone Match")

        if score > best_score:
            best_score = score
            best_match = p
            match_factors = factors

    # Threshold for positive identity match
    if best_match and best_score >= 0.70:
        return {
            "matched": True,
            "patient_id": best_match.id,
            "confidence": round(min(1.0, best_score), 2),
            "match_reason": " + ".join(match_factors),
            "patient_name": best_match.full_name,
            "canonical_demographics": {
                "dob": best_match.dob,
                "gender": best_match.gender,
                "blood_group": best_match.blood_group
            }
        }

    return {
        "matched": False,
        "patient_id": None,
        "confidence": round(best_score, 2),
        "match_reason": "No patient record exceeded multi-factor confidence threshold (0.70)",
        "patient_name": None
    }
