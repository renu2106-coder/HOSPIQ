import React, { useEffect, useState } from 'react';
import { Patient, UnifiedPatientRecord } from '../types';
import { api } from '../services/api';
import {
  Search, RefreshCw, Eye, CheckCircle2, AlertTriangle, FileText,
  Activity, Pill, Stethoscope, Calendar, DollarSign, Bed, ShieldAlert
} from 'lucide-react';

interface PatientsPageProps {
  currentRole: string;
}

export const PatientsPage: React.FC<PatientsPageProps> = ({ currentRole }) => {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedPatientId, setSelectedPatientId] = useState<string | null>(null);
  const [patientBundle, setPatientBundle] = useState<any | null>(null);
  const [unifiedRecord, setUnifiedRecord] = useState<UnifiedPatientRecord | null>(null);
  const [activeTab, setActiveTab] = useState<string>('unified');
  const [loading, setLoading] = useState(true);
  const [bundleLoading, setBundleLoading] = useState(false);
  const [reconsolidating, setReconsolidating] = useState(false);

  useEffect(() => {
    fetchPatients();
  }, [searchQuery]);

  const fetchPatients = async () => {
    setLoading(true);
    try {
      const data = await api.patients.list(searchQuery);
      setPatients(data);
    } catch (err) {
      console.error('Failed to load patients:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectPatient = async (id: string) => {
    setSelectedPatientId(id);
    setBundleLoading(true);
    setActiveTab('unified');
    try {
      const [bundle, unified] = await Promise.all([
        api.records.getPatientRecords(id),
        api.patients.getUnified(id)
      ]);
      setPatientBundle(bundle);
      setUnifiedRecord(unified);
    } catch (err) {
      console.error('Failed to fetch patient records bundle:', err);
    } finally {
      setBundleLoading(false);
    }
  };

  const handleReconsolidate = async () => {
    if (!selectedPatientId) return;
    setReconsolidating(true);
    try {
      await api.patients.reconsolidate(selectedPatientId);
      const unified = await api.patients.getUnified(selectedPatientId);
      setUnifiedRecord(unified);
    } catch (err) {
      alert('Failed to reconsolidate record: ' + err);
    } finally {
      setReconsolidating(false);
    }
  };

  return (
    <div style={{ padding: '28px', maxWidth: '1300px', margin: '0 auto' }}>
      {/* Top Search Bar */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
        <div>
          <h2 style={{ fontSize: '20px', fontWeight: 700, color: 'var(--primary-navy)' }}>
            Patient Health Records Directory
          </h2>
          <p style={{ fontSize: '13px', color: 'var(--secondary-text)', marginTop: '2px' }}>
            Search unified clinical records, cross-department datasets, and source provenance.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          <div style={{ position: 'relative', width: '280px' }}>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by ID, Name, Phone..."
              style={{
                width: '100%',
                padding: '8px 12px 8px 34px',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--border)',
                fontSize: '13px',
                outline: 'none'
              }}
            />
            <Search size={16} color="var(--secondary-text)" style={{ position: 'absolute', left: '10px', top: '10px' }} />
          </div>
          <button onClick={fetchPatients} className="btn-secondary" style={{ padding: '8px 12px' }}>
            <RefreshCw size={14} />
          </button>
        </div>
      </div>

      {/* Patients Table */}
      <div className="card" style={{ padding: '0', overflow: 'hidden' }}>
        <div className="table-container" style={{ border: 'none' }}>
          <table>
            <thead>
              <tr>
                <th>Patient ID</th>
                <th>Full Name</th>
                <th>DOB / Age</th>
                <th>Gender</th>
                <th>Contact Phone</th>
                <th>Blood Group</th>
                <th>Allergies</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={8} style={{ textAlign: 'center', padding: '24px', color: 'var(--secondary-text)' }}>
                    Searching patient directory...
                  </td>
                </tr>
              ) : patients.length === 0 ? (
                <tr>
                  <td colSpan={8} style={{ textAlign: 'center', padding: '24px', color: 'var(--secondary-text)' }}>
                    No patients match your search query.
                  </td>
                </tr>
              ) : (
                patients.map((p) => (
                  <tr
                    key={p.id}
                    style={{
                      backgroundColor: selectedPatientId === p.id ? '#F0F9F8' : 'transparent',
                      cursor: 'pointer'
                    }}
                    onClick={() => handleSelectPatient(p.id)}
                  >
                    <td style={{ fontWeight: 700, color: 'var(--primary-navy)' }}>{p.id}</td>
                    <td style={{ fontWeight: 600 }}>{p.full_name}</td>
                    <td>{p.dob || 'N/A'} {p.age ? `(${p.age}y)` : ''}</td>
                    <td>{p.gender || 'N/A'}</td>
                    <td>{p.contact_phone || 'N/A'}</td>
                    <td>
                      <span className="badge badge-info">{p.blood_group || 'N/A'}</span>
                    </td>
                    <td style={{ fontSize: '12px', color: p.allergies ? 'var(--error)' : 'var(--secondary-text)' }}>
                      {p.allergies || 'None'}
                    </td>
                    <td>
                      <button
                        onClick={(e) => { e.stopPropagation(); handleSelectPatient(p.id); }}
                        className="btn-secondary"
                        style={{ padding: '4px 8px', fontSize: '12px' }}
                      >
                        <Eye size={14} />
                        <span>Inspect</span>
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Detailed Patient Modal / View */}
      {selectedPatientId && patientBundle && (
        <div style={{ marginTop: '24px' }} className="card">
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            borderBottom: '1px solid var(--border)',
            paddingBottom: '16px',
            marginBottom: '16px'
          }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '18px', fontWeight: 800, color: 'var(--primary-navy)' }}>
                  {patientBundle.patient.full_name} ({patientBundle.patient.id})
                </span>
                {unifiedRecord && (
                  <span className={`badge ${
                    unifiedRecord.validation_status === 'Validated' ? 'badge-success' :
                    unifiedRecord.validation_status === 'Requires Attention' ? 'badge-warning' : 'badge-neutral'
                  }`}>
                    {unifiedRecord.validation_status} ({unifiedRecord.completeness_score}% Complete)
                  </span>
                )}
              </div>
              <div style={{ fontSize: '12.5px', color: 'var(--secondary-text)', marginTop: '4px' }}>
                DOB: {patientBundle.patient.dob || 'N/A'} • Contact: {patientBundle.patient.contact_phone || 'N/A'} • Address: {patientBundle.patient.address || 'N/A'}
              </div>
            </div>

            {['Doctor', 'Hospital Administrator', 'Nurse'].includes(currentRole) && (
              <button
                onClick={handleReconsolidate}
                disabled={reconsolidating}
                className="btn-secondary"
                style={{ fontSize: '12px', padding: '6px 12px' }}
              >
                <RefreshCw size={14} className={reconsolidating ? 'spin' : ''} />
                <span>{reconsolidating ? 'Re-consolidating...' : 'Re-run Agent Consolidation'}</span>
              </button>
            )}
          </div>

          {/* Department Tabs Bar */}
          <div style={{
            display: 'flex',
            gap: '6px',
            borderBottom: '1px solid var(--border)',
            paddingBottom: '10px',
            marginBottom: '16px',
            overflowX: 'auto'
          }}>
            {[
              { id: 'unified', label: 'Unified Quality View', count: null },
              { id: 'registration', label: 'Registration', count: patientBundle.registration_records?.length },
              { id: 'laboratory', label: 'Laboratory', count: patientBundle.laboratory_records?.length },
              { id: 'pharmacy', label: 'Pharmacy', count: patientBundle.pharmacy_records?.length },
              { id: 'radiology', label: 'Radiology', count: patientBundle.radiology_records?.length },
              { id: 'nursing', label: 'Nursing Vitals', count: patientBundle.nursing_records?.length },
              { id: 'inpatient', label: 'Inpatient Ward', count: patientBundle.inpatient_records?.length },
              { id: 'appointments', label: 'Appointments', count: patientBundle.appointment_records?.length },
              { id: 'billing', label: 'Billing & Claims', count: patientBundle.billing_records?.length },
              { id: 'provenance', label: 'Source Provenance', count: null },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                style={{
                  padding: '6px 12px',
                  borderRadius: 'var(--radius-sm)',
                  border: 'none',
                  backgroundColor: activeTab === tab.id ? 'var(--primary-navy)' : 'transparent',
                  color: activeTab === tab.id ? '#FFFFFF' : 'var(--primary-text)',
                  fontSize: '12.5px',
                  fontWeight: activeTab === tab.id ? 600 : 500,
                  cursor: 'pointer',
                  whiteSpace: 'nowrap'
                }}
              >
                {tab.label} {tab.count !== null && tab.count !== undefined ? `(${tab.count})` : ''}
              </button>
            ))}
          </div>

          {/* Tab Content Display */}
          {activeTab === 'unified' && unifiedRecord && (
            <div>
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
                gap: '16px',
                marginBottom: '16px'
              }}>
                <div style={{ padding: '14px', backgroundColor: '#F8FAFC', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)' }}>
                  <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--primary-navy)', marginBottom: '8px' }}>
                    Data Completeness & Confidence
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <div style={{ flex: 1, backgroundColor: '#E2E8F0', height: '8px', borderRadius: '4px', overflow: 'hidden' }}>
                      <div style={{
                        width: `${unifiedRecord.completeness_score}%`,
                        backgroundColor: unifiedRecord.completeness_score > 70 ? 'var(--success)' : 'var(--warning)',
                        height: '100%'
                      }} />
                    </div>
                    <span style={{ fontSize: '13px', fontWeight: 700 }}>{unifiedRecord.completeness_score}%</span>
                  </div>
                </div>

                <div style={{ padding: '14px', backgroundColor: '#F8FAFC', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)' }}>
                  <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--primary-navy)', marginBottom: '6px' }}>
                    Missing Mandatory Fields
                  </div>
                  {unifiedRecord.missing_fields_json ? (
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                      {JSON.parse(unifiedRecord.missing_fields_json).length === 0 ? (
                        <span style={{ fontSize: '12.5px', color: 'var(--success)' }}>No mandatory fields missing.</span>
                      ) : (
                        JSON.parse(unifiedRecord.missing_fields_json).map((f: string) => (
                          <span key={f} className="badge badge-warning">{f}</span>
                        ))
                      )}
                    </div>
                  ) : <span style={{ fontSize: '12px' }}>None</span>}
                </div>
              </div>

              {unifiedRecord.conflict_fields_json && JSON.parse(unifiedRecord.conflict_fields_json).length > 0 && (
                <div style={{
                  padding: '14px',
                  backgroundColor: '#FFF9E6',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid #FFE58F',
                  marginBottom: '16px'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#B78103', fontWeight: 700, fontSize: '13px', marginBottom: '8px' }}>
                    <AlertTriangle size={16} />
                    <span>Cross-Department Discrepancies Flagged by Agent:</span>
                  </div>
                  <ul style={{ paddingLeft: '20px', fontSize: '12.5px', color: '#595959' }}>
                    {JSON.parse(unifiedRecord.conflict_fields_json).map((c: any, i: number) => (
                      <li key={i} style={{ marginBottom: '4px' }}>
                        <strong>{c.department}:</strong> {c.description}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {activeTab === 'laboratory' && (
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Test Name</th>
                    <th>Result Value</th>
                    <th>Unit</th>
                    <th>Reference Range</th>
                    <th>Date</th>
                    <th>Ordering Doctor</th>
                    <th>Source</th>
                  </tr>
                </thead>
                <tbody>
                  {patientBundle.laboratory_records.map((l: any) => (
                    <tr key={l.id}>
                      <td style={{ fontWeight: 600 }}>{l.test_name}</td>
                      <td style={{ fontWeight: l.is_abnormal ? 700 : 400, color: l.is_abnormal ? 'var(--error)' : 'inherit' }}>
                        {l.result_value} {l.is_abnormal && <span className="badge badge-error">Abnormal</span>}
                      </td>
                      <td>{l.unit || '-'}</td>
                      <td>{l.reference_range || <span style={{ color: 'var(--warning)' }}>Missing</span>}</td>
                      <td>{l.report_date || '-'}</td>
                      <td>{l.ordering_physician || '-'}</td>
                      <td style={{ fontSize: '11.5px', color: 'var(--secondary-text)' }}>{l.source_file}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {activeTab === 'pharmacy' && (
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Medicine</th>
                    <th>Strength</th>
                    <th>Dosage & Frequency</th>
                    <th>Duration</th>
                    <th>Prescribed</th>
                    <th>Doctor</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {patientBundle.pharmacy_records.map((p: any) => (
                    <tr key={p.id}>
                      <td style={{ fontWeight: 600 }}>{p.medicine_name}</td>
                      <td>{p.strength || '-'}</td>
                      <td>{p.dosage} ({p.frequency})</td>
                      <td>{p.duration || '-'}</td>
                      <td>{p.prescription_date || '-'}</td>
                      <td>{p.prescribing_doctor || '-'}</td>
                      <td>
                        <span className={`badge ${p.status === 'Active' ? 'badge-success' : 'badge-neutral'}`}>
                          {p.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {activeTab === 'radiology' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {patientBundle.radiology_records.map((r: any) => (
                <div key={r.id} style={{ padding: '14px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', backgroundColor: '#F8FAFC' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                    <span style={{ fontWeight: 700, color: 'var(--primary-navy)' }}>
                      {r.imaging_type} ({r.body_part})
                    </span>
                    <span style={{ fontSize: '12px', color: 'var(--secondary-text)' }}>{r.report_date}</span>
                  </div>
                  <p style={{ fontSize: '13px', lineHeight: 1.4, marginBottom: '6px' }}>
                    <strong>Findings:</strong> {r.report_findings}
                  </p>
                  {r.impression && (
                    <p style={{ fontSize: '13px', color: 'var(--clinical-blue)', fontWeight: 600 }}>
                      Impression: {r.impression}
                    </p>
                  )}
                  <div style={{ fontSize: '11.5px', color: 'var(--secondary-text)', marginTop: '6px' }}>
                    Radiologist: {r.radiologist_name} • PACS Ref: {r.source_file}
                  </div>
                </div>
              ))}
            </div>
          )}

          {activeTab === 'nursing' && (
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Blood Pressure</th>
                    <th>Pulse</th>
                    <th>Temperature</th>
                    <th>SpO2</th>
                    <th>Recorded At</th>
                    <th>Nurse</th>
                    <th>Observations</th>
                  </tr>
                </thead>
                <tbody>
                  {patientBundle.nursing_records.map((n: any) => (
                    <tr key={n.id}>
                      <td style={{ fontWeight: 600 }}>{n.vital_bp || '-'}</td>
                      <td>{n.vital_pulse ? `${n.vital_pulse} bpm` : '-'}</td>
                      <td>{n.vital_temp ? `${n.vital_temp} °F` : '-'}</td>
                      <td>{n.vital_spo2 ? `${n.vital_spo2} %` : '-'}</td>
                      <td>{n.recorded_at || '-'}</td>
                      <td>{n.nurse_name || '-'}</td>
                      <td style={{ fontSize: '12px' }}>{n.nurse_notes || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {activeTab === 'inpatient' && (
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Admission Date</th>
                    <th>Discharge Date</th>
                    <th>Ward / Bed</th>
                    <th>Admission Diagnosis</th>
                    <th>Discharge Diagnosis</th>
                    <th>Attending Doctor</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {patientBundle.inpatient_records.map((i: any) => (
                    <tr key={i.id}>
                      <td>{i.admission_date}</td>
                      <td>{i.discharge_date || 'Current Inpatient'}</td>
                      <td>{i.ward} / Bed {i.bed_number}</td>
                      <td style={{ fontSize: '12.5px' }}>{i.admission_diagnosis}</td>
                      <td style={{ fontSize: '12.5px' }}>{i.discharge_diagnosis || 'Pending'}</td>
                      <td>{i.attending_physician}</td>
                      <td><span className="badge badge-info">{i.discharge_status || 'Active'}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {activeTab === 'appointments' && (
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Date & Time</th>
                    <th>Department</th>
                    <th>Doctor</th>
                    <th>Reason for Visit</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {patientBundle.appointment_records.map((a: any) => (
                    <tr key={a.id}>
                      <td style={{ fontWeight: 600 }}>{a.appointment_date} {a.appointment_time}</td>
                      <td>{a.department}</td>
                      <td>{a.doctor}</td>
                      <td style={{ fontSize: '12.5px' }}>{a.reason_for_visit}</td>
                      <td><span className="badge badge-neutral">{a.appointment_status}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {activeTab === 'billing' && (
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Bill ID</th>
                    <th>Service Description</th>
                    <th>Amount ($)</th>
                    <th>Payment Status</th>
                    <th>Date</th>
                    <th>Source Gateway</th>
                  </tr>
                </thead>
                <tbody>
                  {patientBundle.billing_records.map((b: any) => (
                    <tr key={b.id}>
                      <td style={{ fontWeight: 600 }}>{b.bill_id}</td>
                      <td>{b.service}</td>
                      <td style={{ fontWeight: 700 }}>${b.amount.toFixed(2)}</td>
                      <td>
                        <span className={`badge ${b.payment_status === 'Paid' ? 'badge-success' : 'badge-warning'}`}>
                          {b.payment_status}
                        </span>
                      </td>
                      <td>{b.billing_date}</td>
                      <td style={{ fontSize: '11.5px', color: 'var(--secondary-text)' }}>{b.source_file}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {activeTab === 'provenance' && (
            <div style={{ padding: '16px', backgroundColor: '#F8FAFC', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)' }}>
              <h4 style={{ fontSize: '13.5px', fontWeight: 700, color: 'var(--primary-navy)', marginBottom: '12px' }}>
                Department Source Data Provenance & Lineage
              </h4>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '10px' }}>
                {Object.entries(patientBundle.provenance || {}).map(([dept, sources]: any) => (
                  <div key={dept} style={{ padding: '10px 12px', backgroundColor: '#FFFFFF', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)' }}>
                    <div style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', color: 'var(--primary-teal)' }}>
                      {dept}
                    </div>
                    <div style={{ fontSize: '12px', color: 'var(--primary-text)', marginTop: '4px' }}>
                      Sources: {Array.isArray(sources) && sources.length > 0 ? Array.from(new Set(sources)).join(', ') : 'Direct DB System'}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

