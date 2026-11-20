from typing import Dict, Any

CATEGORY_DEPARTMENT_MAP = {
    "Personal Information": "Registration",
    "Appointment": "Appointments",
    "Laboratory Report": "Laboratory",
    "Prescription or Medication": "Pharmacy",
    "Radiology Report": "Radiology",
    "Billing": "Billing",
    "Hospital Service": "Nursing",
    "Website or Technical Issue": "Administration",
    "Other": "Administration"
}


def route_to_department(category: str, description: str = "") -> Dict[str, str]:
    """Determines the responsible hospital department and provides routing rationale."""
    cat_clean = category.strip()
    dept = CATEGORY_DEPARTMENT_MAP.get(cat_clean, "Administration")

    # Keyword overrides if description explicitly points elsewhere
    desc_l = description.lower()
    if "blood test" in desc_l or "lab" in desc_l or "cbc" in desc_l:
        dept = "Laboratory"
    elif "x-ray" in desc_l or "mri" in desc_l or "ct scan" in desc_l:
        dept = "Radiology"
    elif "tablet" in desc_l or "pharmacy" in desc_l or "prescription" in desc_l:
        dept = "Pharmacy"
    elif "bill" in desc_l or "payment" in desc_l or "insurance" in desc_l:
        dept = "Billing"
    elif "reschedule" in desc_l or "booking" in desc_l or "doctor slot" in desc_l:
        dept = "Appointments"

    return {
        "assigned_department": dept,
        "routing_reason": f"Automated routing to {dept} based on classification category '{category}' and issue context."
    }

