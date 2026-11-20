from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.models.models import User
from backend.security.auth import get_current_user
from backend.tools.patient_tools import (
    search_patient, get_patient_record, create_patient,
    insert_lab_result, insert_vital, insert_medication,
    update_patient, archive_record
)

router = APIRouter(prefix="/api/tools", tags=["Agent Tools"])

TOOL_REGISTRY = [
    {
        "name": "search_patient",
        "category": "Patient Data Management",
        "description": "Searches patients by ID, first name, last name, or full name.",
        "parameters": {"query": "string (e.g. 'Ravi' or 'P001')"},
        "page_reference": "Project Task Specification, Page 4 & 11"
    },
    {
        "name": "get_patient_record",
        "category": "Patient Data Management",
        "description": "Retrieves complete longitudinal patient health record across all 8 departments.",
        "parameters": {"patient_id": "string (e.g. 'P001')"},
        "page_reference": "Project Task Specification, Page 4 & 12"
    },
    {
        "name": "create_patient",
        "category": "Patient Data Management",
        "description": "Creates a new patient profile in the central repository.",
        "parameters": {"patient_id": "string", "first_name": "string", "last_name": "string", "dob": "YYYY-MM-DD", "gender": "string"},
        "page_reference": "Project Task Specification, Page 4"
    },
    {
        "name": "insert_lab_result",
        "category": "Clinical Observation",
        "description": "Records laboratory diagnostic findings with normal ranges.",
        "parameters": {"patient_id": "string", "test_name": "string", "result_value": "string", "unit": "string"},
        "page_reference": "Project Task Specification, Page 4"
    },
    {
        "name": "insert_vital",
        "category": "Nursing & Bedside",
        "description": "Inserts blood pressure, pulse, temperature, and SpO2 vital observations.",
        "parameters": {"patient_id": "string", "blood_pressure": "string (e.g. '120/80')"},
        "page_reference": "Project Task Specification, Page 4"
    },
    {
        "name": "insert_medication",
        "category": "Pharmacy & Dispensing",
        "description": "Records prescribed medication, dosage, route, frequency, and duration.",
        "parameters": {"patient_id": "string", "drug_name": "string", "dose": "string", "frequency": "string"},
        "page_reference": "Project Task Specification, Page 4"
    },
    {
        "name": "update_patient",
        "category": "Patient Data Management",
        "description": "Updates patient demographic, allergy, or chronic condition information.",
        "parameters": {"patient_id": "string", "allergies": "string (optional)", "chronic_conditions": "string (optional)"},
        "page_reference": "Project Task Specification, Page 4"
    },
    {
        "name": "archive_record",
        "category": "Governance & Lifecycle",
        "description": "Archives a clinical record and writes an immutable audit trail entry.",
        "parameters": {"entity_type": "string", "entity_id": "integer", "reason": "string"},
        "page_reference": "Project Task Specification, Page 4 & 14"
    }
]


@router.get("", response_model=List[Dict[str, Any]])
def list_available_tools(current_user: User = Depends(get_current_user)):
    """Lists the 8 atomic tools available to the Data Management Agent as specified in the project document."""
    return TOOL_REGISTRY


@router.post("/{tool_name}")
def execute_tool(
    tool_name: str,
    payload: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Executes a specific tool on the database with audit provenance."""
    if tool_name == "search_patient":
        query = payload.get("query", "")
        return {"tool": tool_name, "result": search_patient(db, query)}

    elif tool_name == "get_patient_record":
        pid = payload.get("patient_id", "P001")
        res = get_patient_record(db, pid)
        if not res:
            raise HTTPException(status_code=404, detail=f"Patient {pid} not found.")
        return {"tool": tool_name, "result": res}

    elif tool_name == "create_patient":
        res = create_patient(
            db=db,
            patient_id=payload.get("patient_id", ""),
            first_name=payload.get("first_name", "Test"),
            last_name=payload.get("last_name", "Patient"),
            dob=payload.get("dob", "1990-01-01"),
            gender=payload.get("gender", "Unknown")
        )
        return {"tool": tool_name, "result": res}

    elif tool_name == "insert_lab_result":
        res = insert_lab_result(
            db=db,
            patient_id=payload.get("patient_id", "P001"),
            test_name=payload.get("test_name", "Serum Ferritin"),
            result_value=str(payload.get("result_value", "45")),
            unit=payload.get("unit", "ng/mL")
        )
        return {"tool": tool_name, "result": res}

    elif tool_name == "insert_vital":
        res = insert_vital(
            db=db,
            patient_id=payload.get("patient_id", "P001"),
            blood_pressure=payload.get("blood_pressure", "120/80"),
            pulse=payload.get("pulse", 72)
        )
        return {"tool": tool_name, "result": res}

    elif tool_name == "insert_medication":
        res = insert_medication(
            db=db,
            patient_id=payload.get("patient_id", "P001"),
            drug_name=payload.get("drug_name", "Metformin"),
            dose=payload.get("dose", "500 mg"),
            frequency=payload.get("frequency", "twice daily")
        )
        return {"tool": tool_name, "result": res}

    elif tool_name == "update_patient":
        res = update_patient(
            db=db,
            patient_id=payload.get("patient_id", "P001"),
            allergies=payload.get("allergies"),
            chronic_conditions=payload.get("chronic_conditions")
        )
        return {"tool": tool_name, "result": res}

    elif tool_name == "archive_record":
        res = archive_record(
            db=db,
            entity_type=payload.get("entity_type", "Patient"),
            entity_id=payload.get("entity_id", 1),
            reason=payload.get("reason", "Standard audit archival")
        )
        return {"tool": tool_name, "result": res}

    else:
        raise HTTPException(status_code=400, detail=f"Unknown tool '{tool_name}'.")
