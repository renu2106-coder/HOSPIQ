import React, { useEffect, useState } from 'react';
import { User, DashboardStats, ClinicalDocument, DepartmentAlert } from '../types';
import { api } from '../services/api';
import {
  Users, FileText, AlertTriangle, ShieldCheck,
  CheckCircle2, Clock, Activity, FileSpreadsheet, Sparkles, Siren
} from 'lucide-react';
import { NavTab } from '../components/Sidebar';

interface DashboardPageProps {
  user: User;
  onNavigate: (tab: NavTab) => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({ user, onNavigate }) => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [pendingDocs, setPendingDocs] = useState<ClinicalDocument[]>([]);
  const [recentAlerts, setRecentAlerts] = useState<DepartmentAlert[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, [user]);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      if (user.role !== 'Patient') {
        const metrics = await api.dashboard.getMetrics();
        setStats(metrics);

        const docs = await api.documents.list();
        setPendingDocs(docs.filter(d => d.validation_status === 'Pending Doctor Review').slice(0, 5));

        const alerts = await api.alerts.list({ status_filter: 'Open' });
        setRecentAlerts(alerts.slice(0, 5));
      } else {
        const docs = await api.documents.list();
        setPendingDocs(docs.slice(0, 5));
      }
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div style={{ padding: '32px', textAlign: 'center', color: 'var(--secondary-text)' }}>
        Loading clinical dashboard...
      </div>
    );
  }

  return (
    <div style={{ padding: '24px', maxWidth: '1300px', margin: '0 auto' }}>
      {/* Header bar */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: '20px'
      }}>
        <div>
          <h2 style={{ fontSize: '20px', fontWeight: 700, color: 'var(--primary-navy)' }}>
            {user.role} Dashboard
          </h2>
          <p style={{ fontSize: '13px', color: 'var(--secondary-text)', marginTop: '2px' }}>
            {user.full_name} • {user.department || 'Clinical Operations'}
          </p>
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          {['Doctor', 'Paramedic'].includes(user.role) && (
            <button onClick={() => onNavigate('documents')} className="btn-primary">
              <FileText size={16} />
              <span>Generate / Review Document</span>
            </button>
          )}
          {user.role !== 'Patient' && (
            <button onClick={() => onNavigate('uploads')} className="btn-clinical">
              <FileSpreadsheet size={16} />
              <span>Update Hospital Database</span>
            </button>
          )}
        </div>
      </div>

      {/* KPI Cards Grid */}
      {stats && (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))',
          gap: '16px',
          marginBottom: '24px'
        }}>
          <div className="card">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', color: 'var(--secondary-text)', fontSize: '12px', fontWeight: 600 }}>
              <span>Unified Patients</span>
              <Users size={18} color="var(--primary-teal)" />
            </div>
            <div style={{ fontSize: '24px', fontWeight: 800, color: 'var(--primary-navy)', marginTop: '6px' }}>
              {stats.total_patients}
            </div>
            <div style={{ fontSize: '11px', color: 'var(--secondary-text)', marginTop: '4px' }}>
              8 Connected Departments
            </div>
          </div>

          <div className="card">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', color: 'var(--secondary-text)', fontSize: '12px', fontWeight: 600 }}>
              <span>Clinical Documents</span>
              <FileText size={18} color="var(--clinical-blue)" />
            </div>
            <div style={{ fontSize: '24px', fontWeight: 800, color: 'var(--primary-navy)', marginTop: '6px' }}>
              {stats.documents_generated}
            </div>
            <div style={{ fontSize: '11px', color: 'var(--secondary-text)', marginTop: '4px' }}>
              {stats.documents_approved} Approved • {stats.documents_pending_review} Pending
            </div>
          </div>

          <div className="card">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', color: 'var(--secondary-text)', fontSize: '12px', fontWeight: 600 }}>
              <span>Data Ingestion</span>
              <FileSpreadsheet size={18} color="var(--accent-gold)" />
            </div>
            <div style={{ fontSize: '24px', fontWeight: 800, color: 'var(--primary-navy)', marginTop: '6px' }}>
              {stats.data_ingestion_files}
            </div>
            <div style={{ fontSize: '11px', color: 'var(--secondary-text)', marginTop: '4px' }}>
              Automated PDF & File Updates
            </div>
          </div>

          <div className="card">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', color: 'var(--secondary-text)', fontSize: '12px', fontWeight: 600 }}>
              <span>Emergency & EMS</span>
              <Siren size={18} color="var(--alert-red)" />
            </div>
            <div style={{ fontSize: '24px', fontWeight: 800, color: 'var(--primary-navy)', marginTop: '6px' }}>
              {stats.emergency_documents_issued || 0}
            </div>
            <div style={{ fontSize: '11px', color: 'var(--secondary-text)', marginTop: '4px' }}>
              {stats.total_paramedics || 1} Paramedic Active • Direct Issued
            </div>
          </div>
        </div>
      )}

      {/* Main Grid: Pending Doctor Reviews + Department Alerts */}
      <div style={{ display: 'grid', gridTemplateColumns: user.role === 'Patient' ? '1fr' : '1.3fr 1fr', gap: '20px' }}>
        {/* Section 1: Documents Awaiting Review or Approved Summaries */}
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
            <h3 style={{ fontSize: '14px', fontWeight: 700, color: 'var(--primary-navy)' }}>
              {user.role === 'Doctor' ? 'Documents Awaiting Physician Review' : user.role === 'Paramedic' ? 'Emergency Clinical Documents' : 'Recent Clinical Documents'}
            </h3>
            <button onClick={() => onNavigate('documents')} className="btn-secondary" style={{ padding: '4px 10px', fontSize: '12px' }}>
              View All
            </button>
          </div>

          {pendingDocs.length === 0 ? (
            <div style={{ padding: '24px', textAlign: 'center', color: 'var(--secondary-text)', fontSize: '13px' }}>
              No pending documents. All clinical records reviewed.
            </div>
          ) : (
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Patient</th>
                    <th>Type</th>
                    <th>Status</th>
                    <th>Date</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {pendingDocs.map((doc) => (
                    <tr key={doc.id}>
                      <td style={{ fontWeight: 600 }}>{doc.patient_id}</td>
                      <td>{doc.doc_type}</td>
                      <td>
                        <span className={`badge ${
                          doc.validation_status === 'Approved' ? 'badge-success' :
                          doc.validation_status === 'Validation Failed' ? 'badge-error' :
                          'badge-warning'
                        }`}>
                          {doc.validation_status}
                        </span>
                      </td>
                      <td style={{ fontSize: '12px', color: 'var(--secondary-text)' }}>
                        {new Date(doc.created_at).toLocaleDateString()}
                      </td>
                      <td>
                        <button
                          onClick={() => onNavigate('documents')}
                          className="btn-secondary"
                          style={{ padding: '4px 8px', fontSize: '11.5px' }}
                        >
                          Review
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Section 2: Department Alerts or Patient Info */}
        {user.role !== 'Patient' ? (
          <div className="card">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
              <h3 style={{ fontSize: '14px', fontWeight: 700, color: 'var(--primary-navy)' }}>
                Department Discrepancy Alerts
              </h3>
              <button onClick={() => onNavigate('alerts')} className="btn-secondary" style={{ padding: '4px 10px', fontSize: '12px' }}>
                View All ({recentAlerts.length})
              </button>
            </div>

            {recentAlerts.length === 0 ? (
              <div style={{ padding: '24px', textAlign: 'center', color: 'var(--secondary-text)', fontSize: '13px' }}>
                No active discrepancies detected across departments.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {recentAlerts.map((alert) => (
                  <div
                    key={alert.id}
                    style={{
                      padding: '10px 12px',
                      borderRadius: 'var(--radius-sm)',
                      border: '1px solid var(--border)',
                      backgroundColor: '#FFFFFF',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '4px'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <span style={{ fontSize: '12px', fontWeight: 700, color: 'var(--primary-navy)' }}>
                        {alert.department} • {alert.patient_id}
                      </span>
                      <span className={`badge ${
                        alert.priority === 'Critical' ? 'badge-error' :
                        alert.priority === 'High' ? 'badge-warning' :
                        'badge-info'
                      }`}>
                        {alert.priority}
                      </span>
                    </div>
                    <p style={{ fontSize: '12px', color: 'var(--primary-text)', lineHeight: 1.3 }}>
                      {alert.description}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        ) : (
          <div className="card">
            <h3 style={{ fontSize: '14px', fontWeight: 700, color: 'var(--primary-navy)', marginBottom: '12px' }}>
              My Patient Record Status
            </h3>
            <p style={{ fontSize: '13px', color: 'var(--secondary-text)', lineHeight: 1.5 }}>
              Your record is continuously reconciled across Registration, Laboratory, Pharmacy, Nursing, and Radiology.
            </p>
            <div style={{ marginTop: '16px' }}>
              <button onClick={() => onNavigate('patients')} className="btn-primary" style={{ fontSize: '12px' }}>
                View Full Health Summary
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Department Ingestion Breakdown */}
      {stats && stats.records_by_department && (
        <div className="card" style={{ marginTop: '20px' }}>
          <h4 style={{ fontSize: '13.5px', fontWeight: 700, color: 'var(--primary-navy)', marginBottom: '12px' }}>
            Connected Department Records Breakdown
          </h4>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
            gap: '12px'
          }}>
            {Object.entries(stats.records_by_department).map(([dept, count]) => (
              <div
                key={dept}
                style={{
                  padding: '10px 12px',
                  backgroundColor: '#F8FAFC',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--border)',
                  textAlign: 'center'
                }}
              >
                <div style={{ fontSize: '11px', color: 'var(--secondary-text)', fontWeight: 600, textTransform: 'uppercase' }}>
                  {dept}
                </div>
                <div style={{ fontSize: '18px', fontWeight: 800, color: 'var(--primary-navy)', marginTop: '4px' }}>
                  {count}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
