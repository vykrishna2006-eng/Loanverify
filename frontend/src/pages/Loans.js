import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import Layout from '../components/Layout';
import { loansAPI, uploadsAPI } from '../api/client';
import { StatusBadge } from '../components/SeverityBadge';
import { Search, FileText, RefreshCw } from 'lucide-react';

export default function Loans() {
  const location = useLocation();
  const urlParams = new URLSearchParams(location.search);
  const urlUploadId = urlParams.get('upload_id') || '';

  const [loans, setLoans]       = useState([]);
  const [total, setTotal]       = useState(0);
  const [loading, setLoading]   = useState(true);
  const [page, setPage]         = useState(1);
  const [search, setSearch]     = useState('');
  const [status, setStatus]     = useState('');
  const [uploadId, setUploadId] = useState(urlUploadId);
  const [uploads, setUploads]   = useState([]);
  const PAGE_SIZE = 25;

  useEffect(() => {
    uploadsAPI.list({ page: 1, page_size: 100 }).then(r => setUploads(r.data?.items || [])).catch(() => {});
  }, []);

  const load = async () => {
    setLoading(true);
    try {
      const res = await loansAPI.list({
        page,
        page_size: PAGE_SIZE,
        search: search || undefined,
        payment_status: status || undefined,
        upload_id: uploadId || undefined,
      });
      setLoans(res.data.items || []);
      setTotal(res.data.total || 0);
    } catch {}
    setLoading(false);
  };

  useEffect(() => { load(); }, [page, search, status, uploadId]);

  useEffect(() => {
    if (urlUploadId) setUploadId(urlUploadId);
  }, [location.search]);

  return (
    <Layout title="Loan Records">
      <div className="page-header">
        <h2>Loan Records</h2>
        <p>All imported and normalized loan records across all uploads.</p>
      </div>
      <div className="card">
        <div className="filter-bar">
          <div className="search-input-wrap">
            <Search size={15} />
            <input className="form-input" placeholder="Search loan ID, borrower, servicer…" value={search} onChange={e => { setSearch(e.target.value); setPage(1); }} />
          </div>
          <select className="form-input form-select" style={{ width: 160 }} value={status} onChange={e => { setStatus(e.target.value); setPage(1); }}>
            <option value="">All Statuses</option>
            <option value="CURRENT">Current</option>
            <option value="DELINQUENT">Delinquent</option>
            <option value="DEFAULT">Default</option>
            <option value="PAID_OFF">Paid Off</option>
            <option value="CLOSED">Closed</option>
          </select>
          <select
            className="form-input form-select"
            style={{ width: 220, borderColor: uploadId ? 'var(--accent)' : undefined, fontWeight: uploadId ? 600 : 400 }}
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
        </div>

        {uploadId && (
          <div style={{
            background: 'rgba(59,130,246,.08)',
            border: '1px solid rgba(59,130,246,.25)',
            borderRadius: 8,
            padding: '10px 14px',
            marginBottom: 16,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}>
            <span style={{ fontSize: 13, color: 'var(--accent)', fontWeight: 600 }}>
              📁 Showing loans from file: <u>{uploads.find(u => u.id === uploadId)?.original_filename || 'Selected File'}</u> ({total.toLocaleString()} records)
            </span>
            <button className="btn btn-secondary btn-sm" onClick={() => setUploadId('')}>
              Show All Files
            </button>
          </div>
        )}

        {loading ? (
          <div style={{ textAlign: 'center', padding: 40 }}><span className="spinner" /></div>
        ) : (
          <>
            <div className="table-wrap">
              <table>
                <thead><tr>
                  <th>Loan ID</th><th>Borrower</th><th>Principal</th><th>Balance</th>
                  <th>Rate</th><th>State</th><th>Status</th><th>Orig. Date</th><th>DPD</th><th>Duplicate</th>
                </tr></thead>
                <tbody>
                  {loans.map(l => (
                    <tr key={l.id}>
                      <td className="font-mono" style={{ fontSize: 11 }}>{l.loan_id}</td>
                      <td style={{ fontSize: 12 }}>{l.borrower_name || l.borrower_id || '—'}</td>
                      <td style={{ fontSize: 12 }}>{l.original_principal ? `$${Number(l.original_principal).toLocaleString()}` : '—'}</td>
                      <td style={{ fontSize: 12 }}>{l.current_balance ? `$${Number(l.current_balance).toLocaleString()}` : '—'}</td>
                      <td style={{ fontSize: 12 }}>{l.interest_rate ? `${l.interest_rate}%` : '—'}</td>
                      <td style={{ fontSize: 12 }}>{l.property_state || '—'}</td>
                      <td><StatusBadge status={l.payment_status} /></td>
                      <td style={{ fontSize: 11, color: 'var(--text-muted)' }}>{l.origination_date || '—'}</td>
                      <td style={{ fontSize: 12, color: l.days_past_due > 0 ? 'var(--warning)' : 'var(--text-muted)' }}>{l.days_past_due ?? 0}</td>
                      <td>{l.is_duplicate ? <span className="badge badge-medium">DUP</span> : '—'}</td>
                    </tr>
                  ))}
                  {!loans.length && <tr><td colSpan={10}>
                    <div className="empty-state"><FileText size={32} /><h3>No loans found</h3><p>Upload a CSV to import loan records</p></div>
                  </td></tr>}
                </tbody>
              </table>
            </div>
            {total > PAGE_SIZE && (
              <div className="pagination">
                <span>{total.toLocaleString()} loans</span>
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
