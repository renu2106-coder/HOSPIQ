export interface User {
  id: number;
  username: string;
  full_name: string;
  email: string;
  role: 'Doctor' | 'Nurse' | 'Pharmacist' | 'Radiologist' | 'Hospital Administrator' | 'Patient' | 'Paramedic';
  department?: string | null;
  patient_id?: string | null;
  is_active: boolean;
  created_at: string;
}

export interface AuthToken {
  access_token: string;
  token_type: string;
  user_id: number;
  username: string;
  role: User['role'];
  full_name: string;
  department?: string | null;
  patient_id?: string | null;
}

export interface Patient {
  id: string;
  first_name: string;
  last_name: string;
  full_name: string;
  dob?: string | null;
  age?: number | null;
  gender?: string | null;
  contact_phone?: string | null;
  email?: string | null;
  address?: string | null;
  blood_group?: string | null;
  emergency_contact?: string | null;
  allergies?: string | null;
  chronic_conditions?: string | null;
  registration_date?: string | null;
  created_at: string;
}

export interface UnifiedPatientRecord {
  id: number;
  patient_id: string;
  completeness_score: number;
  summary_json?: string | null;
  missing_fields_json?: string | null;
  conflict_fields_json?: string | null;
  validation_status: string;
  provenance_json?: string | null;
  last_consolidated_at: string;
}

export interface DocumentVersion {
  id: number;
  document_id: number;
  version_number: number;
  content: string;
  changed_by_user_id?: number | null;
  change_summary?: string | null;
  created_at: string;
}

export interface ValidationCheck {
  check_id: string;
  name: string;
  status: 'Passed' | 'Warning' | 'Failed';
  explanation: string;
}

export interface ValidationResult {
  id: number;
  document_id: number;
  total_checks: number;
  passed_checks: number;
  failed_checks: number;
  warnings_count: number;
  status: 'Passed' | 'Warning' | 'Failed';
  details_json: string;
  created_at: string;
}

export interface ClinicalDocument {
  id: number;
  patient_id: string;
  doc_type: string;
  title: string;
  natural_language_request?: string | null;
  content: string;
  validation_status: 'Generating' | 'Validation Failed' | 'Pending Doctor Review' | 'Approved' | 'Rejected' | 'Revised';
  doctor_notes?: string | null;
  reviewed_by_doctor_id?: number | null;
  reviewed_at?: string | null;
  created_by_user_id?: number | null;
  source_references_json?: string | null;
  created_at: string;
  updated_at: string;
  versions?: DocumentVersion[];
  validation_results?: ValidationResult[];
}

export interface DepartmentAlert {
  id: number;
  alert_id: string;
  patient_id?: string | null;
  department: string;
  alert_category: string;
  description: string;
  priority: 'Low' | 'Medium' | 'High' | 'Critical';
  status: 'Open' | 'Under Investigation' | 'Resolution Pending' | 'Resolved' | 'Dismissed';
  assigned_to?: string | null;
  investigation_notes?: string | null;
  created_at: string;
  resolved_at?: string | null;
}

export interface CorrectionRequest {
  id: number;
  alert_id?: number | null;
  patient_id: string;
  department: string;
  field_name: string;
  original_value?: string | null;
  proposed_value: string;
  justification: string;
  requested_by_user_id?: number | null;
  status: 'Pending Review' | 'Approved' | 'Rejected';
  reviewed_by_user_id?: number | null;
  review_notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface PatientIssue {
  id: number;
  issue_id: string;
  patient_id?: string | null;
  category: string;
  description: string;
  attachment_filename?: string | null;
  status: 'Submitted' | 'Assigned' | 'In Progress' | 'Awaiting Patient Information' | 'Resolved' | 'Rejected';
  priority: 'Low' | 'Medium' | 'High' | 'Critical';
  assigned_department?: string | null;
  routing_reason?: string | null;
  resolution_notes?: string | null;
  submitted_at: string;
  updated_at: string;
  resolved_at?: string | null;
}

export interface UploadedFile {
  id: number;
  original_filename: string;
  stored_filename: string;
  file_type: string;
  file_size: number;
  source_department?: string | null;
  upload_status: string;
  extraction_status: string;
  validation_status: string;
  extracted_text?: string | null;
  patient_id_matched?: string | null;
  record_count: number;
  error_message?: string | null;
  uploaded_at: string;
}

export interface AuditLog {
  id: number;
  event_id: string;
  user_id?: number | null;
  user_role?: string | null;
  action: string;
  entity_type?: string | null;
  entity_id?: string | null;
  status: string;
  details_json?: string | null;
  ip_address?: string | null;
  timestamp: string;
}

export interface AgentExecution {
  id: number;
  agent_name: string;
  task: string;
  patient_id?: string | null;
  tools_invoked_json?: string | null;
  execution_status: string;
  result_summary?: string | null;
  error_message?: string | null;
  latency_ms: number;
  timestamp: string;
}

export interface DashboardStats {
  total_users: number;
  total_patients: number;
  total_doctors: number;
  total_paramedics?: number;
  emergency_documents_issued?: number;
  unique_doctors_used: number;
  doctor_login_sessions: number;
  patient_record_accesses: number;
  documents_generated: number;
  documents_pending_review: number;
  documents_approved: number;
  documents_rejected: number;
  doctor_edits: number;
  open_alerts: number;
  open_issues?: number;
  failed_logins: number;
  unauthorized_attempts: number;
  data_ingestion_files: number;
  records_by_department: Record<string, number>;
  alerts_by_priority: Record<string, number>;
}

export interface LLMStatus {
  provider: string;
  base_url: string;
  configured_model: string;
  connected: boolean;
  available_models: string[];
  model_available: boolean;
  status_message: string;
}

