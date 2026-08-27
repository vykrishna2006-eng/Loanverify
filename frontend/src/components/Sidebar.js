import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import ProfileModal from './ProfileModal';
import {
  LayoutDashboard, Upload, AlertTriangle, CheckCircle,
  ClipboardList, Bot, Settings, LogOut, ShieldCheck, FileText, Download, User, Sparkles
} from 'lucide-react';

const NAV = [
  { label: 'Dashboard',        path: '/dashboard',       icon: LayoutDashboard },
  { label: 'Uploads',          path: '/uploads',          icon: Upload, roles: ['DATA_OPERATOR'] },
  { label: 'Loans',            path: '/loans',            icon: FileText },
  { label: 'Exceptions',       path: '/exceptions',       icon: AlertTriangle },
  { label: 'AI Assistant',     path: '/ai-assistant',     icon: Bot },
  { label: 'Verified Loans',   path: '/verified-loans',   icon: CheckCircle },
  { label: 'Audit Trail',      path: '/audit',            icon: ClipboardList },
  { label: 'Validation Rules', path: '/rules',          icon: ShieldCheck, roles: ['DATA_OPERATOR','REVIEWER'] },
  { label: 'Exports',          path: '/exports',          icon: Download },
  { label: 'AI Dev Log',       path: '/ai-dev-log',       icon: Sparkles },
];

export default function Sidebar() {
  const { user, logout, roleName, switchRole } = useAuth();
  const [showProfile, setShowProfile] = useState(false);
  const navigate = useNavigate();
  const { pathname } = useLocation();

  const visible = NAV.filter(n => !n.roles || n.roles.includes(roleName));

  return (
    <>
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
            {/* Clickable User Header to open Profile */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                cursor: 'pointer',
                padding: '4px',
                borderRadius: '8px',
                transition: 'background 0.15s ease',
              }}
              onClick={() => setShowProfile(true)}
              title="Click to view full user profile"
            >
              <div className="user-avatar" style={{ boxShadow: '0 0 10px rgba(59, 130, 246, 0.4)' }}>
                {user?.full_name?.[0] || 'U'}
              </div>
              <div className="user-info" style={{ overflow: 'hidden', flex: 1 }}>
                <div className="user-name" style={{ textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap', fontWeight: 600 }}>
                  {user?.full_name}
                </div>
                <div style={{ fontSize: 10, color: '#60a5fa', display: 'flex', alignItems: 'center', gap: 4 }}>
                  <User size={10} /> View Profile
                </div>
              </div>
            </div>
            
            {/* Interactive Role Switcher */}
            <div style={{ marginTop: 2 }}>
              <select
                value={roleName || 'DATA_OPERATOR'}
                onChange={(e) => switchRole(e.target.value)}
                style={{
                  width: '100%',
                  background: '#f8fafc',
                  color: '#2563eb',
                  border: '1px solid #cbd5e1',
                  borderRadius: 6,
                  padding: '5px 8px',
                  fontSize: 11,
                  fontWeight: 700,
                  cursor: 'pointer',
                  outline: 'none',
                }}
              >
                <option value="DATA_OPERATOR" style={{ background: '#ffffff', color: '#0f172a' }}>Role: Data Operator</option>
                <option value="REVIEWER" style={{ background: '#ffffff', color: '#0f172a' }}>Role: Reviewer</option>
                <option value="DATA_CONSUMER" style={{ background: '#ffffff', color: '#0f172a' }}>Role: Data Consumer</option>
              </select>
            </div>
          </div>
          <button className="btn-logout" onClick={logout} style={{ marginTop: 6 }}>
            <LogOut size={12} style={{ display: 'inline', marginRight: 4 }} />
            Sign out
          </button>
        </div>
      </aside>

      {/* Full Profile Modal */}
      <ProfileModal isOpen={showProfile} onClose={() => setShowProfile(false)} />
    </>
  );
}
