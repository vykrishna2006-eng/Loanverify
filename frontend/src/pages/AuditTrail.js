import React, { useState, useEffect } from 'react';
import Layout from '../components/Layout';
import { auditAPI } from '../api/client';
import { Search, Bot, Download } from 'lucide-react';

const EVENT_COLORS = {
  FILE_UPLOADED: '#3b82f6',
  RECORDS_IMPORTED: '#06b6d4',
  VALIDATION_EXECUTED: '#8b5cf6',
  EXCEPTION_CREATED: '#f59e0b',
  AI_RECOMMENDATION_GENERATED: '#3b82f6',
  REVIEWER_COMMENT_ADDED: '#94a3b8',
  FIELD_EDITED: '#f59e0b',
  LOAN_APPROVED: '#10b981',
  LOAN_REJECTED: '#ef4444',
  VERIFIED_RECORD_CREATED: '#10b981',
  RECORD_EXPORTED: '#06b6d4',
  HASH_VERIFIED: '#10b981',
  HASH_MISMATCH: '#ef4444',
  RULE_ACTIVATED: '#8b5cf6',
};

export default function AuditTrail() {
  const [events, setEvents]   = useState([]);
  const [total, setTotal]     = useState(0);
  const [loading, setLoading] = useState(true);
  const [page, setPage]       = useState(1);
  const [loanFilter, setLoanFilter] = useState('');
  const [eventFilter, setEventFilter] = useState('');
  const [aiFilter, setAiFilter] = useState('');
  const [mode, setMode]       = useState('table'); // table | timeline
  const PAGE_SIZE = 50;

  const load = async () => {
    setLoading(true);
    try {
      const res = await auditAPI.list({
        page, page_size: PAGE_SIZE,
        loan_id: loanFilter || undefined,
        event_type: eventFilter || undefined,
        ai_involved: aiFilter !== '' ? aiFilter === 'true' : undefined,
      });
      setEvents(res.data.items || []);
      setTotal(res.data.total || 0);
    } catch {}
    setLoading(false);
  };

  useEffect(() => { load(); }, [page, loanFilter, eventFilter, aiFilter]);

  const exportAudit = () => {
    const url = `${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/exports/audit/csv${loanFilter ? `?loan_id=${loanFilter}` : ''}`;
    const a = document.createElement('a'); a.href = url; a.download = 'audit_trail.csv'; a.click();
  };

  return (
    <Layout title="Audit Trail — Module F">
      <div className="page-header">
        <h2>Audit Trail</h2>
        <p>Complete, immutable log of every action taken in the system.</p>
      </div>

      {/* Filter bar */}
      <div className="filter-bar mb-4">
        <div className="search-input-wrap">
          <Search size={15} />
          <input className="form-input" placeholder="Filter by Loan ID…" value={loanFilter} onChange={e => { setLoanFilter(e.target.value); setPage(1); }} />
        </div>
        <select className="form-input form-select" style={{ width: 200 }} value={eventFilter} onChange={e => { setEventFilter(e.target.value); setPage(1); }}>
          <option value="">All Event Types</option>
          {Object.keys(EVENT_COLORS).map(t => <option key={t} value={t}>{t.replace(/_/g,' ')}</option>)}
        </select>
        <select className="form-input form-select" style={{ width: 140 }} value={aiFilter} onChange={e => { setAiFilter(e.target.value); setPage(1); }}>
          <option value="">All Events</option>
          <option value="true">AI Events Only</option>
          <option value="false">Human Events Only</option>
        </select>
        <div className="tabs" style={{ margin: 0, border: 'none' }}>
          <div className={`tab ${mode === 'table' ? 'active' : ''}`} onClick={() => setMode('table')} style={{ padding: '6px 12px' }}>Table</div>
          <div className={`tab ${mode === 'timeline' ? 'active' : ''}`} onClick={() => setMode('timeline')} style={{ padding: '6px 12px' }}>Timeline</div>
        </div>
        <button className="btn btn-secondary btn-sm" onClick={exportAudit}><Download size={13} /> Export CSV</button>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: 60 }}><span className="spinner" /></div>
      ) : mode === 'table' ? (
        <div className="card">
          <div className="table-wrap">
            <table>
              <thead><tr>
                <th>Time</th><th>Event</th><th>Actor</th><th>Loan ID</th><th>AI?</th><th>Details</th>
              </tr></thead>
              <tbody>
                {events.map(e => (
                  <tr key={e.id}>
                    <td style={{ fontSize: 11, color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
                      {e.created_at ? new Date(e.created_at).toLocaleString() : '—'}
                    </td>
                    <td>
                      <span style={{
                        display: 'inline-block', width: 8, height: 8, borderRadius: '50%',
                        background: EVENT_COLORS[e.event_type] || '#94a3b8',
                        marginRight: 6,
                      }} />
                      <span style={{ fontSize: 12, fontWeight: 500 }}>{e.event_type?.replace(/_/g,' ')}</span>
                    </td>
                    <td style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{e.actor_email || '—'}</td>
                    <td className="font-mono" style={{ fontSize: 11 }}>{e.loan_id || '—'}</td>
                    <td style={{ textAlign: 'center' }}>
                      {e.ai_involved ? <Bot size={14} color="var(--accent)" title="AI involved" /> : '—'}
                    </td>
                    <td style={{ fontSize: 11, color: 'var(--text-muted)', maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {e.reason || (e.new_value ? JSON.stringify(e.new_value).slice(0, 60) : '—')}
                    </td>
                  </tr>
                ))}
                {!events.length && (
                  <tr><td colSpan={6}>
                    <div className="empty-state">
                      <h3>No audit events</h3>
                      <p>Events appear after upload, validation, and review actions</p>
                    </div>
                  </td></tr>
                )}
              </tbody>
            </table>
          </div>
          {total > PAGE_SIZE && (
            <div className="pagination">
              <span>{total.toLocaleString()} events</span>
              <button className="page-btn" disabled={page === 1} onClick={() => setPage(p => p - 1)}>Prev</button>
              <span>{page} / {Math.ceil(total / PAGE_SIZE)}</span>
              <button className="page-btn" disabled={page >= Math.ceil(total / PAGE_SIZE)} onClick={() => setPage(p => p + 1)}>Next</button>
            </div>
          )}
        </div>
      ) : (
        <div className="card">
          <div className="timeline">
            {events.map((e, i) => (
              <div key={e.id} className="timeline-item">
                <div className="timeline-dot" style={{ background: EVENT_COLORS[e.event_type] || '#94a3b8' }} />
                <div className="timeline-time">
                  {e.created_at ? new Date(e.created_at).toLocaleTimeString() : '—'} · {e.actor_email || 'System'}
                  {e.ai_involved && <span style={{ marginLeft: 6 }}><Bot size={11} style={{ display:'inline' }} color="var(--accent)" /></span>}
                </div>
                <div className="timeline-event">
                  {e.event_type?.replace(/_/g,' ')}
                  {e.loan_id && <span className="font-mono" style={{ fontSize: 11, color: 'var(--text-muted)', marginLeft: 8 }}>#{e.loan_id}</span>}
                </div>
                {e.reason && <div className="timeline-detail">{e.reason}</div>}
              </div>
            ))}
            {!events.length && <div className="empty-state"><h3>No audit events</h3></div>}
          </div>
        </div>
      )}
    </Layout>
  );
}
