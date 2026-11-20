import React from 'react';
import { User } from '../types';
import {
  LayoutDashboard, Users, FileText, UploadCloud,
  AlertTriangle, CheckSquare, MessageSquare, ShieldCheck, Sparkles
} from 'lucide-react';

export type NavTab =
  | 'hub'
  | 'dashboard'
  | 'patients'
  | 'documents'
  | 'uploads'
  | 'alerts'
  | 'corrections'
  | 'audit';

interface SidebarProps {
  currentTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
  userRole: User['role'];
}

export const Sidebar: React.FC<SidebarProps> = ({ currentTab, onSelectTab, userRole }) => {
  const isPatient = userRole === 'Patient';

  const menuItems = [
    { id: 'hub' as NavTab, label: 'AI Workflow Hub', icon: Sparkles, show: true },
    { id: 'dashboard' as NavTab, label: 'Dashboard', icon: LayoutDashboard, show: true },
    { id: 'patients' as NavTab, label: isPatient ? 'My Health Record' : 'Patient Records', icon: Users, show: true },
    { id: 'documents' as NavTab, label: isPatient ? 'My Documents' : 'Clinical Documents', icon: FileText, show: true },
    { id: 'uploads' as NavTab, label: 'Uploads & DB Sync', icon: UploadCloud, show: !isPatient },
    { id: 'alerts' as NavTab, label: 'Clinical Alerts', icon: AlertTriangle, show: !isPatient },
    { id: 'corrections' as NavTab, label: 'Human Review', icon: CheckSquare, show: !isPatient },
    { id: 'audit' as NavTab, label: 'Audit Trail', icon: ShieldCheck, show: ['Hospital Administrator', 'Doctor', 'Nurse', 'Paramedic'].includes(userRole) },
  ];

  return (
    <aside style={{
      width: '240px',
      backgroundColor: 'var(--primary-navy)',
      color: '#FFFFFF',
      display: 'flex',
      flexDirection: 'column',
      flexShrink: 0,
      minHeight: 'calc(100vh - 64px)',
    }}>
      <div style={{ padding: '20px 16px 12px 16px' }}>
        <div style={{
          fontSize: '11px',
          textTransform: 'uppercase',
          letterSpacing: '0.8px',
          color: 'var(--soft-teal)',
          fontWeight: 700,
          marginBottom: '8px'
        }}>
          Navigation
        </div>
      </div>

      <nav style={{ flex: 1, padding: '0 8px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
        {menuItems.filter(item => item.show).map((item) => {
          const Icon = item.icon;
          const isActive = currentTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onSelectTab(item.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                padding: '10px 14px',
                borderRadius: 'var(--radius-sm)',
                border: 'none',
                backgroundColor: isActive ? 'var(--navy-surface)' : 'transparent',
                color: isActive ? 'var(--soft-teal)' : '#CBD5E1',
                fontSize: '13.5px',
                fontWeight: isActive ? 600 : 400,
                textAlign: 'left',
                width: '100%',
                position: 'relative',
              }}
            >
              {isActive && (
                <div style={{
                  position: 'absolute',
                  left: 0,
                  top: '6px',
                  bottom: '6px',
                  width: '3.5px',
                  backgroundColor: 'var(--primary-teal)',
                  borderRadius: '0 4px 4px 0'
                }} />
              )}
              <Icon size={18} color={isActive ? 'var(--soft-teal)' : '#94A3B8'} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>
    </aside>
  );
};

