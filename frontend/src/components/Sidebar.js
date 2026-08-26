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
  const { user, logout, roleName } = useAuth();
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
        <div className="nav-item" onClick={() => window.open('http://localhost:8000/api/docs', '_blank')}>
          <Settings />
          <span>API Docs</span>
        </div>
      </nav>

      <div className="sidebar-footer">
        <div className="user-chip">
          <div className="user-avatar">
            {user?.full_name?.[0] || 'U'}
          </div>
          <div className="user-info">
            <div className="user-name">{user?.full_name}</div>
            <div className="user-role">{roleName?.replace('_', ' ')}</div>
          </div>
        </div>
        <button className="btn-logout" onClick={logout}>
          <LogOut size={12} style={{ display: 'inline', marginRight: 4 }} />
          Sign out
        </button>
      </div>
    </aside>
  );
}
