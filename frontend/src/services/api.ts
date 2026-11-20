import {
  AuthToken, User, Patient, UnifiedPatientRecord, ClinicalDocument,
  DocumentVersion, ValidationResult, DepartmentAlert, CorrectionRequest,
  PatientIssue, UploadedFile, AuditLog, AgentExecution, DashboardStats,
  LLMStatus
} from '../types';

const API_BASE = typeof window !== 'undefined' && window.location.origin.includes(':5173')
  ? 'http://127.0.0.1:8000/api'
  : '/api';

function getAuthHeaders(): HeadersInit {
  const token = localStorage.getItem('hospiq_token');
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const headers = options.body instanceof FormData
    ? {
        ...(localStorage.getItem('hospiq_token')
          ? { Authorization: `Bearer ${localStorage.getItem('hospiq_token')}` }
          : {}),
        ...options.headers,
      }
    : {
        ...getAuthHeaders(),
        ...options.headers,
      };

  const response = await fetch(url, { ...options, headers });
  if (!response.ok) {
    let errorDetail = 'Request failed';
    try {
      const errJson = await response.json();
      errorDetail = errJson.detail || errJson.message || JSON.stringify(errJson);
    } catch {
      errorDetail = await response.text();
    }
    throw new Error(errorDetail || `HTTP ${response.status}`);
  }
  return response.json();
}

export const api = {
  auth: {
    login: (credentials: { username: string; password: string }) =>
      request<AuthToken>('/auth/login', {
        method: 'POST',
        body: JSON.stringify(credentials),
      }),
    initiate2FA: (credentials: { username: string; password: string }) =>
      request<{ requires_2fa: boolean; session_id: string; username: string; full_name: string; role: string; masked_contact: string; security_code: string }>('/auth/initiate-2fa', {
        method: 'POST',
        body: JSON.stringify(credentials),
      }),
    verify2FA: (data: { username: string; code: string }) =>
      request<AuthToken>('/auth/verify-2fa', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    getDemoUsers: () => request<Array<{ role: string; username: string; password: string; name: string; dept: string }>>('/auth/demo-users'),
    getProfile: () => request<User>('/auth/me'),
    logout: () => request<{ message: string; time_of_exit?: string; session_duration?: string }>('/auth/logout', { method: 'POST' }),
  },

  patients: {
    list: (query?: string) => request<Patient[]>(`/patients${query ? `?query=${encodeURIComponent(query)}` : ''}`),
    get: (id: string) => request<Patient>(`/patients/${id}`),
    getUnified: (id: string) => request<UnifiedPatientRecord>(`/patients/${id}/unified`),
    getFHIR: (id: string) => request<any>(`/patients/${id}/fhir`),
    reconsolidate: (id: string) => request<any>(`/patients/${id}/reconsolidate`, { method: 'POST' }),
  },

  records: {
    getPatientRecords: (patientId: string) => request<any>(`/records/patient/${patientId}`),
    getRegistration: (patientId?: string) => request<any[]>(`/records/registration${patientId ? `?patient_id=${patientId}` : ''}`),
    getLaboratory: (patientId?: string) => request<any[]>(`/records/laboratory${patientId ? `?patient_id=${patientId}` : ''}`),
    getPharmacy: (patientId?: string) => request<any[]>(`/records/pharmacy${patientId ? `?patient_id=${patientId}` : ''}`),
    getRadiology: (patientId?: string) => request<any[]>(`/records/radiology${patientId ? `?patient_id=${patientId}` : ''}`),
    getNursing: (patientId?: string) => request<any[]>(`/records/nursing${patientId ? `?patient_id=${patientId}` : ''}`),
    getInpatient: (patientId?: string) => request<any[]>(`/records/inpatient${patientId ? `?patient_id=${patientId}` : ''}`),
    getAppointments: (patientId?: string) => request<any[]>(`/records/appointments${patientId ? `?patient_id=${patientId}` : ''}`),
    getBilling: (patientId?: string) => request<any[]>(`/records/billing${patientId ? `?patient_id=${patientId}` : ''}`),
  },

  documents: {
    generate: (data: { patient_id: string; doc_type: string; natural_language_request?: string }) =>
      request<ClinicalDocument>('/documents/generate', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    list: (patientId?: string) => request<ClinicalDocument[]>(`/documents${patientId ? `?patient_id=${patientId}` : ''}`),
    get: (id: number) => request<ClinicalDocument>(`/documents/${id}`),
    edit: (id: number, data: { content: string; change_summary?: string }) =>
      request<ClinicalDocument>(`/documents/${id}`, {
        method: 'PUT',
        body: JSON.stringify(data),
      }),
    review: (id: number, data: { action: 'APPROVE' | 'REJECT'; doctor_notes?: string; is_emergency?: boolean; emergency_override_reason?: string }) =>
      request<ClinicalDocument>(`/documents/${id}/review`, {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    getVersions: (id: number) => request<DocumentVersion[]>(`/documents/${id}/versions`),
  },

  validation: {
    validateDocument: (docId: number) =>
      request<ValidationResult>(`/validation/document/${docId}`, { method: 'POST' }),
    getValidationResults: (docId: number) =>
      request<ValidationResult[]>(`/validation/document/${docId}`),
  },

  alerts: {
    list: (filters?: { department?: string; priority?: string; status_filter?: string; patient_id?: string }) => {
      const params = new URLSearchParams();
      if (filters?.department) params.append('department', filters.department);
      if (filters?.priority) params.append('priority', filters.priority);
      if (filters?.status_filter) params.append('status_filter', filters.status_filter);
      if (filters?.patient_id) params.append('patient_id', filters.patient_id);
      return request<DepartmentAlert[]>(`/alerts?${params.toString()}`);
    },
    updateStatus: (alertId: string, data: { status: string; investigation_notes?: string; assigned_to?: string }) =>
      request<DepartmentAlert>(`/alerts/${alertId}`, {
        method: 'PATCH',
        body: JSON.stringify(data),
      }),
  },

  corrections: {
    create: (data: { alert_id?: number; patient_id: string; department: string; field_name: string; original_value?: string; proposed_value: string; justification: string }) =>
      request<CorrectionRequest>('/corrections', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    list: (patientId?: string, statusFilter?: string) => {
      const params = new URLSearchParams();
      if (patientId) params.append('patient_id', patientId);
      if (statusFilter) params.append('status_filter', statusFilter);
      return request<CorrectionRequest[]>(`/corrections?${params.toString()}`);
    },
    review: (id: number, data: { action: 'APPROVE' | 'REJECT'; review_notes?: string }) =>
      request<CorrectionRequest>(`/corrections/${id}/review`, {
        method: 'POST',
        body: JSON.stringify(data),
      }),
  },

  uploads: {
    uploadFile: (file: File, department: string, autoSync: boolean = true) => {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('department', department);
      formData.append('auto_sync', autoSync ? 'true' : 'false');
      return request<UploadedFile>('/uploads', {
        method: 'POST',
        body: formData,
      });
    },
    autoSyncFile: (fileId: number) =>
      request<any>(`/uploads/${fileId}/auto-sync`, { method: 'POST' }),
    autoSyncAll: () =>
      request<any>('/uploads/auto-sync-all', { method: 'POST' }),
    getNormalizedText: (fileId: number) =>
      request<any>(`/uploads/${fileId}/normalized-text`),
    list: (department?: string) =>
      request<UploadedFile[]>(`/uploads${department ? `?department=${encodeURIComponent(department)}` : ''}`),
  },

  agents: {
    listExecutions: (agentName?: string, patientId?: string) => {
      const params = new URLSearchParams();
      if (agentName) params.append('agent_name', agentName);
      if (patientId) params.append('patient_id', patientId);
      return request<AgentExecution[]>(`/agents/executions?${params.toString()}`);
    },
    getLLMStatus: () => request<LLMStatus>('/agents/llm-status'),
    getDuplicates: () => request<{ status: string; detected_duplicates_count: number; duplicates: any[] }>('/agents/duplicate-detection'),
    consolidateAll: () => request<any>('/agents/consolidate-all', { method: 'POST' }),
  },

  audit: {
    list: (filters?: { action?: string; user_id?: number; entity_type?: string; status_filter?: string; limit?: number }) => {
      const params = new URLSearchParams();
      if (filters?.action) params.append('action', filters.action);
      if (filters?.user_id) params.append('user_id', filters.user_id.toString());
      if (filters?.entity_type) params.append('entity_type', filters.entity_type);
      if (filters?.status_filter) params.append('status_filter', filters.status_filter);
      if (filters?.limit) params.append('limit', filters.limit.toString());
      return request<AuditLog[]>(`/audit?${params.toString()}`);
    },
    getScope: () =>
      request<{ user_id: number; full_name: string; role: string; is_master_admin: boolean; scope_description: string }>('/audit/scope'),
  },

  dashboard: {
    getMetrics: () => request<DashboardStats>('/dashboard/metrics'),
  },

  tools: {
    list: () => request<Array<{ name: string; category: string; description: string; parameters: any; page_reference: string }>>('/tools'),
    execute: (toolName: string, args: any) =>
      request<any>(`/tools/${toolName}`, {
        method: 'POST',
        body: JSON.stringify(args),
      }),
  },

  testCases: {
    runAll: () => request<Array<{
      test_case_id: number;
      title: string;
      page_reference: string;
      description: string;
      patient_id: string;
      input_summary: string;
      result_status: string;
      details: any;
    }>>('/test-cases/all'),
    runSingle: (id: number) => request<any>(`/test-cases/${id}`),
  },
};

