import React, { useEffect, useState } from 'react';
import { CorrectionRequest } from '../types';
import { api } from '../services/api';
import { CheckSquare, Check, X, RefreshCw, AlertCircle } from 'lucide-react';

interface CorrectionsPageProps {
  currentRole: string;
}

export const CorrectionsPage: React.FC<CorrectionsPageProps> = ({ currentRole }) => {
  const [corrections, setCorrections] = useState<CorrectionRequest[]>([]);
  const [selectedCorrection, setSelectedCorrection] = useState<CorrectionRequest | null>(null);
  const [reviewNotes, setReviewNotes] = useState('');
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);

  const canApprove = ['Doctor', 'Hospital Administrator'].includes(currentRole);

  useEffect(() => {
    loadCorrections();
  }, []);

  const loadCorrections = async () => {
    setLoading(true);
    try {
      const data = await api.corrections.list();
      setCorrections(data);
    } catch (err) {
      console.error('Failed to load correction requests:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleReview = async (action: 'APPROVE' | 'REJECT') => {
    if (!selectedCorrection || !canApprove) return;
    setProcessing(true);
    try {
      await api.corrections.review(selectedCorrection.id, {
        action,
        review_notes: reviewNotes,
      });
      alert(`Correction request ${action === 'APPROVE' ? 'Approved' : 'Rejected'} successfully!`);
      setSelectedCorrection(null);
      setReviewNotes('');
      await loadCorrections();
    } catch (err: any) {
      alert('Review action failed: ' + err.message);
    } finally {
      setProcessing(false);
    }
  };

  return (
    <div style={{ padding: '28px', maxWidth: '1200px', margin: '0 auto' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
        <div>
          <h2 style={{ fontSize: '20px', fontWeight: 700, color: 'var(--primary-navy)' }}>
            Data Correction & Revision Requests
          </h2>
          <p style={{ fontSize: '13px', color: 'var(--secondary-text)', marginTop: '2px' }}>
            Controlled staging of clinical and demographic adjustments. Requires physician or administrator sign-off.
          </p>
        </div>

        <button onClick={loadCorrections} className="btn-secondary" style={{ padding: '6px 12px' }}>
          <RefreshCw size={14} />
          <span>Refresh</span>
        </button>
      </div>

      <div className="card">
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Request ID</th>
                <th>Patient</th>
                <th>Department</th>
                <th>Field Name</th>
                <th>Original Value</th>
                <th>Proposed Value</th>
                <th>Status</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={8} style={{ textAlign: 'center', padding: '24px', color: 'var(--secondary-text)' }}>
                    Loading correction requests...
                  </td>
                </tr>
              ) : corrections.length === 0 ? (
                <tr>
                  <td colSpan={8} style={{ textAlign: 'center', padding: '24px', color: 'var(--secondary-text)' }}>
                    No correction requests currently pending.
                  </td>
                </tr>
              ) : (
                corrections.map((corr) => (
                  <tr key={corr.id}>
                    <td style={{ fontWeight: 700 }}>#{corr.id}</td>
                    <td style={{ fontWeight: 600 }}>{corr.patient_id}</td>
                    <td>{corr.department}</td>
                    <td><code>{corr.field_name}</code></td>
                    <td style={{ color: 'var(--secondary-text)' }}>{corr.original_value || 'None'}</td>
                    <td style={{ fontWeight: 700, color: 'var(--primary-teal)' }}>{corr.proposed_value}</td>
                    <td>
                      <span className={`badge ${
                        corr.status === 'Approved' ? 'badge-success' :
                        corr.status === 'Rejected' ? 'badge-error' :
                        'badge-warning'
                      }`}>
                        {corr.status}
                      </span>
                    </td>
                    <td>
                      {canApprove && corr.status === 'Pending Review' ? (
                        <button
                          onClick={() => {
                            setSelectedCorrection(corr);
                            setReviewNotes('');
                          }}
                          className="btn-primary"
                          style={{ padding: '4px 10px', fontSize: '12px' }}
                        >
                          Review & Sign
                        </button>
                      ) : (
                        <span style={{ fontSize: '12px', color: 'var(--secondary-text)' }}>
                          {corr.status}
                        </span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Review Modal */}
      {selectedCorrection && (
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
            maxWidth: '520px',
            width: '100%',
            backgroundColor: '#FFFFFF',
            borderRadius: 'var(--radius-md)',
            padding: '24px',
            boxShadow: 'var(--shadow-lg)'
          }}>
            <h3 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--primary-navy)', marginBottom: '8px' }}>
              Attest Correction Request #{selectedCorrection.id}
            </h3>
            <p style={{ fontSize: '12.5px', color: 'var(--secondary-text)', marginBottom: '16px' }}>
              Patient: <strong>{selectedCorrection.patient_id}</strong> • Target Field: <strong>{selectedCorrection.field_name}</strong>
            </p>

            <div style={{ padding: '12px', backgroundColor: '#F8FAFC', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', marginBottom: '14px' }}>
              <div style={{ fontSize: '12px', color: 'var(--secondary-text)' }}>Proposed Adjustment:</div>
              <div style={{ fontSize: '13px', marginTop: '4px' }}>
                <span style={{ textDecoration: 'line-through', color: 'var(--error)' }}>
                  {selectedCorrection.original_value || 'None'}
                </span>{' '}
                → <strong style={{ color: 'var(--success)' }}>{selectedCorrection.proposed_value}</strong>
              </div>
              <div style={{ fontSize: '11.5px', color: 'var(--secondary-text)', marginTop: '8px' }}>
                <strong>Justification:</strong> {selectedCorrection.justification}
              </div>
            </div>

            <div style={{ marginBottom: '16px' }}>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, marginBottom: '4px' }}>
                Physician / Administrator Review Notes:
              </label>
              <textarea
                rows={3}
                value={reviewNotes}
                onChange={(e) => setReviewNotes(e.target.value)}
                placeholder="Enter clinical review notes or reason for approval/rejection..."
                style={{ width: '100%', padding: '8px', border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)', fontSize: '12.5px' }}
              />
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
              <button onClick={() => setSelectedCorrection(null)} className="btn-secondary">
                Cancel
              </button>
              <button
                onClick={() => handleReview('REJECT')}
                disabled={processing}
                className="btn-secondary"
                style={{ color: 'var(--error)' }}
              >
                <X size={14} />
                <span>Reject</span>
              </button>
              <button
                onClick={() => handleReview('APPROVE')}
                disabled={processing}
                className="btn-primary"
                style={{ backgroundColor: 'var(--success)' }}
              >
                <Check size={14} />
                <span>Approve & Apply Update</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

