import React, { useState, useEffect } from 'react';
import Layout from '../components/Layout';
import { verifiedLoansAPI, exportsAPI } from '../api/client';
import { StatusBadge } from '../components/SeverityBadge';
import toast from 'react-hot-toast';
import { CheckCircle, Shield, Search, XCircle, Download, Hash, ChevronDown, ChevronUp } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

// ─── Lineage Tree Component ───────────────────────────────────────────────────
function LineageTree({ lineage }) {
  const [expanded, setExpanded] = useState(false);
  const entries    = Object.entries(lineage || {});
  const visible    = expanded ? entries : entries.slice(0, 6);
  const hasMore    = entries.length > 6;

  return (
    <div>
      <div className="lineage-tree">
        {visible.map(([field, info]) => (
          <div key={field} className="lineage-field">
            <div className="lineage-field-name">{field.replace(/_/g, ' ')}</div>
            <div style={{ display: 'flex', alignItems: 'center', fontSize: 11, flexWrap: 'wrap', gap: 4 }}>
              <span style={{ color: 'var(--accent)', fontWeight: 500 }}>{info.source || 'LOAN_TAPE'}</span>
              <span className="lineage-arrow">→</span>
              <span className="lineage-source">{info.source_file}</span>
              <span className="lineage-arrow">→</span>
              <span className="lineage-source">Row {info.source_row}</span>
              <span className="lineage-arrow">→</span>
              <span style={{ color: 'var(--text-primary)', fontWeight: 500 }}>
                {info.value !== null && info.value !== undefined ? String(info.value) : 'null'}
              </span>
            </div>
          </div>
        ))}
      </div>
      {hasMore && (
        <button
          className="btn btn-ghost btn-sm"
          style={{ marginTop: 8, fontSize: 11 }}
          onClick={() => setExpanded(v => !v)}
        >
          {expanded ? <><ChevronUp size={12} /> Show less</> : <><ChevronDown size={12} /> Show all {entries.length} fields</>}
        </button>
      )}
    </div>
  );
}

// ─── Detail Modal ─────────────────────────────────────────────────────────────
function VerifiedLoanDetail({ loanId, onClose }) {
  const [loan, setLoan]           = useState(null);
  const [loading, setLoading]     = useState(true);
  const [hashResult, setHashResult] = useState(null);
  const [checking, setChecking]   = useState(false);
  const [tab, setTab]             = useState('canonical');  // canonical | lineage | validation | meta

  useEffect(() => {
    verifiedLoansAPI.get(loanId)
      .then(r => { setLoan(r.data); setLoading(false); })
      .catch(() => setLoading(false));
  }, [loanId]);

  const verifyHash = async () => {
    setChecking(true);
    try {
      const res = await verifiedLoansAPI.verifyHash(loanId);
      setHashResult(res.data);
      if (res.data.is_valid) toast.success('Hash verified — data intact');
      else toast.error('⚠️ Hash mismatch — possible tampering!');
    } catch { toast.error('Hash check failed'); }
    setChecking(false);
  };

  const exportLoan = async () => {
    try {
      const res = await verifiedLoansAPI.export(loanId);
      const blob = new Blob([JSON.stringify(res.data, null, 2)], { type: 'application/json' });
      const url  = URL.createObjectURL(blob);
      const a    = document.createElement('a');
      a.href = url; a.download = `verified_${loanId}.json`; a.click();
      URL.revokeObjectURL(url);
      toast.success('Exported');
    } catch { toast.error('Export failed'); }
  };

  if (loading) {
    return (
      <div className="modal-overlay">
        <div className="modal" style={{ padding: 40, textAlign: 'center' }}><span className="spinner" /></div>
      </div>
    );
  }
  if (!loan) return null;

  return (
    <div className="modal-overlay" onClick={e => e.target === e.currentTarget && onClose?.()}>
      <div className="modal" style={{ maxWidth: 800 }}>
        {/* Header */}
        <div className="modal-header">
          <div>
            <h2>Verified Loan Record</h2>
            <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>
              <span className="font-mono">{loan.loan_id}</span>
            </div>
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="btn btn-secondary btn-sm" onClick={exportLoan}>
              <Download size={13} /> Export JSON
            </button>
            <button className="btn btn-ghost btn-icon" onClick={onClose}><XCircle size={18} /></button>
          </div>
        </div>

        {/* Verification stamp */}
        <div style={{ margin: '0 24px 0', padding: '12px 16px', background: 'rgba(16,185,129,.07)', border: '1px solid rgba(16,185,129,.2)', borderRadius: 10 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
            <CheckCircle size={18} color="var(--success)" />
            <span style={{ fontWeight: 700, color: 'var(--success)', fontSize: 15 }}>VERIFIED</span>
            <StatusBadge status={loan.status} />
            <span style={{ fontSize: 12, color: 'var(--text-muted)', marginLeft: 'auto' }}>
              {loan.verified_at ? new Date(loan.verified_at).toLocaleString() : '—'}
            </span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 10, marginTop: 10, fontSize: 12 }}>
            <div>
              <span style={{ color: 'var(--text-muted)' }}>Verified by: </span>
              {/* Task 14: show verified_by_name, not just UUID */}
              <strong>{loan.verified_by_name || loan.verified_by || '—'}</strong>
            </div>
            <div>
              <span style={{ color: 'var(--text-muted)' }}>Source: </span>
              {loan.source_file || '—'} {loan.source_row ? `· Row ${loan.source_row}` : ''}
            </div>
            <div>
              <span style={{ color: 'var(--text-muted)' }}>Exceptions: </span>
              {loan.exception_count}
              {loan.reviewer_decision_ids?.length > 0 && (
                <span style={{ color: 'var(--text-muted)' }}> · {loan.reviewer_decision_ids.length} decision{loan.reviewer_decision_ids.length !== 1 ? 's' : ''}</span>
              )}
            </div>
          </div>
        </div>

        {/* Hash integrity row */}
        <div style={{ margin: '12px 24px 0', padding: '12px 16px', background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12 }}>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4, display: 'flex', alignItems: 'center', gap: 6 }}>
                <Hash size={12} /> {loan.hash_algorithm} Record Hash
              </div>
              <div className="hash-display" style={{ fontSize: 11 }}>{loan.record_hash}</div>
            </div>
            <button className="btn btn-secondary btn-sm" onClick={verifyHash} disabled={checking} style={{ flexShrink: 0 }}>
              <Shield size={12} /> {checking ? 'Checking…' : 'Verify Integrity'}
            </button>
          </div>
          {hashResult && (
            <div className={`alert ${hashResult.is_valid ? 'alert-success' : 'alert-danger'}`} style={{ marginTop: 10, marginBottom: 0 }}>
              {hashResult.is_valid ? '✅ ' : '⚠️ '}{hashResult.message}
            </div>
          )}
          <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 6 }}>
            SHA-256 of canonical data. Any post-verification change will invalidate this hash.
          </div>
        </div>

        {/* Tabs */}
        <div className="tabs" style={{ margin: '12px 24px 0' }}>
          {['canonical', 'lineage', 'validation', 'meta'].map(t => (
            <div key={t} className={`tab ${tab === t ? 'active' : ''}`} onClick={() => setTab(t)}>
              {t === 'canonical' ? 'Canonical Data'
               : t === 'lineage' ? `Lineage (${Object.keys(loan.data_lineage || {}).length} fields)`
               : t === 'validation' ? 'Validation'
               : 'Metadata'}
            </div>
          ))}
        </div>

        <div className="modal-body">
          {/* Canonical Data */}
          {tab === 'canonical' && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, fontSize: 12 }}>
              {Object.entries(loan.canonical_data || {}).map(([k, v]) => (
                <div key={k} style={{ background: 'var(--bg-hover)', borderRadius: 6, padding: '8px 10px' }}>
                  <div style={{ fontSize: 10, color: 'var(--text-muted)', marginBottom: 2 }}>{k.replace(/_/g, ' ')}</div>
                  <div style={{ fontWeight: 500 }}>{v !== null && v !== undefined ? String(v) : <span style={{ color: 'var(--text-muted)' }}>—</span>}</div>
                </div>
              ))}
            </div>
          )}

          {/* Full Data Lineage */}
          {tab === 'lineage' && (
            loan.data_lineage
              ? <LineageTree lineage={loan.data_lineage} />
              : <div className="empty-state"><p>No lineage data available</p></div>
          )}

          {/* Validation Summary */}
          {tab === 'validation' && (
            loan.validation_summary?.categories
              ? (
                <>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
                    <div style={{ fontSize: 32, fontWeight: 800, color: 'var(--success)' }}>
                      {loan.validation_summary.overall}%
                    </div>
                    <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>Overall Data Quality Score</div>
                  </div>
                  {Object.entries(loan.validation_summary.categories).map(([cat, score]) => {
                    const color = score >= 90 ? 'var(--success)' : score >= 70 ? 'var(--warning)' : 'var(--danger)';
                    return (
                      <div key={cat} style={{ marginBottom: 10 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 4 }}>
                          <span>{cat}</span>
                          <span style={{ fontWeight: 600, color }}>{score}%</span>
                        </div>
                        <div className="progress-bar">
                          <div className="progress-fill" style={{ width: `${score}%`, background: color }} />
                        </div>
                      </div>
                    );
                  })}
                </>
              )
              : <div className="empty-state"><p>Validation summary not yet computed for this record</p></div>
          )}

          {/* Metadata */}
          {tab === 'meta' && (
            <div style={{ fontSize: 12 }}>
              {[
                ['Loan ID',           loan.loan_id],
                ['Loan Record ID',    loan.loan_record_id],
                ['Upload ID',         loan.upload_id],
                ['Verified By',       `${loan.verified_by_name || '—'} (${loan.verified_by || '—'})`],
                ['Verified At',       loan.verified_at ? new Date(loan.verified_at).toLocaleString() : '—'],
                ['Hash Algorithm',    loan.hash_algorithm],
                ['Is Hash Valid',     loan.is_hash_valid ? 'Yes ✅' : 'No ⚠️'],
                ['Exception Count',   loan.exception_count],
                ['AI Recommendations', (loan.ai_recommendation_ids || []).length],
                ['Reviewer Decisions', (loan.reviewer_decision_ids || []).length],
                ['Export Count',      loan.export_count],
                ['Last Exported',     loan.exported_at ? new Date(loan.exported_at).toLocaleString() : '—'],
                ['Status',            loan.status],
                ['Notes',             loan.notes || '—'],
              ].map(([label, val]) => (
                <div key={label} style={{ display: 'flex', gap: 12, padding: '7px 0', borderBottom: '1px solid var(--border)' }}>
                  <span style={{ width: 160, flexShrink: 0, color: 'var(--text-muted)' }}>{label}</span>
                  <span style={{ fontWeight: 500, wordBreak: 'break-all' }}>{String(val)}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────
export default function VerifiedLoans() {
  const { token } = useAuth();
  const [loans, setLoans]       = useState([]);
  const [total, setTotal]       = useState(0);
  const [loading, setLoading]   = useState(true);
  const [page, setPage]         = useState(1);
  const [search, setSearch]     = useState('');
  const [selected, setSelected] = useState(null);
  const PAGE_SIZE = 20;

  const downloadCSV = async () => {
    try {
      await exportsAPI.downloadVerifiedLoansCSV();
      toast.success('CSV exported successfully!');
    } catch (e) {
      toast.error('Export failed');
    }
  };

  const load = async () => {
    setLoading(true);
    try {
      const res = await verifiedLoansAPI.list({
        page, page_size: PAGE_SIZE, search: search || undefined,
      });
      setLoans(res.data.items || []);
      setTotal(res.data.total  || 0);
    } catch {}
    setLoading(false);
  };

  useEffect(() => { load(); }, [page, search]);

  return (
    <Layout title="Verified Loans — Module E">
      <div className="page-header">
        <h2>Verified Loan Records</h2>
        <p>Canonical records with SHA-256 integrity hash, data lineage, and validation summary.</p>
      </div>

      <div className="card">
        <div className="filter-bar">
          <div className="search-input-wrap">
            <Search size={15} />
            <input
              className="form-input"
              placeholder="Search loan ID or source file…"
              value={search}
              onChange={e => { setSearch(e.target.value); setPage(1); }}
            />
          </div>
          <button
            className="btn btn-secondary"
            onClick={downloadCSV}
          >
            <Download size={14} /> Export All CSV
          </button>
        </div>

        {loading ? (
          <div style={{ textAlign: 'center', padding: 48 }}><span className="spinner" /></div>
        ) : (
          <>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Loan ID</th>
                    <th>Principal</th>
                    <th>Balance</th>
                    <th>Pay Status</th>
                    <th>Exceptions</th>
                    <th>Verified By</th>    {/* resolved name — Task 14 */}
                    <th>Verified At</th>
                    <th>Hash</th>
                    <th>Integrity</th>
                  </tr>
                </thead>
                <tbody>
                  {loans.map(l => (
                    <tr key={l.id} style={{ cursor: 'pointer' }} onClick={() => setSelected(l.loan_id)}>
                      <td className="font-mono" style={{ fontSize: 11 }}>{l.loan_id}</td>
                      <td style={{ fontSize: 12 }}>
                        {l.canonical_data?.original_principal
                          ? `$${Number(l.canonical_data.original_principal).toLocaleString()}`
                          : '—'}
                      </td>
                      <td style={{ fontSize: 12 }}>
                        {l.canonical_data?.current_balance
                          ? `$${Number(l.canonical_data.current_balance).toLocaleString()}`
                          : '—'}
                      </td>
                      <td><StatusBadge status={l.canonical_data?.payment_status || l.status} /></td>
                      <td style={{ textAlign: 'center', fontSize: 12 }}>{l.exception_count}</td>
                      <td style={{ fontSize: 12 }}>
                        {/* Task 14: show name instead of UUID */}
                        {l.verified_by_name || <span style={{ color: 'var(--text-muted)', fontSize: 11 }}>{String(l.verified_by || '—').slice(0, 8)}…</span>}
                      </td>
                      <td style={{ fontSize: 11, color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
                        {l.verified_at ? new Date(l.verified_at).toLocaleDateString() : '—'}
                      </td>
                      <td>
                        <span className="font-mono" style={{ fontSize: 10, color: 'var(--success)' }}>
                          {l.record_hash?.slice(0, 12)}…
                        </span>
                      </td>
                      <td style={{ textAlign: 'center' }}>
                        {l.is_hash_valid
                          ? <CheckCircle size={14} color="var(--success)" title="Hash valid" />
                          : <XCircle    size={14} color="var(--danger)"  title="Hash invalid!" />}
                      </td>
                    </tr>
                  ))}
                  {!loans.length && (
                    <tr>
                      <td colSpan={9}>
                        <div className="empty-state">
                          <CheckCircle size={32} />
                          <h3>No verified loans yet</h3>
                          <p>Resolve exceptions and approve loans to create verified records</p>
                        </div>
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            {total > PAGE_SIZE && (
              <div className="pagination">
                <span>{total.toLocaleString()} verified</span>
                <button className="page-btn" disabled={page === 1} onClick={() => setPage(p => p - 1)}>Prev</button>
                <span>{page} / {Math.ceil(total / PAGE_SIZE)}</span>
                <button className="page-btn" disabled={page >= Math.ceil(total / PAGE_SIZE)} onClick={() => setPage(p => p + 1)}>Next</button>
              </div>
            )}
          </>
        )}
      </div>

      {selected && (
        <VerifiedLoanDetail loanId={selected} onClose={() => { setSelected(null); load(); }} />
      )}
    </Layout>
  );
}
