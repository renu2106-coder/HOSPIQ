import React, { useState } from 'react';
import { User } from '../types';
import {
  Sparkles, CheckCircle2, Shield, Stethoscope, Ambulance,
  UserCheck, Pill, Eye, Database, FileText, ArrowRight, ArrowLeft, X
} from 'lucide-react';

interface TutorialStep {
  title: string;
  badge: string;
  description: string;
  highlights: string[];
}

interface PersonalizedTutorialModalProps {
  user: User;
  isOpen: boolean;
  onClose: () => void;
}

export const PersonalizedTutorialModal: React.FC<PersonalizedTutorialModalProps> = ({
  user,
  isOpen,
  onClose
}) => {
  const [currentStepIndex, setCurrentStepIndex] = useState(0);

  if (!isOpen) return null;

  const role = user.role;

  const getTutorialContent = (): { roleTitle: string; roleIcon: any; steps: TutorialStep[] } => {
    switch (role) {
      case 'Doctor':
        return {
          roleTitle: 'Physician / Doctor Portal',
          roleIcon: Stethoscope,
          steps: [
            {
              title: 'Unified Patient Health Records',
              badge: 'Step 1: Patient Context',
              description: 'Access patient records synthesized from 8 hospital departments: Registration, Laboratory, Pharmacy, Ward Nursing, and Radiology.',
              highlights: [
                'View cross-department timeline of diagnoses and vitals',
                'Detect drug-drug interactions and conflicting lab values automatically',
                'Zero duplicate patient entries via automatic entity matching'
              ]
            },
            {
              title: 'AI Multi-Agent Document Generation',
              badge: 'Step 2: Clinical Drafting',
              description: 'Use the AI Workflow Hub to generate grounded clinical drafts in seconds based strictly on patient health data.',
              highlights: [
                'Automated Discharge Summaries, Encounter Notes, and Patient Education',
                'All drafts are subject to deterministic safety guardrails',
                'Instant cross-language translation into multiple patient languages'
              ]
            },
            {
              title: 'Physician Attestation & Human Review',
              badge: 'Step 3: Clinical Sign-off',
              description: 'No AI-generated document is finalized or released to patients without explicit physician sign-off.',
              highlights: [
                'Review side-by-side grounded evidence and verification scorecards',
                'Edit clinical content directly prior to attestation',
                'One-click digital signature with immutable cryptographic audit logging'
              ]
            },
            {
              title: 'Personalized Doctor Audit Trail',
              badge: 'Step 4: Security & Provenance',
              description: 'Every action you take—login entry, document approval, rejection, and exit—is recorded for compliance.',
              highlights: [
                'Track exact login entry and logout exit timestamps',
                'Tamper-evident audit trail showing all physician-signed documents',
                'Compliant with international healthcare audit standards'
              ]
            }
          ]
        };

      case 'Paramedic':
        return {
          roleTitle: 'Paramedic / EMS Field Operations',
          roleIcon: Ambulance,
          steps: [
            {
              title: 'Pre-Hospital Triage & Patient Lookup',
              badge: 'Step 1: Emergency Access',
              description: 'Access critical patient allergy profiles, past conditions, and current medications directly from ambulance or field triage.',
              highlights: [
                'Rapid search by Patient ID or name during urgent transfers',
                'Instant allergy alerts and emergency contact records',
                'Read-only access to prior physician discharge summaries'
              ]
            },
            {
              title: 'Clinical Summary Editing & Preparation',
              badge: 'Step 2: EMS Documentation',
              description: 'Generate and edit clinical encounter summaries reflecting immediate field interventions and vital sign trends.',
              highlights: [
                'Prepare handover notes for receiving hospital physicians',
                'Edit drafts with paramedic field observations before physician review',
                'Automatic FHIR data schema generation for emergency records'
              ]
            },
            {
              title: 'Extreme Emergency Direct Attestation',
              badge: 'Step 3: Life-Critical Protocol',
              description: 'Under severe, time-critical life emergencies, paramedics can directly issue documentation with logged justification.',
              highlights: [
                'Bypasses physician queue only in extreme emergency triage scenarios',
                'Mandatory justification input required for accountability',
                'Immediately flagged in audit trail with high-priority notice'
              ]
            },
            {
              title: 'EMS Activity & Shift Audit Log',
              badge: 'Step 4: Accountability',
              description: 'Personalized audit trail reflecting all your emergency actions, login entries, and session duration.',
              highlights: [
                'Verified entry/exit session logging',
                'Immutable records of emergency document overrides',
                'Full transparency with hospital administration'
              ]
            }
          ]
        };

      case 'Nurse':
        return {
          roleTitle: 'Inpatient Ward Nursing Portal',
          roleIcon: UserCheck,
          steps: [
            {
              title: 'Ward Patient Monitoring & Vitals',
              badge: 'Step 1: Bedside Care',
              description: 'Track inpatient vital signs, bedside medication administration, and nursing notes in real-time.',
              highlights: [
                'Immediate visual indicators for elevated blood pressure and abnormal labs',
                'Patient timeline tracking from ward admission to discharge planning',
                'Continuous synchronization with central hospital database'
              ]
            },
            {
              title: 'Clinical Discrepancy Alerts',
              badge: 'Step 2: Safety Verification',
              description: 'Stay ahead of medication conflicts and dosage anomalies flagged by the multi-agent detection engine.',
              highlights: [
                'Inspect pharmacy vs doctor prescription differences',
                'Receive immediate alerts on unvalidated medication orders',
                'Coordinate with supervising physician before administration'
              ]
            },
            {
              title: 'Nurse Shift Audits & Session Tracking',
              badge: 'Step 3: Duty Log',
              description: 'View your personalized shift activity with exact login entry time, logout exit time, and completed verifications.',
              highlights: [
                'Tracks active ward duty duration',
                'Personalized audit views protecting nursing staff integrity',
                'Fully integrated with two-factor authentication'
              ]
            }
          ]
        };

      case 'Pharmacist':
        return {
          roleTitle: 'Hospital Pharmacy Portal',
          roleIcon: Pill,
          steps: [
            {
              title: 'Prescription & Dosage Reconciliations',
              badge: 'Step 1: Medication Review',
              description: 'Detect discrepancies between physician orders, ward administration, and dispensary inventory.',
              highlights: [
                'Automated identification of diverging dosages and conflicting frequencies',
                'Instant cross-reference with patient kidney/liver function labs',
                'Prevent dangerous medication errors before dispensing'
              ]
            },
            {
              title: 'Patient Medication Education',
              badge: 'Step 2: Patient Guidance',
              description: 'Generate clear, plain-language medication advisories tailored to patient literacy and preferred languages.',
              highlights: [
                'Automatic generation of dosage schedules and food interaction warnings',
                'Multi-language translation for patient discharge packets',
                'Verified by clinical pharmacotherapy guardrails'
              ]
            }
          ]
        };

      case 'Radiologist':
        return {
          roleTitle: 'Diagnostic Imaging & Radiology',
          roleIcon: Eye,
          steps: [
            {
              title: 'Imaging Study Ingestion & Linking',
              badge: 'Step 1: Diagnostic Integration',
              description: 'Link imaging impressions, CT scans, and MRI findings directly into the unified patient longitudinal record.',
              highlights: [
                'Synchronize radiology reports with hospital database',
                'AI summarizes key findings for attending physician review',
                'Cross-references clinical symptoms with imaging observations'
              ]
            }
          ]
        };

      case 'Hospital Administrator':
        return {
          roleTitle: 'Hospital Administrator Portal',
          roleIcon: Database,
          steps: [
            {
              title: 'Automated Database Synchronization',
              badge: 'Step 1: Data Integration',
              description: 'Normalize legacy hospital PDF records and tabular datasets with one-click automated synchronization.',
              highlights: [
                'Converts raw unstructured records and lab tables into clean database records',
                'Reconciles duplicate patient identifiers across all 8 hospital systems',
                'Fully automated pipeline with real-time progress indicators'
              ]
            },
            {
              title: 'System-Wide Master Audit Trail',
              badge: 'Step 2: Compliance & Governance',
              description: 'As Administrator, you have complete global visibility over all user actions, entry/exit times, and document lifecycles.',
              highlights: [
                'Inspect 2FA verification results and exact entry/exit session durations',
                'Filter by Action, User, Entity, and Status across all hospital departments',
                'Export tamper-evident CSV audit reports for healthcare accreditation'
              ]
            },
            {
              title: 'Role-Based Access Control (RBAC)',
              badge: 'Step 3: Security & Boundaries',
              description: 'Ensure strict confidentiality: doctors view doctor audits, nurses view nurse schedules, and patients only view their personal records.',
              highlights: [
                'Strict cryptographic barriers between clinical tiers',
                'Two-Step Verification enforced across all accounts',
                'Zero unauthorized data access across departments'
              ]
            }
          ]
        };

      default: // Patient
        return {
          roleTitle: 'Patient Portal',
          roleIcon: Shield,
          steps: [
            {
              title: 'Your Unified Health Record',
              badge: 'Step 1: Your Records',
              description: 'View your integrated medical summary consolidating your visits, laboratory results, medications, and care plans.',
              highlights: [
                'Consolidated record from all hospital departments',
                'Transparent access to test results and vital history',
                'Secure and private with Two-Step Verification protection'
              ]
            },
            {
              title: 'Physician-Approved Discharge Documents',
              badge: 'Step 2: Care Instructions',
              description: 'Read and download care instructions, medication guides, and discharge summaries approved by your doctor.',
              highlights: [
                'Care plans written in plain, easy-to-understand language',
                'Available in multiple languages for you and your family',
                'Download official PDF copies anytime'
              ]
            }
          ]
        };
    }
  };

  const { roleTitle, roleIcon: RoleIcon, steps } = getTutorialContent();
  const currentStep = steps[currentStepIndex] || steps[0];
  const isFirst = currentStepIndex === 0;
  const isLast = currentStepIndex === steps.length - 1;

  const handleNext = () => {
    if (isLast) {
      onClose();
    } else {
      setCurrentStepIndex(prev => prev + 1);
    }
  };

  const handlePrev = () => {
    if (!isFirst) {
      setCurrentStepIndex(prev => prev - 1);
    }
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(15, 23, 42, 0.65)',
      backdropFilter: 'blur(4px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
      padding: '20px'
    }}>
      <div style={{
        maxWidth: '620px',
        width: '100%',
        backgroundColor: '#FFFFFF',
        borderRadius: '16px',
        boxShadow: '0 20px 40px -15px rgba(0, 0, 0, 0.25)',
        border: '1px solid #E2E8F0',
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column',
        animation: 'fadeIn 0.2s ease-out'
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
              <RoleIcon size={22} />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '16px', fontWeight: 700 }}>{roleTitle}</span>
                <span style={{
                  fontSize: '11px',
                  backgroundColor: 'rgba(56, 189, 248, 0.2)',
                  color: '#38BDF8',
                  padding: '2px 8px',
                  borderRadius: '12px',
                  fontWeight: 600
                }}>
                  Personalized Guide
                </span>
              </div>
              <div style={{ fontSize: '12px', color: '#94A3B8', marginTop: '2px' }}>
                Welcome, {user.full_name} • Tailored for your clinical role
              </div>
            </div>
          </div>

          <button
            onClick={onClose}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#94A3B8',
              cursor: 'pointer',
              padding: '4px',
              borderRadius: '6px'
            }}
            title="Close Tutorial"
          >
            <X size={20} />
          </button>
        </div>

        {/* Step Progress Bar */}
        <div style={{ display: 'flex', padding: '0 24px', gap: '8px', marginTop: '20px' }}>
          {steps.map((_, idx) => (
            <div
              key={idx}
              onClick={() => setCurrentStepIndex(idx)}
              style={{
                flex: 1,
                height: '6px',
                borderRadius: '3px',
                backgroundColor: idx <= currentStepIndex ? '#0284C7' : '#E2E8F0',
                cursor: 'pointer',
                transition: 'all 0.3s ease'
              }}
              title={`Jump to step ${idx + 1}`}
            />
          ))}
        </div>

        {/* Modal Body */}
        <div style={{ padding: '24px 28px', minHeight: '260px' }}>
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            padding: '4px 10px',
            backgroundColor: '#F0F9FF',
            color: '#0284C7',
            borderRadius: '6px',
            fontSize: '11.5px',
            fontWeight: 700,
            letterSpacing: '0.5px',
            textTransform: 'uppercase',
            marginBottom: '10px'
          }}>
            <Sparkles size={14} />
            <span>{currentStep.badge}</span>
          </div>

          <h2 style={{
            fontSize: '19px',
            fontWeight: 800,
            color: '#0F172A',
            marginBottom: '10px'
          }}>
            {currentStep.title}
          </h2>

          <p style={{
            fontSize: '13.5px',
            color: '#475569',
            lineHeight: 1.6,
            marginBottom: '18px'
          }}>
            {currentStep.description}
          </p>

          <div style={{
            backgroundColor: '#F8FAFC',
            border: '1px solid #E2E8F0',
            borderRadius: '10px',
            padding: '14px 18px',
            display: 'flex',
            flexDirection: 'column',
            gap: '8px'
          }}>
            <div style={{ fontSize: '11px', fontWeight: 700, color: '#64748B', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Key Workflow Capabilities:
            </div>
            {currentStep.highlights.map((item, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', fontSize: '12.5px', color: '#1E293B' }}>
                <CheckCircle2 size={16} color="#059669" style={{ flexShrink: 0, marginTop: '2px' }} />
                <span>{item}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Footer Actions */}
        <div style={{
          padding: '16px 24px',
          backgroundColor: '#F8FAFC',
          borderTop: '1px solid #E2E8F0',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <span style={{ fontSize: '12px', color: '#64748B', fontWeight: 500 }}>
            Step {currentStepIndex + 1} of {steps.length}
          </span>

          <div style={{ display: 'flex', gap: '10px' }}>
            {!isFirst && (
              <button
                type="button"
                onClick={handlePrev}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '8px 14px',
                  backgroundColor: '#FFFFFF',
                  color: '#475569',
                  border: '1px solid #CBD5E1',
                  borderRadius: '8px',
                  fontSize: '13px',
                  fontWeight: 600,
                  cursor: 'pointer'
                }}
              >
                <ArrowLeft size={15} />
                <span>Previous</span>
              </button>
            )}

            <button
              type="button"
              onClick={handleNext}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '8px 18px',
                backgroundColor: isLast ? '#059669' : '#0284C7',
                color: '#FFFFFF',
                border: 'none',
                borderRadius: '8px',
                fontSize: '13px',
                fontWeight: 600,
                cursor: 'pointer',
                boxShadow: isLast ? '0 2px 8px rgba(5, 150, 105, 0.3)' : '0 2px 8px rgba(2, 132, 199, 0.3)'
              }}
            >
              <span>{isLast ? "Got It, Let's Begin" : 'Next Step'}</span>
              <ArrowRight size={15} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
