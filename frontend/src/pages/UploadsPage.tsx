import React, { useEffect, useState, useRef } from 'react';
import { UploadedFile } from '../types';
import { api } from '../services/api';
import {
  UploadCloud, FileText, CheckCircle2, AlertTriangle,
  Eye, RefreshCw, Zap, ClipboardPaste
} from 'lucide-react';

const SAMPLE_DIGITALIZED_REPORT = `Patient Name : Mr. Ramesh Naidu
Age/Gender : 47Y / Male
Patient Id : 8845120
Consultant : Dr. Dakshina Murthy D
Report Date : 25-Nov-2026
DEPARTMENT OF HAEMATOLOGY & RADIOLOGY
Haemoglobin : 11.2 gm%
Platelet Count : 1.32 Lakhs/cumm
ESR (Erythrocyte Sedimentation Rate) : 44 mm 1st hour
CRP : 14.5 mg/L
X-RAY CHEST PA VIEW
Findings: Mild cardiomegaly with clear costophrenic angles. No active lung parenchymal lesion or bony injury noted.
Impression: Borderline cardiomegaly; clinical correlation advised.`;

export const UploadsPage: React.FC = () => {
  const [uploads, setUploads] = useState<UploadedFile[]>([]);
  const [selectedDepartment, setSelectedDepartment] = useState('Laboratory');
  const [autoSyncOnUpload, setAutoSyncOnUpload] = useState(true);
  const [ingestMode, setIngestMode] = useState<'file' | 'text'>('file');
  const [rawReportText, setRawReportText] = useState('');
  const [reportLabel, setReportLabel] = useState('Hospital_Digital_Report.txt');
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [syncingAll, setSyncingAll] = useState(false);
  const [selectedFilePreview, setSelectedFilePreview] = useState<UploadedFile | null>(null);
  const [normalizedDetails, setNormalizedDetails] = useState<any | null>(null);
  const [statusMessage, setStatusMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    loadUploads();
  }, []);

  const loadUploads = async () => {
    try {
      const data = await api.uploads.list();
      setUploads(data);
    } catch (err) {
      console.error('Failed to load uploads:', err);
    }
  };

  const handleFileUpload = async (file: File) => {
    setUploading(true);
    setStatusMessage(null);
    try {
      const result = await api.uploads.uploadFile(file, selectedDepartment, autoSyncOnUpload);
      setStatusMessage({
        type: 'success',
        text: `"${file.name}" normalized and synced (${result.record_count} record(s)${result.patient_id_matched ? ` • Matched Patient: ${result.patient_id_matched}` : ''}).`
      });
      await loadUploads();
      inspectFile(result);
    } catch (err: any) {
      setStatusMessage({
        type: 'error',
        text: err.message || 'Upload failed.'
      });
    } finally {
      setUploading(false);
    }
  };

  const handleIngestText = async () => {
    if (!rawReportText.trim()) return;
    setUploading(true);
    setStatusMessage(null);
    try {
      const res = await api.uploads.ingestText({
        text: rawReportText,
        department: selectedDepartment,
        filename: reportLabel.trim() || 'Digitalized_Report.txt'
      });
      setStatusMessage({
        type: 'success',
        text: `Automated Sync Complete! Extracted ${res.sync_summary.records_ingested} clinical record(s) across ${res.sync_summary.departments_affected.join(', ')} for Patient ${res.matched_patient_id}. Ready in AI Workflow Hub!`
      });
      setRawReportText('');
      await loadUploads();
      if (res.uploaded_file_id) {
        const latest = (await api.uploads.list()).find(u => u.id === res.uploaded_file_id);
        if (latest) inspectFile(latest);
      }
    } catch (err: any) {
      setStatusMessage({
        type: 'error',
        text: err.message || 'Failed to parse digitalized report text.'
      });
    } finally {
      setUploading(false);
    }
  };

  const inspectFile = async (file: UploadedFile) => {
    setSelectedFilePreview(file);
    try {
      const norm = await api.uploads.getNormalizedText(file.id);
      setNormalizedDetails(norm);
    } catch {
      setNormalizedDetails(null);
    }
  };

  const handleSyncFile = async (fileId: number) => {
    try {
      const res = await api.uploads.autoSyncFile(fileId);
      setStatusMessage({
        type: 'success',
        text: `Automated sync completed! Ingested ${res.records_ingested} record(s) across ${res.departments_affected?.join(', ') || 'General'}.`
      });
      await loadUploads();
      if (selectedFilePreview?.id === fileId) {
        inspectFile({ ...selectedFilePreview, validation_status: 'Synced & Reconciled' });
      }
    } catch (err: any) {
      alert('Sync error: ' + err.message);
    }
  };

  const handleSyncAll = async () => {
    setSyncingAll(true);
    try {
      const res = await api.uploads.autoSyncAll();
      setStatusMessage({
        type: 'success',
        text: `Full Automated Database Sync Complete! Ingested ${res.total_records_ingested} records and reconciled ${res.patients_reconciled?.length} patient records.`
      });
      await loadUploads();
    } catch (err: any) {
      alert('Full sync failed: ' + err.message);
    } finally {
      setSyncingAll(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  };

  const departments = [
    'Registration',
    'Laboratory',
    'Pharmacy',
    'Radiology',
    'Nursing',
    'Inpatient',
    'Appointments',
    'Billing',
    'General'
  ];

  const getFormatBadge = (ext: string) => {
    const e = ext.toLowerCase();
    if (['csv', 'xlsx', 'xls', 'json'].includes(e)) {
      return <span className="badge badge-info">{ext.toUpperCase()}</span>;
    } else if (e === 'zip') {
      return <span className="badge badge-info">ZIP BUNDLE</span>;
    } else if (['jpg', 'jpeg', 'png', 'tiff', 'webp'].includes(e)) {
      return <span className="badge badge-warning">IMAGE (OCR)</span>;
    } else if (['pdf', 'txt'].includes(e)) {
      return <span className="badge badge-success">{e === 'pdf' ? 'PDF NORMALIZED' : 'TEXT / OCR'}</span>;
    }
    return <span className="badge badge-neutral">{ext.toUpperCase()}</span>;
  };

  return (
    <div style={{ padding: '24px', maxWidth: '1300px', margin: '0 auto' }}>
      {/* Title & Automated Database Sync Hub Header */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: '20px'
      }}>
        <div>
          <h2 style={{ fontSize: '20px', fontWeight: 700, color: 'var(--primary-navy)' }}>
            Hospital Database Ingestion &amp; Automated Synchronization
          </h2>
          <p style={{ fontSize: '13px', color: 'var(--secondary-text)', marginTop: '2px' }}>
            Upload hospital reports (PDF, ZIP, CSV, Excel, JSON, Images) or paste digitalized text to auto-update patient records and clinical alerts.
          </p>
        </div>

        <button
          onClick={handleSyncAll}
          disabled={syncingAll}
          className="btn-primary"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            backgroundColor: '#059669',
            borderColor: '#047857'
          }}
        >
          <Zap size={16} />
          <span>{syncingAll ? 'Reconciling System...' : 'Full Automated Database Sync'}</span>
        </button>
      </div>

      {statusMessage && (
        <div style={{
          padding: '12px 16px',
          borderRadius: 'var(--radius-sm)',
          marginBottom: '16px',
          backgroundColor: statusMessage.type === 'success' ? '#ECFDF5' : '#FEF2F2',
          color: statusMessage.type === 'success' ? '#065F46' : '#991B1B',
          border: `1px solid ${statusMessage.type === 'success' ? '#A7F3D0' : '#FECACA'}`,
          fontSize: '13px',
          display: 'flex',
          alignItems: 'center',
          gap: '8px'
        }}>
          {statusMessage.type === 'success' ? <CheckCircle2 size={16} /> : <AlertTriangle size={16} />}
          <span>{statusMessage.text}</span>
        </div>
      )}

      {/* Upload & Digitalized Text Automation Card */}
      <div className="card" style={{ marginBottom: '20px', backgroundColor: '#FBFCFE' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px', flexWrap: 'wrap', gap: '12px' }}>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              type="button"
              onClick={() => setIngestMode('file')}
              className={ingestMode === 'file' ? 'btn-primary' : 'btn-secondary'}
              style={{ padding: '7px 14px', fontSize: '12.5px' }}
            >
              <UploadCloud size={15} />
              <span>Upload Report File</span>
            </button>
            <button
              type="button"
              onClick={() => setIngestMode('text')}
              className={ingestMode === 'text' ? 'btn-primary' : 'btn-secondary'}
              style={{ padding: '7px 14px', fontSize: '12.5px' }}
            >
              <ClipboardPaste size={15} />
              <span>Paste Digitalized Report Text</span>
            </button>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            {ingestMode === 'file' && (
              <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12.5px', fontWeight: 600, color: 'var(--primary-navy)', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={autoSyncOnUpload}
                  onChange={(e) => setAutoSyncOnUpload(e.target.checked)}
                  style={{ width: '16px', height: '16px', cursor: 'pointer' }}
                />
                <span>Auto-Sync to Database</span>
              </label>
            )}

            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <label style={{ fontSize: '12px', fontWeight: 600, color: 'var(--primary-text)' }}>
                Department:
              </label>
              <select
                value={selectedDepartment}
                onChange={(e) => setSelectedDepartment(e.target.value)}
                style={{
                  padding: '5px 10px',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--border)',
                  fontSize: '12.5px',
                  fontWeight: 600
                }}
              >
                {departments.map(d => (
                  <option key={d} value={d}>{d}</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {ingestMode === 'file' ? (
          <div
            onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            style={{
              border: `2px dashed ${isDragging ? 'var(--primary-teal)' : 'var(--border)'}`,
              borderRadius: 'var(--radius-md)',
              padding: '30px 20px',
              textAlign: 'center',
              backgroundColor: isDragging ? '#F0F9F8' : '#FFFFFF',
              cursor: 'pointer',
              transition: 'all 0.2s ease-in-out'
            }}
          >
            <input
              type="file"
              ref={fileInputRef}
              onChange={(e) => {
                if (e.target.files && e.target.files.length > 0) {
                  handleFileUpload(e.target.files[0]);
                }
              }}
              style={{ display: 'none' }}
            />

            <div style={{
              width: '42px',
              height: '42px',
              borderRadius: '50%',
              backgroundColor: '#EBF5F4',
              color: 'var(--primary-teal)',
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '8px'
            }}>
              <UploadCloud size={22} />
            </div>

            <div style={{ fontSize: '14px', fontWeight: 700, color: 'var(--primary-navy)' }}>
              {uploading ? 'Normalizing Text & Updating Database...' : 'Click to Upload or Drag Hospital File Here'}
            </div>

            <div style={{ fontSize: '11.5px', color: 'var(--secondary-text)', marginTop: '4px' }}>
              Supported: <strong>PDF, ZIP Archives, CSV, JSON, Excel (.xlsx), Images (JPG/PNG OCR), TXT</strong>
            </div>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
              <input
                type="text"
                value={reportLabel}
                onChange={(e) => setReportLabel(e.target.value)}
                placeholder="Source label (e.g. Lab_Order_2026.txt)"
                style={{
                  padding: '6px 10px',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--border)',
                  fontSize: '12.5px',
                  width: '280px'
                }}
              />
              <button
                type="button"
                onClick={() => setRawReportText(SAMPLE_DIGITALIZED_REPORT)}
                className="btn-secondary"
                style={{ fontSize: '12px', padding: '6px 12px' }}
              >
                <FileText size={13} />
                <span>Load Sample Hospital Report</span>
              </button>
            </div>

            <textarea
              rows={7}
              value={rawReportText}
              onChange={(e) => setRawReportText(e.target.value)}
              placeholder="Paste text copied from any LIMS lab PDF, Radiology X-Ray/MRI viewer, or EMR intake form (Patient Name, UHID/Patient Id, Labs, Findings, Impression)..."
              style={{
                width: '100%',
                padding: '10px 12px',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--border)',
                fontFamily: 'monospace',
                fontSize: '12.5px',
                lineHeight: 1.5
              }}
            />

            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <button
                type="button"
                onClick={handleIngestText}
                disabled={uploading || !rawReportText.trim()}
                className="btn-primary"
                style={{ backgroundColor: '#059669', borderColor: '#047857' }}
              >
                <Zap size={15} />
                <span>{uploading ? 'Extracting & Reconciling...' : 'Normalize & Auto-Sync to Database'}</span>
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Main Grid: Upload History & File Inspector */}
      <div style={{ display: 'grid', gridTemplateColumns: selectedFilePreview ? '1.2fr 1fr' : '1fr', gap: '20px' }}>
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
            <h3 style={{ fontSize: '14px', fontWeight: 700, color: 'var(--primary-navy)' }}>
              Ingested Files ({uploads.length})
            </h3>
            <button onClick={loadUploads} className="btn-secondary" style={{ padding: '4px 10px', fontSize: '12px' }}>
              <RefreshCw size={14} />
              <span>Refresh</span>
            </button>
          </div>

          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Original File</th>
                  <th>Department</th>
                  <th>Format</th>
                  <th>Status</th>
                  <th>Matched Patient</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {uploads.length === 0 ? (
                  <tr>
                    <td colSpan={6} style={{ textAlign: 'center', padding: '24px', color: 'var(--secondary-text)' }}>
                      No files uploaded yet. Upload a hospital report or paste digitalized text above.
                    </td>
                  </tr>
                ) : (
                  uploads.map((file) => (
                    <tr
                      key={file.id}
                      style={{
                        backgroundColor: selectedFilePreview?.id === file.id ? '#F0FDF4' : 'transparent',
                        cursor: 'pointer'
                      }}
                      onClick={() => inspectFile(file)}
                    >
                      <td style={{ fontWeight: 600 }}>{file.original_filename}</td>
                      <td>{file.source_department || 'General'}</td>
                      <td>{getFormatBadge(file.file_type)}</td>
                      <td>
                        <span className={`badge ${
                          file.validation_status.includes('Synced') ? 'badge-success' :
                          file.extraction_status === 'Extracted' ? 'badge-info' :
                          'badge-warning'
                        }`}>
                          {file.validation_status || file.extraction_status}
                        </span>
                      </td>
                      <td>
                        {file.patient_id_matched ? (
                          <span className="badge badge-info">{file.patient_id_matched}</span>
                        ) : (
                          <span style={{ fontSize: '11.5px', color: 'var(--secondary-text)' }}>Multi-Record</span>
                        )}
                      </td>
                      <td>
                        <div style={{ display: 'flex', gap: '6px' }}>
                          <button
                            onClick={(e) => { e.stopPropagation(); inspectFile(file); }}
                            className="btn-secondary"
                            style={{ padding: '3px 8px', fontSize: '11px' }}
                            title="Inspect Normalized Text"
                          >
                            <Eye size={12} />
                            <span>View</span>
                          </button>
                          <button
                            onClick={(e) => { e.stopPropagation(); handleSyncFile(file.id); }}
                            className="btn-primary"
                            style={{ padding: '3px 8px', fontSize: '11px', backgroundColor: '#059669', borderColor: '#047857' }}
                            title="Automated Database Update"
                          >
                            <Zap size={12} />
                            <span>Sync</span>
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Selected File Details Inspector */}
        {selectedFilePreview && (
          <div className="card">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px', borderBottom: '1px solid var(--border)', paddingBottom: '8px' }}>
              <div>
                <h4 style={{ fontSize: '14px', fontWeight: 700, color: 'var(--primary-navy)' }}>
                  {selectedFilePreview.original_filename}
                </h4>
                <div style={{ fontSize: '11.5px', color: 'var(--secondary-text)' }}>
                  Department: {selectedFilePreview.source_department} • Size: {(selectedFilePreview.file_size / 1024).toFixed(1)} KB
                </div>
              </div>
              <div style={{ display: 'flex', gap: '6px' }}>
                <button
                  onClick={() => handleSyncFile(selectedFilePreview.id)}
                  className="btn-primary"
                  style={{ padding: '4px 10px', fontSize: '11.5px', backgroundColor: '#059669' }}
                >
                  <Zap size={12} />
                  <span>Sync to DB</span>
                </button>
                <button
                  onClick={() => { setSelectedFilePreview(null); setNormalizedDetails(null); }}
                  className="btn-secondary"
                  style={{ padding: '4px 8px', fontSize: '11px' }}
                >
                  Close
                </button>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginBottom: '12px' }}>
              <div style={{ padding: '8px', backgroundColor: '#F8FAFC', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)' }}>
                <div style={{ fontSize: '11px', color: 'var(--secondary-text)' }}>Extracted Records</div>
                <div style={{ fontSize: '15px', fontWeight: 700, color: 'var(--primary-navy)' }}>
                  {selectedFilePreview.record_count}
                </div>
              </div>
              <div style={{ padding: '8px', backgroundColor: '#F8FAFC', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)' }}>
                <div style={{ fontSize: '11px', color: 'var(--secondary-text)' }}>Matched Patient</div>
                <div style={{ fontSize: '15px', fontWeight: 700, color: 'var(--primary-teal)' }}>
                  {selectedFilePreview.patient_id_matched || 'Multi-Record'}
                </div>
              </div>
            </div>

            <div>
              <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--primary-navy)', marginBottom: '4px' }}>
                Normalized Text View (Converted from PDF / Record):
              </div>
              <div style={{
                maxHeight: '320px',
                overflowY: 'auto',
                padding: '10px',
                backgroundColor: '#F8FAFC',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--border)',
                fontFamily: 'monospace',
                fontSize: '11.5px',
                lineHeight: 1.5,
                whiteSpace: 'pre-wrap',
                color: 'var(--primary-text)'
              }}>
                {normalizedDetails?.normalized_text || selectedFilePreview.extracted_text || 'No normalized text captured.'}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
