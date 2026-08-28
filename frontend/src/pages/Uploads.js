import React, { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDropzone } from 'react-dropzone';
import toast from 'react-hot-toast';
import Layout from '../components/Layout';
import { uploadsAPI } from '../api/client';
import { StatusBadge } from '../components/SeverityBadge';
import { DEMO_CSV_CONTENT } from '../data/demoTape';
import { Upload, FileText, AlertTriangle, ChevronDown, ChevronUp, Info, Trash2, Sparkles, CheckCircle, ArrowRight } from 'lucide-react';

const SOURCE_TYPES = [
  { value: 'LOAN_TAPE',         label: 'Loan Tape',          desc: 'Primary loan-level dataset' },
  { value: 'SERVICER_UPDATE',   label: 'Servicer Update',    desc: 'Partial update from servicer portal' },
  { value: 'DOCUMENT_MANIFEST', label: 'Document Manifest',  desc: 'Document availability by loan ID' },
  { value: 'COLLATERAL',        label: 'Collateral File',    desc: 'Collateral / property information' },
];

// ─── Upload Zone ──────────────────────────────────────────────────────────────
function UploadZone({ onUploadComplete }) {
  const [uploading, setUploading]   = useState(false);
  const [progress, setProgress]     = useState(0);
  const [result, setResult]         = useState(null);
  const [sourceType, setSourceType] = useState('LOAN_TAPE');
  const [file, setFile]             = useState(null);
  const [showFailed, setShowFailed] = useState(false);

  const onDrop = useCallback((accepted) => {
    if (accepted.length > 0) { setFile(accepted[0]); setResult(null); }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'text/csv': ['.csv'] },
    multiple: false,
  });

  const uploadFileObject = async (fileObj) => {
    setUploading(true); setProgress(10); setResult(null); setShowFailed(false);

    const form = new FormData();
    form.append('file', fileObj);
    form.append('source_type', sourceType);
    form.append('run_validation', 'true');

    const timer = setInterval(() => setProgress(p => p < 80 ? p + 15 : p), 200);

    try {
      const res = await uploadsAPI.upload(form);
      clearInterval(timer);
      setProgress(100);
      setResult(res.data);
      toast.success(`Imported ${res.data.imported_rows.toLocaleString()} loans!`);
      onUploadComplete?.();
    } catch (err) {
      clearInterval(timer);
      setUploading(false);
      toast.error(err.response?.data?.detail || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    await uploadFileObject(file);
  };

  const handleLoadDemoTape = async () => {
    const demoBlob = new Blob([DEMO_CSV_CONTENT], { type: 'text/csv' });
    const demoFile = new File([demoBlob], 'hackathon_demo_tape.csv', { type: 'text/csv' });
    setFile(demoFile);
    await uploadFileObject(demoFile);
  };

  return (
    <div className="card mb-4" style={{ marginBottom: 24 }}>
      <div className="card-title" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span>Upload Loan Tape</span>
        <button
          type="button"
          className="btn btn-secondary btn-sm"
          style={{
            background: 'linear-gradient(135deg, rgba(59,130,246,0.1), rgba(168,85,247,0.1))',
            borderColor: 'var(--accent)',
            color: 'var(--accent)',
            fontWeight: 700,
            fontSize: 12,
          }}
          disabled={uploading}
          onClick={handleLoadDemoTape}
          title="Pre-loads a realistic 20-record loan dataset with clean and exception loans for demo"
        >
          <Sparkles size={13} />
          Load Demo Tape (20 Records)
        </button>
      </div>

      {/* Source type selector */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 10, marginBottom: 16 }}>
        {SOURCE_TYPES.map(st => (
          <div
            key={st.value}
            onClick={() => setSourceType(st.value)}
            style={{
              padding: '10px 14px',
              border: `1.5px solid ${sourceType === st.value ? 'var(--accent)' : 'var(--border)'}`,
              borderRadius: 8,
              cursor: 'pointer',
              background: sourceType === st.value ? 'rgba(59,130,246,0.08)' : 'transparent',
              transition: 'all .15s',
            }}
          >
            <div style={{ fontWeight: 600, fontSize: 13, color: sourceType === st.value ? 'var(--accent)' : 'inherit' }}>
              {st.label}
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>{st.desc}</div>
          </div>
        ))}
      </div>

      {/* Drop zone */}
      <div
        {...getRootProps()}
        className={`drop-zone ${isDragActive ? 'active' : ''}`}
        style={{
          border: `2px dashed ${isDragActive ? 'var(--accent)' : 'var(--border)'}`,
          borderRadius: 10,
          padding: '36px 20px',
          textAlign: 'center',
          cursor: 'pointer',
          background: isDragActive ? 'rgba(59,130,246,0.04)' : 'transparent',
          marginBottom: 16,
        }}
      >
        <input {...getInputProps()} />
        <Upload size={32} color="var(--accent)" style={{ margin: '0 auto 10px' }} />
        {file ? (
          <div>
            <span style={{ fontWeight: 600, color: 'var(--accent)' }}>{file.name}</span>
            <span style={{ fontSize: 12, color: 'var(--text-muted)', marginLeft: 8 }}>
              ({(file.size / 1024).toFixed(1)} KB)
            </span>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>Click or drop to replace</div>
          </div>
        ) : (
          <div>
            <p style={{ fontWeight: 500 }}>Drop CSV file here, or <span style={{ color: 'var(--accent)' }}>browse</span></p>
            <p style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>Supports .csv format · Up to 50MB</p>
          </div>
        )}
      </div>

      {/* Progress */}
      {uploading && (
        <div className="mb-4">
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: `${progress}%` }} />
          </div>
          <p style={{ fontSize: 11, color: 'var(--text-muted)', textAlign: 'center', marginTop: 4 }}>
            Parsing & validating loan records… {progress}%
          </p>
        </div>
      )}

      {/* Action button */}
      {!result && (
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
          {file && (
            <button className="btn btn-ghost btn-sm" onClick={() => { setFile(null); setResult(null); }}>
              Clear
            </button>
          )}
          <button
            className="btn btn-primary"
            disabled={!file || uploading}
            onClick={handleUpload}
          >
            <Upload size={14} />
            {uploading ? 'Processing…' : 'Ingest & Validate'}
          </button>
        </div>
      )}

      {/* Upload result summary */}
      {result && (
        <div style={{ marginTop: 20, padding: 16, background: 'rgba(59,130,246,0.06)', borderRadius: 8, border: '1px solid rgba(59,130,246,0.2)' }}>
          <div style={{ fontWeight: 600, marginBottom: 10, display: 'flex', alignItems: 'center', gap: 6 }}>
            <Info size={16} color="var(--accent)" />
            Import Summary
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, marginBottom: 12 }}>
            <div style={{ background: 'var(--card-bg)', padding: '10px 14px', borderRadius: 6, border: '1px solid var(--border)' }}>
              <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Total Rows</div>
              <div style={{ fontSize: 18, fontWeight: 700 }}>{result.total_rows?.toLocaleString()}</div>
            </div>
            <div style={{ background: 'var(--card-bg)', padding: '10px 14px', borderRadius: 6, border: '1px solid var(--border)' }}>
              <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Imported</div>
              <div style={{ fontSize: 18, fontWeight: 700, color: 'var(--success)' }}>{result.imported_rows?.toLocaleString()}</div>
            </div>
            <div style={{ background: 'var(--card-bg)', padding: '10px 14px', borderRadius: 6, border: '1px solid var(--border)' }}>
              <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Failed Rows</div>
              <div style={{ fontSize: 18, fontWeight: 700, color: result.failed_rows > 0 ? 'var(--danger)' : 'inherit' }}>
                {result.failed_rows?.toLocaleString()}
              </div>
            </div>
            <div style={{ background: 'var(--card-bg)', padding: '10px 14px', borderRadius: 6, border: '1px solid var(--border)' }}>
              <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Exceptions Flagged</div>
              <div style={{ fontSize: 18, fontWeight: 700, color: 'var(--warning)' }}>
                {result.exceptions_created?.toLocaleString()}
              </div>
            </div>
          </div>

          {result.failed_rows > 0 && result.failed_row_details?.length > 0 && (
            <div>
              <button
                className="btn btn-ghost btn-sm"
                style={{ fontSize: 12, padding: 0, color: 'var(--danger)' }}
                onClick={() => setShowFailed(v => !v)}
              >
                {showFailed ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                {showFailed ? 'Hide' : 'View'} {result.failed_row_details.length} row failure details
              </button>

              {showFailed && (
                <div style={{ marginTop: 10, maxHeight: 180, overflowY: 'auto', fontSize: 11, background: 'var(--bg)', padding: 10, borderRadius: 6 }}>
                  {result.failed_row_details.map((f, i) => (
                    <div key={i} style={{ marginBottom: 6, color: 'var(--danger)' }}>
                      Row {f.row}: {f.reason} {f.field ? `(${f.field})` : ''}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          <button className="btn btn-secondary btn-sm" style={{ marginTop: 10 }} onClick={() => { setResult(null); setFile(null); }}>
            Upload Another File
          </button>
        </div>
      )}
    </div>
  );
}

// ─── Import History ───────────────────────────────────────────────────────────
export default function Uploads() {
  const navigate = useNavigate();
  const [uploads, setUploads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage]       = useState(1);
  const [total, setTotal]     = useState(0);
  const [deletingId, setDeletingId] = useState(null);
  const PAGE_SIZE = 15;

  const load = async () => {
    setLoading(true);
    try {
      const res = await uploadsAPI.list({ page, page_size: PAGE_SIZE });
      setUploads(res.data.items || []);
      setTotal(res.data.total  || 0);
    } catch {}
    setLoading(false);
  };

  const handleDelete = async (upload) => {
    const filename = upload.original_filename || upload.filename;
    if (!window.confirm(`Are you sure you want to delete "${filename}"?\n\nThis will permanently delete all loan records, validation results, and exceptions associated with this file.`)) {
      return;
    }
    setDeletingId(upload.id);
    try {
      await uploadsAPI.delete(upload.id);
      toast.success(`Deleted "${filename}" and all associated data.`);
      load();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to delete file');
    } finally {
      setDeletingId(null);
    }
  };

  React.useEffect(() => { load(); }, [page]);

  return (
    <Layout title="Uploads — Module A">
      <div className="page-header">
        <h2>Data Ingestion</h2>
        <p>Upload CSV loan tapes, servicer updates, and document manifests. System parses, normalizes, and validates automatically.</p>
      </div>

      <UploadZone onUploadComplete={load} />

      <div className="card">
        <div className="card-title">Import History</div>
        {loading ? (
          <div style={{ textAlign: 'center', padding: 40 }}><span className="spinner" /></div>
        ) : (
          <>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>File</th><th>Source</th><th>Total</th><th>Imported</th><th>Failed</th><th>Status</th><th>Uploaded</th><th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {uploads.map(u => (
                    <tr key={u.id}>
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          <FileText size={14} color="var(--text-muted)" />
                          <span style={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', display: 'block', fontSize: 12, fontWeight: 600 }}>
                            {u.original_filename}
                          </span>
                        </div>
                      </td>
                      <td><span className="badge badge-blue" style={{ fontSize: 10 }}>{u.source_type?.replace('_', ' ')}</span></td>
                      <td style={{ fontSize: 12 }}>{u.total_rows?.toLocaleString()}</td>
                      <td style={{ fontSize: 12, color: 'var(--success)' }}>{u.imported_rows?.toLocaleString()}</td>
                      <td style={{ fontSize: 12, color: u.failed_rows > 0 ? 'var(--danger)' : 'var(--text-muted)' }}>
                        {u.failed_rows?.toLocaleString()}
                      </td>
                      <td><StatusBadge status={u.status} /></td>
                      <td style={{ fontSize: 11, color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
                        {u.created_at ? new Date(u.created_at).toLocaleString() : '—'}
                      </td>
                      <td>
                        <button
                          className="btn btn-ghost btn-sm"
                          style={{ color: 'var(--danger)', fontSize: 11, padding: '3px 8px', display: 'flex', alignItems: 'center', gap: 4 }}
                          disabled={deletingId === u.id}
                          onClick={() => handleDelete(u)}
                          title="Delete file and all associated records & exceptions"
                        >
                          <Trash2 size={12} />
                          {deletingId === u.id ? 'Deleting…' : 'Delete'}
                        </button>
                      </td>
                    </tr>
                  ))}
                  {!uploads.length && (
                    <tr>
                      <td colSpan={8}>
                        <div className="empty-state">
                          <Upload size={32} />
                          <h3>No uploads yet</h3>
                          <p>Upload a CSV file above to get started</p>
                        </div>
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
            {total > PAGE_SIZE && (
              <div className="pagination">
                <span>{total.toLocaleString()} uploads</span>
                <button className="page-btn" disabled={page === 1} onClick={() => setPage(p => p - 1)}>Prev</button>
                <span>{page} / {Math.ceil(total / PAGE_SIZE)}</span>
                <button className="page-btn" disabled={page >= Math.ceil(total / PAGE_SIZE)} onClick={() => setPage(p => p + 1)}>Next</button>
              </div>
            )}
          </>
        )}
      </div>
    </Layout>
  );
}
