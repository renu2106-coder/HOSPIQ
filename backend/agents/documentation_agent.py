import time
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from backend.models.models import Document, DocumentVersion, AgentExecution
from backend.skills.document_generation_skill import generate_clinical_document


class DocumentationAgent:
    """Agent 2: Retrieves patient records and synthesizes clinical documentation

    grounded in actual verified sources. Never modifies database records directly.
    """

    def __init__(self, db: Session):
        self.db = db

    def generate_document(
        self,
        patient_id: str,
        doc_type: str,
        natural_language_request: Optional[str] = None,
        created_by_user_id: Optional[int] = None
    ) -> Document:
        """Generates a structured clinical document draft."""
        start_time = time.time()
        clean_id = patient_id.strip().upper()
        tools_called = ["retrieve_patient_records", "generate_clinical_document", "trace_provenance"]

        content, sources, llm_used = generate_clinical_document(
            db=self.db,
            patient_id=clean_id,
            doc_type=doc_type,
            natural_language_request=natural_language_request or ""
        )

        title = f"{doc_type} - {clean_id} ({datetime.utcnow().strftime('%b %d, %Y')})"

        # Document must start in Pending Doctor Review (never auto-approved!)
        doc = Document(
            patient_id=clean_id,
            doc_type=doc_type,
            title=title,
            natural_language_request=natural_language_request,
            content=content,
            validation_status="Pending Doctor Review",
            source_references_json=json.dumps(sources),
            created_by_user_id=created_by_user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)

        # Version 1 tracking
        v1 = DocumentVersion(
            document_id=doc.id,
            version_number=1,
            content=content,
            changed_by_user_id=created_by_user_id,
            change_summary="Initial AI-generated draft synthesized from verified records.",
            created_at=datetime.utcnow()
        )
        self.db.add(v1)
        self.db.commit()

        latency = int((time.time() - start_time) * 1000)
        summary_msg = f"Generated {doc_type} for {clean_id}. Cited {len(sources)} source departments. LLM utilized: {llm_used}."
        self._log_execution(
            task=f"Generate {doc_type} for {clean_id}",
            patient_id=clean_id,
            tools=tools_called,
            status="Success",
            summary=summary_msg,
            error=None,
            latency_ms=latency
        )

        return doc

    def _log_execution(self, task: str, patient_id: Optional[str], tools: List[str], status: str, summary: str, error: Optional[str], latency_ms: int):
        exec_entry = AgentExecution(
            agent_name="Documentation Agent",
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

