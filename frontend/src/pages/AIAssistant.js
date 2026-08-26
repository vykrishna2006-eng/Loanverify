import React, { useState } from 'react';
import Layout from '../components/Layout';
import { aiAPI, rulesAPI } from '../api/client';
import toast from 'react-hot-toast';
import {
  Bot, Scale, FileText, List, Lightbulb,
  CheckCircle, XCircle, Wrench, ShieldCheck,
} from 'lucide-react';

// ── Shared collapsible card ────────────────────────────────────────────────
function FeatureCard({ icon: Icon, title, description, color = 'var(--accent)', badge, children }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="card" style={{ marginBottom: 14 }}>
      <div
        style={{ display: 'flex', alignItems: 'flex-start', gap: 12, cursor: 'pointer' }}
        onClick={() => setOpen(o => !o)}
      >
        <div style={{
          width: 38, height: 38, borderRadius: 8, flexShrink: 0,
          background: `${color}20`, display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <Icon size={18} color={color} />
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ fontWeight: 600 }}>{title}</span>
            {badge && <span className="badge badge-blue">{badge}</span>}
          </div>
          <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>{description}</div>
        </div>
        <span style={{ color: 'var(--text-muted)', fontSize: 16 }}>{open ? '▲' : '▼'}</span>
      </div>
      {open && (
        <div style={{ marginTop: 16, paddingTop: 16, borderTop: '1px solid var(--border)' }}>
          {children}
        </div>
      )}
    </div>
  );
}

// ── Shared exception ID input ──────────────────────────────────────────────
function ExcInput({ value, onChange, placeholder = 'Exception ID (UUID)' }) {
  return (
    <input
      className="form-input"
      style={{ flex: 1 }}
      placeholder={placeholder}
      value={value}
      onChange={e => onChange(e.target.value)}
    />
  );
}

// ── AI result box ─────────────────────────────────────────────────────────
function AIBox({ header, children }) {
  return (
    <div className="ai-box">
      <div className="ai-box-header"><Bot size={14} /> {header}</div>
      {children}
      <div className="ai-safety-note">
        ⚠️ AI RECOMMENDATION ONLY — no data changes until a human accepts, edits, or rejects.
      </div>
    </div>
  );
}

// ── Feature 1: Explain Exception ──────────────────────────────────────────
function Feature1() {
  const [id, setId]       = useState('');
  const [res, setRes]     = useState(null);
  const [loading, setLoading] = useState(false);

  const run = async () => {
    if (!id.trim()) { toast.error('Enter an Exception ID'); return; }
    setLoading(true);
    try {
      const r = await aiAPI.getRecommendation(id.trim());
      setRes(r.data);
    } catch (e) {
      toast.error(e.response?.data?.detail || 'No recommendation — generate one in the Exception Queue first');
    }
    setLoading(false);
  };

  return (
    <div>
      <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
        <ExcInput value={id} onChange={setId} />
        <button className="btn btn-primary" onClick={run} disabled={loading}>
          {loading ? <span className="spinner" /> : 'Explain'}
        </button>
      </div>
      {res && (
        <AIBox header="Exception Explanation">
          <p style={{ fontSize: 13, lineHeight: 1.7, marginBottom: 10 }}>{res.explanation}</p>
          {res.suggested_value && (
            <div style={{ fontSize: 12, marginBottom: 6 }}>
              <span style={{ color: 'var(--text-muted)' }}>Suggested value: </span>
              <span style={{ color: 'var(--success)', fontWeight: 600 }}>{res.suggested_value}</span>
            </div>
          )}
          {res.confidence_score != null && (
            <div style={{ fontSize: 12, marginBottom: 6 }}>
              <span style={{ color: 'var(--text-muted)' }}>Confidence: </span>
              <span style={{ fontWeight: 600 }}>{parseFloat(res.confidence_score).toFixed(1)}%</span>
            </div>
          )}
          {res.model_used && (
            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>
              Model: {res.model_used} · Tokens: {res.prompt_tokens ?? '—'} prompt / {res.completion_tokens ?? '—'} completion
            </div>
          )}
        </AIBox>
      )}
    </div>
  );
}

// ── Feature 2: Suggest Correction ────────────────────────────────────────
function Feature2() {
  const [id, setId]       = useState('');
  const [res, setRes]     = useState(null);
  const [loading, setLoading] = useState(false);

  const run = async () => {
    if (!id.trim()) { toast.error('Enter an Exception ID'); return; }
    setLoading(true);
    try {
      const r = await aiAPI.suggestCorrection(id.trim());
      setRes(r.data);
    } catch (e) {
      toast.error(e.response?.data?.detail || 'No suggestion — generate AI review in Exception Queue first');
    }
    setLoading(false);
  };

  return (
    <div>
      <p style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 12 }}>
        Retrieve the AI's suggested corrected value for an exception. To generate a fresh suggestion,
        use <strong>Generate AI Recommendation</strong> in the Exception Queue first.
      </p>
      <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
        <ExcInput value={id} onChange={setId} />
        <button className="btn btn-primary" onClick={run} disabled={loading}>
          {loading ? <span className="spinner" /> : 'Get Suggestion'}
        </button>
      </div>
      {res && (
        <AIBox header="Suggested Correction">
          {res.suggested_value ? (
            <>
              <div style={{ marginBottom: 10 }}>
                <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 4 }}>Corrected Value</div>
                <div style={{
                  fontSize: 20, fontWeight: 700, color: 'var(--success)',
                  background: 'rgba(16,185,129,.08)', border: '1px solid rgba(16,185,129,.2)',
                  borderRadius: 8, padding: '10px 16px', display: 'inline-block',
                }}>
                  {res.suggested_value}
                </div>
              </div>
              <div style={{ fontSize: 12, marginBottom: 6 }}>
                <span style={{ color: 'var(--text-muted)' }}>Suggested action: </span>
                <span className="badge badge-blue">{res.suggested_action?.replace(/_/g, ' ')}</span>
              </div>
              <div style={{ fontSize: 12 }}>
                <span style={{ color: 'var(--text-muted)' }}>Confidence: </span>
                <span style={{ fontWeight: 600 }}>{res.confidence_score ? `${parseFloat(res.confidence_score).toFixed(1)}%` : '—'}</span>
              </div>
            </>
          ) : (
            <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>
              No specific corrected value suggested for this exception type. {res.suggested_action?.replace(/_/g, ' ')} is recommended.
            </p>
          )}
          {res.explanation && (
            <div style={{ marginTop: 10, padding: '8px 12px', background: 'var(--bg-primary)', borderRadius: 6, fontSize: 12, color: 'var(--text-secondary)', fontStyle: 'italic' }}>
              "{res.explanation}"
            </div>
          )}
        </AIBox>
      )}
    </div>
  );
}

// ── Feature 3: Compare Sources ────────────────────────────────────────────
function Feature3() {
  const [id, setId]       = useState('');
  const [res, setRes]     = useState(null);
  const [loading, setLoading] = useState(false);

  const run = async () => {
    if (!id.trim()) { toast.error('Enter an Exception ID'); return; }
    setLoading(true);
    try {
      const r = await aiAPI.compareSources(id.trim());
      setRes(r.data);
    } catch (e) { toast.error(e.response?.data?.detail || 'Error comparing sources'); }
    setLoading(false);
  };

  return (
    <div>
      <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
        <ExcInput value={id} onChange={setId} />
        <button className="btn btn-primary" onClick={run} disabled={loading}>
          {loading ? <span className="spinner" /> : 'Compare'}
        </button>
      </div>
      {res && (
        <AIBox header="Source Comparison">
          <table className="compare-table" style={{ marginBottom: 12 }}>
            <thead>
              <tr>
                <th>Field</th>
                <th>{res.comparison?.source_a?.name || 'Loan Tape'}</th>
                <th>{res.comparison?.source_b?.name || 'Servicer Update'}</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>{res.field || '—'}</td>
                <td className={res.comparison?.preferred_source === 'TAPE' ? 'preferred' : ''}>
                  {res.comparison?.source_a?.value || '—'}
                  {res.comparison?.source_a?.updated_date && (
                    <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>
                      Updated: {res.comparison.source_a.updated_date}
                    </div>
                  )}
                </td>
                <td className={res.comparison?.preferred_source === 'SERVICER' ? 'preferred' : ''}>
                  {res.comparison?.source_b?.value || '—'}
                  {res.comparison?.source_b?.updated_date && (
                    <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>
                      Updated: {res.comparison.source_b.updated_date}
                    </div>
                  )}
                </td>
              </tr>
            </tbody>
          </table>
          <div style={{ fontSize: 13, fontWeight: 500 }}>
            <span style={{ color: 'var(--text-muted)' }}>AI Recommendation: </span>
            <span style={{ color: 'var(--accent)' }}>{res.comparison?.recommendation}</span>
          </div>
          <div style={{ marginTop: 8, fontSize: 12 }}>
            <span style={{ color: 'var(--text-muted)' }}>Prefer: </span>
            <span className="badge badge-blue">{res.comparison?.preferred_source}</span>
          </div>
        </AIBox>
      )}
    </div>
  );
}

// ── Feature 4: Generate Reviewer Note ────────────────────────────────────
function Feature4() {
  const [id, setId]       = useState('');
  const [res, setRes]     = useState(null);
  const [loading, setLoading] = useState(false);
  const [copied, setCopied]   = useState(false);

  const run = async () => {
    if (!id.trim()) { toast.error('Enter an Exception ID'); return; }
    setLoading(true);
    try {
      const r = await aiAPI.generateNote(id.trim());
      setRes(r.data);
      setCopied(false);
    } catch (e) { toast.error('Error generating note'); }
    setLoading(false);
  };

  const copyNote = () => {
    navigator.clipboard.writeText(res.generated_note || '');
    setCopied(true);
    toast.success('Note copied to clipboard');
  };

  return (
    <div>
      <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
        <ExcInput value={id} onChange={setId} />
        <button className="btn btn-primary" onClick={run} disabled={loading}>
          {loading ? <span className="spinner" /> : 'Generate Note'}
        </button>
      </div>
      {res && (
        <AIBox header="Generated Reviewer Note">
          <p style={{ fontStyle: 'italic', color: 'var(--text-secondary)', fontSize: 13, lineHeight: 1.7, marginBottom: 12 }}>
            "{res.generated_note}"
          </p>
          <button className="btn btn-secondary btn-sm" onClick={copyNote}>
            {copied ? '✅ Copied' : '📋 Copy to clipboard'}
          </button>
        </AIBox>
      )}
    </div>
  );
}

// ── Feature 5: Classify Severity ─────────────────────────────────────────
function Feature5() {
  const [id, setId]       = useState('');
  const [res, setRes]     = useState(null);
  const [loading, setLoading] = useState(false);

  const run = async () => {
    if (!id.trim()) { toast.error('Enter an Exception ID'); return; }
    setLoading(true);
    try {
      const r = await aiAPI.classifySeverity(id.trim());
      setRes(r.data);
    } catch (e) { toast.error(e.response?.data?.detail || 'Error classifying severity'); }
    setLoading(false);
  };

  const sevColor = { HIGH: 'var(--danger)', MEDIUM: 'var(--warning)', LOW: 'var(--success)' };

  return (
    <div>
      <p style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 12 }}>
        AI explains why this exception has its current severity level and whether the classification is appropriate.
      </p>
      <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
        <ExcInput value={id} onChange={setId} />
        <button className="btn btn-primary" onClick={run} disabled={loading}>
          {loading ? <span className="spinner" /> : 'Classify'}
        </button>
      </div>
      {res && (
        <AIBox header="Severity Classification">
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
            <div style={{
              fontSize: 28, fontWeight: 800,
              color: sevColor[res.severity] || 'var(--text-primary)',
            }}>
              {res.severity}
            </div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
              {res.exception_type?.replace(/_/g, ' ')}
            </div>
          </div>
          <div style={{
            background: 'var(--bg-primary)', borderRadius: 8, padding: '12px 14px',
            fontSize: 13, lineHeight: 1.7, color: 'var(--text-secondary)',
          }}>
            {res.reason}
          </div>
          {res.loan_id && (
            <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 8 }}>
              Loan: <span className="font-mono">{res.loan_id}</span>
            </div>
          )}
        </AIBox>
      )}
    </div>
  );
}

// ── Feature 6: Batch Summary ──────────────────────────────────────────────
function Feature6() {
  const [uploadId, setUploadId] = useState('');
  const [res, setRes]           = useState(null);
  const [loading, setLoading]   = useState(false);

  const run = async () => {
    if (!uploadId.trim()) { toast.error('Enter an Upload ID'); return; }
    setLoading(true);
    try {
      const r = await aiAPI.batchSummary(uploadId.trim());
      setRes(r.data);
    } catch (e) { toast.error('Error generating batch summary'); }
    setLoading(false);
  };

  return (
    <div>
      <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
        <input
          className="form-input"
          style={{ flex: 1 }}
          placeholder="Upload ID (UUID) — find in the Uploads page"
          value={uploadId}
          onChange={e => setUploadId(e.target.value)}
        />
        <button className="btn btn-primary" onClick={run} disabled={loading}>
          {loading ? <span className="spinner" /> : 'Summarise'}
        </button>
      </div>
      {res && (
        <AIBox header="Batch Exception Summary">
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 12, marginBottom: 16, textAlign: 'center' }}>
            {[
              { label: 'High', val: res.high_severity, color: 'var(--danger)' },
              { label: 'Medium', val: res.medium_severity, color: 'var(--warning)' },
              { label: 'Low', val: res.low_severity, color: 'var(--success)' },
            ].map(({ label, val, color }) => (
              <div key={label} style={{ background: 'var(--bg-primary)', borderRadius: 8, padding: 12 }}>
                <div style={{ fontSize: 24, fontWeight: 700, color }}>{val}</div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{label}</div>
              </div>
            ))}
          </div>
          <p style={{ fontSize: 13, lineHeight: 1.7, marginBottom: 12 }}>{res.summary_text}</p>
          {res.recommendations?.length > 0 && (
            <>
              <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 6 }}>Recommendations:</div>
              {res.recommendations.map((r, i) => (
                <div key={i} style={{ display: 'flex', gap: 6, fontSize: 12, marginBottom: 4 }}>
                  <span style={{ color: 'var(--accent)' }}>→</span> {r}
                </div>
              ))}
            </>
          )}
        </AIBox>
      )}
    </div>
  );
}

// ── Feature 7: NL → Rule Generation (with backend activation) ─────────────
function Feature7() {
  const [desc, setDesc]           = useState('');
  const [res, setRes]             = useState(null);
  const [loading, setLoading]     = useState(false);
  const [activating, setActivating] = useState(false);
  const [activated, setActivated] = useState(false);
  const [rejected, setRejected]   = useState(false);

  const generate = async () => {
    if (!desc.trim()) { toast.error('Describe a rule'); return; }
    setLoading(true);
    setActivated(false); setRejected(false); setRes(null);
    try {
      const r = await aiAPI.generateRule(desc.trim());
      setRes(r.data);
    } catch (e) { toast.error('Error generating rule'); }
    setLoading(false);
  };

  // Feature 7 critical: Activate calls the backend — NOT a frontend-only mock
  const activateRule = async () => {
    if (!res) return;
    setActivating(true);
    try {
      await rulesAPI.activateAiRule(
        res.rule_name,
        res.description,
        res.rule_expression,
        res.suggested_severity,
      );
      setActivated(true);
      toast.success('Rule saved and activated after human review!');
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to activate rule');
    }
    setActivating(false);
  };

  const rejectRule = () => {
    setRejected(true);
    setRes(null);
    toast('Rule rejected — not saved', { icon: '🗑️' });
  };

  return (
    <div>
      <p style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 12 }}>
        Describe a validation rule in plain English. AI generates the expression.
        The rule is <strong>not active</strong> until you explicitly activate it.
      </p>
      <div className="form-group">
        <label className="form-label">Rule Description</label>
        <textarea
          className="form-input"
          rows={2}
          placeholder="e.g. Flag loans where the balance is more than 90% of the original principal"
          value={desc}
          onChange={e => setDesc(e.target.value)}
        />
      </div>
      <button className="btn btn-primary" onClick={generate} disabled={loading}>
        {loading ? <span className="spinner" /> : 'Generate Rule'}
      </button>

      {res && !activated && !rejected && (
        <div className="ai-box" style={{ marginTop: 16 }}>
          <div className="ai-box-header">
            <Lightbulb size={14} /> Generated Rule
            <span className="badge badge-medium" style={{ marginLeft: 8 }}>PENDING HUMAN REVIEW</span>
          </div>

          <div className="form-group">
            <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 4 }}>Rule Name</div>
            <div style={{ fontWeight: 600 }}>{res.rule_name}</div>
          </div>

          <div className="form-group">
            <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 4 }}>Expression</div>
            <div className="hash-display" style={{ color: 'var(--accent)' }}>{res.rule_expression}</div>
          </div>

          <div style={{ fontSize: 13, marginBottom: 10 }}>{res.explanation}</div>

          <div style={{ display: 'flex', gap: 12, alignItems: 'center', marginBottom: 12 }}>
            <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>Suggested severity:</span>
            <span className={`badge badge-${res.suggested_severity?.toLowerCase()}`}>
              {res.suggested_severity}
            </span>
          </div>

          <div className="ai-safety-note" style={{ marginBottom: 12 }}>
            ⚠️ This rule is <strong>NOT active</strong>. It will only apply to future validation runs
            after you explicitly click Activate below.
          </div>

          <div style={{ display: 'flex', gap: 10 }}>
            <button className="btn btn-success" onClick={activateRule} disabled={activating}>
              {activating ? <span className="spinner" /> : '✅ Activate Rule'}
            </button>
            <button className="btn btn-danger" onClick={rejectRule}>
              ❌ Reject
            </button>
          </div>
        </div>
      )}

      {activated && (
        <div className="alert alert-success" style={{ marginTop: 12 }}>
          <CheckCircle size={14} style={{ display: 'inline', marginRight: 6 }} />
          Rule <strong>"{res?.rule_name}"</strong> activated after human review. It will apply to the next validation run.
        </div>
      )}
      {rejected && (
        <div className="alert alert-warning" style={{ marginTop: 12 }}>
          Rule rejected — not saved to the system.
        </div>
      )}
    </div>
  );
}

// ── Page ─────────────────────────────────────────────────────────────────────
export default function AIAssistant() {
  return (
    <Layout title="AI Assistant — Module D">
      <div className="page-header">
        <h2>AI Review Assistant</h2>
        <p>7 AI-powered features — all outputs are recommendations only. Humans make every final decision.</p>
      </div>

      <div className="alert alert-warning" style={{ marginBottom: 20 }}>
        <strong>AI Safety (Section 9):</strong> AI recommendations are never applied directly to the database.
        Every suggestion requires explicit human Accept, Edit, or Reject before any data changes.
        <span style={{ marginLeft: 8, fontSize: 11 }}>silent_ai_changes = 0</span>
      </div>

      <FeatureCard icon={Bot}        title="Feature 1 — Explain Exception"   description="Why did this record fail validation? Plain-English explanation."          color="var(--accent)"  badge="Explain">   <Feature1 /> </FeatureCard>
      <FeatureCard icon={Wrench}     title="Feature 2 — Suggest Correction"  description="AI recommends a specific corrected value for the failing field."          color="var(--success)" badge="Suggest">   <Feature2 /> </FeatureCard>
      <FeatureCard icon={Scale}      title="Feature 3 — Compare Sources"     description="Side-by-side: loan tape vs servicer update — which value to trust?"       color="var(--info)"    badge="Compare">   <Feature3 /> </FeatureCard>
      <FeatureCard icon={FileText}   title="Feature 4 — Generate Note"       description="AI drafts a professional reviewer note for the audit trail."              color="#10b981"        badge="Draft Note"> <Feature4 /> </FeatureCard>
      <FeatureCard icon={ShieldCheck} title="Feature 5 — Classify Severity"  description="AI explains why this exception has its severity rating."                  color="var(--warning)" badge="Severity">  <Feature5 /> </FeatureCard>
      <FeatureCard icon={List}       title="Feature 6 — Batch Summary"       description="Natural-language summary of all exceptions across an entire upload."       color="#f59e0b"        badge="Summarise"> <Feature6 /> </FeatureCard>
      <FeatureCard icon={Lightbulb}  title="Feature 7 — Generate Rule"       description="Describe a validation rule in plain English — AI generates the expression." color="#a78bfa"     badge="NL → Rule"> <Feature7 /> </FeatureCard>
    </Layout>
  );
}
