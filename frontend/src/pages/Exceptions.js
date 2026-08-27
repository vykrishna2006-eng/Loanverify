import React, { useState, useEffect, useCallback } from 'react';
import { useLocation } from 'react-router-dom';
import Layout from '../components/Layout';
import { exceptionsAPI, uploadsAPI } from '../api/client';
import { SeverityBadge, StatusBadge } from '../components/SeverityBadge';
import toast from 'react-hot-toast';
import {
  AlertTriangle, Bot, MessageSquare, CheckCircle,
  XCircle, Search, RefreshCw, ChevronRight, Clock,
} from 'lucide-react';

// ─── Exception Detail Modal ───────────────────────────────────────────────────
function ExceptionDetail({ id, onClose }) {
  const [exc, setExc]           = useState(null);
  const [loading, setLoading]   = useState(true);
  const [aiLoading, setAiLoad]  = useState(false);
  const [comment, setComment]   = useState('');
  const [decision, setDecision] = useState('');
  const [corrected, setCorrected] = useState('');
  const [note, setNote]         = useState('');
  const [aiFollowed, setAiFollowed] = useState(null);
  const [tab, setTab]           = useState('detail'); // detail | history

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const r = await exceptionsAPI.get(id);
      setExc(r.data);
    } catch {}
    setLoading(false);
  }, [id]);

  useEffect(() => { load(); }, [load]);

  const generateAI = async () => {
    setAiLoad(true);
    try {
      const r = await exceptionsAPI.generateAIReview(id);
      setExc(prev => ({ ...prev, ai_recommendation: r.data }));
      toast.success('AI recommendation generated');
    } catch (e) {
      toast.error(e.response?.data?.detail || 'AI review failed');
    }
    setAiLoad(false);
  };

  const addComment = async () => {
    if (!comment.trim()) return;
    try {
      await exceptionsAPI.addComment(id, comment);
      toast.success('Comment added');
      setComment('');
      load();
    } catch { toast.error('Failed to add comment'); }
  };

  const submitDecision = async () => {
    if (!decision) { toast.error('Select a decision'); return; }
    if (decision === 'EDITED' && !corrected.trim()) { toast.error('Enter a corrected value'); return; }
    try {
      const res = await exceptionsAPI.submitDecision(id, {
        decision,
        corrected_value: corrected || null,
        reviewer_note:   note     || null,
        ai_decision_followed: aiFollowed,
      });
      toast.success(res.data.message || `Decision: ${decision}`);
      if (res.data.field_updated) {
        toast.success(`Field "${res.data.field_updated}" updated to ${res.data.corrected_value}`);
      }
      onClose?.();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to submit decision');
    }
  };

  if (loading) {
    return (
      <div className="modal-overlay">
        <div className="modal" style={{ padding: 40, textAlign: 'center' }}><span className="spinner" /></div>
      </div>
    );
  }
  if (!exc) return null;

  const e   = exc.exception;
  const ai  = exc.ai_recommendation;
  const history = exc.review_history || [];

  return (
    <div className="modal-overlay" onClick={ev => ev.target === ev.currentTarget && onClose?.()}>
      <div className="modal" style={{ maxWidth: 740 }}>
        {/* Header */}
        <div className="modal-header">
          <div>
            <h2>Exception Detail</h2>
            <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>
              Loan <span className="font-mono">{e?.loan_id}</span>
              &nbsp;·&nbsp;{e?.exception_type?.replace(/_/g, ' ')}
              &nbsp;·&nbsp;<span className="badge badge-blue">{e?.rule_id}</span>
            </div>
          </div>
          <button className="btn btn-ghost btn-icon" onClick={onClose}><XCircle size={18} /></button>
        </div>

        {/* Tabs */}
        <div className="tabs" style={{ margin: '0 24px' }}>
          {['detail', 'history', 'comments'].map(t => (
            <div key={t} className={`tab ${tab === t ? 'active' : ''}`} onClick={() => setTab(t)}>
              {t === 'detail' ? 'Review' : t === 'history' ? `History (${history.length})` : `Comments (${exc.comments?.length || 0})`}
            </div>
          ))}
        </div>

        <div className="modal-body" style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>

          {/* ── Detail tab ────────────────────────────────── */}
          {tab === 'detail' && <>
            {/* Exception facts */}
            <div className="card" style={{ margin: 0, padding: 16 }}>
              <div style={{ display: 'flex', gap: 8, marginBottom: 10 }}>
                <SeverityBadge severity={e?.severity} />
                <StatusBadge status={e?.status} />
              </div>
              <div style={{ fontWeight: 600, marginBottom: 10 }}>{e?.message}</div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, fontSize: 12 }}>
                <div><span style={{ color: 'var(--text-muted)' }}>Field: </span>{e?.field_name || '—'}</div>
                <div><span style={{ color: 'var(--text-muted)' }}>Type: </span>{e?.exception_type?.replace(/_/g,' ')}</div>
                <div><span style={{ color: 'var(--text-muted)' }}>Actual: </span>
                  <span style={{ color: 'var(--danger)', fontWeight: 500 }}>{e?.actual_value || '—'}</span></div>
                <div><span style={{ color: 'var(--text-muted)' }}>Expected: </span>
                  <span style={{ color: 'var(--success)', fontWeight: 500 }}>{e?.expected_value || '—'}</span></div>
              </div>
            </div>

            {/* Loan context */}
            {exc.loan && (
              <div style={{ fontSize: 12, background: 'var(--bg-hover)', borderRadius: 8, padding: '8px 12px' }}>
                <span style={{ color: 'var(--text-muted)' }}>Borrower: </span>{exc.loan.borrower_name || exc.loan.borrower_id || '—'}
                <span style={{ color: 'var(--text-muted)', marginLeft: 16 }}>Balance: </span>
                {exc.loan.current_balance != null ? `$${Number(exc.loan.current_balance).toLocaleString()}` : '—'}
                <span style={{ color: 'var(--text-muted)', marginLeft: 16 }}>Status: </span>
                {exc.loan.payment_status || '—'}
              </div>
            )}

            {/* AI Recommendation */}
            {ai ? (
              <div className="ai-box">
                <div className="ai-box-header">
                  <Bot size={14} /> AI Recommendation
                  <span style={{ marginLeft: 'auto', fontSize: 11, color: 'var(--text-muted)' }}>
                    Confidence: {ai.confidence_score != null ? `${parseFloat(ai.confidence_score).toFixed(1)}%` : '—'}
                    {ai.model_used && ` · ${ai.model_used}`}
                  </span>
                </div>
                <p style={{ fontSize: 13, lineHeight: 1.6, marginBottom: 10 }}>{ai.explanation}</p>
                {ai.suggested_value && (
                  <div style={{ fontSize: 12, marginBottom: 6 }}>
                    <span style={{ color: 'var(--text-muted)' }}>Suggested value: </span>
                    <strong style={{ color: 'var(--success)' }}>{ai.suggested_value}</strong>
                  </div>
                )}
                <div style={{ fontSize: 12, marginBottom: 6 }}>
                  <span style={{ color: 'var(--text-muted)' }}>Action: </span>
                  <span className="badge badge-blue">{ai.suggested_action?.replace(/_/g,' ')}</span>
                </div>
                {ai.generated_note && (
                  <div style={{ marginTop: 8, padding: '8px 12px', background: 'var(--bg-primary)', borderRadius: 6, fontSize: 12, color: 'var(--text-secondary)', fontStyle: 'italic' }}>
                    "{ai.generated_note}"
                  </div>
                )}
                {ai.prompt_text && (
                  <details style={{ marginTop: 8 }}>
                    <summary style={{ fontSize: 11, color: 'var(--text-muted)', cursor: 'pointer' }}>Show prompt sent to AI</summary>
                    <pre style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 6, whiteSpace: 'pre-wrap' }}>{ai.prompt_text}</pre>
                  </details>
                )}
                <div className="ai-safety-note">
                  ⚠️ AI RECOMMENDATION ONLY — no data changes until you submit a decision.
                </div>
              </div>
            ) : (
              <button className="btn btn-secondary" onClick={generateAI} disabled={aiLoading}>
                <Bot size={14} />
                {aiLoading ? 'Generating…' : 'Generate AI Recommendation'}
              </button>
            )}

            {/* Human Decision form */}
            {e?.status !== 'RESOLVED' && (
              <div className="card" style={{ margin: 0, padding: 16 }}>
                <div style={{ fontWeight: 600, marginBottom: 14, display: 'flex', alignItems: 'center', gap: 8 }}>
                  Human Decision
                  <span style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 400 }}>
                    (AI cannot submit this form)
                  </span>
                </div>
                <div className="form-group">
                  <label className="form-label">Decision *</label>
                  <select className="form-input form-select" value={decision} onChange={ev => setDecision(ev.target.value)}>
                    <option value="">Select decision…</option>
                    <option value="APPROVED">✅ Approve — data is correct as-is</option>
                    <option value="REJECTED">❌ Reject — exception is invalid</option>
                    <option value="EDITED">✏️ Edit — apply a corrected value</option>
                    <option value="ESCALATED">⬆️ Escalate — needs senior review</option>
                    <option value="REQUEST_CORRECTION">📋 Request Correction from source</option>
                  </select>
                </div>
                {decision === 'EDITED' && (
                  <div className="form-group">
                    <label className="form-label">Corrected Value *</label>
                    <input
                      className="form-input"
                      value={corrected}
                      onChange={ev => setCorrected(ev.target.value)}
                      placeholder={`New value for "${e?.field_name}"`}
                    />
                    <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>
                      This value will be written to the loan record and logged in the audit trail.
                    </div>
                  </div>
                )}
                {ai && (
                  <div className="form-group">
                    <label className="form-label">Did you follow the AI recommendation?</label>
                    <div style={{ display: 'flex', gap: 10 }}>
                      <button className={`btn btn-sm ${aiFollowed === true ? 'btn-success' : 'btn-secondary'}`} onClick={() => setAiFollowed(true)}>Yes</button>
                      <button className={`btn btn-sm ${aiFollowed === false ? 'btn-danger' : 'btn-secondary'}`} onClick={() => setAiFollowed(false)}>No</button>
                    </div>
                  </div>
                )}
                <div className="form-group">
                  <label className="form-label">Reviewer Note (optional — logged in audit trail)</label>
                  <textarea className="form-input" rows={2} value={note} onChange={ev => setNote(ev.target.value)} placeholder="Your reasoning…" />
                </div>
                <button className="btn btn-primary" onClick={submitDecision} disabled={!decision}>
                  <CheckCircle size={14} /> Submit Decision
                </button>
              </div>
            )}
            {e?.status === 'RESOLVED' && (
              <div className="alert alert-success">
                This exception has been resolved. View the decision in the History tab.
              </div>
            )}
          </>}

          {/* ── History tab — full reviewer history ──────── */}
          {tab === 'history' && (
            <div>
              {history.length === 0 ? (
                <div className="empty-state">
                  <Clock size={28} />
                  <h3>No decisions yet</h3>
                  <p>Decision history will appear here after a reviewer acts on this exception.</p>
                </div>
              ) : (
                <div className="timeline">
                  {history.map((d, i) => (
                    <div key={d.id} className="timeline-item">
                      <div className="timeline-dot" style={{
                        background: d.decision === 'APPROVED' || d.decision === 'EDITED' ? 'var(--success)'
                          : d.decision === 'REJECTED' ? 'var(--danger)'
                          : d.decision === 'ESCALATED' ? 'var(--warning)'
                          : 'var(--border)',
                      }} />
                      <div className="timeline-time">
                        {d.created_at ? new Date(d.created_at).toLocaleString() : '—'}
                        &nbsp;·&nbsp;{d.reviewer_name || 'Reviewer'}
                      </div>
                      <div className="timeline-event">
                        <StatusBadge status={d.decision} />
                        {d.ai_decision_followed === true && <span style={{ marginLeft: 8, fontSize: 11, color: 'var(--accent)' }}>followed AI</span>}
                        {d.ai_decision_followed === false && <span style={{ marginLeft: 8, fontSize: 11, color: 'var(--text-muted)' }}>overrode AI</span>}
                      </div>
                      {d.corrected_value && (
                        <div className="timeline-detail">
                          Field corrected → <strong style={{ color: 'var(--success)' }}>{d.corrected_value}</strong>
                          <span style={{ color: 'var(--text-muted)', marginLeft: 8 }}>(was: {d.original_value})</span>
                        </div>
                      )}
                      {d.reviewer_note && (
                        <div className="timeline-detail" style={{ fontStyle: 'italic' }}>"{d.reviewer_note}"</div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* ── Comments tab ─────────────────────────────── */}
          {tab === 'comments' && (
            <div>
              {(exc.comments || []).map((c, i) => (
                <div key={i} style={{ background: 'var(--bg-hover)', borderRadius: 8, padding: '10px 12px', marginBottom: 8 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                    <span style={{ fontWeight: 500, fontSize: 12 }}>{c.author_name || 'User'}</span>
                    <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                      {c.created_at ? new Date(c.created_at).toLocaleString() : ''}
                    </span>
                  </div>
                  <div style={{ fontSize: 13 }}>{c.comment}</div>
                </div>
              ))}
              <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
                <input
                  className="form-input"
                  style={{ flex: 1 }}
                  placeholder="Add a comment…"
                  value={comment}
                  onChange={ev => setComment(ev.target.value)}
                  onKeyDown={ev => ev.key === 'Enter' && addComment()}
                />
                <button className="btn btn-secondary" onClick={addComment}>
                  <MessageSquare size={14} />
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ─── Main Exceptions Page ─────────────────────────────────────────────────────
export default function Exceptions() {
  const location = useLocation();

  // Read pre-filters from URL query params (e.g. /exceptions?severity=HIGH or /exceptions?upload_id=xxx)
  const urlParams   = new URLSearchParams(location.search);
  const urlSeverity = urlParams.get('severity')  || '';
  const urlStatus   = urlParams.get('status')    || '';
  const urlUploadId = urlParams.get('upload_id') || '';

  const [exceptions, setExceptions] = useState([]);
  const [summary, setSummary]       = useState({});
  const [total, setTotal]           = useState(0);
  const [loading, setLoading]       = useState(true);
  const [page, setPage]             = useState(1);
  const [selected, setSelected]     = useState(null);

  // Filters — initialise from URL params
  const [search,   setSearch]   = useState('');
  const [severity, setSeverity] = useState(urlSeverity);
  const [status,   setStatus]   = useState(urlStatus);
  const [excType,  setExcType]  = useState('');
  const [uploadId, setUploadId] = useState(urlUploadId);
  const [excTypes, setExcTypes] = useState([]);  // dropdown options from backend
  const [uploads,  setUploads]  = useState([]);   // available uploaded files list

  const PAGE_SIZE = 20;

  // Fetch distinct exception types and uploads list for dropdowns
  useEffect(() => {
    exceptionsAPI.listTypes().then(r => setExcTypes(r.data || [])).catch(() => {});
    uploadsAPI.list({ page: 1, page_size: 100 }).then(r => setUploads(r.data?.items || [])).catch(() => {});
  }, []);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await exceptionsAPI.list({
        page,
        page_size:      PAGE_SIZE,
        search:         search   || undefined,
        severity:       severity || undefined,
        status:         status   || undefined,
        exception_type: excType  || undefined,
        upload_id:      uploadId || undefined,
      });
      setExceptions(res.data.items || []);
      setSummary(res.data.summary  || {});
      setTotal(res.data.total      || 0);
    } catch {}
    setLoading(false);
  }, [page, search, severity, status, excType, uploadId]);

  useEffect(() => { load(); }, [load]);

  // If URL params change (e.g. navigation from Dashboard/Uploads), apply them
  useEffect(() => {
    if (urlSeverity) setSeverity(urlSeverity);
    if (urlStatus)   setStatus(urlStatus);
    if (urlUploadId) setUploadId(urlUploadId);
  }, [location.search]);

  const resetFilters = () => {
    setSearch(''); setSeverity(''); setStatus(''); setExcType(''); setUploadId(''); setPage(1);
  };

  return (
    <Layout title="Exception Queue — Module C">
      <div className="page-header">
        <h2>Exception Queue</h2>
        <p>Review and resolve validation exceptions. AI recommendations guide — only humans decide.</p>
      </div>

      {/* Summary counts */}
      <div className="stat-grid mb-4" style={{ gridTemplateColumns: 'repeat(4,1fr)' }}>
        {[
          { label: 'Total', val: summary.total || 0, color: 'var(--text-primary)', filter: null },
          { label: 'High',   val: summary.HIGH   || 0, color: 'var(--danger)',  filter: 'HIGH' },
          { label: 'Medium', val: summary.MEDIUM || 0, color: 'var(--warning)', filter: 'MEDIUM' },
          { label: 'Low',    val: summary.LOW    || 0, color: 'var(--success)', filter: 'LOW' },
        ].map(({ label, val, color, filter }) => (
          <div
            key={label}
            className="stat-card"
            style={{ cursor: filter ? 'pointer' : 'default' }}
            onClick={() => { if (filter) { setSeverity(filter); setPage(1); } }}
          >
            <div className="stat-label">{label} Severity</div>
            <div className="stat-value" style={{ color }}>{val.toLocaleString()}</div>
          </div>
        ))}
      </div>

      <div className="card">
        {/* Filter bar */}
        <div className="filter-bar">
          <div className="search-input-wrap" style={{ flex: 2, minWidth: 200 }}>
            <Search size={15} />
            <input
              className="form-input"
              placeholder="Search loan ID, borrower ID, type…"
              value={search}
              onChange={e => { setSearch(e.target.value); setPage(1); }}
            />
          </div>

          <select
            className="form-input form-select"
            style={{ width: 130 }}
            value={severity}
            onChange={e => { setSeverity(e.target.value); setPage(1); }}
          >
            <option value="">All Severity</option>
            <option value="HIGH">High</option>
            <option value="MEDIUM">Medium</option>
            <option value="LOW">Low</option>
          </select>

          <select
            className="form-input form-select"
            style={{ width: 140 }}
            value={status}
            onChange={e => { setStatus(e.target.value); setPage(1); }}
          >
            <option value="">All Status</option>
            <option value="OPEN">Open</option>
            <option value="IN_REVIEW">In Review</option>
            <option value="RESOLVED">Resolved</option>
          </select>

          {/* Exception type dropdown — populated from backend */}
          <select
            className="form-input form-select"
            style={{ width: 200 }}
            value={excType}
            onChange={e => { setExcType(e.target.value); setPage(1); }}
          >
            <option value="">All Types</option>
            {excTypes.map(t => (
              <option key={t} value={t}>{t.replace(/_/g, ' ')}</option>
            ))}
          </select>

          {/* File selector dropdown */}
          <select
            className="form-input form-select"
            style={{ width: 200, borderColor: uploadId ? 'var(--accent)' : undefined, fontWeight: uploadId ? 600 : 400 }}
            value={uploadId}
            onChange={e => { setUploadId(e.target.value); setPage(1); }}
          >
            <option value="">📁 All Uploaded Files</option>
            {uploads.map((u, i) => (
              <option key={u.id} value={u.id}>
                📁 {u.original_filename || u.filename} (#{uploads.length - i})
              </option>
            ))}
          </select>

          <button className="btn btn-secondary btn-icon" onClick={load} title="Refresh">
            <RefreshCw size={14} />
          </button>
          {(search || severity || status || excType || uploadId) && (
            <button className="btn btn-ghost btn-sm" onClick={resetFilters} title="Clear filters">
              Clear
            </button>
          )}
        </div>

        {/* Active file isolation banner */}
        {uploadId && (
          <div style={{
            background: 'rgba(59,130,246,.08)',
            border: '1px solid rgba(59,130,246,.25)',
            borderRadius: 8,
            padding: '10px 14px',
            margin: '0 0 16px 0',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}>
            <span style={{ fontSize: 13, color: 'var(--accent)', fontWeight: 600 }}>
              📁 Showing exceptions for file: <u>{uploads.find(u => u.id === uploadId)?.original_filename || 'Selected File'}</u> ({total.toLocaleString()} exceptions)
            </span>
            <button className="btn btn-secondary btn-sm" onClick={() => setUploadId('')}>
              Show All Files
            </button>
          </div>
        )}

        {loading ? (
          <div style={{ textAlign: 'center', padding: 48 }}><span className="spinner" /></div>
        ) : (
          <>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Loan ID</th>
                    <th>Exception Type</th>
                    <th>Field</th>
                    <th>Actual</th>
                    <th>Expected</th>
                    <th>Severity</th>
                    <th>Status</th>
                    <th>Created</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {exceptions.map(e => (
                    <tr
                      key={e.id}
                      style={{ cursor: 'pointer' }}
                      onClick={() => setSelected(e.id)}
                    >
                      <td className="font-mono" style={{ fontSize: 11 }}>{e.loan_id}</td>
                      <td style={{ fontSize: 11, maxWidth: 160, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {e.exception_type?.replace(/_/g, ' ')}
                      </td>
                      <td style={{ fontSize: 11, color: 'var(--text-muted)' }}>{e.field_name || '—'}</td>
                      <td style={{ fontSize: 11, color: 'var(--danger)', maxWidth: 100, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {e.actual_value || '—'}
                      </td>
                      <td style={{ fontSize: 11, color: 'var(--success)', maxWidth: 100, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {e.expected_value || '—'}
                      </td>
                      <td><SeverityBadge severity={e.severity} /></td>
                      <td><StatusBadge status={e.status} /></td>
                      <td style={{ fontSize: 11, color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
                        {e.created_at ? new Date(e.created_at).toLocaleDateString() : '—'}
                      </td>
                      <td><ChevronRight size={14} color="var(--text-muted)" /></td>
                    </tr>
                  ))}
                  {!exceptions.length && (
                    <tr>
                      <td colSpan={9}>
                        <div className="empty-state">
                          <AlertTriangle size={32} />
                          <h3>No exceptions found</h3>
                          <p>
                            {search || severity || status || excType
                              ? 'Try clearing filters'
                              : 'Upload a CSV to run validation'}
                          </p>
                        </div>
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            {total > PAGE_SIZE && (
              <div className="pagination">
                <span>{total.toLocaleString()} exceptions</span>
                <button className="page-btn" disabled={page === 1} onClick={() => setPage(p => p - 1)}>Prev</button>
                <span>{page} / {Math.ceil(total / PAGE_SIZE)}</span>
                <button className="page-btn" disabled={page >= Math.ceil(total / PAGE_SIZE)} onClick={() => setPage(p => p + 1)}>Next</button>
              </div>
            )}
          </>
        )}
      </div>

      {selected && (
        <ExceptionDetail id={selected} onClose={() => { setSelected(null); load(); }} />
      )}
    </Layout>
  );
}
