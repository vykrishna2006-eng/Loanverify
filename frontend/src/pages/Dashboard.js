import React, { useState, useEffect } from 'react';
import Layout from '../components/Layout';
import { useAuth } from '../context/AuthContext';
import { dashboardAPI, exportsAPI } from '../api/client';
import { SeverityBadge, StatusBadge } from '../components/SeverityBadge';
import { useNavigate } from 'react-router-dom';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import {
  Upload, AlertTriangle, CheckCircle, TrendingUp,
  FileText, Bot, ShieldCheck, ArrowRight, Download,
} from 'lucide-react';

function StatCard({ label, value, sub, icon: Icon, color = 'var(--accent)', onClick }) {
  return (
    <div className="stat-card" style={{ cursor: onClick ? 'pointer' : 'default' }} onClick={onClick}>
      {Icon && (
        <div className="stat-icon" style={{ background: `${color}20` }}>
          <Icon size={18} color={color} />
        </div>
      )}
      <div className="stat-label">{label}</div>
      <div className="stat-value">{value ?? '—'}</div>
      {sub && <div className="stat-sub">{sub}</div>}
    </div>
  );
}

// ─── Data Operator ────────────────────────────────────────────────────────────
function OperatorDashboard({ data, navigate }) {
  const m = data.metrics;
  return (
    <>
      <div className="stat-grid mb-4">
        <StatCard label="Total Uploads"        value={m.total_uploads}                       icon={Upload}        color="var(--accent)"  onClick={() => navigate('/uploads')} />
        <StatCard label="Records Imported"     value={m.total_records_imported?.toLocaleString()} icon={FileText} color="var(--success)" />
        <StatCard label="Import Success Rate"  value={`${m.import_success_rate ?? 0}%`}      icon={TrendingUp}    color="var(--success)"
          sub={`${m.completed_uploads} of ${m.total_uploads} uploads completed`} />
        <StatCard label="Open Exceptions"      value={m.open_exceptions}                     icon={AlertTriangle} color="var(--warning)" onClick={() => navigate('/exceptions')} />
        <StatCard label="Needs Correction"     value={m.records_needing_correction}          icon={ShieldCheck}   color="var(--danger)"  onClick={() => navigate('/exceptions')} />
        <StatCard label="Total Exceptions"     value={m.validation_failures}                 icon={AlertTriangle} color="var(--danger)" />
      </div>

      <div className="grid-2" style={{ marginBottom: 16 }}>
        {/* Recent uploads table */}
        <div className="card">
          <div className="card-title">Recent Uploads</div>
          <div className="table-wrap">
            <table>
              <thead><tr><th>File</th><th>Type</th><th>Rows</th><th>Imported</th><th>Failed</th><th>Status</th></tr></thead>
              <tbody>
                {(data.recent_uploads || []).map(u => (
                  <tr key={u.id} style={{ cursor: 'pointer' }} onClick={() => navigate('/uploads')}>
                    <td style={{ maxWidth: 120, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontSize: 12 }}>
                      {u.filename}
                    </td>
                    <td><span className="badge badge-blue" style={{ fontSize: 10 }}>{u.source_type?.replace('_',' ')}</span></td>
                    <td style={{ fontSize: 12 }}>{u.total_rows?.toLocaleString()}</td>
                    <td style={{ fontSize: 12, color: 'var(--success)' }}>{u.imported_rows?.toLocaleString()}</td>
                    <td style={{ fontSize: 12, color: u.failed_rows > 0 ? 'var(--danger)' : 'var(--text-muted)' }}>{u.failed_rows?.toLocaleString()}</td>
                    <td><StatusBadge status={u.status} /></td>
                  </tr>
                ))}
                {!data.recent_uploads?.length && (
                  <tr><td colSpan={6} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: 20 }}>No uploads yet</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Source type chart */}
        <div className="card">
          <div className="card-title">Source Type Breakdown</div>
          {Object.keys(data.source_breakdown || {}).length > 0 ? (
            <ResponsiveContainer width="100%" height={170}>
              <BarChart data={Object.entries(data.source_breakdown).map(([k, v]) => ({ name: k.replace('_', ' '), count: v }))}>
                <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#94a3b8' }} />
                <YAxis tick={{ fontSize: 10, fill: '#94a3b8' }} />
                <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8, fontSize: 12 }} />
                <Bar dataKey="count" fill="var(--accent)" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="empty-state"><p>Upload a CSV to see breakdown</p></div>
          )}
        </div>
      </div>

      <div style={{ display: 'flex', gap: 12 }}>
        <button className="btn btn-primary" onClick={() => navigate('/uploads')}>
          <Upload size={14} /> Upload CSV
        </button>
        <button className="btn btn-secondary" onClick={() => navigate('/exceptions')}>
          <AlertTriangle size={14} /> Exception Queue
        </button>
        <button className="btn btn-secondary" onClick={() => navigate('/rules')}>
          <ShieldCheck size={14} /> Validation Rules
        </button>
      </div>
    </>
  );
}

// ─── Reviewer ────────────────────────────────────────────────────────────────
function ReviewerDashboard({ data, navigate }) {
  const m = data.metrics;
  return (
    <>
      <div className="stat-grid mb-4">
        <StatCard label="Open Exceptions"   value={m.open_exceptions}       icon={AlertTriangle} color="var(--warning)" onClick={() => navigate('/exceptions')} />
        <StatCard label="High Severity"     value={m.high_severity_open}    icon={AlertTriangle} color="var(--danger)"  onClick={() => navigate('/exceptions?severity=HIGH')} />
        <StatCard label="Pending Decisions" value={m.pending_decisions}     icon={ShieldCheck}   color="var(--info)" />
        <StatCard label="AI Reviews Done"   value={m.ai_reviews_generated}  icon={Bot}           color="var(--accent)" />
        <StatCard label="My Decisions"      value={m.total_decisions_made}  icon={CheckCircle}   color="var(--success)" />
        <StatCard label="AI Follow Rate"    value={`${m.ai_followed_rate}%`} icon={Bot}          color="var(--accent)"   sub="Agreement with AI recommendations" />
      </div>

      <div className="grid-2" style={{ marginBottom: 16 }}>
        {/* Pending exceptions */}
        <div className="card">
          <div className="card-title">Pending Exceptions</div>
          <div className="table-wrap">
            <table>
              <thead><tr><th>Loan ID</th><th>Type</th><th>Severity</th><th>Status</th><th></th></tr></thead>
              <tbody>
                {(data.recent_exceptions || []).slice(0, 8).map(e => (
                  <tr key={e.id} style={{ cursor: 'pointer' }} onClick={() => navigate('/exceptions')}>
                    <td className="font-mono" style={{ fontSize: 11 }}>{e.loan_id}</td>
                    <td style={{ fontSize: 11 }}>{e.exception_type?.replace(/_/g, ' ')}</td>
                    <td><SeverityBadge severity={e.severity} /></td>
                    <td><StatusBadge status={e.status} /></td>
                    <td><ArrowRight size={12} color="var(--text-muted)" /></td>
                  </tr>
                ))}
                {!data.recent_exceptions?.length && (
                  <tr><td colSpan={5} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: 20 }}>No open exceptions</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* AI panel — exceptions awaiting AI review */}
        <div className="card">
          <div className="card-title" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Bot size={14} color="var(--accent)" /> AI Panel
          </div>
          {(data.ai_pending_review || []).length > 0 ? (
            <>
              <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 12 }}>
                {data.ai_pending_review.length} exception{data.ai_pending_review.length !== 1 ? 's' : ''} have AI recommendations awaiting your decision:
              </div>
              {data.ai_pending_review.map(e => (
                <div
                  key={e.id}
                  className="ai-box"
                  style={{ marginBottom: 8, cursor: 'pointer', padding: 12 }}
                  onClick={() => navigate('/exceptions')}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <span className="font-mono" style={{ fontSize: 11 }}>{e.loan_id}</span>
                      <span style={{ marginLeft: 8, fontSize: 11, color: 'var(--text-muted)' }}>
                        {e.exception_type?.replace(/_/g, ' ')}
                      </span>
                    </div>
                    <SeverityBadge severity={e.severity} />
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--accent)', marginTop: 4 }}>
                    ● AI recommendation ready — click to review
                  </div>
                </div>
              ))}
            </>
          ) : (
            <div className="empty-state" style={{ padding: '24px 0' }}>
              <Bot size={28} />
              <h3>No AI reviews pending</h3>
              <p>Generate AI recommendations in the Exception Queue</p>
            </div>
          )}

          <div className="divider" />

          {/* My recent decisions */}
          <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 8 }}>My Recent Decisions</div>
          {(data.my_recent_decisions || []).length > 0 ? (
            <div className="table-wrap">
              <table>
                <thead><tr><th>Decision</th><th>AI</th><th>Time</th></tr></thead>
                <tbody>
                  {data.my_recent_decisions.slice(0, 6).map(d => (
                    <tr key={d.id}>
                      <td><StatusBadge status={d.decision} /></td>
                      <td style={{ fontSize: 11 }}>
                        {d.ai_followed === true ? '✅' : d.ai_followed === false ? '❌' : '—'}
                      </td>
                      <td style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                        {d.created_at ? new Date(d.created_at).toLocaleDateString() : '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div style={{ fontSize: 12, color: 'var(--text-muted)', textAlign: 'center', padding: 12 }}>No decisions yet</div>
          )}
        </div>
      </div>

      <div style={{ display: 'flex', gap: 12 }}>
        <button className="btn btn-primary" onClick={() => navigate('/exceptions')}>
          <AlertTriangle size={14} /> Exception Queue
        </button>
        <button className="btn btn-secondary" onClick={() => navigate('/ai-assistant')}>
          <Bot size={14} /> AI Assistant
        </button>
        <button className="btn btn-secondary" onClick={() => navigate('/verified-loans')}>
          <CheckCircle size={14} /> Verified Loans
        </button>
      </div>
    </>
  );
}

// ─── Data Consumer ────────────────────────────────────────────────────────────
function ConsumerDashboard({ data, navigate }) {
  const m = data.metrics;

  const downloadCSV = () => {
    const url = exportsAPI.verifiedLoansCSV();
    const a = document.createElement('a');
    a.href = url; a.download = 'verified_loans.csv'; a.click();
  };

  return (
    <>
      <div className="stat-grid mb-4">
        <StatCard label="Total Loans"        value={m.total_loans?.toLocaleString()}    icon={FileText}      color="var(--accent)" />
        <StatCard label="Verified Loans"     value={m.verified_loans?.toLocaleString()} icon={CheckCircle}   color="var(--success)" onClick={() => navigate('/verified-loans')} />
        <StatCard label="Verification Rate"  value={`${m.verification_rate}%`}          icon={TrendingUp}    color="var(--success)" />
        <StatCard
          label="Data Quality Score"
          value={m.data_quality_score != null ? `${m.data_quality_score}%` : '—'}
          icon={ShieldCheck}
          color={m.data_quality_score >= 90 ? 'var(--success)' : m.data_quality_score >= 70 ? 'var(--warning)' : 'var(--danger)'}
        />
        <StatCard label="Open Exceptions"    value={m.open_exceptions}                  icon={AlertTriangle} color="var(--warning)" />
        <StatCard label="Exception Rate"     value={`${m.exception_rate}%`}             icon={AlertTriangle} color="var(--danger)" />
      </div>

      {/* Before → After */}
      {data.before_after && (
        <div className="card mb-4">
          <div className="card-title">Before → After Review</div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 48px 1fr', gap: 16, alignItems: 'center' }}>
            <div style={{ background: 'rgba(239,68,68,.07)', border: '1px solid rgba(239,68,68,.18)', borderRadius: 10, padding: 20 }}>
              <div style={{ fontSize: 12, color: '#f87171', fontWeight: 600, marginBottom: 10, textTransform: 'uppercase', letterSpacing: '.04em' }}>Before</div>
              <div style={{ fontSize: 28, fontWeight: 800 }}>{data.before_after.before.total_records?.toLocaleString()}</div>
              <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 6 }}>Records</div>
              <div style={{ fontSize: 13 }}>{(data.before_after.before.exceptions || 0).toLocaleString()} exceptions</div>
              <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{data.before_after.before.exception_rate}% exception rate</div>
            </div>
            <div style={{ textAlign: 'center', fontSize: 24, color: 'var(--text-muted)' }}>→</div>
            <div style={{ background: 'rgba(16,185,129,.07)', border: '1px solid rgba(16,185,129,.18)', borderRadius: 10, padding: 20 }}>
              <div style={{ fontSize: 12, color: '#34d399', fontWeight: 600, marginBottom: 10, textTransform: 'uppercase', letterSpacing: '.04em' }}>After Review</div>
              <div style={{ fontSize: 28, fontWeight: 800 }}>{data.before_after.after.total_records?.toLocaleString()}</div>
              <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 6 }}>Records</div>
              <div style={{ fontSize: 13 }}>{(data.before_after.after.verified || 0).toLocaleString()} verified</div>
              <div style={{ fontSize: 12, color: '#34d399', fontWeight: 600 }}>
                {data.before_after.after.silent_ai_changes ?? 0} Silent AI Changes
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Quality breakdown with progress bars */}
      {Object.keys(data.quality_breakdown || {}).length > 0 && (
        <div className="card mb-4">
          <div className="card-title">Data Quality Breakdown</div>
          {Object.entries(data.quality_breakdown).map(([cat, score]) => {
            const color = score >= 90 ? 'var(--success)' : score >= 70 ? 'var(--warning)' : 'var(--danger)';
            return (
              <div key={cat} style={{ marginBottom: 12 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4, fontSize: 12 }}>
                  <span>{cat}</span>
                  <span style={{ fontWeight: 600, color }}>{score}%</span>
                </div>
                <div className="progress-bar">
                  <div className="progress-fill" style={{ width: `${score}%`, background: color }} />
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Recent verifications */}
      {(data.recent_verifications || []).length > 0 && (
        <div className="card mb-4">
          <div className="card-title">Recent Verifications</div>
          <div className="table-wrap">
            <table>
              <thead><tr><th>Loan ID</th><th>Verified At</th><th>Hash (preview)</th><th>Integrity</th><th>Exceptions</th></tr></thead>
              <tbody>
                {data.recent_verifications.map(v => (
                  <tr key={v.id} style={{ cursor: 'pointer' }} onClick={() => navigate('/verified-loans')}>
                    <td className="font-mono" style={{ fontSize: 11 }}>{v.loan_id}</td>
                    <td style={{ fontSize: 11, color: 'var(--text-muted)' }}>{v.verified_at ? new Date(v.verified_at).toLocaleString() : '—'}</td>
                    <td><span className="font-mono" style={{ fontSize: 10, color: 'var(--success)' }}>{v.record_hash}</span></td>
                    <td style={{ textAlign: 'center' }}>{v.is_hash_valid ? '✅' : '⚠️'}</td>
                    <td style={{ textAlign: 'center' }}>{v.exception_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Action buttons — export button required by Module G spec */}
      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
        <button className="btn btn-primary" onClick={() => navigate('/verified-loans')}>
          <CheckCircle size={14} /> Verified Records
        </button>
        <button className="btn btn-secondary" onClick={() => navigate('/audit')}>
          <FileText size={14} /> Audit Trail
        </button>
        {/* Direct export button on the Consumer dashboard */}
        <button className="btn btn-secondary" onClick={downloadCSV}>
          <Download size={14} /> Export Verified CSV
        </button>
      </div>
    </>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────
export default function Dashboard() {
  const { roleName, user } = useAuth();
  const [data, setData]    = useState(null);
  const [err, setErr]      = useState(false);
  const navigate           = useNavigate();

  useEffect(() => {
    const fn =
      roleName === 'DATA_OPERATOR' ? dashboardAPI.operator :
      roleName === 'REVIEWER'      ? dashboardAPI.reviewer :
                                     dashboardAPI.consumer;
    fn()
      .then(r => setData(r.data))
      .catch(() => setErr(true));
  }, [roleName]);

  if (!data && !err) {
    return (
      <Layout title="Dashboard">
        <div style={{ display: 'flex', justifyContent: 'center', padding: 60 }}>
          <span className="spinner" />
        </div>
      </Layout>
    );
  }

  if (err || !data) {
    return (
      <Layout title="Dashboard">
        <div className="alert alert-danger">
          Failed to load dashboard data. Please refresh or check your connection.
        </div>
      </Layout>
    );
  }

  const subtitle = {
    DATA_OPERATOR: 'Manage uploads and track validation progress.',
    REVIEWER:      'Review exceptions, accept or reject AI recommendations.',
    DATA_CONSUMER: 'View verified loan records and data quality metrics.',
  }[roleName] || '';

  return (
    <Layout title="Dashboard">
      <div className="page-header">
        <h2>Welcome back, {user?.full_name?.split(' ')[0]}</h2>
        <p>{subtitle}</p>
      </div>

      {roleName === 'DATA_OPERATOR' && <OperatorDashboard data={data} navigate={navigate} />}
      {roleName === 'REVIEWER'      && <ReviewerDashboard data={data} navigate={navigate} />}
      {(roleName === 'DATA_CONSUMER' || (!roleName && data)) && <ConsumerDashboard data={data} navigate={navigate} />}
    </Layout>
  );
}
