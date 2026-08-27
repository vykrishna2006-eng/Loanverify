import React, { useState } from 'react';
import Layout from '../components/Layout';
import { Download, FileText, ClipboardList } from 'lucide-react';
import { exportsAPI } from '../api/client';
import toast from 'react-hot-toast';

export default function Exports() {
  const [downloadingVerified, setDownloadingVerified] = useState(false);
  const [downloadingAudit, setDownloadingAudit] = useState(false);

  const handleDownloadVerified = async () => {
    setDownloadingVerified(true);
    try {
      await exportsAPI.downloadVerifiedLoansCSV();
      toast.success('Verified loans CSV exported successfully!');
    } catch (e) {
      toast.error('Failed to download verified loans CSV');
    } finally {
      setDownloadingVerified(false);
    }
  };

  const handleDownloadAudit = async () => {
    setDownloadingAudit(true);
    try {
      await exportsAPI.downloadAuditCSV();
      toast.success('Audit trail CSV exported successfully!');
    } catch (e) {
      toast.error('Failed to download audit trail CSV');
    } finally {
      setDownloadingAudit(false);
    }
  };

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
          <button className="btn btn-success" onClick={handleDownloadVerified} disabled={downloadingVerified}>
            <Download size={14} /> {downloadingVerified ? 'Downloading…' : 'Download CSV'}
          </button>
        </div>
        <div className="card" style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
          <div style={{ width: 48, height: 48, borderRadius: 10, background: 'rgba(59,130,246,.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <ClipboardList size={22} color="var(--accent)" />
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ fontWeight: 600, marginBottom: 4 }}>Full Audit Trail CSV</div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Complete audit log of all system actions, AI recommendations, and human decisions.</div>
          </div>
          <button className="btn btn-primary" onClick={handleDownloadAudit} disabled={downloadingAudit}>
            <Download size={14} /> {downloadingAudit ? 'Downloading…' : 'Download CSV'}
          </button>
        </div>
      </div>
    </Layout>
  );
}
