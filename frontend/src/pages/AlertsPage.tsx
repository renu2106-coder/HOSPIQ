import React, { useEffect, useState } from 'react';
import { DepartmentAlert } from '../types';
import { api } from '../services/api';
import {
  AlertTriangle, CheckCircle2, Clock, Filter, MessageSquare,
  ArrowRight, RefreshCw, Send
} from 'lucide-react';

interface AlertsPageProps {
  currentRole: string;
}

export const AlertsPage: React.FC<AlertsPageProps> = ({ currentRole }) => {
  const [alerts, setAlerts] = useState<DepartmentAlert[]>([]);
  const [statusFilter, setStatusFilter] = useState('');
  const [priorityFilter, setPriorityFilter] = useState('');
  const [selectedAlert, setSelectedAlert] = useState<DepartmentAlert | null>(null);
  const [investigationNotes, setInvestigationNotes] = useState('');
  const [newStatus, setNewStatus] = useState('Under Investigation');
  const [updating, setUpdating] = useState(false);
  const [loading, setLoading] = useState(true);

  // Correction request prefill
  const [showCorrectionModal, setShowCorrectionModal] = useState(false);
  const [fieldName, setFieldName] = useState('blood_group');
  const [originalValue, setOriginalValue] = useState('');
  const [proposedValue, setProposedValue] = useState('');
  const [justification, setJustification] = useState('');
  const [submittingCorrection, setSubmittingCorrection] = useState(false);

  useEffect(() => {
    loadAlerts();
  }, [statusFilter, priorityFilter]);

  const loadAlerts = async () => {
    setLoading(true);
    try {
      const data = await api.alerts.list({
        status_filter: statusFilter || undefined,
        priority: priorityFilter || undefined
      });
      setAlerts(data);
    } catch (err) {
      console.error('Failed to load alerts:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateAlert = async () => {
    if (!selectedAlert) return;
    setUpdating(true);
    try {
      const updated = await api.alerts.updateStatus(selectedAlert.alert_id, {
        status: newStatus,
        investigation_notes: investigationNotes || undefined
      });
      setSelectedAlert(updated);
      setInvestigationNotes('');
      await loadAlerts();
    } catch (err: any) {
      alert('Failed to update alert: ' + err.message);
    } finally {
      setUpdating(false);
    }
  };

  const handleSubmitCorrection = async () => {
    if (!selectedAlert || !selectedAlert.patient_id) return;
    setSubmittingCorrection(true);
    try {
      await api.corrections.create({
        alert_id: selectedAlert.id,
        patient_id: selectedAlert.patient_id,
        department: selectedAlert.department,
        field_name: fieldName,
        original_value: originalValue,
        proposed_value: proposedValue,
        justification: justification
      });
      alert('Correction request submitted successfully! Staged for physician/administrator approval.');
      setShowCorrectionModal(false);
      await loadAlerts();
    } catch (err: any) {
      alert('Error submitting correction: ' + err.message);
    } finally {
      setSubmittingCorrection(false);
    }
  };

  return (
    <div style={{ padding: '28px', maxWidth: '1300px', margin: '0 auto' }}>
      {/* Title */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
        <div>
          <h2 style={{ fontSize: '20px', fontWeight: 700, color: 'var(--primary-navy)' }}>
            Cross-Department Data Discrepancy Alerts
          </h2>
          <p style={{ fontSize: '13px', color: 'var(--secondary-text)', marginTop: '2px' }}>
            Automated conflict detection across Registration, Laboratory, Pharmacy, and Clinical systems.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            style={{ padding: '6px 12px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', fontSize: '13px' }}
          >
            <option value="">All Statuses</option>
            <option value="Open">Open</option>
            <option value="Under Investigation">Under Investigation</option>
            <option value="Resolution Pending">Resolution Pending</option>
            <option value="Resolved">Resolved</option>
          </select>

          <select
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value)}
            style={{ padding: '6px 12px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', fontSize: '13px' }}
          >
            <option value="">All Priorities</option>
            <option value="Critical">Critical</option>
            <option value="High">High</option>
            <option value="Medium">Medium</option>
            <option value="Low">Low</option>
          </select>

          <button onClick={loadAlerts} className="btn-secondary" style={{ padding: '6px 10px' }}>
            <RefreshCw size={14} />
          </button>
        </div>
      </div>

      {/* Main Grid: Alerts List & Alert Inspector */}
      <div style={{ display: 'grid', gridTemplateColumns: selectedAlert ? '1.3fr 1fr' : '1fr', gap: '20px' }}>
        {/* Table */}
        <div className="card">
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Alert ID</th>
                  <th>Patient</th>
                  <th>Department</th>
                  <th>Category</th>
                  <th>Priority</th>
                  <th>Status</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan={7} style={{ textAlign: 'center', padding: '24px', color: 'var(--secondary-text)' }}>
                      Scanning for department alerts...
                    </td>
                  </tr>
                ) : alerts.length === 0 ? (
                  <tr>
                    <td colSpan={7} style={{ textAlign: 'center', padding: '24px', color: 'var(--secondary-text)' }}>
                      No active department alerts matching criteria.
                    </td>
                  </tr>
                ) : (
                  alerts.map((alert) => (
                    <tr
                      key={alert.id}
                      style={{
                        backgroundColor: selectedAlert?.id === alert.id ? '#F0F9F8' : 'transparent',
                        cursor: 'pointer'
                      }}
                      onClick={() => {
                        setSelectedAlert(alert);
                        setNewStatus(alert.status);
                      }}
                    >
                      <td style={{ fontWeight: 700, color: 'var(--primary-navy)' }}>{alert.alert_id}</td>
                      <td style={{ fontWeight: 600 }}>{alert.patient_id || 'System'}</td>
                      <td>{alert.department}</td>
                      <td>{alert.alert_category}</td>
                      <td>
                        <span className={`badge ${
                          alert.priority === 'Critical' ? 'badge-error' :
                          alert.priority === 'High' ? 'badge-warning' :
                          'badge-info'
                        }`}>
                          {alert.priority}
                        </span>
                      </td>
                      <td>
                        <span className={`badge ${
                          alert.status === 'Resolved' ? 'badge-success' :
                          alert.status === 'Open' ? 'badge-error' :
                          'badge-warning'
                        }`}>
                          {alert.status}
                        </span>
                      </td>
                      <td>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedAlert(alert);
                            setNewStatus(alert.status);
                          }}
                          className="btn-secondary"
                          style={{ padding: '4px 8px', fontSize: '11.5px' }}
                        >
                          Investigate
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Selected Alert Details */}
        {selectedAlert && (
          <div className="card">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid var(--border)', paddingBottom: '12px', marginBottom: '14px' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ fontSize: '15px', fontWeight: 800, color: 'var(--primary-navy)' }}>
                    {selectedAlert.alert_id}
                  </span>
                  <span className={`badge ${selectedAlert.priority === 'Critical' ? 'badge-error' : 'badge-warning'}`}>
                    {selectedAlert.priority}
                  </span>
                </div>
                <div style={{ fontSize: '12px', color: 'var(--secondary-text)' }}>
                  {selectedAlert.department} • Patient: {selectedAlert.patient_id}
                </div>
              </div>
              <button onClick={() => setSelectedAlert(null)} className="btn-secondary" style={{ padding: '3px 8px', fontSize: '11px' }}>
                Close
              </button>
            </div>

            <div style={{ marginBottom: '16px' }}>
              <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--primary-navy)', marginBottom: '4px' }}>
                Discrepancy Description:
              </div>
              <div style={{
                padding: '10px 12px',
                backgroundColor: '#F8FAFC',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--border)',
                fontSize: '13px',
                lineHeight: 1.4,
                color: 'var(--primary-text)'
              }}>
                {selectedAlert.description}
              </div>
            </div>

            {selectedAlert.investigation_notes && (
              <div style={{ marginBottom: '16px' }}>
                <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--primary-navy)', marginBottom: '4px' }}>
                  Investigation Audit Trail:
                </div>
                <div style={{
                  padding: '10px 12px',
                  backgroundColor: '#FFFFFF',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--border)',
                  fontSize: '12px',
                  maxHeight: '120px',
                  overflowY: 'auto',
                  whiteSpace: 'pre-wrap'
                }}>
                  {selectedAlert.investigation_notes}
                </div>
              </div>
            )}

            {/* Investigation Actions Form */}
            <div style={{ borderTop: '1px solid var(--border)', paddingTop: '14px' }}>
              <div style={{ fontSize: '12.5px', fontWeight: 700, color: 'var(--primary-navy)', marginBottom: '8px' }}>
                Update Investigation Status:
              </div>

              <div style={{ marginBottom: '10px' }}>
                <select
                  value={newStatus}
                  onChange={(e) => setNewStatus(e.target.value)}
                  style={{ width: '100%', padding: '7px 10px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', fontSize: '13px' }}
                >
                  <option value="Open">Open</option>
                  <option value="Under Investigation">Under Investigation</option>
                  <option value="Resolution Pending">Resolution Pending</option>
                  <option value="Resolved">Resolved</option>
                  <option value="Dismissed">Dismissed</option>
                </select>
              </div>

              <div style={{ marginBottom: '12px' }}>
                <textarea
                  rows={3}
                  value={investigationNotes}
                  onChange={(e) => setInvestigationNotes(e.target.value)}
                  placeholder="Add clinical investigation observations or resolution steps..."
                  style={{ width: '100%', padding: '8px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', fontSize: '12.5px', outline: 'none' }}
                />
              </div>

              <div style={{ display: 'flex', gap: '8px' }}>
                <button
                  onClick={handleUpdateAlert}
                  disabled={updating}
                  className="btn-primary"
                  style={{ flex: 1, justifyContent: 'center', fontSize: '12.5px' }}
                >
                  <span>Save Investigation Note</span>
                </button>

                {selectedAlert.patient_id && (
                  <button
                    onClick={() => {
                      setOriginalValue('');
                      setProposedValue('');
                      setJustification(`Correction generated from ${selectedAlert.alert_id}: ${selectedAlert.description}`);
                      setShowCorrectionModal(true);
                    }}
                    className="btn-clinical"
                    style={{ fontSize: '12.5px' }}
                  >
                    <span>Submit Correction</span>
                  </button>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Modal for Submitting Formal Correction */}
      {showCorrectionModal && selectedAlert && (
        <div style={{
          position: 'fixed',
          top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(16, 38, 63, 0.4)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 99
        }}>
          <div style={{
            maxWidth: '500px',
            width: '100%',
            backgroundColor: '#FFFFFF',
            borderRadius: 'var(--radius-md)',
            padding: '24px',
            boxShadow: 'var(--shadow-lg)'
          }}>
            <h3 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--primary-navy)', marginBottom: '8px' }}>
              Submit Data Correction Request
            </h3>
            <p style={{ fontSize: '12.5px', color: 'var(--secondary-text)', marginBottom: '16px' }}>
              All modifications are staged with original and proposed values for authorized approval.
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, marginBottom: '4px' }}>Target Field</label>
                <input
                  type="text"
                  value={fieldName}
                  onChange={(e) => setFieldName(e.target.value)}
                  style={{ width: '100%', padding: '8px', border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)', fontSize: '13px' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, marginBottom: '4px' }}>Current Discrepant Value</label>
                <input
                  type="text"
                  value={originalValue}
                  onChange={(e) => setOriginalValue(e.target.value)}
                  placeholder="e.g. O+ or 1975-09-02"
                  style={{ width: '100%', padding: '8px', border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)', fontSize: '13px' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, marginBottom: '4px' }}>Verified Proposed Value</label>
                <input
                  type="text"
                  value={proposedValue}
                  onChange={(e) => setProposedValue(e.target.value)}
                  placeholder="e.g. B+ or 1975-08-30"
                  style={{ width: '100%', padding: '8px', border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)', fontSize: '13px' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, marginBottom: '4px' }}>Clinical Justification</label>
                <textarea
                  rows={3}
                  value={justification}
                  onChange={(e) => setJustification(e.target.value)}
                  style={{ width: '100%', padding: '8px', border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)', fontSize: '12.5px' }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '12px' }}>
                <button onClick={() => setShowCorrectionModal(false)} className="btn-secondary">
                  Cancel
                </button>
                <button onClick={handleSubmitCorrection} disabled={submittingCorrection} className="btn-primary">
                  {submittingCorrection ? 'Submitting...' : 'Submit for Physician Sign-off'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

