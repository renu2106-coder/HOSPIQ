import React from 'react';
import { User } from '../types';
import { LogOut, User as UserIcon, Shield, HelpCircle, FlaskConical, GraduationCap } from 'lucide-react';

interface NavbarProps {
  user: User;
  onLogout: () => void;
  onOpenTutorial?: () => void;
  onOpenTestCases?: () => void;
  onOpenVivaGuide?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  user,
  onLogout,
  onOpenTutorial,
  onOpenTestCases,
  onOpenVivaGuide
}) => {
  return (
    <header style={{
      height: '64px',
      backgroundColor: '#FFFFFF',
      borderBottom: '1px solid #E2E8F0',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 24px',
      position: 'sticky',
      top: 0,
      zIndex: 10,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span style={{
            fontSize: '17px',
            fontWeight: 800,
            color: '#0F172A',
            letterSpacing: '-0.3px'
          }}>
            Agentic Hospital Management System
          </span>
          <span style={{
            fontSize: '11.5px',
            color: '#64748B',
            borderLeft: '1px solid #CBD5E1',
            paddingLeft: '10px',
            fontWeight: 500
          }}>
            Multi-Agent AI Integration, Documentation &amp; Validation
          </span>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        {/* Spec Test Suite Button (Section 19, Page 16) */}
        {onOpenTestCases && (
          <button
            onClick={onOpenTestCases}
            type="button"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 11px',
              borderRadius: '8px',
              backgroundColor: '#EFF6FF',
              border: '1px solid #BFDBFE',
              color: '#2563EB',
              fontSize: '12px',
              fontWeight: 700,
              cursor: 'pointer',
              transition: 'all 0.15s ease'
            }}
            title="Evaluate the 6 Official Test Cases (Section 19, Page 16)"
          >
            <FlaskConical size={14} />
            <span>Spec Tests (6)</span>
          </button>
        )}

        {/* MSc Viva Defense Guide Button (Section 25, Page 22) */}
        {onOpenVivaGuide && (
          <button
            onClick={onOpenVivaGuide}
            type="button"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 11px',
              borderRadius: '8px',
              backgroundColor: '#ECFDF5',
              border: '1px solid #A7F3D0',
              color: '#059669',
              fontSize: '12px',
              fontWeight: 700,
              cursor: 'pointer',
              transition: 'all 0.15s ease'
            }}
            title="MSc Viva Defense Guide & Questions (Section 25, Page 22-23)"
          >
            <GraduationCap size={14} />
            <span>Viva Guide</span>
          </button>
        )}

        {/* Tutorial / Role Guide Button */}
        {onOpenTutorial && (
          <button
            onClick={onOpenTutorial}
            type="button"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 11px',
              borderRadius: '8px',
              backgroundColor: '#F0F9FF',
              border: '1px solid #BAE6FD',
              color: '#0284C7',
              fontSize: '12px',
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'all 0.15s ease'
            }}
            title="Open Role-Based Workflow Guide"
          >
            <HelpCircle size={14} />
            <span>Tutorial</span>
          </button>
        )}

        {/* 2FA Security Pill */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '5px',
          padding: '5px 9px',
          borderRadius: '20px',
          backgroundColor: '#F8FAFC',
          border: '1px solid #E2E8F0',
          color: '#059669',
          fontSize: '11px',
          fontWeight: 700
        }}>
          <Shield size={12} />
          <span>2FA OK</span>
        </div>

        {/* User Pill */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          padding: '4px 10px',
          borderRadius: '8px',
          backgroundColor: '#F8FAFC',
          border: '1px solid #E2E8F0'
        }}>
          <div style={{
            width: '28px',
            height: '28px',
            borderRadius: '50%',
            backgroundColor: '#0F172A',
            color: '#FFFFFF',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '12px',
            fontWeight: 700
          }}>
            {user.full_name ? user.full_name.charAt(0).toUpperCase() : 'U'}
          </div>
          <div>
            <div style={{ fontSize: '12.5px', fontWeight: 600, color: '#0F172A', lineHeight: 1.2 }}>
              {user.full_name}
            </div>
            <div style={{ fontSize: '10.5px', color: '#0284C7', fontWeight: 600 }}>
              {user.role}
            </div>
          </div>
        </div>

        {/* Logout Button */}
        <button
          onClick={onLogout}
          type="button"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '5px',
            padding: '6px 10px',
            borderRadius: '8px',
            backgroundColor: '#FFFFFF',
            border: '1px solid #CBD5E1',
            color: '#475569',
            fontSize: '12px',
            fontWeight: 600,
            cursor: 'pointer'
          }}
          title="Sign out and record session exit"
        >
          <LogOut size={13} />
          <span>Logout</span>
        </button>
      </div>
    </header>
  );
};
