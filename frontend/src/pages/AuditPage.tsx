import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import type { AuditLog } from '../types';
import {
  ShieldCheck, Search, Filter, RefreshCw,
  UserCheck, Lock, ArrowDownToLine, Clock, LogIn, LogOut, KeyRound
} from 'lucide-react';

export const AuditPage: React.FC = () => {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [scope, setScope] = useState<{ user_id: number; full_name: string; role: string; is_master_admin: boolean; scope_description: string } | null>(null);
  const [selectedAction, setSelectedAction] = useState<string>('ALL');
  const [selectedEntity, setSelectedEntity] = useState<string>('ALL');
  const [selectedStatus, setSelectedStatus] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedLog, setSelectedLog] = useState<AuditLog | null>(null);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const [data, scopeInfo] = await Promise.all([
        api.audit.list({
          action: selectedAction !== 'ALL' ? selectedAction : undefined,
          entity_type: selectedEntity !== 'ALL' ? selectedEntity : undefined,
          status_filter: selectedStatus !== 'ALL' ? selectedStatus : undefined,
          limit: 150
        }),
        api.audit.getScope().catch(() => null)
      ]);
      setLogs(data);
      if (scopeInfo) setScope(scopeInfo);
    } catch (err: any) {
      console.error('Failed to load audit trail:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [selectedAction, selectedEntity, selectedStatus]);

  const actions = [
    'ALL',
    'LOGIN_ENTRY',
    'LOGOUT_EXIT',
    '2FA_CHALLENGE_ISSUED',
    'LOGIN_SUCCESS',
    'LOGIN_FAILED',
    'DOCUMENT_GENERATED',
    'DOCUMENT_APPROVED',
    'DOCUMENT_REJECTED',
    'DOCUMENT_EDITED',
    'EMERGENCY_DOCUMENT_ISSUED',
    'DATABASE_AUTOMATED_SYNC',
    'PATIENT_CONSOLIDATED',
    'FILE_UPLOADED',
    'CORRECTION_REQUESTED'
  ];

  const entityTypes = [
    'ALL',
    'Auth',
    'DOCUMENT',
    'PATIENT',
    'USER',
    'FILE',
    'CORRECTION',
    'ALERT',
    'HospitalDatabase'
  ];

  const filteredLogs = logs.filter(log => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      (log.action && log.action.toLowerCase().includes(q)) ||
      (log.details_json && log.details_json.toLowerCase().includes(q)) ||
      (log.entity_id && log.entity_id.toLowerCase().includes(q)) ||
      (log.user_id && log.user_id.toString().includes(q))
    );
  });

  // Calculate session entry/exit statistics
  const entryCount = logs.filter(l => l.action === 'LOGIN_ENTRY' || l.action === 'LOGIN_SUCCESS').length;
  const exitCount = logs.filter(l => l.action === 'LOGOUT_EXIT' || l.action === 'LOGOUT').length;

  const parseDetails = (jsonStr?: string | null) => {
    if (!jsonStr) return {};
    try {
      return JSON.parse(jsonStr);
    } catch {
      return {};
    }
  };

  const exportCSV = () => {
    const headers = ['ID', 'Event ID', 'Timestamp', 'User ID', 'Role', 'Action', 'Entity Type', 'Entity ID', 'Status', 'IP Address', 'Details'];
    const rows = filteredLogs.map(l => [
      l.id,
      l.event_id || '',
      l.timestamp,
      l.user_id || 'System',
      l.user_role || '',
      l.action,
      l.entity_type || '',
      l.entity_id || '',
      l.status,
      l.ip_address || '',
      `"${(l.details_json || '').replace(/"/g, '""')}"`
    ]);
    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map(e => e.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `hospiq_audit_trail_${new Date().toISOString().split('T')[0]}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '22px', fontWeight: 800, color: 'var(--primary-navy)', marginBottom: '4px' }}>
            Audit Trail &amp; Data Provenance
          </h1>
          <p style={{ fontSize: '13px', color: 'var(--secondary-text)' }}>
            Immutable, append-only logs tracking entry/exit sessions, document attestations, and security verifications.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '10px' }}>
          <button
            onClick={exportCSV}
            className="btn-secondary"
            style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
          >
            <ArrowDownToLine size={15} />
            <span>Export CSV</span>
          </button>
          <button
            onClick={fetchLogs}
            disabled={loading}
            className="btn-primary"
            style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
          >
            <RefreshCw size={15} className={loading ? 'spin' : ''} />
            <span>Refresh Trail</span>
          </button>
        </div>
      </div>

      {/* Role Personalization Banner */}
      {scope && (
        <div style={{
          padding: '14px 18px',
          borderRadius: 'var(--radius-md)',
          backgroundColor: scope.is_master_admin ? '#EFF6FF' : '#F0FDF4',
          border: `1px solid ${scope.is_master_admin ? '#BFDBFE' : '#BBF7D0'}`,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <div>
            <div style={{ fontSize: '13.5px', fontWeight: 700, color: scope.is_master_admin ? '#1E40AF' : '#166534' }}>
              {scope.is_master_admin ? 'Master Administrator Audit View' : `Personalized Audit Trail: ${scope.full_name} (${scope.role})`}
            </div>
            <div style={{ fontSize: '12px', color: 'var(--secondary-text)', marginTop: '2px' }}>
              {scope.is_master_admin
                ? 'Authorized to inspect all personnel actions, logins, session entry/exit times, and patient modifications across every hospital department.'
                : 'Showing only your personal authenticated clinical actions. Audit records are cryptographically verified and cannot be manipulated.'}
            </div>
          </div>
          <span style={{
            fontSize: '11px',
            fontWeight: 700,
            padding: '4px 10px',
            borderRadius: '6px',
            backgroundColor: scope.is_master_admin ? '#DBEAFE' : '#DCFCE7',
            color: scope.is_master_admin ? '#1E40AF' : '#15803D'
          }}>
            {scope.is_master_admin ? 'MASTER SCOPE' : 'PERSONALIZED • IMMUTABLE'}
          </span>
        </div>
      )}

      {/* Security & Session Tracking Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px' }}>
        <div className="card" style={{ padding: '16px', display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            width: '38px',
            height: '38px',
            borderRadius: '8px',
            backgroundColor: '#EFF6FF',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#2563EB'
          }}>
            <Lock size={20} />
          </div>
          <div>
            <div style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--secondary-text)', fontWeight: 700 }}>
              Audit Integrity
            </div>
            <div style={{ fontSize: '13.5px', fontWeight: 700, color: 'var(--primary-navy)' }}>
              Append-Only Immutability
            </div>
          </div>
        </div>

        <div className="card" style={{ padding: '16px', display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            width: '38px',
            height: '38px',
            borderRadius: '8px',
            backgroundColor: '#ECFDF5',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#059669'
          }}>
            <ShieldCheck size={20} />
          </div>
          <div>
            <div style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--secondary-text)', fontWeight: 700 }}>
              Logged Operations
            </div>
            <div style={{ fontSize: '13.5px', fontWeight: 700, color: 'var(--primary-navy)' }}>
              {logs.length} Traceable Events
            </div>
          </div>
        </div>

        <div className="card" style={{ padding: '16px', display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            width: '38px',
            height: '38px',
            borderRadius: '8px',
            backgroundColor: '#F0F9FF',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#0284C7'
          }}>
            <UserCheck size={20} />
          </div>
          <div>
            <div style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--secondary-text)', fontWeight: 700 }}>
              RBAC Provenance
            </div>
            <div style={{ fontSize: '13.5px', fontWeight: 700, color: 'var(--primary-navy)' }}>
              Strict Role Attestation
            </div>
          </div>
        </div>

        <div className="card" style={{ padding: '16px', display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            width: '38px',
            height: '38px',
            borderRadius: '8px',
            backgroundColor: '#F5F3FF',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#7C3AED'
          }}>
            <Clock size={20} />
          </div>
          <div>
            <div style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--secondary-text)', fontWeight: 700 }}>
              Entry / Exit Sessions
            </div>
            <div style={{ fontSize: '13.5px', fontWeight: 700, color: '#7C3AED' }}>
              {entryCount} Entries • {exitCount} Exits
            </div>
          </div>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="card" style={{ padding: '16px', display: 'flex', gap: '16px', alignItems: 'center', flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Filter size={16} color="var(--secondary-text)" />
          <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--primary-navy)' }}>Action:</span>
          <select
            value={selectedAction}
            onChange={(e) => setSelectedAction(e.target.value)}
            className="hospiq-input"
            style={{ width: '190px', padding: '6px 10px', fontSize: '13px' }}
          >
            {actions.map((act) => (
              <option key={act} value={act}>{act}</option>
            ))}
          </select>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--primary-navy)' }}>Entity:</span>
          <select
            value={selectedEntity}
            onChange={(e) => setSelectedEntity(e.target.value)}
            className="hospiq-input"
            style={{ width: '140px', padding: '6px 10px', fontSize: '13px' }}
          >
            {entityTypes.map((ent) => (
              <option key={ent} value={ent}>{ent}</option>
            ))}
          </select>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--primary-navy)' }}>Status:</span>
          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="hospiq-input"
            style={{ width: '120px', padding: '6px 10px', fontSize: '13px' }}
          >
            <option value="ALL">ALL</option>
            <option value="SUCCESS">SUCCESS</option>
            <option value="FAILED">FAILED</option>
          </select>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flex: 1, minWidth: '220px' }}>
          <Search size={16} color="var(--secondary-text)" />
          <input
            type="text"
            placeholder="Search details, entry/exit timestamp, or keyword..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="hospiq-input"
            style={{ padding: '6px 12px', fontSize: '13px', width: '100%' }}
          />
        </div>
      </div>

      {/* Audit Log Table */}
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <div style={{
          padding: '16px 20px',
          borderBottom: '1px solid var(--border)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <div>
            <div style={{ fontSize: '15px', fontWeight: 700, color: 'var(--primary-navy)' }}>
              Audit Trail Entries
            </div>
            <div style={{ fontSize: '12px', color: 'var(--secondary-text)' }}>
              Showing {filteredLogs.length} events • Login Entry &amp; Logout Exit Tracking Active
            </div>
          </div>
        </div>

        {loading ? (
          <div style={{ padding: '40px', textAlign: 'center', color: 'var(--secondary-text)' }}>
            <RefreshCw size={24} className="spin" style={{ margin: '0 auto 8px auto' }} />
            <div>Loading audit records...</div>
          </div>
        ) : filteredLogs.length === 0 ? (
          <div style={{ padding: '40px', textAlign: 'center', color: 'var(--secondary-text)' }}>
            <ShieldCheck size={32} style={{ margin: '0 auto 8px auto', opacity: 0.4 }} />
            <div>No audit log entries found matching criteria.</div>
          </div>
        ) : (
          <div className="table-container" style={{ border: 'none', borderRadius: 0 }}>
            <table>
              <thead>
                <tr>
                  <th>Log ID</th>
                  <th>Timestamp</th>
                  <th>User ID</th>
                  <th>Role</th>
                  <th>Action</th>
                  <th>Entity Type</th>
                  <th>Status</th>
                  <th>Session Tracking &amp; Details</th>
                </tr>
              </thead>
              <tbody>
                {filteredLogs.map((log) => {
                  const isSuccess = log.status === 'SUCCESS';
                  const details = parseDetails(log.details_json);
                  const isEntry = log.action === 'LOGIN_ENTRY' || log.action === 'LOGIN_SUCCESS';
                  const isExit = log.action === 'LOGOUT_EXIT' || log.action === 'LOGOUT';
                  const is2FA = log.action === '2FA_CHALLENGE_ISSUED';

                  return (
                    <tr key={log.id} style={{ cursor: 'pointer' }} onClick={() => setSelectedLog(log)}>
                      <td>
                        <code style={{ fontSize: '11px', color: 'var(--secondary-text)' }}>
                          #{log.id}
                        </code>
                      </td>
                      <td style={{ fontSize: '11.5px', color: 'var(--secondary-text)', whiteSpace: 'nowrap' }}>
                        {log.timestamp ? new Date(log.timestamp).toLocaleString() : 'N/A'}
                      </td>
                      <td>
                        <span style={{ fontWeight: 600, color: 'var(--primary-navy)' }}>
                          {log.user_id ? `User #${log.user_id}` : 'System Agent'}
                        </span>
                      </td>
                      <td>
                        <span style={{ fontSize: '12px', color: 'var(--primary-text)', fontWeight: 500 }}>
                          {log.user_role || 'System'}
                        </span>
                      </td>
                      <td>
                        {isEntry ? (
                          <span style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '4px',
                            backgroundColor: '#ECFDF5',
                            color: '#059669',
                            padding: '3px 8px',
                            borderRadius: '6px',
                            fontSize: '11px',
                            fontWeight: 700,
                            border: '1px solid #A7F3D0'
                          }}>
                            <LogIn size={12} />
                            <span>ENTRY (Login)</span>
                          </span>
                        ) : isExit ? (
                          <span style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '4px',
                            backgroundColor: '#F5F3FF',
                            color: '#7C3AED',
                            padding: '3px 8px',
                            borderRadius: '6px',
                            fontSize: '11px',
                            fontWeight: 700,
                            border: '1px solid #DDD6FE'
                          }}>
                            <LogOut size={12} />
                            <span>EXIT (Logout)</span>
                          </span>
                        ) : is2FA ? (
                          <span style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '4px',
                            backgroundColor: '#EFF6FF',
                            color: '#2563EB',
                            padding: '3px 8px',
                            borderRadius: '6px',
                            fontSize: '11px',
                            fontWeight: 700,
                            border: '1px solid #BFDBFE'
                          }}>
                            <KeyRound size={12} />
                            <span>2FA CHALLENGE</span>
                          </span>
                        ) : (
                          <span style={{
                            fontSize: '11.5px',
                            fontWeight: 700,
                            color: log.action.includes('REJECT') ? 'var(--danger)' : log.action.includes('APPROVE') ? 'var(--success)' : 'var(--primary-navy)'
                          }}>
                            {log.action}
                          </span>
                        )}
                      </td>
                      <td>
                        <span className="badge badge-info">
                          {log.entity_type || '—'}
                        </span>
                      </td>
                      <td>
                        <span className={`badge ${isSuccess ? 'badge-success' : 'badge-error'}`}>
                          {log.status}
                        </span>
                      </td>
                      <td style={{ maxWidth: '340px' }}>
                        {isExit && details.session_duration ? (
                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <span style={{
                              padding: '2px 8px',
                              borderRadius: '4px',
                              backgroundColor: '#EDE9FE',
                              color: '#6D28D9',
                              fontSize: '11.5px',
                              fontWeight: 700
                            }}>
                              Duration: {details.session_duration}
                            </span>
                            <span style={{ fontSize: '11.5px', color: 'var(--secondary-text)' }}>
                              Exit: {details.time_of_exit?.split(' ')[1] || 'Recorded'}
                            </span>
                          </div>
                        ) : isEntry && details.time_of_entry ? (
                          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                            <span style={{
                              padding: '2px 8px',
                              borderRadius: '4px',
                              backgroundColor: '#D1FAE5',
                              color: '#065F46',
                              fontSize: '11.5px',
                              fontWeight: 700
                            }}>
                              Entry: {details.time_of_entry}
                            </span>
                            {details.two_factor_verified && (
                              <span style={{ fontSize: '11px', color: '#059669', fontWeight: 600 }}>
                                • 2FA OK
                              </span>
                            )}
                          </div>
                        ) : (
                          <div
                            style={{
                              fontSize: '12px',
                              color: 'var(--secondary-text)',
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap'
                            }}
                            title="Click to view full details"
                          >
                            {log.details_json || '—'}
                          </div>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Details Modal */}
      {selectedLog && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(15, 23, 42, 0.6)',
          backdropFilter: 'blur(3px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
          padding: '20px'
        }}>
          <div className="card" style={{
            width: '640px',
            maxWidth: '100%',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
            padding: 0
          }}>
            <div style={{
              padding: '18px 24px',
              backgroundColor: '#0F172A',
              color: '#FFFFFF',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}>
              <div>
                <div style={{ fontSize: '16px', fontWeight: 800 }}>
                  Audit Event #{selectedLog.id}
                </div>
                <div style={{ fontSize: '12px', color: '#94A3B8', marginTop: '2px' }}>
                  Action: {selectedLog.action} • {selectedLog.timestamp ? new Date(selectedLog.timestamp).toLocaleString() : ''}
                </div>
              </div>
              <button
                onClick={() => setSelectedLog(null)}
                style={{
                  background: 'none',
                  border: 'none',
                  fontSize: '18px',
                  fontWeight: 700,
                  cursor: 'pointer',
                  color: '#94A3B8'
                }}
              >
                ✕
              </button>
            </div>

            <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div>
                  <div style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--secondary-text)', fontWeight: 700 }}>User ID &amp; Role</div>
                  <div style={{ fontSize: '13.5px', fontWeight: 600, color: 'var(--primary-navy)' }}>
                    {selectedLog.user_id ? `User #${selectedLog.user_id}` : 'System Agent'} ({selectedLog.user_role || 'System'})
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--secondary-text)', fontWeight: 700 }}>IP Address</div>
                  <div style={{ fontSize: '13px', fontFamily: 'monospace' }}>{selectedLog.ip_address || '127.0.0.1'}</div>
                </div>
                <div>
                  <div style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--secondary-text)', fontWeight: 700 }}>Entity Type</div>
                  <div style={{ fontSize: '13px', fontWeight: 600 }}>{selectedLog.entity_type || 'N/A'}</div>
                </div>
                <div>
                  <div style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--secondary-text)', fontWeight: 700 }}>Entity ID</div>
                  <div style={{ fontSize: '13px', fontFamily: 'monospace' }}>{selectedLog.entity_id || 'N/A'}</div>
                </div>
              </div>

              {/* Special Entry / Exit Card */}
              {(() => {
                const details = parseDetails(selectedLog.details_json);
                if (details.event_type === 'ENTRY' || details.event_type === 'EXIT') {
                  return (
                    <div style={{
                      backgroundColor: details.event_type === 'ENTRY' ? '#ECFDF5' : '#F5F3FF',
                      border: `1px solid ${details.event_type === 'ENTRY' ? '#A7F3D0' : '#DDD6FE'}`,
                      borderRadius: '8px',
                      padding: '14px',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '6px'
                    }}>
                      <div style={{
                        fontSize: '12px',
                        fontWeight: 700,
                        color: details.event_type === 'ENTRY' ? '#065F46' : '#6D28D9',
                        textTransform: 'uppercase'
                      }}>
                        {details.event_type === 'ENTRY' ? '🟢 Session Entry Recorded' : '🔴 Session Exit Recorded'}
                      </div>
                      {details.time_of_entry && (
                        <div style={{ fontSize: '12.5px', color: '#1E293B' }}>
                          <strong>Time of Entry:</strong> {details.time_of_entry}
                        </div>
                      )}
                      {details.time_of_exit && (
                        <div style={{ fontSize: '12.5px', color: '#1E293B' }}>
                          <strong>Time of Exit:</strong> {details.time_of_exit}
                        </div>
                      )}
                      {details.session_duration && (
                        <div style={{ fontSize: '12.5px', color: '#1E293B' }}>
                          <strong>Total Session Duration:</strong> {details.session_duration}
                        </div>
                      )}
                      {details.two_factor_verified && (
                        <div style={{ fontSize: '12.5px', color: '#059669', fontWeight: 600 }}>
                          🛡️ Authenticated with Two-Step Verification
                        </div>
                      )}
                    </div>
                  );
                }
                return null;
              })()}

              <div>
                <div style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--secondary-text)', fontWeight: 700, marginBottom: '6px' }}>
                  Event Payload &amp; Details
                </div>
                <div style={{
                  padding: '12px',
                  backgroundColor: '#F8FAFC',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--border)',
                  fontSize: '12px',
                  lineHeight: '1.5',
                  wordBreak: 'break-word',
                  fontFamily: 'monospace'
                }}>
                  {selectedLog.details_json || 'No additional payload stored.'}
                </div>
              </div>
            </div>

            <div style={{
              padding: '14px 24px',
              borderTop: '1px solid var(--border)',
              display: 'flex',
              justifyContent: 'flex-end',
              backgroundColor: '#F8FAFC'
            }}>
              <button
                onClick={() => setSelectedLog(null)}
                className="btn-secondary"
                style={{ padding: '8px 18px', fontSize: '13px' }}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
