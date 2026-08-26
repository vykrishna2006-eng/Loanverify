import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  LayoutDashboard, Upload, AlertTriangle, CheckCircle,
  ClipboardList, Bot, Settings, LogOut, ShieldCheck, FileText, Download
} from 'lucide-react';

const NAV = [
  { label: 'Dashboard',      path: '/dashboard',       icon: LayoutDashboard },
  { label: 'Uploads',        path: '/uploads',          icon: Upload, roles: ['DATA_OPERATOR'] },
  { label: 'Loans',          path: '/loans',            icon: FileText },
  { label: 'Exceptions',     path: '/exceptions',       icon: AlertTriangle },
  { label: 'AI Assistant',   path: '/ai-assistant',     icon: Bot },
  { label: 'Verified Loans', path: '/verified-loans',   icon: CheckCircle },
  { label: 'Audit Trail',    path: '/audit',            icon: ClipboardList },
  { label: 'Validation Rules', path: '/rules',          icon: ShieldCheck, roles: ['DATA_OPERATOR','REVIEWER'] },
  { label: 'Exports',        path: '/exports',          icon: Download },
];

export default function Sidebar() {
  const { user, logout, roleName, switchRole } = useAuth();
  const navigate = useNavigate();
  const { pathname } = useLocation();

  const visible = NAV.filter(n => !n.roles || n.roles.includes(roleName));

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <h1>🏦 LoanVerify AI</h1>
        <p>Loan Data Verification Copilot</p>
      </div>

      <nav className="sidebar-nav">
        <div className="nav-section-label">Navigation</div>
        {visible.map(item => {
          const Icon = item.icon;
          const active = pathname.startsWith(item.path);
          return (
            <div
              key={item.path}
              className={`nav-item ${active ? 'active' : ''}`}
              onClick={() => navigate(item.path)}
            >
              <Icon />
              <span>{item.label}</span>
            </div>
          );
        })}

        <div className="nav-section-label" style={{ marginTop: 8 }}>System</div>
        <div className="nav-item" onClick={() => window.open('https://loanverify-backend.onrender.com/api/docs', '_blank')}>
          <Settings />
          <span>API Docs</span>
        </div>
      </nav>

      <div className="sidebar-footer">
        <div className="user-chip" style={{ flexDirection: 'column', alignItems: 'stretch', gap: 6 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div className="user-avatar">
              {user?.full_name?.[0] || 'U'}
            </div>
            <div className="user-info" style={{ overflow: 'hidden' }}>
              <div className="user-name" style={{ textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>{user?.full_name}</div>
            </div>
          </div>
          
          {/* Interactive Role Switcher */}
          <div style={{ marginTop: 2 }}>
            <select
              value={roleName || 'DATA_OPERATOR'}
              onChange={(e) => switchRole(e.target.value)}
              style={{
                width: '100%',
                background: 'rgba(255, 255, 255, 0.08)',
                color: '#60a5fa',
                border: '1px solid rgba(255, 255, 255, 0.15)',
                borderRadius: 6,
                padding: '4px 6px',
                fontSize: 11,
                fontWeight: 600,
                cursor: 'pointer',
                outline: 'none',
              }}
            >
              <option value="DATA_OPERATOR" style={{ background: '#0f172a', color: '#fff' }}>Role: Data Operator</option>
              <option value="REVIEWER" style={{ background: '#0f172a', color: '#fff' }}>Role: Reviewer</option>
              <option value="DATA_CONSUMER" style={{ background: '#0f172a', color: '#fff' }}>Role: Data Consumer</option>
            </select>
          </div>
        </div>
        <button className="btn-logout" onClick={logout} style={{ marginTop: 6 }}>
          <LogOut size={12} style={{ display: 'inline', marginRight: 4 }} />
          Sign out
        </button>
      </div>
    </aside>
  );
}
