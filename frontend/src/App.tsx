import React, { useState, useEffect } from 'react';
import { User, AuthToken, LLMStatus } from './types';
import { api } from './services/api';
import { Navbar } from './components/Navbar';
import { Sidebar, NavTab } from './components/Sidebar';
import { PersonalizedTutorialModal } from './components/PersonalizedTutorialModal';
import { TestCasesModal } from './components/TestCasesModal';
import { VivaDefenseModal } from './components/VivaDefenseModal';
import { AgenticHubPage } from './pages/AgenticHubPage';
import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';
import { PatientsPage } from './pages/PatientsPage';
import { DocumentationPage } from './pages/DocumentationPage';
import { UploadsPage } from './pages/UploadsPage';
import { AlertsPage } from './pages/AlertsPage';
import { CorrectionsPage } from './pages/CorrectionsPage';
import { AuditPage } from './pages/AuditPage';
import { Activity } from 'lucide-react';

export function App() {
  const [user, setUser] = useState<User | null>(null);
  const [currentTab, setCurrentTab] = useState<NavTab>('dashboard');
  const [llmStatus, setLlmStatus] = useState<LLMStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [showTutorial, setShowTutorial] = useState(false);
  const [showTestCases, setShowTestCases] = useState(false);
  const [showVivaGuide, setShowVivaGuide] = useState(false);

  // Initialize session from token
  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem('hospiq_token');
      if (token) {
        try {
          const profile = await api.auth.getProfile();
          setUser(profile);
        } catch (err) {
          console.error('Session expired or invalid:', err);
          localStorage.removeItem('hospiq_token');
          localStorage.removeItem('hospiq_user');
          setUser(null);
        }
      }

      // Check Agent AI status
      try {
        const status = await api.agents.getLLMStatus();
        setLlmStatus(status);
      } catch (err) {
        console.warn('Could not contact LLM agent status endpoint:', err);
      } finally {
        setLoading(false);
      }
    };

    initAuth();
  }, []);

  const handleLoginSuccess = async (tokenData: AuthToken) => {
    try {
      const profile = await api.auth.getProfile();
      setUser(profile);
    } catch {
      setUser({
        id: tokenData.user_id,
        username: tokenData.username,
        full_name: tokenData.full_name,
        email: `${tokenData.username}@hospiq.org`,
        role: tokenData.role,
        department: tokenData.department,
        patient_id: tokenData.patient_id,
        is_active: true,
        created_at: new Date().toISOString(),
      });
    }
    setCurrentTab('dashboard');
    setShowTutorial(true);

    api.agents.getLLMStatus().then(setLlmStatus).catch(() => null);
  };

  const handleLogout = async () => {
    try {
      await api.auth.logout();
    } catch {
      // ignore
    } finally {
      localStorage.removeItem('hospiq_token');
      localStorage.removeItem('hospiq_user');
      setUser(null);
      setCurrentTab('dashboard');
      setShowTutorial(false);
      setShowTestCases(false);
      setShowVivaGuide(false);
    }
  };

  if (loading) {
    return (
      <div style={{
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: '#F8FAFC',
        gap: '16px'
      }}>
        <div style={{
          width: '48px',
          height: '48px',
          borderRadius: '12px',
          backgroundColor: '#0F172A',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#38BDF8'
        }}>
          <Activity size={28} className="spin" />
        </div>
        <div style={{ fontSize: '15px', fontWeight: 700, color: '#0F172A' }}>
          Agentic Hospital Management System
        </div>
        <div style={{ fontSize: '12.5px', color: '#64748B' }}>
          Verifying two-step security credentials &amp; clinical data pipelines...
        </div>
      </div>
    );
  }

  // Not logged in -> Show Login Page
  if (!user) {
    return <LoginPage onLoginSuccess={handleLoginSuccess} />;
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Top Navigation Bar */}
      <Navbar
        user={user}
        onLogout={handleLogout}
        onOpenTutorial={() => setShowTutorial(true)}
        onOpenTestCases={() => setShowTestCases(true)}
        onOpenVivaGuide={() => setShowVivaGuide(true)}
      />

      {/* Main Body with Sidebar + Tab Workspace */}
      <div style={{ display: 'flex', flex: 1 }}>
        <Sidebar
          currentTab={currentTab}
          onSelectTab={setCurrentTab}
          userRole={user.role}
        />

        <main style={{
          flex: 1,
          backgroundColor: '#F8FAFC',
          padding: '24px 32px',
          overflowY: 'auto',
          maxHeight: 'calc(100vh - 64px)'
        }}>
          {currentTab === 'hub' && (
            <AgenticHubPage currentRole={user.role} />
          )}

          {currentTab === 'dashboard' && (
            <DashboardPage user={user} onNavigate={setCurrentTab} />
          )}

          {currentTab === 'patients' && (
            <PatientsPage currentRole={user.role} />
          )}

          {currentTab === 'documents' && (
            <DocumentationPage currentRole={user.role} />
          )}

          {currentTab === 'uploads' && (
            <UploadsPage />
          )}

          {currentTab === 'alerts' && (
            <AlertsPage currentRole={user.role} />
          )}

          {currentTab === 'corrections' && (
            <CorrectionsPage currentRole={user.role} />
          )}

          {currentTab === 'audit' && (
            <AuditPage />
          )}
        </main>
      </div>

      {/* Role-Specific Interactive Tutorial Modal */}
      <PersonalizedTutorialModal
        user={user}
        isOpen={showTutorial}
        onClose={() => setShowTutorial(false)}
      />

      {/* Specification Test Suite Modal (Section 19, Page 16) */}
      <TestCasesModal
        isOpen={showTestCases}
        onClose={() => setShowTestCases(false)}
      />

      {/* MSc Viva Defense Guide Modal (Section 25, Page 22-23) */}
      <VivaDefenseModal
        isOpen={showVivaGuide}
        onClose={() => setShowVivaGuide(false)}
      />
    </div>
  );
}

export default App;
