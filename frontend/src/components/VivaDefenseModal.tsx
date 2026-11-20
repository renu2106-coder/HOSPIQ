import React, { useState } from 'react';
import {
  GraduationCap, Search, CheckCircle2, BookOpen,
  HelpCircle, ChevronDown, ChevronUp, X
} from 'lucide-react';

interface VivaQuestion {
  id: number;
  question: string;
  category: string;
  answer: string;
  keyPoints: string[];
}

const VIVA_QUESTIONS: VivaQuestion[] = [
  {
    id: 1,
    question: "Why do we need a Data Management Agent?",
    category: "Architecture & Agents",
    answer: "Healthcare data originates in fragmented, heterogeneous departmental silos (CSV lab results, JSON prescriptions, TXT radiology reports). Raw hospital data cannot be fed directly into an LLM because it contains inconsistencies, duplicates, conflicting records, and unstructured formats. The Data Management Agent normalizes data, detects duplicates across departments, matches patient identities, and maintains an authoritative, queryable relational record.",
    keyPoints: [
      "Heterogeneous data harmonization (Registration, Lab, Pharmacy, Nursing, Radiology)",
      "Prevents garbage-in, garbage-out errors in clinical LLM prompts",
      "Executes deterministic matching algorithms rather than probabilistic guesses"
    ]
  },
  {
    id: 2,
    question: "Why can't we simply send all hospital data to an LLM?",
    category: "Architecture & Agents",
    answer: "Sending entire hospital databases to an LLM violates context window limits, incurs prohibitive latency/costs, breaches data privacy (HIPAA/GDPR), and drastically increases hallucination rates. Furthermore, LLMs cannot execute deterministic transactional database queries or enforce strict ACID constraints. An agentic architecture retrieves only the scoped context required for a specific task.",
    keyPoints: [
      "Context window exhaustion and high token latency",
      "Extreme risk of clinical hallucinations on large unstructured dumps",
      "Privacy principle of least privilege / data minimization"
    ]
  },
  {
    id: 3,
    question: "What is the difference between an agent and a chatbot?",
    category: "Architecture & Agents",
    answer: "A chatbot is a conversational text-in, text-out interface that predicts tokens based on prompt context without autonomy. An Agent possesses goal-directed agency: it decomposes goals, selects and invokes external tools/skills, queries relational databases, inspects execution feedback, and enforces deterministic validation guardrails before presenting output.",
    keyPoints: [
      "Chatbot = Conversational token predictor",
      "Agent = Goal-oriented orchestrator with tool use and environment feedback",
      "Agents operate over multi-step clinical pipelines, not single prompt turns"
    ]
  },
  {
    id: 4,
    question: "What is a tool? What is a skill?",
    category: "Tools & Skills",
    answer: "A Tool is an atomic, deterministic function that executes a single bounded operation (e.g. search_patient(), insert_lab_result()). A Skill is a composed, reusable workflow that sequences multiple tools and algorithmic checks to accomplish a meaningful clinical task (e.g. summarize_encounter(), patient_matching()).",
    keyPoints: [
      "Tool: Single atomic operation (e.g. search_patient, insert_vital)",
      "Skill: Reusable workflow combining multiple operations (e.g. patient_matching)",
      "Agent: The decision-maker choosing which skills and tools to apply"
    ]
  },
  {
    id: 5,
    question: "Which parts of your system use an LLM? Which do not?",
    category: "Multi-Agent Design",
    answer: "The LLM is used strictly where natural language synthesis is essential: clinical narrative drafting (Discharge Summary, Encounter Notes, Plain-language Patient Education) and multi-language translation. Non-LLM deterministic code handles: CSV/PDF parsing, regex date/gender normalization, SQL database insertion, fuzzy patient identity matching, 7-point validation scorecards, and audit trail logging.",
    keyPoints: [
      "LLM: Clinical narrative generation, multilingual translation",
      "Non-LLM: DB CRUD, fuzzy matching, entity normalization, validation checks, audit logging",
      "Guarantees predictability and prevents AI hallucinations in critical math/logic"
    ]
  },
  {
    id: 6,
    question: "How does your system identify the same patient across different sources?",
    category: "Data & Matching",
    answer: "Our system employs a multi-factor fuzzy matching skill (Section 11, Page 10). It does not rely on a single field. It combines: Jaro-Winkler name similarity (handling abbreviations like 'R. Kumar' vs 'Ravi Kumar'), normalized Date of Birth (converting DD/MM/YYYY to ISO), phone number matching, and gender normalization. Matches above 0.85 confidence are consolidated into the canonical record.",
    keyPoints: [
      "Multi-factor matching: Name similarity + Normalized DOB + Phone + Gender",
      "Handles spelling variants: 'Ravi Kumar', 'R. Kumar', 'Ravi K.', 'RAVI KUMAR'",
      "Assigns canonical Patient ID (e.g. P001) with provenance citations"
    ]
  },
  {
    id: 7,
    question: "How do you handle conflicting information across departments?",
    category: "Safety & Conflicts",
    answer: "When departments present contradictory observations (e.g. Nursing records BP 120/80 while OPD records 160/100, or Pharmacy has diverging dosages), our Conflict Detection Skill flags the discrepancy with priority ratings ('High' / 'Critical'). It generates a Department Alert and locks document auto-approval, requiring human physician review.",
    keyPoints: [
      "Automated cross-department discrepancy detection",
      "Generates explicit Department Alerts (Priority: High / Critical)",
      "Stops automatic finalization; forces physician review"
    ]
  },
  {
    id: 8,
    question: "How do you detect hallucinations in generated documents?",
    category: "Validation Agent",
    answer: "The Validation Agent executes deterministic 7-point validation (Check 5: Unsupported Statements). It parses all medications, lab values, and clinical claims in the generated draft and verifies each against the authoritative source database. If an unverified drug (e.g. Insulin 10 units) appears in the draft without existing in Pharmacy records, the document is marked Status: FLAGGED.",
    keyPoints: [
      "Strict grounding verification against SQL database records",
      "Flags unsupported medications or unverified lab values",
      "Produces structured FLAGGED output matching Page 6 specifications"
    ]
  },
  {
    id: 9,
    question: "What constitutes agent memory and state vs persistent database?",
    category: "Architecture & Agents",
    answer: "The persistent database (SQLite) stores immutable clinical truth: patients, encounters, lab results, prescriptions, and append-only audit logs. Agent working state/memory is ephemeral context: active patient ID, selected task, tool execution results, interim LLM drafts, and validation scorecards during the live session.",
    keyPoints: [
      "Persistent DB: Authoritative healthcare truth across encounters",
      "Agent State: Ephemeral working context, active step, and tool responses",
      "Clean separation prevents state pollution across different patient sessions"
    ]
  },
  {
    id: 10,
    question: "How can you trace a generated clinical statement back to its source?",
    category: "Provenance & Audit",
    answer: "Through granular provenance metadata (Section 17, Page 14-15). Every extracted lab and medication record retains source department, record ID, and date. Generated documents append source department citations (e.g. Source: Laboratory LAB1023, Pharmacy PHARM-002), and all actions are recorded in the immutable audit trail.",
    keyPoints: [
      "Source department, record ID, and date tagged on every clinical data item",
      "Document metadata cites exact retrieved source records",
      "Cryptographic audit log records who generated, reviewed, and approved"
    ]
  },
  {
    id: 11,
    question: "Could your system work without Internet connectivity?",
    category: "Advanced Extensions",
    answer: "Yes (Section 15, Page 13-14). HOSPIQ supports full local/offline operation on a hospital LAN using a local Ollama instance (e.g. llama3.2 or qwen2.5) with local SQLite and Python. When internet access is restricted or down, the system continues running offline with zero external API dependencies.",
    keyPoints: [
      "Local Ollama LLM integration on hospital LAN",
      "Embedded SQLite database requiring no cloud network infrastructure",
      "Ensures continuous clinical operation during disaster or network outages"
    ]
  },
  {
    id: 12,
    question: "What are the major risks of deploying such a system in a real hospital?",
    category: "Clinical Safety & Ethics",
    answer: "Major risks include: clinical hallucinations leading to incorrect medication dosages, silent automation bias where clinicians rubber-stamp AI drafts, edge-case failure in patient matching merging two distinct individuals, and data breaches. Our architecture mitigates this via mandatory human physician attestation, 7-point validation scorecards, 2FA security, and immutable audit logging.",
    keyPoints: [
      "Automation bias: Clinicians over-relying on AI drafts without reading",
      "Identity merger error: Inappropriate fuzzy matching of separate individuals",
      "Mitigated by strict human-in-the-loop sign-off, validation scorecards, and 2FA"
    ]
  }
];

interface VivaDefenseModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const VivaDefenseModal: React.FC<VivaDefenseModalProps> = ({ isOpen, onClose }) => {
  const [search, setSearch] = useState('');
  const [expandedId, setExpandedId] = useState<number | null>(1);
  const [selectedCategory, setSelectedCategory] = useState<string>('ALL');

  if (!isOpen) return null;

  const categories = ['ALL', 'Architecture & Agents', 'Tools & Skills', 'Multi-Agent Design', 'Data & Matching', 'Safety & Conflicts', 'Validation Agent', 'Provenance & Audit', 'Clinical Safety & Ethics'];

  const filtered = VIVA_QUESTIONS.filter(q => {
    const matchesCat = selectedCategory === 'ALL' || q.category === selectedCategory;
    const matchesSearch = !search.trim() ||
      q.question.toLowerCase().includes(search.toLowerCase()) ||
      q.answer.toLowerCase().includes(search.toLowerCase());
    return matchesCat && matchesSearch;
  });

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
        maxWidth: '860px',
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
              backgroundColor: '#059669',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#FFFFFF'
            }}>
              <GraduationCap size={22} />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '17px', fontWeight: 800 }}>MSc Viva Defense Guide</span>
                <span style={{
                  fontSize: '11px',
                  backgroundColor: 'rgba(16, 185, 129, 0.2)',
                  color: '#34D399',
                  padding: '2px 8px',
                  borderRadius: '12px',
                  fontWeight: 600
                }}>
                  Section 25: Questions (Page 22-23)
                </span>
              </div>
              <div style={{ fontSize: '12px', color: '#94A3B8', marginTop: '2px' }}>
                Comprehensive academic answers to official evaluation questions
              </div>
            </div>
          </div>

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

        {/* Search & Filter Toolbar */}
        <div style={{
          padding: '14px 24px',
          backgroundColor: '#F8FAFC',
          borderBottom: '1px solid #E2E8F0',
          display: 'flex',
          gap: '12px',
          flexWrap: 'wrap',
          alignItems: 'center'
        }}>
          <div style={{ position: 'relative', flex: 1, minWidth: '220px' }}>
            <Search size={15} color="#64748B" style={{ position: 'absolute', left: '10px', top: '10px' }} />
            <input
              type="text"
              placeholder="Search viva questions or keywords..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{
                width: '100%',
                padding: '7px 12px 7px 32px',
                borderRadius: '8px',
                border: '1px solid #CBD5E1',
                fontSize: '13px',
                outline: 'none'
              }}
            />
          </div>

          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            style={{
              padding: '7px 12px',
              borderRadius: '8px',
              border: '1px solid #CBD5E1',
              fontSize: '12.5px',
              fontWeight: 600,
              color: '#0F172A',
              backgroundColor: '#FFFFFF',
              outline: 'none'
            }}
          >
            {categories.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
        </div>

        {/* Questions Accordion */}
        <div style={{ padding: '20px 24px', overflowY: 'auto', flex: 1, display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {filtered.map((item) => {
            const isExpanded = expandedId === item.id;
            return (
              <div
                key={item.id}
                style={{
                  border: `1px solid ${isExpanded ? '#0284C7' : '#E2E8F0'}`,
                  borderRadius: '10px',
                  overflow: 'hidden',
                  backgroundColor: '#FFFFFF',
                  transition: 'all 0.2s ease'
                }}
              >
                <div
                  onClick={() => setExpandedId(isExpanded ? null : item.id)}
                  style={{
                    padding: '14px 18px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    cursor: 'pointer',
                    backgroundColor: isExpanded ? '#F0F9FF' : '#FFFFFF'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      width: '24px',
                      height: '24px',
                      borderRadius: '50%',
                      backgroundColor: isExpanded ? '#0284C7' : '#E2E8F0',
                      color: isExpanded ? '#FFFFFF' : '#475569',
                      fontSize: '11.5px',
                      fontWeight: 700
                    }}>
                      {item.id}
                    </span>
                    <span style={{ fontSize: '14px', fontWeight: 700, color: '#0F172A' }}>
                      {item.question}
                    </span>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{
                      fontSize: '11px',
                      padding: '2px 8px',
                      borderRadius: '6px',
                      backgroundColor: '#F1F5F9',
                      color: '#475569',
                      fontWeight: 600
                    }}>
                      {item.category}
                    </span>
                    {isExpanded ? <ChevronUp size={18} color="#0284C7" /> : <ChevronDown size={18} color="#94A3B8" />}
                  </div>
                </div>

                {isExpanded && (
                  <div style={{ padding: '16px 20px', borderTop: '1px solid #BAE6FD', backgroundColor: '#FFFFFF' }}>
                    <p style={{ fontSize: '13.5px', color: '#334155', lineHeight: 1.6, marginBottom: '14px' }}>
                      {item.answer}
                    </p>

                    <div style={{
                      backgroundColor: '#F8FAFC',
                      border: '1px solid #E2E8F0',
                      borderRadius: '8px',
                      padding: '12px 16px'
                    }}>
                      <div style={{ fontSize: '11px', fontWeight: 700, color: '#64748B', textTransform: 'uppercase', marginBottom: '6px' }}>
                        Key Points for Examiner:
                      </div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                        {item.keyPoints.map((pt, idx) => (
                          <div key={idx} style={{ display: 'flex', alignItems: 'flex-start', gap: '6px', fontSize: '12.5px', color: '#1E293B' }}>
                            <CheckCircle2 size={15} color="#059669" style={{ flexShrink: 0, marginTop: '2px' }} />
                            <span>{pt}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
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
          <span style={{ fontSize: '12px', color: '#64748B' }}>
            Showing {filtered.length} curated academic defense questions &amp; answers.
          </span>
          <button
            onClick={onClose}
            style={{
              padding: '8px 18px',
              backgroundColor: '#0F172A',
              color: '#FFFFFF',
              border: 'none',
              borderRadius: '8px',
              fontSize: '13px',
              fontWeight: 600,
              cursor: 'pointer'
            }}
          >
            Close Guide
          </button>
        </div>
      </div>
    </div>
  );
};
