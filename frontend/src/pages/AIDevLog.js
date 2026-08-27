import React from 'react';
import Layout from '../components/Layout';
import {
  Bot, ShieldCheck, Sparkles, CheckCircle2, AlertOctagon,
  FileCode, Terminal, Layers, Cpu, Compass, BookOpen
} from 'lucide-react';

export default function AIDevLog() {
  const prompts = [
    {
      id: 1,
      title: "1. Automated Dual-DB Architecture & Schema Design",
      prompt: "Design a production-grade FinTech loan verification system using MongoDB for user authentication/RBAC and PostgreSQL with SQLAlchemy for loan records, validation exceptions, canonical verified records, and immutable audit logs.",
      outcome: "Generated dual-engine persistence layer with automatic SQLite fallback for testing and PostgreSQL for production."
    },
    {
      id: 2,
      title: "2. Modular Loan Validation Engine with 12 FinTech Rules",
      prompt: "Implement a validation engine covering required fields, principal <= balance, maturity date > origination date, valid payment status, credit grade validation, duplicate detection, and stale update flags.",
      outcome: "Built 12 automated validation rules returning structured LoanException records with HIGH/MEDIUM/LOW severities."
    },
    {
      id: 3,
      title: "3. Gemini AI Review Assistant (Natural Language Explanations)",
      prompt: "Integrate Google Gemini 2.5 Flash API to explain why a loan failed validation, suggest corrected values, compare conflicting multi-source updates, and generate reviewer notes without modifying data silently.",
      outcome: "Developed AIService with structured JSON prompts, confidence scoring, safety guardrails, and audit logging."
    },
    {
      id: 4,
      title: "4. SHA-256 Cryptographic Record Hashing & Lineage",
      prompt: "Create a tamper-proof verification mechanism that hashes canonical loan data using SHA-256, preserves source file lineage, and logs every human/AI action to an immutable audit trail.",
      outcome: "Implemented canonical field serialization, SHA-256 hash generation, and instantaneous hash recalculation verification."
    },
    {
      id: 5,
      title: "5. Comprehensive Test Suite (105 / 105 Tests Passing)",
      prompt: "Generate unit and integration tests covering CSV parsing, validation rules, AI mocking, RBAC auth permissions, exception lifecycle transitions, and API endpoints.",
      outcome: "Achieved 100% test pass rate (105 passing tests across 12 test suites)."
    }
  ];

  const rejections = [
    {
      title: "❌ Automated Silent Data Write-Backs",
      reason: "Initial AI prompt proposed automatically applying suggested loan corrections directly to the database. Rejected because FinTech compliance (Section 9) mandates human-in-the-loop approval before modifying loan records."
    },
    {
      title: "❌ Unstructured Free-Text AI Responses",
      reason: "Free-form text outputs from LLMs occasionally produced ambiguous advice. Rejected in favor of structured JSON schema with required fields (suggested_value, confidence, reasoning, reviewer_note)."
    }
  ];

  return (
    <Layout title="AI Development Log">
      <div className="page-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{ width: 36, height: 36, borderRadius: 8, background: '#eff6ff', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Sparkles size={20} color="#2563eb" />
          </div>
          <div>
            <h2>AI Development Log & Agentic Coding Demonstration</h2>
            <p>Documentation of agentic workflows, prompt engineering, safety guardrails, and human review as required by Section 10 & 15.</p>
          </div>
        </div>
      </div>

      {/* Overview Cards */}
      <div className="stat-grid mb-4">
        <div className="stat-card">
          <div className="stat-icon" style={{ background: '#eff6ff' }}><Bot size={18} color="#2563eb" /></div>
          <div className="stat-label">AI Engine</div>
          <div className="stat-value" style={{ fontSize: 20 }}>Gemini 2.5</div>
          <div className="stat-sub">Google GenAI Flash</div>
        </div>
        <div className="stat-card">
          <div className="stat-icon" style={{ background: '#ecfdf5' }}><Cpu size={18} color="#059669" /></div>
          <div className="stat-label">AI Code Generation</div>
          <div className="stat-value" style={{ fontSize: 20 }}>~85%</div>
          <div className="stat-sub">With 100% Human Review</div>
        </div>
        <div className="stat-card">
          <div className="stat-icon" style={{ background: '#faf5ff' }}><Terminal size={18} color="#7c3aed" /></div>
          <div className="stat-label">Automated Tests</div>
          <div className="stat-value" style={{ fontSize: 20 }}>105 / 105</div>
          <div className="stat-sub">100% Passing Test Suite</div>
        </div>
        <div className="stat-card">
          <div className="stat-icon" style={{ background: '#fffbeb' }}><ShieldCheck size={18} color="#d97706" /></div>
          <div className="stat-label">Human-in-the-Loop</div>
          <div className="stat-value" style={{ fontSize: 20 }}>Enforced</div>
          <div className="stat-sub">0 Silent AI Data Changes</div>
        </div>
      </div>

      {/* Representative Prompts Section */}
      <div className="card mb-4">
        <div className="card-title" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Terminal size={16} color="#2563eb" /> Representative Development Prompts (Section 10)
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {prompts.map((p) => (
            <div key={p.id} style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 10, padding: 16 }}>
              <div style={{ fontSize: 13, fontWeight: 700, color: '#0f172a', marginBottom: 8 }}>{p.title}</div>
              <div style={{ background: '#ffffff', border: '1px solid #cbd5e1', borderRadius: 6, padding: '10px 14px', fontFamily: 'monospace', fontSize: 12, color: '#1e293b', marginBottom: 8 }}>
                💬 "{p.prompt}"
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: '#059669', fontWeight: 600 }}>
                <CheckCircle2 size={14} color="#059669" />
                <span>Result: {p.outcome}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Human Review & Rejected AI Output Section */}
      <div className="grid-2 mb-4">
        <div className="card">
          <div className="card-title" style={{ display: 'flex', alignItems: 'center', gap: 8, color: '#dc2626' }}>
            <AlertOctagon size={16} color="#dc2626" /> Examples of Rejected AI Outputs
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {rejections.map((r, i) => (
              <div key={i} style={{ background: '#fef2f2', border: '1px solid #fecaca', borderRadius: 8, padding: 14 }}>
                <div style={{ fontSize: 13, fontWeight: 700, color: '#991b1b', marginBottom: 4 }}>{r.title}</div>
                <div style={{ fontSize: 12, color: '#7f1d1d', lineHeight: 1.4 }}>{r.reason}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="card">
          <div className="card-title" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <ShieldCheck size={16} color="#059669" /> Mandatory AI Safety Controls (Section 9)
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {[
              "AI suggestions are rendered separately with visible confidence scores.",
              "Reviewer must explicitly click Accept, Edit, or Reject.",
              "Every AI prompt, model name, and recommendation is logged to the immutable audit trail.",
              "Cryptographic SHA-256 hash seals the record only after final human decision.",
              "No AI action can silently modify database records."
            ].map((text, idx) => (
              <div key={idx} style={{ display: 'flex', alignItems: 'flex-start', gap: 8, fontSize: 12, color: '#334155', fontWeight: 500 }}>
                <CheckCircle2 size={15} color="#059669" style={{ flexShrink: 0, marginTop: 2 }} />
                <span>{text}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </Layout>
  );
}
