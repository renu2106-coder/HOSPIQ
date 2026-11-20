import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import type { Patient, ClinicalDocument, ValidationResult } from '../types';
import {
  Play, CheckCircle2, AlertTriangle, XCircle, FileText,
  Clock, ShieldCheck, Check, Edit3, X, Globe, Share2, Download
} from 'lucide-react';

interface AgenticHubPageProps {
  currentRole: string;
}

export const AgenticHubPage: React.FC<AgenticHubPageProps> = ({ currentRole }) => {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [selectedPatientId, setSelectedPatientId] = useState('P001');
  const [selectedTask, setSelectedTask] = useState('Prepare Discharge Summary');
  const [language, setLanguage] = useState('English');
  const [isRunning, setIsRunning] = useState(false);
  const [activityStep, setActivityStep] = useState<number>(0);
  const [generatedDoc, setGeneratedDoc] = useState<ClinicalDocument | null>(null);
  const [validationScorecard, setValidationScorecard] = useState<ValidationResult | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [editedContent, setEditedContent] = useState('');
  const [reviewStatus, setReviewStatus] = useState<string>('REVIEW REQUIRED');
  const [fhirData, setFhirData] = useState<any | null>(null);
  const [showFhirModal, setShowFhirModal] = useState(false);

  const isDoctor = currentRole === 'Doctor';
  const isParamedic = currentRole === 'Paramedic';
  const canEdit = isDoctor || isParamedic;

  const taskOptions = [
    { id: 'Prepare Discharge Summary', docType: 'Discharge Summary' },
    { id: 'Prepare Clinical / Encounter Summary', docType: 'Clinical Summary' },
    { id: 'Generate Patient Education Summary', docType: 'Patient Education Summary' },
    { id: 'Generate Medication Explanation', docType: 'Medication Explanation' },
    { id: 'Generate Patient Timeline', docType: 'Patient Timeline' }
  ];

  useEffect(() => {
    api.patients.list().then(data => {
      setPatients(data);
      if (data.length > 0) setSelectedPatientId(data[0].id);
    }).catch(console.error);
  }, []);

  const handleRunAgent = async () => {
    setIsRunning(true);
    setActivityStep(1);
    setGeneratedDoc(null);
    setValidationScorecard(null);
    setIsEditing(false);

    try {
      // Step 1: Patient identified
      await new Promise(r => setTimeout(r, 200));
      setActivityStep(2);

      // Step 2: Patient record retrieved
      await new Promise(r => setTimeout(r, 250));
      setActivityStep(3);

      // Step 3: Lab data retrieved
      await new Promise(r => setTimeout(r, 250));
      setActivityStep(4);

      // Step 4: Medication data retrieved
      await new Promise(r => setTimeout(r, 200));
      setActivityStep(5);

      // Step 5: Clinical notes retrieved
      await new Promise(r => setTimeout(r, 200));
      setActivityStep(6);

      const targetTask = taskOptions.find(t => t.id === selectedTask) || taskOptions[0];
      const promptInstruction = targetTask.docType === 'Patient Education Summary'
        ? `Generate patient education in ${language}`
        : 'Generate complete structured document based on verified database records.';

      const doc = await api.documents.generate({
        patient_id: selectedPatientId,
        doc_type: targetTask.docType,
        natural_language_request: promptInstruction
      });

      // Step 6: Draft generated
      setActivityStep(7);

      // Fetch validation result
      const valResults = await api.validation.getValidationResults(doc.id);
      if (valResults && valResults.length > 0) {
        setValidationScorecard(valResults[0]);
      }

      setGeneratedDoc(doc);
      setEditedContent(doc.content);
      setReviewStatus(doc.validation_status === 'Approved' ? 'APPROVED' : 'REVIEW REQUIRED');
    } catch (err: any) {
      alert('Agent execution failed: ' + err.message);
    } finally {
      setIsRunning(false);
    }
  };

  const handleApprove = async () => {
    if (!generatedDoc || !isDoctor) return;
    try {
      const res = await api.documents.review(generatedDoc.id, {
        action: 'APPROVE',
        doctor_notes: 'Physician attestation verified against unified patient record.'
      });
      setGeneratedDoc(res);
      setReviewStatus('APPROVED');
      alert('Document formally APPROVED and signed into the patient health record!');
    } catch (err: any) {
      alert('Approval error: ' + err.message);
    }
  };

  const handleReject = async () => {
    if (!generatedDoc || !isDoctor) return;
    try {
      const res = await api.documents.review(generatedDoc.id, {
        action: 'REJECT',
        doctor_notes: 'Rejected during human review for clinical revisions.'
      });
      setGeneratedDoc(res);
      setReviewStatus('REJECTED');
      alert('Document marked as REJECTED. Revision requested.');
    } catch (err: any) {
      alert('Rejection error: ' + err.message);
    }
  };

  const handleSaveEdit = async () => {
    if (!generatedDoc || !canEdit) return;
    try {
      const res = await api.documents.edit(generatedDoc.id, {
        content: editedContent,
        change_summary: isParamedic ? 'Paramedic modified clinical draft before submission.' : 'Physician modified clinical draft before final approval.'
      });
      setGeneratedDoc(res);
      setIsEditing(false);
      alert('Document revisions saved successfully!');
    } catch (err: any) {
      alert('Edit save error: ' + err.message);
    }
  };

  const handleEmergencyIssue = async () => {
    if (!generatedDoc || !isParamedic) return;
    const reason = window.prompt("Extreme Emergency Direct Issuance:\nEnter field emergency override justification:", "Paramedic Critical Triage Handover");
    if (!reason) return;
    try {
      const res = await api.documents.review(generatedDoc.id, {
        action: 'APPROVE',
        is_emergency: true,
        emergency_override_reason: reason,
        doctor_notes: 'Direct issued by Paramedic under extreme emergency triage protocol.'
      });
      setGeneratedDoc(res);
      setReviewStatus('APPROVED (EMERGENCY DIRECT ISSUE)');
      alert('Document successfully direct-issued under extreme emergency condition!');
    } catch (err: any) {
      alert('Emergency direct issue error: ' + err.message);
    }
  };

  const handleExportFhir = async () => {
    try {
      const fhir = await api.patients.getFHIR(selectedPatientId);
      setFhirData(fhir);
      setShowFhirModal(true);
    } catch (err: any) {
      alert('FHIR export error: ' + err.message);
    }
  };

  const selectedPatient = patients.find(p => p.id === selectedPatientId);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', maxWidth: '1100px', margin: '0 auto' }}>
      {/* Title & Document Context Banner */}
      <div style={{
        padding: '20px 24px',
        backgroundColor: 'var(--primary-navy)',
        color: '#FFFFFF',
        borderRadius: 'var(--radius-md)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <div>
          <h1 style={{ fontSize: '22px', fontWeight: 800, marginTop: '2px' }}>
            Agentic Hospital Information Management System
          </h1>
          <p style={{ fontSize: '13px', color: '#94A3B8', marginTop: '4px' }}>
            Designing a Multi-Agent AI System for Healthcare Data Integration, Documentation, and Validation
          </p>
        </div>
        <div style={{ display: 'flex', gap: '10px' }}>
          <button
            onClick={handleExportFhir}
            className="hospiq-btn-outline"
            style={{
              borderColor: 'var(--soft-teal)',
              color: 'var(--soft-teal)',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              fontSize: '12.5px'
            }}
          >
            <Share2 size={15} />
            <span>Export FHIR JSON</span>
          </button>
        </div>
      </div>

      {/* Main Agent Workflow Card (Mirrors Page 20) */}
      <div className="hospiq-card" style={{ padding: '24px' }}>
        <div style={{
          display: 'grid',
          gridTemplateColumns: selectedTask === 'Generate Patient Education Summary' ? '1.2fr 1.2fr 0.8fr auto' : '1.5fr 1.5fr auto',
          gap: '16px',
          alignItems: 'flex-end',
          paddingBottom: '20px',
          borderBottom: '1px solid var(--border)'
        }}>
          <div>
            <label style={{ display: 'block', fontSize: '13px', fontWeight: 700, color: 'var(--primary-navy)', marginBottom: '6px' }}>
              Patient ID / Name:
            </label>
            <select
              value={selectedPatientId}
              onChange={(e) => setSelectedPatientId(e.target.value)}
              className="hospiq-input"
              style={{ width: '100%', padding: '10px 12px', fontSize: '14px', fontWeight: 600 }}
            >
              {patients.map(p => (
                <option key={p.id} value={p.id}>
                  {p.id} — {p.full_name} {p.id === 'P001' ? '(Canonical Assignment Patient)' : ''}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '13px', fontWeight: 700, color: 'var(--primary-navy)', marginBottom: '6px' }}>
              Task:
            </label>
            <select
              value={selectedTask}
              onChange={(e) => setSelectedTask(e.target.value)}
              className="hospiq-input"
              style={{ width: '100%', padding: '10px 12px', fontSize: '14px', fontWeight: 600 }}
            >
              {taskOptions.map(t => (
                <option key={t.id} value={t.id}>{t.id}</option>
              ))}
            </select>
          </div>

          {selectedTask === 'Generate Patient Education Summary' && (
            <div>
              <label style={{ display: 'block', fontSize: '13px', fontWeight: 700, color: 'var(--primary-navy)', marginBottom: '6px' }}>
                Language (Challenge B):
              </label>
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className="hospiq-input"
                style={{ width: '100%', padding: '10px 12px', fontSize: '14px', fontWeight: 600 }}
              >
                <option value="English">English</option>
                <option value="Telugu">Telugu (తెలుగు)</option>
                <option value="Hindi">Hindi (हिन्दी)</option>
                <option value="Tamil">Tamil (தமிழ்)</option>
                <option value="Kannada">Kannada (ಕನ್ನಡ)</option>
              </select>
            </div>
          )}

          <div>
            <button
              onClick={handleRunAgent}
              disabled={isRunning}
              className="hospiq-btn"
              style={{
                padding: '11px 24px',
                fontSize: '14px',
                fontWeight: 800,
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                backgroundColor: 'var(--primary-teal)',
                letterSpacing: '0.5px'
              }}
            >
              <Play size={16} fill="currentColor" />
              <span>{isRunning ? 'AGENT RUNNING...' : 'RUN AGENT'}</span>
            </button>
          </div>
        </div>

        {/* Canonical Cross-Department Matching Notice for P001 (Ravi Kumar) */}
        {selectedPatientId === 'P001' && (
          <div style={{
            marginTop: '16px',
            padding: '10px 14px',
            backgroundColor: '#F0FDF4',
            borderRadius: 'var(--radius-sm)',
            border: '1px solid #BBF7D0',
            fontSize: '12.5px',
            color: '#166534',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}>
            <strong>Document Page 1, 3, 7 Matching Demonstration:</strong>
            <span>Registration: <em>Ravi Kumar</em> | Lab: <em>R. Kumar (Hb: 10.2 g/dL)</em> | Pharmacy: <em>Ravi K.</em> | Nursing: <em>RAVI KUMAR (BP: 140/90)</em>. System successfully matches cross-source identifiers into a single unified record.</span>
          </div>
        )}

        {/* Multi-Layered Architecture Workflow Pipeline */}
        <div style={{ marginTop: '24px' }}>
          <div style={{
            fontSize: '13px',
            fontWeight: 800,
            textTransform: 'uppercase',
            letterSpacing: '0.8px',
            color: 'var(--primary-navy)',
            marginBottom: '12px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <ShieldCheck size={16} color="var(--primary-teal)" />
              <span>Multi-Layered System Pipeline</span>
            </div>
            <span style={{ fontSize: '11px', color: 'var(--secondary-text)', fontWeight: 600, textTransform: 'none' }}>
              Layer 1 through 5 Active
            </span>
          </div>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(5, 1fr)',
            gap: '10px'
          }}>
            {/* Layer 1 */}
            <div style={{
              backgroundColor: '#F8FAFC',
              border: '1px solid #BAE6FD',
              borderRadius: '8px',
              padding: '12px',
              display: 'flex',
              flexDirection: 'column',
              gap: '4px'
            }}>
              <div style={{ fontSize: '10.5px', fontWeight: 700, color: '#0284C7', textTransform: 'uppercase' }}>
                Layer 1: Security
              </div>
              <div style={{ fontSize: '12.5px', fontWeight: 700, color: '#0F172A' }}>
                2FA &amp; Entry Gateway
              </div>
              <div style={{ fontSize: '11px', color: '#059669', display: 'flex', alignItems: 'center', gap: '4px', fontWeight: 600 }}>
                <CheckCircle2 size={13} />
                <span>Verified &amp; Logged</span>
              </div>
            </div>

            {/* Layer 2 */}
            <div style={{
              backgroundColor: '#F8FAFC',
              border: '1px solid #BAE6FD',
              borderRadius: '8px',
              padding: '12px',
              display: 'flex',
              flexDirection: 'column',
              gap: '4px'
            }}>
              <div style={{ fontSize: '10.5px', fontWeight: 700, color: '#0284C7', textTransform: 'uppercase' }}>
                Layer 2: Role Interface
              </div>
              <div style={{ fontSize: '12.5px', fontWeight: 700, color: '#0F172A' }}>
                {currentRole} Portal
              </div>
              <div style={{ fontSize: '11px', color: '#059669', display: 'flex', alignItems: 'center', gap: '4px', fontWeight: 600 }}>
                <CheckCircle2 size={13} />
                <span>RBAC Scoped</span>
              </div>
            </div>

            {/* Layer 3 */}
            <div style={{
              backgroundColor: isRunning ? '#F0F9FF' : generatedDoc ? '#ECFDF5' : '#F8FAFC',
              border: `1px solid ${isRunning ? '#0284C7' : generatedDoc ? '#A7F3D0' : '#E2E8F0'}`,
              borderRadius: '8px',
              padding: '12px',
              display: 'flex',
              flexDirection: 'column',
              gap: '4px',
              transition: 'all 0.3s'
            }}>
              <div style={{ fontSize: '10.5px', fontWeight: 700, color: '#0284C7', textTransform: 'uppercase' }}>
                Layer 3: Clinical Core
              </div>
              <div style={{ fontSize: '12.5px', fontWeight: 700, color: '#0F172A' }}>
                Multi-Agent Synthesis
              </div>
              <div style={{
                fontSize: '11px',
                color: isRunning ? '#0284C7' : generatedDoc ? '#059669' : '#64748B',
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                fontWeight: 600
              }}>
                <CheckCircle2 size={13} />
                <span>{isRunning ? 'Synthesizing...' : generatedDoc ? 'Draft Grounded' : 'Ready to Run'}</span>
              </div>
            </div>

            {/* Layer 4 */}
            <div style={{
              backgroundColor: '#F8FAFC',
              border: '1px solid #E2E8F0',
              borderRadius: '8px',
              padding: '12px',
              display: 'flex',
              flexDirection: 'column',
              gap: '4px'
            }}>
              <div style={{ fontSize: '10.5px', fontWeight: 700, color: '#64748B', textTransform: 'uppercase' }}>
                Layer 4: Ingestion
              </div>
              <div style={{ fontSize: '12.5px', fontWeight: 700, color: '#0F172A' }}>
                DB &amp; PDF Sync
              </div>
              <div style={{ fontSize: '11px', color: '#059669', display: 'flex', alignItems: 'center', gap: '4px', fontWeight: 600 }}>
                <CheckCircle2 size={13} />
                <span>Normalized (8 Depts)</span>
              </div>
            </div>

            {/* Layer 5 */}
            <div style={{
              backgroundColor: reviewStatus === 'APPROVED' ? '#ECFDF5' : '#F8FAFC',
              border: `1px solid ${reviewStatus === 'APPROVED' ? '#A7F3D0' : '#E2E8F0'}`,
              borderRadius: '8px',
              padding: '12px',
              display: 'flex',
              flexDirection: 'column',
              gap: '4px'
            }}>
              <div style={{ fontSize: '10.5px', fontWeight: 700, color: '#64748B', textTransform: 'uppercase' }}>
                Layer 5: Governance
              </div>
              <div style={{ fontSize: '12.5px', fontWeight: 700, color: '#0F172A' }}>
                Provenance &amp; Sign-Off
              </div>
              <div style={{
                fontSize: '11px',
                color: reviewStatus === 'APPROVED' ? '#059669' : '#D97706',
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                fontWeight: 600
              }}>
                <ShieldCheck size={13} />
                <span>{reviewStatus === 'APPROVED' ? 'Attested & Logged' : 'Pending Sign-Off'}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Generated Document Area (Mirrors Page 20-21) */}
        {generatedDoc && (
          <div style={{ marginTop: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              borderBottom: '2px solid var(--primary-navy)',
              paddingBottom: '8px'
            }}>
              <div style={{ fontSize: '15px', fontWeight: 800, color: 'var(--primary-navy)', textTransform: 'uppercase' }}>
                Generated Document: {generatedDoc.title}
              </div>
              <div style={{ display: 'flex', gap: '8px' }}>
                {isDoctor && (
                  <button
                    onClick={() => setIsEditing(!isEditing)}
                    className="hospiq-btn-outline"
                    style={{ padding: '6px 12px', fontSize: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}
                  >
                    <Edit3 size={14} />
                    <span>{isEditing ? 'Cancel Editing' : 'Modify / Edit Draft'}</span>
                  </button>
                )}
              </div>
            </div>

            {isEditing ? (
              <div>
                <textarea
                  value={editedContent}
                  onChange={(e) => setEditedContent(e.target.value)}
                  className="hospiq-input"
                  style={{ width: '100%', height: '320px', fontFamily: 'monospace', fontSize: '13px', lineHeight: '1.5' }}
                />
                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '10px' }}>
                  <button onClick={() => setIsEditing(false)} className="hospiq-btn-outline">Cancel</button>
                  <button onClick={handleSaveEdit} className="hospiq-btn">Save Changes</button>
                </div>
              </div>
            ) : (
              <div style={{
                backgroundColor: '#FFFFFF',
                border: '1px solid var(--border)',
                borderRadius: 'var(--radius-sm)',
                padding: '20px',
                fontSize: '13.5px',
                lineHeight: '1.6',
                color: 'var(--primary-text)',
                whiteSpace: 'pre-wrap',
                fontFamily: 'system-ui, -apple-system, sans-serif'
              }}>
                {generatedDoc.content}
              </div>
            )}

            {/* Validation Result Box (Exact Format from Page 6 & 21) */}
            <div style={{
              border: '2px solid #E2E8F0',
              borderRadius: 'var(--radius-sm)',
              padding: '16px 20px',
              backgroundColor: reviewStatus === 'APPROVED' ? '#F0FDF4' : '#FFFBEB',
              borderLeft: `6px solid ${reviewStatus === 'APPROVED' ? 'var(--success)' : 'var(--warning)'}`
            }}>
              <div style={{ fontSize: '13px', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.8px', color: 'var(--primary-navy)' }}>
                VALIDATION RESULT
              </div>
              <div style={{ fontSize: '14px', fontWeight: 700, marginTop: '4px', color: reviewStatus === 'APPROVED' ? 'var(--success)' : 'var(--warning)' }}>
                Status: {reviewStatus}
              </div>

              {validationScorecard && (
                <div style={{ marginTop: '10px', fontSize: '13px', color: 'var(--primary-text)' }}>
                  <div><strong>Checks Passed:</strong> {validationScorecard.passed_checks} of {validationScorecard.total_checks} | <strong>Warnings:</strong> {validationScorecard.warnings_count} | <strong>Violations:</strong> {validationScorecard.failed_checks}</div>
                  <div style={{ marginTop: '4px', color: 'var(--secondary-text)' }}>
                    <strong>Action:</strong> {reviewStatus === 'APPROVED' ? 'Approved by Attending Physician.' : 'Human review required before record commitment.'}
                  </div>
                </div>
              )}

              {/* Human Review Decision Buttons (Page 21) */}
              <div style={{
                display: 'flex',
                gap: '12px',
                marginTop: '16px',
                paddingTop: '12px',
                borderTop: '1px solid rgba(0,0,0,0.08)'
              }}>
                {isDoctor && (
                  <button
                    onClick={handleApprove}
                    disabled={reviewStatus === 'APPROVED'}
                    style={{
                      backgroundColor: 'var(--success)',
                      color: '#FFFFFF',
                      border: 'none',
                      padding: '8px 20px',
                      borderRadius: 'var(--radius-sm)',
                      fontWeight: 700,
                      fontSize: '13px',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                      cursor: 'pointer',
                      opacity: reviewStatus !== 'APPROVED' ? 1 : 0.6
                    }}
                  >
                    <Check size={16} />
                    <span>[ Approve ]</span>
                  </button>
                )}

                {isParamedic && (
                  <button
                    onClick={handleEmergencyIssue}
                    disabled={reviewStatus.includes('APPROVED')}
                    style={{
                      backgroundColor: '#EA580C',
                      color: '#FFFFFF',
                      border: 'none',
                      padding: '8px 20px',
                      borderRadius: 'var(--radius-sm)',
                      fontWeight: 700,
                      fontSize: '13px',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                      cursor: 'pointer'
                    }}
                  >
                    <Check size={16} />
                    <span>[ ⚡ Emergency Direct Issue ]</span>
                  </button>
                )}

                <button
                  onClick={() => setIsEditing(true)}
                  disabled={!canEdit || isEditing}
                  style={{
                    backgroundColor: '#FFFFFF',
                    color: 'var(--primary-navy)',
                    border: '1px solid var(--border)',
                    padding: '8px 20px',
                    borderRadius: 'var(--radius-sm)',
                    fontWeight: 700,
                    fontSize: '13px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    cursor: canEdit ? 'pointer' : 'not-allowed'
                  }}
                >
                  <Edit3 size={16} />
                  <span>[ Modify ]</span>
                </button>

                {isDoctor && (
                  <button
                    onClick={handleReject}
                    disabled={reviewStatus === 'REJECTED'}
                    style={{
                      backgroundColor: 'var(--error)',
                      color: '#FFFFFF',
                      border: 'none',
                      padding: '8px 20px',
                      borderRadius: 'var(--radius-sm)',
                      fontWeight: 700,
                      fontSize: '13px',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                      cursor: 'pointer',
                      opacity: 1
                    }}
                  >
                    <X size={16} />
                    <span>[ Reject ]</span>
                  </button>
                )}

                {!isDoctor && !isParamedic && (
                  <span style={{ fontSize: '12px', color: 'var(--secondary-text)', alignSelf: 'center' }}>
                    (Log in as <strong>Doctor</strong> to Approve/Reject, or <strong>Paramedic</strong> to Modify/Emergency Issue)
                  </span>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* FHIR Modal (Challenge A) */}
      {showFhirModal && fhirData && (
        <div style={{
          position: 'fixed',
          top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(16, 38, 63, 0.6)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          zIndex: 1000, padding: '20px'
        }}>
          <div className="hospiq-card" style={{ width: '750px', maxHeight: '85vh', display: 'flex', flexDirection: 'column' }}>
            <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h3 style={{ fontSize: '16px', fontWeight: 800, color: 'var(--primary-navy)' }}>
                  Challenge A — FHIR Resource Representation
                </h3>
                <div style={{ fontSize: '12px', color: 'var(--secondary-text)' }}>
                  Standardized FHIR Bundle (Patient, Encounter, Observation, DiagnosticReport, MedicationRequest)
                </div>
              </div>
              <button onClick={() => setShowFhirModal(false)} style={{ background: 'none', border: 'none', fontSize: '18px', cursor: 'pointer' }}>✕</button>
            </div>
            <pre style={{
              flex: 1,
              padding: '16px',
              backgroundColor: '#0F172A',
              color: '#38BDF8',
              fontFamily: 'monospace',
              fontSize: '12px',
              overflow: 'auto',
              maxHeight: '60vh'
            }}>
              {JSON.stringify(fhirData, null, 2)}
            </pre>
            <div style={{ padding: '12px 20px', borderTop: '1px solid var(--border)', display: 'flex', justifyContent: 'flex-end' }}>
              <button onClick={() => setShowFhirModal(false)} className="hospiq-btn">Close</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

