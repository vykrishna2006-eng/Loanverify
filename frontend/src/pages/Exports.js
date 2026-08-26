import React from 'react';
import Layout from '../components/Layout';
import { Download, FileText, ClipboardList } from 'lucide-react';

const API = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export default function Exports() {
  return (
    <Layout title="Exports">
      <div className="page-header">
        <h2>Exports</h2>
        <p>Download verified loan records and audit trail as CSV.</p>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        <div className="card" style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
          <div style={{ width: 48, height: 48, borderRadius: 10, background: 'rgba(16,185,129,.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <FileText size={22} color="var(--success)" />
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ fontWeight: 600, marginBottom: 4 }}>Verified Loans CSV</div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>All verified loan records with canonical data and record hashes.</div>
          </div>
          <a className="btn btn-success" href={`${API}/api/exports/verified-loans/csv`} download>
            <Download size={14} /> Download CSV
          </a>
        </div>
        <div className="card" style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
          <div style={{ width: 48, height: 48, borderRadius: 10, background: 'rgba(59,130,246,.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <ClipboardList size={22} color="var(--accent)" />
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ fontWeight: 600, marginBottom: 4 }}>Full Audit Trail CSV</div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Complete audit log of all system actions, AI recommendations, and human decisions.</div>
          </div>
          <a className="btn btn-primary" href={`${API}/api/exports/audit/csv`} download>
            <Download size={14} /> Download CSV
          </a>
        </div>
      </div>
    </Layout>
  );
}
