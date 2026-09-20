import React from 'react';
import Layout from '../components/Layout';
import { Bot, CheckCircle, XCircle, BookOpen } from 'lucide-react';

export default function AIDevLog() {
  return (
    <Layout title="AI Development Log">
      <div className="page-header">
        <h2>AI Development Log</h2>
        <p>Required deliverable — demonstrates how AI was used during development of LoanVerify AI.</p>
      </div>

      <div className="card" style={{ marginBottom: 16 }}>
        <div className="card-title">Tools Used</div>
        {[
          { tool: 'Kiro (Claude-based agentic IDE)', use: 'Primary — architecture, code generation, debugging, documentation' },
          { tool: 'OpenAI GPT-4o', use: 'In-app AI features — exception explanation, rule generation, source comparison' },
          { tool: 'GitHub Copilot', use: 'Inline autocomplete for repetitive patterns' },
        ].map(({ tool, use }) => (
          <div key={tool} style={{ display: 'flex', gap: 12, padding: '10px 14px', background: 'var(--bg-hover)', borderRadius: 8, marginBottom: 8 }}>
            <Bot size={16} color="var(--accent)" style={{ flexShrink: 0, marginTop: 2 }} />
            <div>
              <div style={{ fontWeight: 600, fontSize: 13 }}>{tool}</div>
              <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>{use}</div>
            </div>
          </div>
        ))}
      </div>

      <div className="card" style={{ marginBottom: 16 }}>
        <div className="card-title">AI Use Cases During Development</div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
          {[
            'Database schema design (14-table PostgreSQL)',
            'API endpoint design (Module H spec)',
            'Validation rule engine (18 rules)',
            'AI service with 7 features',
            'React component generation',
            'Unit + integration test generation (76 tests)',
            'Debugging (metadata reserved word, SQLite compat)',
            'Documentation generation',
          ].map(item => (
            <div key={item} style={{ display: 'flex', gap: 8, alignItems: 'center', fontSize: 13 }}>
              <CheckCircle size={13} color="var(--success)" />
              {item}
            </div>
          ))}
        </div>
      </div>

      <div className="card" style={{ marginBottom: 16 }}>
        <div className="card-title">Estimated AI-Generated Code — ~76% overall</div>
        {[
          { layer: 'Database schema (SQL)', pct: 85 },
          { layer: 'SQLAlchemy models', pct: 80 },
          { layer: 'FastAPI routers', pct: 75 },
          { layer: 'Service layer', pct: 70 },
          { layer: 'Validation rules', pct: 80 },
          { layer: 'React components', pct: 80 },
          { layer: 'Unit tests', pct: 70 },
        ].map(({ layer, pct }) => (
          <div key={layer} style={{ marginBottom: 10 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 4 }}>
              <span>{layer}</span>
              <span style={{ fontWeight: 600, color: 'var(--accent)' }}>{pct}%</span>
            </div>
            <div className="progress-bar">
              <div className="progress-fill" style={{ width: `${pct}%` }} />
            </div>
          </div>
        ))}
      </div>

      <div className="card" style={{ marginBottom: 16 }}>
        <div className="card-title">Rejected AI Outputs</div>
        {[
          {
            title: 'Rejection 1 — AI rule auto-activation',
            output: 'AI returned { "status": "ACTIVE", "is_active": true } for generated rules',
            reason: 'Violated Section 9: AI must not silently change data.',
            fix: 'Status always PENDING_REVIEW. Human must explicitly activate.',
          },
          {
            title: 'Rejection 2 — Direct AI-to-database writes',
            output: 'AI wrote corrected_value to loan record if confidence > 80%',
            reason: 'Core safety violation — only humans can modify the database.',
            fix: 'AI output stored in ai_recommendations only. Human submits ReviewDecision first.',
          },
          {
            title: 'Rejection 3 — Loading all records into browser',
            output: 'fetch(\'/api/loans?page_size=10000\')',
            reason: 'Crashes browser tab on large datasets.',
            fix: 'Server-side pagination on every list endpoint.',
          },
        ].map(({ title, output, reason, fix }) => (
          <div key={title} style={{ border: '1px solid var(--border)', borderRadius: 8, padding: 14, marginBottom: 10 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontWeight: 600, marginBottom: 8 }}>
              <XCircle size={14} color="var(--danger)" />{title}
            </div>
            <div style={{ fontSize: 12, marginBottom: 4 }}>
              <span style={{ color: 'var(--text-muted)' }}>AI Output: </span>
              <span style={{ color: 'var(--danger)' }}>{output}</span>
            </div>
            <div style={{ fontSize: 12, marginBottom: 4 }}>
              <span style={{ color: 'var(--text-muted)' }}>Why Rejected: </span>{reason}
            </div>
            <div style={{ fontSize: 12 }}>
              <span style={{ color: 'var(--text-muted)' }}>Fix: </span>
              <span style={{ color: 'var(--success)' }}>{fix}</span>
            </div>
          </div>
        ))}
      </div>

      <div className="card">
        <div className="card-title">Lessons Learned</div>
        <div style={{ fontWeight: 600, fontSize: 13, color: 'var(--success)', marginBottom: 8 }}>
          Where AI Helped Most
        </div>
        {[
          'Boilerplate elimination — models, schemas, router stubs 3x faster',
          'Test coverage — 76 test cases generated in minutes',
          'CSS design system — consistent dark FinTech theme from one prompt',
          'Dataset generation — 10,000-row loan tape with exact error distribution',
        ].map(i => (
          <div key={i} style={{ display: 'flex', gap: 8, fontSize: 13, marginBottom: 6 }}>
            <CheckCircle size={13} color="var(--success)" style={{ flexShrink: 0, marginTop: 2 }} />{i}
          </div>
        ))}
        <div style={{ fontWeight: 600, fontSize: 13, color: 'var(--warning)', marginTop: 12, marginBottom: 8 }}>
          Where Human Judgment Was Critical
        </div>
        {[
          'AI safety architecture — human-in-the-loop required deliberate design',
          'Reserved word conflicts — metadata in SQLAlchemy, Exception as Python built-in',
          'Cross-database compatibility — SQLite tests + PostgreSQL production',
          'Transaction boundaries — flush() vs commit() for audit trail consistency',
          'Security review — verifying every endpoint has correct auth dependency',
        ].map(i => (
          <div key={i} style={{ display: 'flex', gap: 8, fontSize: 13, marginBottom: 6 }}>
            <BookOpen size={13} color="var(--warning)" style={{ flexShrink: 0, marginTop: 2 }} />{i}
          </div>
        ))}
      </div>
    </Layout>
  );
}
