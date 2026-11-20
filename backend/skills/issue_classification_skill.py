import re
from typing import Dict, Any
from backend.skills.department_routing_skill import route_to_department
from backend.services.llm_service import query_llm


def classify_patient_issue(category: str, description: str) -> Dict[str, Any]:
    """Analyzes a patient-reported issue, prioritizes it, and routes it to the correct department."""
    routing = route_to_department(category, description)
    dept = routing["assigned_department"]

    # Severity analysis
    desc_l = description.lower()
    priority = "Medium"
    if any(k in desc_l for k in ["urgent", "emergency", "severe", "chest pain", "allergic", "wrong blood", "life-threatening", "critical"]):
        priority = "Critical"
    elif any(k in desc_l for k in ["wrong medicine", "incorrect dose", "missed appointment", "overcharge", "dispute", "delayed"]):
        priority = "High"
    elif any(k in desc_l for k in ["spelling", "typo", "general question", "portal feedback"]):
        priority = "Low"

    # Generate concise summary
    words = description.strip().split()
    summary = " ".join(words[:20]) + ("..." if len(words) > 20 else "")

    return {
        "category": category,
        "priority": priority,
        "assigned_department": dept,
        "routing_reason": routing["routing_reason"],
        "summary": summary
    }

