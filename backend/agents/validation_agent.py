import time
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from backend.models.models import Document, ValidationResult, AgentExecution
from backend.skills.document_validation_skill import validate_clinical_document


class ValidationAgent:
    """Agent 3: Validates generated documents for completeness, consistency,

    date validity, unsupported statements, and source provenance.
    """

    def __init__(self, db: Session):
        self.db = db

    def validate_document(self, document_id: int) -> ValidationResult:
        """Executes the validation suite against the specified document."""
        start_time = time.time()
        tools_called = ["validate_clinical_document", "cross_reference_sources", "check_hallucinations"]

        doc = self.db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            raise ValueError(f"Document with ID {document_id} not found.")

        sources = json.loads(doc.source_references_json) if doc.source_references_json else []

        val_outcome = validate_clinical_document(
            db=self.db,
            patient_id=doc.patient_id,
            doc_type=doc.doc_type,
            content=doc.content,
            source_references=sources
        )

        # Store validation result in database
        val_record = ValidationResult(
            document_id=doc.id,
            total_checks=val_outcome["total_checks"],
            passed_checks=val_outcome["passed_checks"],
            failed_checks=val_outcome["failed_checks"],
            warnings_count=val_outcome["warnings_count"],
            status=val_outcome["status"],
            details_json=json.dumps(val_outcome["checks"]),
            created_at=datetime.utcnow()
        )
        self.db.add(val_record)

        # Update document validation status if critical failure
        if val_outcome["status"] == "Failed":
            doc.validation_status = "Validation Failed"
        elif doc.validation_status in ("Generating", "Validation Failed"):
            doc.validation_status = "Pending Doctor Review"

        self.db.commit()
        self.db.refresh(val_record)

        latency = int((time.time() - start_time) * 1000)
        summary_msg = f"Validation completed for Doc #{doc.id}: Status={val_outcome['status']} ({val_outcome['passed_checks']}/{val_outcome['total_checks']} Passed)."
        self._log_execution(
            task=f"Validate Document #{doc.id} ({doc.doc_type})",
            patient_id=doc.patient_id,
            tools=tools_called,
            status="Success",
            summary=summary_msg,
            error=None,
            latency_ms=latency
        )

        return val_record

    def _log_execution(self, task: str, patient_id: Optional[str], tools: List[str], status: str, summary: str, error: Optional[str], latency_ms: int):
        exec_entry = AgentExecution(
            agent_name="Validation Agent",
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

