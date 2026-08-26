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
        backgroundColor: 'rgba(0, 0, 0, 0.75)',
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
          background: '#0f172a',
          border: '1px solid #334155',
          borderRadius: 16,
          padding: 24,
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)',
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
            background: 'rgba(255,255,255,0.06)',
            border: 'none',
            borderRadius: 8,
            color: '#94a3b8',
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
              background: 'linear-gradient(135deg, #3b82f6, #1d4ed8)',
              color: '#fff',
              fontSize: 24,
              fontWeight: 700,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 0 20px rgba(59, 130, 246, 0.3)',
            }}
          >
            {user.full_name?.[0] || 'U'}
          </div>
          <div>
            <h3 style={{ margin: 0, fontSize: 18, fontWeight: 700, color: '#f8fafc' }}>
              {user.full_name}
            </h3>
            <div style={{ color: '#94a3b8', fontSize: 13, marginTop: 2 }}>{user.email}</div>
          </div>
        </div>

        {/* Active Role Card */}
        <div
          style={{
            background: 'rgba(30, 41, 59, 0.7)',
            border: '1px solid rgba(51, 65, 85, 0.8)',
            borderRadius: 12,
            padding: 16,
            marginBottom: 16,
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
            <span style={{ fontSize: 11, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '.06em', color: '#94a3b8' }}>
              Active Platform Role
            </span>
            <span className={`badge ${roleMeta.badgeClass}`} style={{ fontSize: 11 }}>
              {roleMeta.title}
            </span>
          </div>
          <p style={{ fontSize: 13, color: '#cbd5e1', margin: '0 0 10px 0', lineHeight: 1.4 }}>
            {roleMeta.desc}
          </p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            {roleMeta.permissions.map((p, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: '#94a3b8' }}>
                <Check size={13} color="#10b981" />
                <span>{p}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Quick Role Switcher Buttons */}
        <div style={{ marginBottom: 16 }}>
          <div style={{ fontSize: 11, fontWeight: 600, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '.06em', marginBottom: 8 }}>
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
                  fontWeight: 600,
                  border: currentRole === r.id ? '1px solid #3b82f6' : '1px solid #334155',
                  background: currentRole === r.id ? 'rgba(59, 130, 246, 0.15)' : 'rgba(255,255,255,0.03)',
                  color: currentRole === r.id ? '#60a5fa' : '#94a3b8',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
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
            color: '#64748b',
            background: 'rgba(15, 23, 42, 0.6)',
            padding: 12,
            borderRadius: 8,
            marginBottom: 20,
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <Database size={13} color="#3b82f6" />
            <span>Auth: MongoDB</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <Database size={13} color="#10b981" />
            <span>Data: PostgreSQL</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <Sparkles size={13} color="#8b5cf6" />
            <span>AI: Gemini 2.5</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <Shield size={13} color="#f59e0b" />
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
