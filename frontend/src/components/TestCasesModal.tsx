import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import {
  FlaskConical, CheckCircle2, AlertTriangle, XCircle, RefreshCw,
  FileCheck, ShieldAlert, ArrowRight, X, Play
} from 'lucide-react';

interface TestCaseResult {
  test_case_id: number;
  title: string;
  page_reference: string;
  description: string;
  patient_id: string;
  input_summary: string;
  result_status: string;
  details: any;
}

interface TestCasesModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const TestCasesModal: React.FC<TestCasesModalProps> = ({ isOpen, onClose }) => {
  const [results, setResults] = useState<TestCaseResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<number>(1);

  const runTests = async () => {
    setLoading(true);
    try {
      const data = await api.testCases.runAll();
      setResults(data);
    } catch (err) {
      console.error('Failed to run test cases:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen && results.length === 0) {
      runTests();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const currentTest = results.find(r => r.test_case_id === activeTab) || results[0];

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(15, 23, 42, 0.7)',
      backdropFilter: 'blur(4px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
      padding: '20px'
    }}>
      <div style={{
        maxWidth: '840px',
        width: '100%',
        maxHeight: '90vh',
        backgroundColor: '#FFFFFF',
        borderRadius: '16px',
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
        border: '1px solid #CBD5E1',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden'
      }}>
        {/* Header */}
        <div style={{
          backgroundColor: '#0F172A',
          padding: '20px 24px',
          color: '#FFFFFF',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{
              width: '40px',
              height: '40px',
              borderRadius: '10px',
              backgroundColor: '#0284C7',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#FFFFFF'
            }}>
              <FlaskConical size={22} />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '17px', fontWeight: 800 }}>Academic Specification Test Suite</span>
                <span style={{
                  fontSize: '11px',
                  backgroundColor: 'rgba(56, 189, 248, 0.2)',
                  color: '#38BDF8',
                  padding: '2px 8px',
                  borderRadius: '12px',
                  fontWeight: 600
                }}>
                  Section 19: Testing (Page 16)
                </span>
              </div>
              <div style={{ fontSize: '12px', color: '#94A3B8', marginTop: '2px' }}>
                Live evaluation of all 6 test cases mandated by the reference document
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <button
              onClick={runTests}
              disabled={loading}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '6px 12px',
                backgroundColor: 'rgba(255, 255, 255, 0.1)',
                border: '1px solid rgba(255, 255, 255, 0.2)',
                borderRadius: '8px',
                color: '#FFFFFF',
                fontSize: '12px',
                fontWeight: 600,
                cursor: loading ? 'not-allowed' : 'pointer'
              }}
            >
              <RefreshCw size={14} className={loading ? 'spin' : ''} />
              <span>{loading ? 'Executing...' : 'Re-run Tests'}</span>
            </button>
            <button
              onClick={onClose}
              style={{
                background: 'none',
                border: 'none',
                color: '#94A3B8',
                cursor: 'pointer',
                padding: '4px'
              }}
            >
              <X size={20} />
            </button>
          </div>
        </div>

        {/* Tab Strip for the 6 Test Cases */}
        <div style={{
          display: 'flex',
          backgroundColor: '#F8FAFC',
          borderBottom: '1px solid #E2E8F0',
          overflowX: 'auto',
          padding: '0 12px'
        }}>
          {[1, 2, 3, 4, 5, 6].map((num) => {
            const isActive = activeTab === num;
            const res = results.find(r => r.test_case_id === num);
            const statusPassed = res?.result_status?.includes('PASS') || res?.result_status?.includes('VERIF');

            return (
              <button
                key={num}
                onClick={() => setActiveTab(num)}
                style={{
                  padding: '12px 16px',
                  border: 'none',
                  background: 'none',
                  borderBottom: isActive ? '3px solid #0284C7' : '3px solid transparent',
                  color: isActive ? '#0284C7' : '#64748B',
                  fontWeight: isActive ? 700 : 500,
                  fontSize: '13px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  cursor: 'pointer',
                  whiteSpace: 'nowrap'
                }}
              >
                <span>Test {num}</span>
                {res && (
                  <span style={{
                    width: '8px',
                    height: '8px',
                    borderRadius: '50%',
                    backgroundColor: statusPassed ? '#059669' : '#D97706'
                  }} />
                )}
              </button>
            );
          })}
        </div>

        {/* Modal Body */}
        <div style={{ padding: '24px', overflowY: 'auto', flex: 1 }}>
          {loading && results.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px', color: '#64748B' }}>
              <RefreshCw size={24} className="spin" style={{ margin: '0 auto 8px auto' }} />
              <div>Running 6 specification test cases against hospital database...</div>
            </div>
          ) : currentTest ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {/* Test Header Card */}
              <div style={{
                padding: '16px 20px',
                borderRadius: '10px',
                backgroundColor: '#F0F9FF',
                border: '1px solid #BAE6FD',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center'
              }}>
                <div>
                  <div style={{ fontSize: '11px', fontWeight: 700, color: '#0284C7', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                    {currentTest.page_reference}
                  </div>
                  <h3 style={{ fontSize: '17px', fontWeight: 800, color: '#0F172A', marginTop: '2px' }}>
                    Test Case {currentTest.test_case_id}: {currentTest.title}
                  </h3>
                  <div style={{ fontSize: '12.5px', color: '#475569', marginTop: '4px' }}>
                    {currentTest.description}
                  </div>
                </div>

                <div style={{
                  padding: '6px 14px',
                  borderRadius: '20px',
                  backgroundColor: '#ECFDF5',
                  color: '#059669',
                  border: '1px solid #A7F3D0',
                  fontSize: '12px',
                  fontWeight: 700,
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px'
                }}>
                  <CheckCircle2 size={16} />
                  <span>{currentTest.result_status}</span>
                </div>
              </div>

              {/* Input Scenario */}
              <div style={{
                backgroundColor: '#FFFFFF',
                borderRadius: '10px',
                border: '1px solid #E2E8F0',
                padding: '16px'
              }}>
                <div style={{ fontSize: '11.5px', fontWeight: 700, color: '#64748B', textTransform: 'uppercase', marginBottom: '6px' }}>
                  Input Scenario (Simulated Hospital Input)
                </div>
                <div style={{
                  padding: '10px 14px',
                  backgroundColor: '#F8FAFC',
                  borderRadius: '6px',
                  fontFamily: 'monospace',
                  fontSize: '12.5px',
                  color: '#0F172A',
                  border: '1px solid #E2E8F0'
                }}>
                  {currentTest.input_summary}
                </div>
              </div>

              {/* Execution Details & Verification */}
              <div style={{
                backgroundColor: '#FFFFFF',
                borderRadius: '10px',
                border: '1px solid #E2E8F0',
                padding: '16px'
              }}>
                <div style={{ fontSize: '11.5px', fontWeight: 700, color: '#64748B', textTransform: 'uppercase', marginBottom: '8px' }}>
                  Agent Behavior &amp; Verification Evidence
                </div>
                <pre style={{
                  padding: '12px 14px',
                  backgroundColor: '#0F172A',
                  color: '#38BDF8',
                  borderRadius: '6px',
                  fontSize: '12px',
                  lineHeight: '1.5',
                  overflowX: 'auto',
                  fontFamily: 'monospace'
                }}>
                  {JSON.stringify(currentTest.details, null, 2)}
                </pre>
              </div>
            </div>
          ) : null}
        </div>

        {/* Footer */}
        <div style={{
          padding: '14px 24px',
          backgroundColor: '#F8FAFC',
          borderTop: '1px solid #E2E8F0',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <div style={{ fontSize: '12px', color: '#64748B' }}>
            All 6 tests verify requirements from Page 16 of the MSc project task document.
          </div>
          <button
            onClick={onClose}
            style={{
              padding: '8px 18px',
              backgroundColor: '#0284C7',
              color: '#FFFFFF',
              border: 'none',
              borderRadius: '8px',
              fontSize: '13px',
              fontWeight: 600,
              cursor: 'pointer'
            }}
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
