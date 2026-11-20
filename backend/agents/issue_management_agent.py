import time
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from backend.models.models import PatientIssue, AgentExecution
from backend.skills.issue_classification_skill import classify_patient_issue


class IssueManagementAgent:
    """Agent 4: Classifies patient-reported complaints, assigns priority,

    recommends department routing, and tracks resolution lifecycle.
    """

    def __init__(self, db: Session):
        self.db = db

    def process_and_route_issue(self, issue_id: int) -> PatientIssue:
        """Processes an incoming patient issue through NLP classification and department routing."""
        start_time = time.time()
        tools_called = ["classify_patient_issue", "route_to_department", "assign_priority"]

        issue = self.db.query(PatientIssue).filter(PatientIssue.id == issue_id).first()
        if not issue:
            raise ValueError(f"Issue #{issue_id} not found.")

        classification = classify_patient_issue(
            category=issue.category,
            description=issue.description
        )

        issue.priority = classification["priority"]
        issue.assigned_department = classification["assigned_department"]
        issue.routing_reason = classification["routing_reason"]
        issue.status = "Assigned"
        issue.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(issue)

        latency = int((time.time() - start_time) * 1000)
        summary_msg = f"Routed Issue {issue.issue_id} to '{classification['assigned_department']}' with '{classification['priority']}' priority."
        self._log_execution(
            task=f"Classify and Route Issue {issue.issue_id}",
            patient_id=issue.patient_id,
            tools=tools_called,
            status="Success",
            summary=summary_msg,
            error=None,
            latency_ms=latency
        )

        return issue

    def _log_execution(self, task: str, patient_id: Optional[str], tools: List[str], status: str, summary: str, error: Optional[str], latency_ms: int):
        exec_entry = AgentExecution(
            agent_name="Issue Management Agent",
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

