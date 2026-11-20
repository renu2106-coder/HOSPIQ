import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import type { AgentExecution, LLMStatus } from '../types';
import {
  Cpu, Sparkles, RefreshCw, CheckCircle, AlertCircle, Clock,
  Filter, Search, Layers, Database, Check
} from 'lucide-react';

export const AgentTracePage: React.FC = () => {
  const [executions, setExecutions] = useState<AgentExecution[]>([]);
  const [llmStatus, setLlmStatus] = useState<LLMStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedAgent, setSelectedAgent] = useState<string>('ALL');
  const [searchPatient, setSearchPatient] = useState('');
  const [selectedExec, setSelectedExec] = useState<AgentExecution | null>(null);
  const [actionMessage, setActionMessage] = useState<{ type: 'success' | 'info' | 'error'; text: string } | null>(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [duplicatesData, setDuplicatesData] = useState<any | null>(null);

  const fetchStatusAndExecutions = async () => {
    setLoading(true);
    try {
      const [statusRes, execRes] = await Promise.all([
        api.agents.getLLMStatus().catch(() => null),
        api.agents.listExecutions(
          selectedAgent !== 'ALL' ? selectedAgent : undefined,
          searchPatient.trim() || undefined
        ).catch(() => [])
      ]);
      if (statusRes) setLlmStatus(statusRes);
      if (execRes) setExecutions(execRes);
    } catch (err: any) {
      console.error('Failed to load agent trace data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatusAndExecutions();
  }, [selectedAgent]);

  const handleRunDuplicateDetection = async () => {
    setActionLoading(true);
    setActionMessage({ type: 'info', text: 'Patient Data Management Agent analyzing registration records for duplicates...' });
    try {
      const res = await api.agents.getDuplicates();
      setDuplicatesData(res);
      setActionMessage({
        type: 'success',
        text: `Duplicate detection completed! Detected ${res.detected_duplicates_count} potential duplicates across records.`
      });
      fetchStatusAndExecutions();
    } catch (err: any) {
      setActionMessage({ type: 'error', text: `Detection failed: ${err.message}` });
    } finally {
      setActionLoading(false);
    }
  };

  const handleConsolidateAll = async () => {
    setActionLoading(true);
    setActionMessage({ type: 'info', text: 'Orchestrator Agent running batch consolidation across all 15 patient records...' });
    try {
      const res = await api.agents.consolidateAll();
      setActionMessage({
        type: 'success',
        text: `Batch consolidation succeeded: ${res.consolidated_count || 15} patient records consolidated into Unified Patient Database.`
      });
      fetchStatusAndExecutions();
    } catch (err: any) {
      setActionMessage({ type: 'error', text: `Consolidation failed: ${err.message}` });
    } finally {
      setActionLoading(false);
    }
  };

  const agentNames = [
    'ALL',
    'Orchestrator Agent',
    'Patient Data Management Agent',
    'Documentation Agent',
    'Validation Agent'
  ];

  const filteredExecutions = executions.filter(e => {
    if (searchPatient.trim() && e.patient_id) {
      return e.patient_id.toLowerCase().includes(searchPatient.toLowerCase().trim());
    }
    return true;
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '24px', fontWeight: 800, color: 'var(--primary-navy)', marginBottom: '4px' }}>
            Multi-Agent AI Coordination & Execution Trace
          </h1>
          <p style={{ fontSize: '14px', color: 'var(--secondary-text)' }}>
            Inspect live agent workflows, deterministic fallback telemetry, latency, and skill execution logs.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '10px' }}>
          <button
            onClick={handleRunDuplicateDetection}
            disabled={actionLoading}
            className="hospiq-btn-outline"
            style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
          >
            <Layers size={15} />
            <span>Detect Duplicates</span>
          </button>
          <button
            onClick={handleConsolidateAll}
            disabled={actionLoading}
            className="hospiq-btn-outline"
            style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
          >
            <Database size={15} />
            <span>Consolidate All</span>
          </button>
          <button
            onClick={fetchStatusAndExecutions}
            disabled={loading}
            className="hospiq-btn"
            style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
          >
            <RefreshCw size={15} className={loading ? 'spin' : ''} />
            <span>Refresh Trace</span>
          </button>
        </div>
      </div>

      {/* Banner / Feedback Message */}
      {actionMessage && (
        <div style={{
          padding: '12px 16px',
          borderRadius: 'var(--radius-sm)',
          fontSize: '13.5px',
          fontWeight: 600,
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          backgroundColor: actionMessage.type === 'success' ? '#E6F4EA' : actionMessage.type === 'error' ? '#FCE8E6' : '#E8F0FE',
          color: actionMessage.type === 'success' ? 'var(--success)' : actionMessage.type === 'error' ? 'var(--danger)' : 'var(--accent-blue)',
          border: `1px solid ${actionMessage.type === 'success' ? '#CEEAD6' : actionMessage.type === 'error' ? '#FAD2CF' : '#D2E3FC'}`
        }}>
          {actionMessage.type === 'success' ? <Check size={18} /> : actionMessage.type === 'error' ? <AlertCircle size={18} /> : <Sparkles size={18} />}
          <span>{actionMessage.text}</span>
        </div>
      )}

      {/* LLM Status & Agent Architecture Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px' }}>
        <div className="hospiq-card" style={{ padding: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
            <div style={{
              width: '32px',
              height: '32px',
              borderRadius: '8px',
              backgroundColor: llmStatus?.connected ? '#E6F4EA' : '#FEF3D6',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: llmStatus?.connected ? 'var(--success)' : 'var(--warning)'
            }}>
              <Sparkles size={18} />
            </div>
            <div>
              <div style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--secondary-text)', fontWeight: 700 }}>
                AI Clinical Core
              </div>
              <div style={{ fontSize: '14px', fontWeight: 700, color: 'var(--primary-navy)' }}>
                Multi-Agent Orchestrator
              </div>
            </div>
          </div>
          <div style={{ fontSize: '12px', color: 'var(--secondary-text)' }}>
            Architecture: <code style={{ fontWeight: 600, color: 'var(--primary-teal)' }}>Grounded Clinical Synthesis</code>
          </div>
          <div style={{ fontSize: '12px', marginTop: '4px', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              backgroundColor: 'var(--success)',
              display: 'inline-block'
            }} />
            <span style={{ fontWeight: 600, color: 'var(--success)' }}>
              Active &amp; Operational
            </span>
          </div>
        </div>

        <div className="hospiq-card" style={{ padding: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
            <div style={{
              width: '32px',
              height: '32px',
              borderRadius: '8px',
              backgroundColor: '#E8F0FE',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--accent-blue)'
            }}>
              <Cpu size={18} />
            </div>
            <div>
              <div style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--secondary-text)', fontWeight: 700 }}>
                Active Agent System
              </div>
              <div style={{ fontSize: '14px', fontWeight: 700, color: 'var(--primary-navy)' }}>
                5 Coordinated Agents
              </div>
            </div>
          </div>
          <div style={{ fontSize: '12px', color: 'var(--secondary-text)' }}>
            Supervised by Orchestrator Agent with human doctor sign-off barrier.
          </div>
        </div>

        <div className="hospiq-card" style={{ padding: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
            <div style={{
              width: '32px',
              height: '32px',
              borderRadius: '8px',
              backgroundColor: '#EDFDFD',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--primary-teal)'
            }}>
              <Clock size={18} />
            </div>
            <div>
              <div style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--secondary-text)', fontWeight: 700 }}>
                Total Executions Logged
              </div>
              <div style={{ fontSize: '14px', fontWeight: 700, color: 'var(--primary-navy)' }}>
                {executions.length} Runs Recorded
              </div>
            </div>
          </div>
          <div style={{ fontSize: '12px', color: 'var(--secondary-text)' }}>
            Average Latency: {executions.length > 0 ? (executions.reduce((acc, curr) => acc + (curr.latency_ms || 0), 0) / executions.length).toFixed(1) : '0'} ms
          </div>
        </div>

        <div className="hospiq-card" style={{ padding: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
            <div style={{
              width: '32px',
              height: '32px',
              borderRadius: '8px',
              backgroundColor: '#F3E8FD',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#9333EA'
            }}>
              <CheckCircle size={18} />
            </div>
            <div>
              <div style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--secondary-text)', fontWeight: 700 }}>
                7-Point Safety Check
              </div>
              <div style={{ fontSize: '14px', fontWeight: 700, color: 'var(--primary-navy)' }}>
                Deterministic Guardrails
              </div>
            </div>
          </div>
          <div style={{ fontSize: '12px', color: 'var(--secondary-text)' }}>
            Zero uncontrolled writes; documents locked until physician attestation.
          </div>
        </div>
      </div>

      {/* Duplicate detection findings preview */}
      {duplicatesData && duplicatesData.duplicates && duplicatesData.duplicates.length > 0 && (
        <div className="hospiq-card" style={{ padding: '16px', borderLeft: '4px solid var(--warning)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
            <div style={{ fontSize: '14px', fontWeight: 700, color: 'var(--primary-navy)' }}>
              Detected Demographic Duplicates ({duplicatesData.detected_duplicates_count})
            </div>
            <button
              onClick={() => setDuplicatesData(null)}
              style={{ background: 'none', border: 'none', color: 'var(--secondary-text)', cursor: 'pointer', fontSize: '12px' }}
            >
              Dismiss
            </button>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {duplicatesData.duplicates.map((dup: any, idx: number) => (
              <div key={idx} style={{
                fontSize: '12.5px',
                padding: '8px 12px',
                backgroundColor: '#FFFBEB',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid #FEF3C7'
              }}>
                <div style={{ fontWeight: 600, color: 'var(--warning)' }}>
                  Reason: {dup.reason}
                </div>
                <div style={{ color: 'var(--primary-text)', marginTop: '2px' }}>
                  Primary Patient: <strong>{dup.primary_patient_id}</strong> ({dup.name}) | Conflicting Record ID: <strong>{dup.conflicting_patient_id || 'N/A'}</strong>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Execution Filter Toolbar */}
      <div className="hospiq-card" style={{ padding: '16px', display: 'flex', gap: '16px', alignItems: 'center', flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Filter size={16} color="var(--secondary-text)" />
          <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--primary-navy)' }}>Agent:</span>
          <select
            value={selectedAgent}
            onChange={(e) => setSelectedAgent(e.target.value)}
            className="hospiq-input"
            style={{ width: '220px', padding: '6px 10px', fontSize: '13px' }}
          >
            {agentNames.map((name) => (
              <option key={name} value={name}>{name}</option>
            ))}
          </select>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flex: 1, minWidth: '240px' }}>
          <Search size={16} color="var(--secondary-text)" />
          <input
            type="text"
            placeholder="Filter by Patient ID (e.g. P001)..."
            value={searchPatient}
            onChange={(e) => setSearchPatient(e.target.value)}
            className="hospiq-input"
            style={{ padding: '6px 12px', fontSize: '13px', width: '100%' }}
          />
        </div>
      </div>

      {/* Executions Table */}
      <div className="hospiq-card" style={{ overflow: 'hidden' }}>
        <div style={{
          padding: '16px 20px',
          borderBottom: '1px solid var(--border)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <div>
            <div style={{ fontSize: '15px', fontWeight: 700, color: 'var(--primary-navy)' }}>
              Agent Execution Telemetry Log
            </div>
            <div style={{ fontSize: '12px', color: 'var(--secondary-text)' }}>
              Showing {filteredExecutions.length} recorded events with tool calls and timings
            </div>
          </div>
        </div>

        {loading ? (
          <div style={{ padding: '40px', textAlign: 'center', color: 'var(--secondary-text)' }}>
            <RefreshCw size={24} className="spin" style={{ margin: '0 auto 8px auto' }} />
            <div>Loading agent traces...</div>
          </div>
        ) : filteredExecutions.length === 0 ? (
          <div style={{ padding: '40px', textAlign: 'center', color: 'var(--secondary-text)' }}>
            <Cpu size={32} style={{ margin: '0 auto 8px auto', opacity: 0.4 }} />
            <div>No agent executions recorded matching the current filters.</div>
          </div>
        ) : (
          <table className="hospiq-table">
            <thead>
              <tr>
                <th>Execution ID</th>
                <th>Agent</th>
                <th>Task Description</th>
                <th>Patient ID</th>
                <th>Latency</th>
                <th>Status</th>
                <th>Tools Called</th>
                <th>Timestamp</th>
                <th>Inspect</th>
              </tr>
            </thead>
            <tbody>
              {filteredExecutions.map((exec) => {
                const isSuccess = exec.execution_status === 'SUCCESS';
                return (
                  <tr key={exec.id}>
                    <td>
                      <code style={{ fontSize: '11px', color: 'var(--secondary-text)' }}>
                        #{exec.id}
                      </code>
                    </td>
                    <td>
                      <span style={{ fontWeight: 600, color: 'var(--primary-navy)' }}>
                        {exec.agent_name}
                      </span>
                    </td>
                    <td style={{ maxWidth: '260px' }}>
                      <div style={{ fontSize: '12.5px', color: 'var(--primary-text)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {exec.task}
                      </div>
                    </td>
                    <td>
                      {exec.patient_id ? (
                        <span className="hospiq-badge hospiq-badge-info" style={{ fontFamily: 'monospace' }}>
                          {exec.patient_id}
                        </span>
                      ) : (
                        <span style={{ color: 'var(--secondary-text)', fontSize: '12px' }}>System</span>
                      )}
                    </td>
                    <td>
                      <span style={{
                        fontSize: '12px',
                        fontFamily: 'monospace',
                        color: (exec.latency_ms || 0) > 1000 ? 'var(--warning)' : 'var(--primary-teal)',
                        fontWeight: 600
                      }}>
                        {exec.latency_ms ? `${exec.latency_ms.toFixed(1)} ms` : '< 1 ms'}
                      </span>
                    </td>
                    <td>
                      <span className={`hospiq-badge ${isSuccess ? 'hospiq-badge-success' : 'hospiq-badge-danger'}`}>
                        {exec.execution_status}
                      </span>
                    </td>
                    <td>
                      {exec.tools_invoked_json ? (
                        <span style={{
                          fontSize: '11px',
                          backgroundColor: '#F1F5F9',
                          padding: '2px 6px',
                          borderRadius: '4px',
                          fontFamily: 'monospace'
                        }}>
                          {exec.tools_invoked_json.split(',').length} tools
                        </span>
                      ) : (
                        <span style={{ fontSize: '11px', color: 'var(--secondary-text)' }}>None</span>
                      )}
                    </td>
                    <td style={{ fontSize: '11.5px', color: 'var(--secondary-text)', whiteSpace: 'nowrap' }}>
                      {exec.timestamp ? new Date(exec.timestamp).toLocaleString() : 'N/A'}
                    </td>
                    <td>
                      <button
                        onClick={() => setSelectedExec(exec)}
                        className="hospiq-btn-outline"
                        style={{ padding: '4px 8px', fontSize: '11px' }}
                      >
                        Details
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      {/* Detail Modal */}
      {selectedExec && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(16, 38, 63, 0.6)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
          padding: '20px'
        }}>
          <div className="hospiq-card" style={{
            width: '750px',
            maxWidth: '100%',
            maxHeight: '85vh',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden'
          }}>
            <div style={{
              padding: '16px 20px',
              borderBottom: '1px solid var(--border)',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}>
              <div>
                <div style={{ fontSize: '16px', fontWeight: 800, color: 'var(--primary-navy)' }}>
                  Execution Trace #{selectedExec.id} – {selectedExec.agent_name}
                </div>
                <div style={{ fontSize: '12px', color: 'var(--secondary-text)' }}>
                  Patient: {selectedExec.patient_id || 'System-Wide'} • Latency: {selectedExec.latency_ms ? `${selectedExec.latency_ms.toFixed(1)} ms` : 'N/A'}
                </div>
              </div>
              <button
                onClick={() => setSelectedExec(null)}
                style={{
                  background: 'none',
                  border: 'none',
                  fontSize: '18px',
                  fontWeight: 700,
                  cursor: 'pointer',
                  color: 'var(--secondary-text)'
                }}
              >
                ✕
              </button>
            </div>

            <div style={{ padding: '20px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div>
                <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--secondary-text)', textTransform: 'uppercase', marginBottom: '4px' }}>
                  Task Description
                </div>
                <div style={{
                  padding: '10px 14px',
                  backgroundColor: '#F8FAFC',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '13px',
                  fontWeight: 600,
                  color: 'var(--primary-navy)'
                }}>
                  {selectedExec.task}
                </div>
              </div>

              <div>
                <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--secondary-text)', textTransform: 'uppercase', marginBottom: '4px' }}>
                  Registered Tools Executed
                </div>
                <div style={{
                  padding: '10px 14px',
                  backgroundColor: '#F8FAFC',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '12px',
                  fontFamily: 'monospace',
                  color: 'var(--primary-teal)'
                }}>
                  {selectedExec.tools_invoked_json || 'Direct Python API invocation (No secondary subtools)'}
                </div>
              </div>

              {selectedExec.result_summary && (
                <div>
                  <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--secondary-text)', textTransform: 'uppercase', marginBottom: '4px' }}>
                    Agent Output Summary
                  </div>
                  <pre style={{
                    backgroundColor: '#0F172A',
                    color: '#38BDF8',
                    padding: '12px',
                    borderRadius: 'var(--radius-sm)',
                    fontSize: '11.5px',
                    fontFamily: 'monospace',
                    overflowX: 'auto',
                    maxHeight: '160px'
                  }}>
                    {selectedExec.result_summary}
                  </pre>
                </div>
              )}

              {selectedExec.error_message && (
                <div>
                  <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--danger)', textTransform: 'uppercase', marginBottom: '4px' }}>
                    Error Message
                  </div>
                  <div style={{
                    padding: '10px 14px',
                    backgroundColor: '#FEE2E2',
                    borderRadius: 'var(--radius-sm)',
                    fontSize: '12px',
                    color: 'var(--danger)'
                  }}>
                    {selectedExec.error_message}
                  </div>
                </div>
              )}
            </div>

            <div style={{
              padding: '12px 20px',
              borderTop: '1px solid var(--border)',
              display: 'flex',
              justifyContent: 'flex-end',
              backgroundColor: '#F8FAFC'
            }}>
              <button
                onClick={() => setSelectedExec(null)}
                className="hospiq-btn"
                style={{ padding: '6px 16px', fontSize: '13px' }}
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
