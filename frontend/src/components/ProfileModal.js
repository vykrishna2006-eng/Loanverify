import React from 'react';
import { useAuth } from '../context/AuthContext';
import { Shield, Database, Sparkles, X, Check, LogOut } from 'lucide-react';

const ROLE_INFO = {
  DATA_OPERATOR: {
    title: 'Data Operator',
    badgeClass: 'badge-blue',
    desc: 'Ingests loan tapes, runs automated validation engine, and monitors upload health.',
    permissions: ['Upload CSV Tapes', 'Run Automated Validations', 'View Data Quality Score'],
  },
  REVIEWER: {
    title: 'Reviewer',
    badgeClass: 'badge-yellow',
    desc: 'Investigates validation exceptions, leverages Gemini AI Copilot, and approves verified records.',
    permissions: ['Exception Queue Management', 'Gemini AI Review Assistant', 'Submit Approval / Rejection Decisions'],
  },
  DATA_CONSUMER: {
    title: 'Data Consumer',
    badgeClass: 'badge-green',
    desc: 'Inspects clean verified loans, verifies SHA-256 tamper-proof hashes, and exports audit records.',
    permissions: ['View Verified Loan Records', 'Verify SHA-256 Hashes', 'Export Verified CSV & Full Audit Trail'],
  },
};

export default function ProfileModal({ isOpen, onClose }) {
  const { user, roleName, switchRole, logout } = useAuth();

  if (!isOpen || !user) return null;

  const currentRole = roleName || 'DATA_OPERATOR';
  const roleMeta = ROLE_INFO[currentRole] || ROLE_INFO.DATA_OPERATOR;

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(15, 23, 42, 0.5)',
        backdropFilter: 'blur(4px)',
        zIndex: 9999,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 16,
      }}
      onClick={onClose}
    >
      <div
        className="card"
        style={{
          width: '100%',
          maxWidth: 500,
          background: '#ffffff',
          border: '1px solid #e2e8f0',
          borderRadius: 16,
          padding: 24,
          boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.04)',
          position: 'relative',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close button */}
        <button
          onClick={onClose}
          style={{
            position: 'absolute',
            top: 18,
            right: 18,
            background: '#f1f5f9',
            border: 'none',
            borderRadius: 8,
            color: '#64748b',
            cursor: 'pointer',
            padding: 6,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <X size={18} />
        </button>

        {/* Header with Avatar */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 20 }}>
          <div
            style={{
              width: 56,
              height: 56,
              borderRadius: 16,
              background: 'linear-gradient(135deg, #2563eb, #1d4ed8)',
              color: '#fff',
              fontSize: 24,
              fontWeight: 800,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 4px 12px rgba(37, 99, 235, 0.25)',
            }}
          >
            {user.full_name?.[0] || 'U'}
          </div>
          <div>
            <h3 style={{ margin: 0, fontSize: 18, fontWeight: 800, color: '#0f172a' }}>
              {user.full_name}
            </h3>
            <div style={{ color: '#64748b', fontSize: 13, marginTop: 2, fontWeight: 500 }}>{user.email}</div>
          </div>
        </div>

        {/* Active Role Card */}
        <div
          style={{
            background: '#f8fafc',
            border: '1px solid #e2e8f0',
            borderRadius: 12,
            padding: 16,
            marginBottom: 16,
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
            <span style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '.06em', color: '#64748b' }}>
              Active Platform Role
            </span>
            <span className={`badge ${roleMeta.badgeClass}`} style={{ fontSize: 11 }}>
              {roleMeta.title}
            </span>
          </div>
          <p style={{ fontSize: 13, color: '#334155', margin: '0 0 10px 0', lineHeight: 1.4, fontWeight: 500 }}>
            {roleMeta.desc}
          </p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
            {roleMeta.permissions.map((p, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: '#475569', fontWeight: 500 }}>
                <Check size={14} color="#059669" strokeWidth={2.5} />
                <span>{p}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Quick Role Switcher Buttons */}
        <div style={{ marginBottom: 16 }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: '#64748b', textTransform: 'uppercase', letterSpacing: '.06em', marginBottom: 8 }}>
            Switch Role (Instant Demo)
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 8 }}>
            {[
              { id: 'DATA_OPERATOR', label: 'Operator' },
              { id: 'REVIEWER', label: 'Reviewer' },
              { id: 'DATA_CONSUMER', label: 'Consumer' },
            ].map((r) => (
              <button
                key={r.id}
                onClick={() => switchRole(r.id)}
                style={{
                  padding: '8px 6px',
                  borderRadius: 8,
                  fontSize: 12,
                  fontWeight: 700,
                  border: currentRole === r.id ? '1px solid #2563eb' : '1px solid #cbd5e1',
                  background: currentRole === r.id ? '#eff6ff' : '#ffffff',
                  color: currentRole === r.id ? '#1d4ed8' : '#475569',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                  boxShadow: currentRole === r.id ? '0 1px 2px rgba(37, 99, 235, 0.1)' : 'none',
                }}
              >
                {r.label}
              </button>
            ))}
          </div>
        </div>

        {/* System & Architecture Info */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: 8,
            fontSize: 11,
            fontWeight: 600,
            color: '#475569',
            background: '#f8fafc',
            border: '1px solid #e2e8f0',
            padding: 12,
            borderRadius: 8,
            marginBottom: 20,
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <Database size={13} color="#2563eb" />
            <span>Auth: MongoDB</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <Database size={13} color="#059669" />
            <span>Data: PostgreSQL</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <Sparkles size={13} color="#7c3aed" />
            <span>AI: Gemini 2.5</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <Shield size={13} color="#d97706" />
            <span>Integrity: SHA-256</span>
          </div>
        </div>

        {/* Footer Actions */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <button className="btn btn-secondary btn-sm" onClick={onClose}>
            Close
          </button>
          <button
            className="btn btn-danger btn-sm"
            onClick={() => {
              onClose();
              logout();
            }}
          >
            <LogOut size={13} />
            Sign Out
          </button>
        </div>
      </div>
    </div>
  );
}
