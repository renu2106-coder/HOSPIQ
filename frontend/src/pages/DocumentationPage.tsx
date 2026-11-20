import React, { useEffect, useState } from 'react';
import { ClinicalDocument, ValidationResult, ValidationCheck, DocumentVersion } from '../types';
import { api } from '../services/api';
import {
  FileText, Sparkles, CheckCircle2, AlertTriangle, XCircle,
  Clock, Edit3, Check, X, History, ArrowRight, ShieldCheck, Stethoscope
} from 'lucide-react';

interface DocumentationPageProps {
  currentRole: string;
}

export const DocumentationPage: React.FC<DocumentationPageProps> = ({ currentRole }) => {
  const [documents, setDocuments] = useState<ClinicalDocument[]>([]);
  const [selectedDoc, setSelectedDoc] = useState<ClinicalDocument | null>(null);
  const [patientIdInput, setPatientIdInput] = useState('P001');
  const [docType, setDocType] = useState('Clinical Summary');
  const [prompt, setPrompt] = useState('Generate a comprehensive clinical summary of this patient\'s available medical records.');
  const [generating, setGenerating] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editedContent, setEditedContent] = useState('');
  const [doctorNotes, setDoctorNotes] = useState('');
  const [reviewing, setReviewing] = useState(false);
  const [validationScorecard, setValidationScorecard] = useState<ValidationResult | null>(null);
  const [versions, setVersions] = useState<DocumentVersion[]>([]);
  const [showVersions, setShowVersions] = useState(false);
  const [loading, setLoading] = useState(true);

  const isDoctor = currentRole === 'Doctor';
  const isParamedic = currentRole === 'Paramedic';
  const canEdit = isDoctor || isParamedic;

  useEffect(() => {
    loadDocuments();
  }, []);

  const loadDocuments = async () => {
    setLoading(true);
    try {
      const docs = await api.documents.list();
      setDocuments(docs);
      if (docs.length > 0 && !selectedDoc) {
        selectDocument(docs[0].id);
      }
    } catch (err) {
      console.error('Failed to load documents:', err);
    } finally {
      setLoading(false);
    }
  };

  const selectDocument = async (docId: number) => {
    try {
      const doc = await api.documents.get(docId);
      setSelectedDoc(doc);
      setEditedContent(doc.content);
      setIsEditing(false);
      setDoctorNotes(doc.doctor_notes || '');

      // Load validation result
      const valResults = await api.validation.getValidationResults(docId);
      if (valResults && valResults.length > 0) {
        setValidationScorecard(valResults[0]);
      } else {
        setValidationScorecard(null);
      }

      // Load versions
      const vers = await api.documents.getVersions(docId);
      setVersions(vers);
    } catch (err) {
      console.error('Error fetching document details:', err);
    }
  };

  const handleGenerate = async () => {
    if (!patientIdInput) return;
    setGenerating(true);
    try {
      const doc = await api.documents.generate({
        patient_id: patientIdInput.trim().toUpperCase(),
        doc_type: docType,
        natural_language_request: prompt,
      });
      await loadDocuments();
      await selectDocument(doc.id);
    } catch (err: any) {
      alert('Generation error: ' + err.message);
    } finally {
      setGenerating(false);
    }
  };

  const handleSaveEdit = async () => {
    if (!selectedDoc || !canEdit) return;
    try {
      const updated = await api.documents.edit(selectedDoc.id, {
        content: editedContent,
        change_summary: isParamedic ? 'Paramedic field update and clinical revision.' : 'Physician revision and clinical adjustments.'
      });
      setSelectedDoc(updated);
      setIsEditing(false);
      await selectDocument(updated.id);
      await loadDocuments();
    } catch (err: any) {
      alert('Failed to save document revision: ' + err.message);
    }
  };

  const handleReviewAction = async (action: 'APPROVE' | 'REJECT') => {
    if (!selectedDoc || !isDoctor) return;
    setReviewing(true);
    try {
      const reviewed = await api.documents.review(selectedDoc.id, {
        action,
        doctor_notes: doctorNotes,
      });
      setSelectedDoc(reviewed);
      await selectDocument(reviewed.id);
      await loadDocuments();
    } catch (err: any) {
      alert('Review action failed: ' + err.message);
    } finally {
      setReviewing(false);
    }
  };

  const handleEmergencyIssue = async () => {
    if (!selectedDoc || !isParamedic) return;
    const reason = window.prompt(
      "EXTREME EMERGENCY DIRECT ISSUANCE:\nEnter Emergency Override Reason (e.g., Critical field triage handover, Cardiac arrest en route):",
      "Critical Emergency Field Triage Attestation"
    );
    if (!reason) return;

    setReviewing(true);
    try {
      const reviewed = await api.documents.review(selectedDoc.id, {
        action: 'APPROVE',
        is_emergency: true,
        emergency_override_reason: reason,
        doctor_notes: doctorNotes || 'Directly issued by Paramedic under extreme emergency protocol.',
      });
      setSelectedDoc(reviewed);
      await selectDocument(reviewed.id);
      await loadDocuments();
      alert('Emergency Document Successfully Direct-Issued!');
    } catch (err: any) {
      alert('Emergency issuance failed: ' + err.message);
    } finally {
      setReviewing(false);
    }
  };

  const quickPrompts = [
    'Generate a summary of this patient\'s available medical records.',
    'Prepare a visit summary using the latest available records.',
    'Generate a discharge summary using the available inpatient information.',
    'Summarize the patient\'s recent laboratory results and abnormal findings.'
  ];

  return (
    <div style={{ padding: '28px', maxWidth: '1350px', margin: '0 auto' }}>
      {/* Title */}
      <div style={{ marginBottom: '20px' }}>
        <h2 style={{ fontSize: '20px', fontWeight: 700, color: 'var(--primary-navy)' }}>
          AI Clinical Documentation & Verification Studio
        </h2>
        <p style={{ fontSize: '13px', color: 'var(--secondary-text)', marginTop: '2px' }}>
          Grounded multi-agent synthesis with 7-point validation and mandatory physician attestation.
        </p>
      </div>

      {/* Generation Workspace Card */}
      {canEdit && (
        <div className="card" style={{ marginBottom: '24px', backgroundColor: '#FBFDFF' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
            <Sparkles size={18} color="var(--primary-teal)" />
            <h3 style={{ fontSize: '15px', fontWeight: 700, color: 'var(--primary-navy)' }}>
              {isParamedic ? 'Paramedic Emergency Documentation Draft' : 'Orchestrate New Clinical Document Draft'}
            </h3>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.5fr 2fr auto', gap: '12px', alignItems: 'flex-end' }}>
            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--primary-text)', marginBottom: '4px' }}>
                Patient ID
              </label>
              <input
                type="text"
                value={patientIdInput}
                onChange={(e) => setPatientIdInput(e.target.value)}
                placeholder="e.g. P001"
                style={{
                  width: '100%',
                  padding: '8px 10px',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--border)',
                  fontSize: '13px'
                }}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--primary-text)', marginBottom: '4px' }}>
                Document Type
              </label>
              <select
                value={docType}
                onChange={(e) => setDocType(e.target.value)}
                style={{
                  width: '100%',
                  padding: '8px 10px',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--border)',
                  fontSize: '13px'
                }}
              >
                <option value="Clinical Summary">Clinical Summary</option>
                <option value="Patient Visit Summary">Patient Visit Summary</option>
                <option value="Discharge Summary">Discharge Summary</option>
                <option value="Laboratory Summary">Laboratory Summary</option>
              </select>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--primary-text)', marginBottom: '4px' }}>
                Natural Language Request
              </label>
              <input
                type="text"
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Specific instructions for the Documentation Agent..."
                style={{
                  width: '100%',
                  padding: '8px 10px',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--border)',
                  fontSize: '13px'
                }}
              />
            </div>

            <button
              onClick={handleGenerate}
              disabled={generating}
              className="btn-primary"
              style={{ padding: '9px 18px', whiteSpace: 'nowrap' }}
            >
              <Sparkles size={16} />
              <span>{generating ? 'Agents Synthesizing...' : 'Synthesize Draft'}</span>
            </button>
          </div>

          {/* Quick suggestions */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '12px', flexWrap: 'wrap' }}>
            <span style={{ fontSize: '11px', fontWeight: 600, color: 'var(--secondary-text)' }}>Prompt Presets:</span>
            {quickPrompts.map((preset, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => setPrompt(preset)}
                style={{
                  padding: '3px 8px',
                  fontSize: '11.5px',
                  borderRadius: '12px',
                  border: '1px solid var(--border)',
                  backgroundColor: '#FFFFFF',
                  color: 'var(--primary-text)',
                  cursor: 'pointer'
                }}
              >
                {preset}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Main Grid: Document List Sidebar + Document Review View */}
      <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: '20px' }}>
        {/* Left: Document List */}
        <div className="card" style={{ padding: '16px', maxHeight: '720px', overflowY: 'auto' }}>
          <h3 style={{ fontSize: '14px', fontWeight: 700, color: 'var(--primary-navy)', marginBottom: '12px' }}>
            Generated Documents ({documents.length})
          </h3>

          {loading ? (
            <div style={{ fontSize: '12.5px', color: 'var(--secondary-text)', textAlign: 'center', padding: '20px' }}>
              Loading documents...
            </div>
          ) : documents.length === 0 ? (
            <div style={{ fontSize: '12.5px', color: 'var(--secondary-text)', textAlign: 'center', padding: '20px' }}>
              No clinical documents on file.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {documents.map((doc) => (
                <div
                  key={doc.id}
                  onClick={() => selectDocument(doc.id)}
                  style={{
                    padding: '10px 12px',
                    borderRadius: 'var(--radius-sm)',
                    border: `1px solid ${selectedDoc?.id === doc.id ? 'var(--primary-teal)' : 'var(--border)'}`,
                    backgroundColor: selectedDoc?.id === doc.id ? '#F0F9F8' : '#FFFFFF',
                    cursor: 'pointer',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '4px'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '13px', fontWeight: 700, color: 'var(--primary-navy)' }}>
                      {doc.patient_id} • {doc.doc_type}
                    </span>
                    <span className={`badge ${
                      doc.validation_status === 'Approved' ? 'badge-success' :
                      doc.validation_status === 'Validation Failed' ? 'badge-error' :
                      'badge-warning'
                    }`} style={{ fontSize: '10.5px' }}>
                      {doc.validation_status}
                    </span>
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--secondary-text)' }}>
                    Created: {new Date(doc.created_at).toLocaleDateString()}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right: Document Inspector & Review Workspace */}
        {selectedDoc ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {/* Top Status & Attestation Controls Card */}
            <div className="card">
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <h3 style={{ fontSize: '16px', fontWeight: 800, color: 'var(--primary-navy)' }}>
                      {selectedDoc.title}
                    </h3>
                    <span className={`badge ${
                      selectedDoc.validation_status === 'Approved' ? 'badge-success' :
                      selectedDoc.validation_status === 'Validation Failed' ? 'badge-error' :
                      'badge-warning'
                    }`}>
                      {selectedDoc.validation_status}
                    </span>
                  </div>
                  <div style={{ fontSize: '12px', color: 'var(--secondary-text)', marginTop: '2px' }}>
                    Patient: <strong>{selectedDoc.patient_id}</strong> • Created: {new Date(selectedDoc.created_at).toLocaleString()}
                  </div>
                </div>

                <div style={{ display: 'flex', gap: '8px' }}>
                  <button
                    onClick={() => setShowVersions(!showVersions)}
                    className="btn-secondary"
                    style={{ fontSize: '12px', padding: '6px 12px' }}
                  >
                    <History size={14} />
                    <span>Version History ({versions.length})</span>
                  </button>

                  {canEdit && !isEditing && selectedDoc.validation_status !== 'Approved' && (
                    <button
                      onClick={() => setIsEditing(true)}
                      className="btn-secondary"
                      style={{ fontSize: '12px', padding: '6px 12px' }}
                    >
                      <Edit3 size={14} />
                      <span>{isParamedic ? 'Edit Summary (Paramedic)' : 'Edit Content'}</span>
                    </button>
                  )}
                </div>
              </div>

              {/* Review & Attestation Banner */}
              {isDoctor ? (
                <div style={{
                  padding: '12px 16px',
                  backgroundColor: '#F8FAFC',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--border)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: '16px'
                }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--primary-navy)', marginBottom: '4px' }}>
                      Physician Attestation & Clinical Review Notes:
                    </div>
                    <input
                      type="text"
                      value={doctorNotes}
                      onChange={(e) => setDoctorNotes(e.target.value)}
                      placeholder="Enter physician sign-off notes or revision rationale..."
                      style={{
                        width: '100%',
                        padding: '6px 10px',
                        borderRadius: 'var(--radius-sm)',
                        border: '1px solid var(--border)',
                        fontSize: '12.5px'
                      }}
                    />
                  </div>

                  <div style={{ display: 'flex', gap: '8px', flexShrink: 0 }}>
                    <button
                      onClick={() => handleReviewAction('APPROVE')}
                      disabled={reviewing}
                      className="btn-primary"
                      style={{ padding: '8px 14px', fontSize: '13px', backgroundColor: 'var(--success)' }}
                    >
                      <Check size={16} />
                      <span>Approve Document</span>
                    </button>
                    <button
                      onClick={() => handleReviewAction('REJECT')}
                      disabled={reviewing}
                      className="btn-secondary"
                      style={{ padding: '8px 14px', fontSize: '13px', color: 'var(--error)' }}
                    >
                      <X size={16} />
                      <span>Reject</span>
                    </button>
                  </div>
                </div>
              ) : isParamedic ? (
                <div style={{
                  padding: '12px 16px',
                  backgroundColor: '#FFF7ED',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid #FED7AA',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: '16px'
                }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: '12px', fontWeight: 700, color: '#9A3412', marginBottom: '4px' }}>
                      Paramedic Access • Discharge & Clinical Summary:
                    </div>
                    <div style={{ fontSize: '11.5px', color: '#C2410C', marginBottom: '6px' }}>
                      You can edit this summary. Routine reviews are approved by Doctors. In extreme emergency conditions, you can directly issue this document below.
                    </div>
                    <input
                      type="text"
                      value={doctorNotes}
                      onChange={(e) => setDoctorNotes(e.target.value)}
                      placeholder="Optional paramedic field notes..."
                      style={{
                        width: '100%',
                        padding: '6px 10px',
                        borderRadius: 'var(--radius-sm)',
                        border: '1px solid #FED7AA',
                        fontSize: '12.5px',
                        backgroundColor: '#FFFFFF'
                      }}
                    />
                  </div>

                  <div style={{ display: 'flex', gap: '8px', flexShrink: 0 }}>
                    <button
                      onClick={handleEmergencyIssue}
                      disabled={reviewing}
                      className="btn-primary"
                      style={{
                        padding: '8px 14px',
                        fontSize: '13px',
                        backgroundColor: '#EA580C',
                        borderColor: '#C2410C'
                      }}
                    >
                      <Check size={16} />
                      <span>⚡ Extreme Emergency Direct Issue</span>
                    </button>
                  </div>
                </div>
              ) : (
                <div style={{
                  padding: '10px 14px',
                  backgroundColor: '#F8FAFC',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--border)',
                  fontSize: '12px',
                  color: 'var(--secondary-text)'
                }}>
                  <strong>Notice:</strong> Document review is reserved for Doctors and Paramedics (in emergency overrides). Your role ({currentRole}) has read-only access.
                </div>
              )}
            </div>

            {/* Validation Scorecard Card */}
            {validationScorecard && (
              <div className="card" style={{ backgroundColor: '#FCFDFE' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <ShieldCheck size={18} color="var(--clinical-blue)" />
                    <h4 style={{ fontSize: '14px', fontWeight: 700, color: 'var(--primary-navy)' }}>
                      7-Point Validation Agent Scorecard
                    </h4>
                  </div>
                  <div style={{ fontSize: '12px', fontWeight: 600 }}>
                    Score: <span style={{ color: 'var(--success)' }}>{validationScorecard.passed_checks} Passed</span> •{' '}
                    <span style={{ color: 'var(--warning)' }}>{validationScorecard.warnings_count} Warnings</span> •{' '}
                    <span style={{ color: 'var(--error)' }}>{validationScorecard.failed_checks} Failed</span>
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '8px' }}>
                  {JSON.parse(validationScorecard.details_json).map((check: ValidationCheck) => (
                    <div
                      key={check.check_id}
                      style={{
                        padding: '8px 10px',
                        borderRadius: 'var(--radius-sm)',
                        border: '1px solid var(--border)',
                        backgroundColor: '#FFFFFF',
                        display: 'flex',
                        alignItems: 'flex-start',
                        gap: '8px'
                      }}
                    >
                      {check.status === 'Passed' && <CheckCircle2 size={16} color="var(--success)" style={{ flexShrink: 0, marginTop: '2px' }} />}
                      {check.status === 'Warning' && <AlertTriangle size={16} color="var(--warning)" style={{ flexShrink: 0, marginTop: '2px' }} />}
                      {check.status === 'Failed' && <XCircle size={16} color="var(--error)" style={{ flexShrink: 0, marginTop: '2px' }} />}
                      <div>
                        <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--primary-text)' }}>
                          {check.name}
                        </div>
                        <div style={{ fontSize: '11px', color: 'var(--secondary-text)', lineHeight: 1.3 }}>
                          {check.explanation}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Document Content Workspace */}
            <div className="card">
              {isEditing ? (
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                    <span style={{ fontSize: '13px', fontWeight: 700, color: 'var(--primary-navy)' }}>
                      Editing Clinical Text
                    </span>
                    <div style={{ display: 'flex', gap: '8px' }}>
                      <button onClick={handleSaveEdit} className="btn-primary" style={{ padding: '6px 12px', fontSize: '12px' }}>
                        Save Revision
                      </button>
                      <button onClick={() => setIsEditing(false)} className="btn-secondary" style={{ padding: '6px 12px', fontSize: '12px' }}>
                        Cancel
                      </button>
                    </div>
                  </div>
                  <textarea
                    rows={18}
                    value={editedContent}
                    onChange={(e) => setEditedContent(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '12px',
                      borderRadius: 'var(--radius-sm)',
                      border: '1px solid var(--border)',
                      fontFamily: 'monospace',
                      fontSize: '13px',
                      lineHeight: 1.5,
                      outline: 'none'
                    }}
                  />
                </div>
              ) : (
                <div style={{
                  padding: '8px',
                  backgroundColor: '#FFFFFF',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '13.5px',
                  lineHeight: 1.6,
                  color: 'var(--primary-text)',
                  whiteSpace: 'pre-wrap'
                }}>
                  {selectedDoc.content}
                </div>
              )}
            </div>

            {/* Version History Drawer */}
            {showVersions && (
              <div className="card">
                <h4 style={{ fontSize: '14px', fontWeight: 700, color: 'var(--primary-navy)', marginBottom: '10px' }}>
                  Immutable Document Versions
                </h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {versions.map((v) => (
                    <div
                      key={v.id}
                      style={{
                        padding: '10px 12px',
                        backgroundColor: '#F8FAFC',
                        borderRadius: 'var(--radius-sm)',
                        border: '1px solid var(--border)',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center'
                      }}
                    >
                      <div>
                        <span style={{ fontSize: '12.5px', fontWeight: 700, color: 'var(--primary-navy)' }}>
                          Version {v.version_number}
                        </span>
                        <span style={{ fontSize: '12px', color: 'var(--secondary-text)', marginLeft: '8px' }}>
                          {v.change_summary || 'No description'}
                        </span>
                      </div>
                      <span style={{ fontSize: '11px', color: 'var(--secondary-text)' }}>
                        {new Date(v.created_at).toLocaleString()}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="card" style={{ padding: '40px', textAlign: 'center', color: 'var(--secondary-text)' }}>
            Select a document from the left or generate a new draft using the clinical orchestrator.
          </div>
        )}
      </div>
    </div>
  );
};

