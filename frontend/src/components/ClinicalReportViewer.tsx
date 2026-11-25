import React from 'react';
import { stripReportMarkdown } from '../utils/formatClinicalReport';

interface ClinicalReportViewerProps {
  content: string;
  compact?: boolean;
}

/**
 * Renders clinical reports cleanly without raw Markdown stars (*) or hashtags (#).
 */
export const ClinicalReportViewer: React.FC<ClinicalReportViewerProps> = ({ content, compact = false }) => {
  const cleanText = stripReportMarkdown(content);
  const lines = cleanText.split('\n');

  const elements: React.ReactNode[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];
    const nextLine = i + 1 < lines.length ? lines[i + 1].trim() : '';
    const trimmed = line.trim();

    // Document title underlined with '====' or first all-caps title line
    if (trimmed && (/^={5,}$/.test(nextLine) || (i === 0 && /^[A-Z0-9\s/&()-]{4,}$/.test(trimmed)))) {
      elements.push(
        <div
          key={i}
          style={{
            fontSize: '18px',
            fontWeight: 800,
            color: '#0F172A',
            letterSpacing: '0.4px',
            paddingBottom: '8px',
            marginBottom: '8px',
            borderBottom: '2px solid #0F172A'
          }}
        >
          {trimmed}
        </div>
      );
      i += /^={5,}$/.test(nextLine) ? 2 : 1;
      continue;
    }

    // Section heading underlined with '----' or numbered section heading like '1. PATIENT DEMOGRAPHICS'
    if (trimmed && (/^-{5,}$/.test(nextLine) || /^\d+\.\s+[A-Za-z].+$/.test(trimmed))) {
      elements.push(
        <div
          key={i}
          style={{
            fontSize: '14px',
            fontWeight: 800,
            color: '#0F172A',
            marginTop: '14px',
            marginBottom: '6px',
            paddingBottom: '4px',
            borderBottom: '1px solid #E2E8F0'
          }}
        >
          {trimmed}
        </div>
      );
      i += /^-{5,}$/.test(nextLine) ? 2 : 1;
      continue;
    }

    // Standalone divider lines
    if (/^[=-]{5,}$/.test(trimmed)) {
      i += 1;
      continue;
    }

    // Blank spacer
    if (!trimmed) {
      elements.push(<div key={i} style={{ height: '6px' }} />);
      i += 1;
      continue;
    }

    // Bullet item (• or - )
    if (trimmed.startsWith('• ') || trimmed.startsWith('- ')) {
      const body = trimmed.slice(2);
      const colonIdx = body.indexOf(':');
      const pipeIdx = body.indexOf('|');

      // Highlight key label only when colon appears before any pipe separator
      if (colonIdx > 0 && colonIdx < 48 && (pipeIdx === -1 || colonIdx < pipeIdx)) {
        const label = body.slice(0, colonIdx + 1);
        const value = body.slice(colonIdx + 1);
        elements.push(
          <div key={i} style={{ paddingLeft: '10px', marginBottom: '3px', display: 'flex', gap: '6px' }}>
            <span style={{ color: '#0284C7', fontWeight: 700 }}>•</span>
            <span>
              <strong style={{ color: '#1E293B', fontWeight: 700 }}>{label}</strong>
              <span style={{ color: '#334155' }}>{value}</span>
            </span>
          </div>
        );
      } else {
        elements.push(
          <div key={i} style={{ paddingLeft: '10px', marginBottom: '3px', display: 'flex', gap: '6px', color: '#334155' }}>
            <span style={{ color: '#0284C7', fontWeight: 700 }}>•</span>
            <span>{body}</span>
          </div>
        );
      }
      i += 1;
      continue;
    }

    // Bracketed Panel / Category Subheader e.g. [Haematology & Blood Counts]
    if (/^\[[^\]]+\]$/.test(trimmed)) {
      elements.push(
        <div
          key={i}
          style={{
            display: 'inline-block',
            marginTop: '10px',
            marginBottom: '6px',
            padding: '3px 10px',
            borderRadius: '6px',
            backgroundColor: '#EFF6FF',
            color: '#0369A1',
            fontSize: '12px',
            fontWeight: 700,
            letterSpacing: '0.2px'
          }}
        >
          {trimmed.slice(1, -1)}
        </div>
      );
      i += 1;
      continue;
    }

    // Standard header/metadata or narrative explanation paragraph
    elements.push(
      <div key={i} style={{ color: '#1E293B', fontWeight: 500, marginBottom: '6px' }}>
        {trimmed}
      </div>
    );
    i += 1;
  }

  return (
    <div
      style={{
        backgroundColor: '#FFFFFF',
        border: compact ? 'none' : '1px solid var(--border)',
        borderRadius: 'var(--radius-sm)',
        padding: compact ? '8px' : '20px 24px',
        fontSize: '13.5px',
        lineHeight: 1.55,
        color: 'var(--primary-text)',
        fontFamily: 'system-ui, -apple-system, sans-serif'
      }}
    >
      {elements}
    </div>
  );
};
