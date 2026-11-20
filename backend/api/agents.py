from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.models.models import User, AgentExecution, Patient
from backend.schemas.schemas import AgentExecutionOut
from backend.security.auth import get_current_user, require_roles
from backend.services.llm_service import check_ollama_status
from backend.skills.duplicate_detection_skill import detect_duplicate_records
from backend.agents.patient_data_agent import PatientDataManagementAgent

router = APIRouter(prefix="/api/agents", tags=["AI Agents & Orchestration"])


@router.get("/executions", response_model=List[AgentExecutionOut])
def list_agent_executions(
    agent_name: Optional[str] = None,
    patient_id: Optional[str] = None,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves immutable agent execution trace logs with tool calls and timings."""
    if current_user.role == "Patient":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized")

    q = db.query(AgentExecution)
    if agent_name:
        q = q.filter(AgentExecution.agent_name.ilike(f"%{agent_name}%"))
    if patient_id:
        q = q.filter(AgentExecution.patient_id == patient_id.strip().upper())

    return q.order_by(AgentExecution.timestamp.desc()).limit(limit).all()


@router.get("/llm-status")
def get_llm_status():
    """Honest evaluation of local Ollama connection, configured model, and operational instructions."""
    return check_ollama_status()


@router.get("/duplicate-detection")
def run_duplicate_patient_detection(
    current_user: User = Depends(require_roles(["Doctor", "Hospital Administrator"])),
    db: Session = Depends(get_db)
):
    """Runs the duplicate detection skill to locate redundant patient records or shared demographics."""
    dupes = detect_duplicate_records(db)
    return {
        "status": "Success",
        "detected_duplicates_count": len(dupes),
        "duplicates": dupes
    }


@router.post("/consolidate-all")
def consolidate_all_patients(
    current_user: User = Depends(require_roles(["Hospital Administrator"])),
    db: Session = Depends(get_db)
):
    """Triggers batch consolidation of all 15+ patient records by the Patient Data Management Agent."""
    patients = db.query(Patient).all()
    agent = PatientDataManagementAgent(db)
    consolidated = []
    for p in patients:
        res = agent.consolidate_unified_record(p.id)
        consolidated.append(res)
    return {
        "status": "Success",
        "patients_processed": len(consolidated),
        "results": consolidated
    }

