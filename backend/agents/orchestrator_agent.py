import time
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from backend.models.models import Document, AgentExecution
from backend.agents.patient_data_agent import PatientDataManagementAgent
from backend.agents.documentation_agent import DocumentationAgent
from backend.agents.validation_agent import ValidationAgent


class OrchestratorAgent:
    """Agent 5: Coordinates end-to-end clinical workflow execution across agents,

    ensuring deterministic sequencing, validation enforcement, and human oversight.
    """

    def __init__(self, db: Session):
        self.db = db
        self.data_agent = PatientDataManagementAgent(db)
        self.doc_agent = DocumentationAgent(db)
        self.val_agent = ValidationAgent(db)

    def execute_document_generation_pipeline(
        self,
        patient_id: str,
        doc_type: str,
        natural_language_request: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Runs the orchestrated pipeline:

        Consolidate Records -> Generate Document -> Validate Document -> Stage for Doctor Review.
        """
        start_time = time.time()
        clean_id = patient_id.strip().upper()
        tools_called = [
            "Orchestrator:initiate_pipeline",
            "PatientDataAgent:consolidate_unified_record",
            "DocumentationAgent:generate_document",
            "ValidationAgent:validate_document"
        ]

        # Step 1: Consolidate Unified Record
        consolidation = self.data_agent.consolidate_unified_record(clean_id)
        if "error" in consolidation:
            self._log_execution(
                task=f"Pipeline Document Generation: {clean_id}",
                patient_id=clean_id,
                tools=tools_called,
                status="Failed",
                summary="Pipeline aborted during data consolidation.",
                error=consolidation["error"],
                latency_ms=int((time.time() - start_time) * 1000)
            )
            return {"error": consolidation["error"]}

        # Step 2: Generate Document
        doc = self.doc_agent.generate_document(
            patient_id=clean_id,
            doc_type=doc_type,
            natural_language_request=natural_language_request,
            created_by_user_id=user_id
        )

        # Step 3: Validate Document
        val_result = self.val_agent.validate_document(doc.id)

        latency = int((time.time() - start_time) * 1000)
        summary_msg = (
            f"Successfully orchestrated pipeline for Patient {clean_id}: "
            f"Doc #{doc.id} created ({doc_type}), Validation={val_result.status} "
            f"({val_result.passed_checks}/{val_result.total_checks}), Status='{doc.validation_status}'."
        )

        self._log_execution(
            task=f"Pipeline Document Generation: {clean_id} ({doc_type})",
            patient_id=clean_id,
            tools=tools_called,
            status="Success",
            summary=summary_msg,
            error=None,
            latency_ms=latency
        )

        return {
            "document_id": doc.id,
            "patient_id": clean_id,
            "doc_type": doc_type,
            "title": doc.title,
            "validation_status": doc.validation_status,
            "validation_checks": {
                "total": val_result.total_checks,
                "passed": val_result.passed_checks,
                "failed": val_result.failed_checks,
                "warnings": val_result.warnings_count,
                "status": val_result.status
            },
            "requires_doctor_review": True,
            "execution_time_ms": latency
        }

    def _log_execution(self, task: str, patient_id: Optional[str], tools: List[str], status: str, summary: str, error: Optional[str], latency_ms: int):
        exec_entry = AgentExecution(
            agent_name="Orchestrator Agent",
            task=task,
            patient_id=patient_id,
            tools_invoked_json=json.dumps(tools),
            execution_status=status,
            result_summary=summary,
            error_message=error,
            latency_ms=latency_ms,
            timestamp=datetime.utcnow()
        )
        self.db.add(exec_entry)
        self.db.commit()

