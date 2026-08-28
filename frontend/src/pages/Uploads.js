import React, { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDropzone } from 'react-dropzone';
import Layout from '../components/Layout';
import { uploadsAPI } from '../api/client';
import { StatusBadge } from '../components/SeverityBadge';
import toast from 'react-hot-toast';
import { Upload, FileText, AlertTriangle, ChevronDown, ChevronUp, Info } from 'lucide-react';

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

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true); setProgress(10); setResult(null); setShowFailed(false);

    const form = new FormData();
    form.append('file', file);
    form.append('source_type', sourceType);
    form.append('run_validation', 'true');

    try {
      setProgress(40);
      const res = await uploadsAPI.upload(form);
      setProgress(100);
      setResult(res.data);
      toast.success(
        `Imported ${res.data.imported_rows?.toLocaleString()} records` +
        (res.data.failed_rows > 0 ? ` · ${res.data.failed_rows} failed` : '')
      );
      onUploadComplete?.();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const failedRows = result?.failed_row_details || [];

  return (
    <div className="card" style={{ marginBottom: 24 }}>
      <div className="card-title">Upload Loan Tape</div>

      {/* Source type selector — includes DOCUMENT_MANIFEST */}
      <div style={{ marginBottom: 16 }}>
        <label className="form-label">Source Type</label>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2,1fr)', gap: 8 }}>
          {SOURCE_TYPES.map(st => (
            <label
              key={st.value}
              style={{
                display: 'flex', alignItems: 'flex-start', gap: 10, padding: '10px 12px',
                borderRadius: 8, cursor: 'pointer',
                border: `1px solid ${sourceType === st.value ? 'var(--accent)' : 'var(--border)'}`,
                background: sourceType === st.value ? 'rgba(59,130,246,.06)' : 'var(--bg-primary)',
                transition: 'all .15s',
              }}
            >
              <input
                type="radio"
                style={{ marginTop: 2 }}
                checked={sourceType === st.value}
                onChange={() => setSourceType(st.value)}
              />
              <div>
                <div style={{ fontWeight: 500, fontSize: 13 }}>{st.label}</div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 1 }}>{st.desc}</div>
              </div>
            </label>
          ))}
        </div>
      </div>

      {/* Drop zone */}
      <div {...getRootProps()} className={`dropzone ${isDragActive ? 'active' : ''}`}>
        <input {...getInputProps()} />
        <div className="dropzone-icon"><Upload size={38} /></div>
        <div className="dropzone-title">
          {file ? file.name : isDragActive ? 'Drop the CSV here' : 'Drag & drop a CSV file'}
        </div>
        <div className="dropzone-sub">
          {file
            ? `${(file.size / 1024).toFixed(1)} KB · ready to upload`
            : 'or click to browse · CSV only · Max 50 MB'}
        </div>
      </div>

      {/* Progress bar */}
      {uploading && (
        <div style={{ marginTop: 12 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 4 }}>
            <span>Parsing, normalizing, validating…</span><span>{progress}%</span>
          </div>
          <div className="progress-bar"><div className="progress-fill" style={{ width: `${progress}%` }} /></div>
        </div>
      )}

      {/* Upload button */}
      {file && !uploading && !result && (
        <button className="btn btn-primary" style={{ marginTop: 16 }} onClick={handleUpload}>
          <Upload size={14} /> Import &amp; Validate
        </button>
      )}

      {/* Result summary */}
      {result && (
        <div style={{ marginTop: 16 }}>
          <div className="alert alert-success">
            <div style={{ fontWeight: 600, marginBottom: 10 }}>Import Complete</div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 12, textAlign: 'center', marginBottom: 10 }}>
              {[
                { label: 'Total Rows',  val: result.total_rows,    color: 'var(--text-primary)' },
                { label: 'Imported',    val: result.imported_rows, color: 'var(--success)' },
                { label: 'Failed',      val: result.failed_rows,   color: result.failed_rows > 0 ? 'var(--danger)' : 'var(--success)' },
                { label: 'Exceptions',  val: result.exceptions_created, color: result.exceptions_created > 0 ? 'var(--warning)' : 'var(--success)' },
              ].map(({ label, val, color }) => (
                <div key={label}>
                  <div style={{ fontSize: 22, fontWeight: 700, color }}>{(val || 0).toLocaleString()}</div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{label}</div>
                </div>
              ))}
            </div>
            {result.exceptions_created > 0 && (
              <div style={{ fontSize: 12, color: 'var(--warning)', display: 'flex', alignItems: 'center', gap: 6 }}>
                <AlertTriangle size={12} />
                {result.exceptions_created} validation exceptions created — review in the Exception Queue
              </div>
            )}
          </div>

          {/* Failed row details — expanded on demand */}
          {failedRows.length > 0 && (
            <div style={{ marginTop: 10 }}>
              <button
                className="btn btn-secondary btn-sm"
                onClick={() => setShowFailed(v => !v)}
                style={{ width: '100%', justifyContent: 'space-between' }}
              >
                <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <AlertTriangle size={13} color="var(--danger)" />
                  {failedRows.length} failed row{failedRows.length !== 1 ? 's' : ''} — click to inspect
                </span>
                {showFailed ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
              </button>

              {showFailed && (
                <div style={{ marginTop: 8, border: '1px solid var(--border)', borderRadius: 8, overflow: 'hidden' }}>
                  <div style={{ background: 'rgba(239,68,68,.06)', padding: '8px 14px', fontSize: 12, color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: 6 }}>
                    <Info size={12} /> Showing up to {failedRows.length} failed rows. Fix the data and re-upload to import these records.
                  </div>
                  <div className="table-wrap">
                    <table>
                      <thead>
                        <tr>
                          <th>Row #</th>
                          <th>Error</th>
                          <th>Raw Data (preview)</th>
                        </tr>
                      </thead>
                      <tbody>
                        {failedRows.map((fr, i) => (
                          <tr key={i}>
                            <td style={{ fontSize: 12, color: 'var(--danger)', fontWeight: 600 }}>{fr.row || i + 1}</td>
                            <td style={{ fontSize: 12, color: 'var(--warning)' }}>{fr.error || 'Parse error'}</td>
                            <td style={{ fontSize: 10, fontFamily: 'monospace', color: 'var(--text-muted)', maxWidth: 260, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                              {fr.data ? Object.entries(fr.data).slice(0, 4).map(([k, v]) => `${k}: ${v}`).join(' | ') : '—'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
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
                    <th>File</th><th>Source</th><th>Total</th><th>Imported</th><th>Failed</th><th>Status</th><th>Uploaded</th>
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
                    </tr>
                  ))}
                  {!uploads.length && (
                    <tr>
                      <td colSpan={7}>
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
