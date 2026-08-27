import React, { useState } from 'react';
import Sidebar from './Sidebar';
import ProfileModal from './ProfileModal';
import { useAuth } from '../context/AuthContext';
import { Toaster } from 'react-hot-toast';
import { User, Sparkles } from 'lucide-react';

export default function Layout({ children, title }) {
  const { user, roleName, switchRole } = useAuth();
  const [profileOpen, setProfileOpen] = useState(false);

  const currentRole = roleName || 'DATA_OPERATOR';

  const roles = [
    { id: 'DATA_OPERATOR', label: 'Operator', icon: '📂' },
    { id: 'REVIEWER',      label: 'Reviewer', icon: '⚖️' },
    { id: 'DATA_CONSUMER',  label: 'Consumer', icon: '📊' },
  ];

  return (
    <div className="app-shell">
      <Sidebar />
      <div className="main-area">
        {/* Modern Top Header Bar */}
        <header className="topbar">
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <span className="topbar-title">{title || 'LoanVerify AI'}</span>
          </div>

          <div className="topbar-actions" style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            {/* Topbar Role Switcher Pills */}
            <div
              style={{
                display: 'flex',
                background: '#f1f5f9',
                padding: '3px',
                borderRadius: '8px',
                border: '1px solid #e2e8f0',
                gap: '2px',
              }}
              title="Click any role to immediately switch views"
            >
              {roles.map((r) => {
                const isActive = currentRole === r.id;
                return (
                  <button
                    key={r.id}
                    onClick={() => switchRole(r.id)}
                    style={{
                      border: 'none',
                      background: isActive ? '#ffffff' : 'transparent',
                      color: isActive ? '#2563eb' : '#64748b',
                      fontWeight: isActive ? 700 : 500,
                      fontSize: '12px',
                      padding: '5px 12px',
                      borderRadius: '6px',
                      cursor: 'pointer',
                      boxShadow: isActive ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '5px',
                      transition: 'all 0.15s ease',
                    }}
                  >
                    <span>{r.icon}</span>
                    <span>{r.label}</span>
                  </button>
                );
              })}
            </div>

            {/* Profile Avatar Button */}
            <button
              onClick={() => setProfileOpen(true)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                background: '#ffffff',
                border: '1px solid #e2e8f0',
                padding: '4px 12px 4px 6px',
                borderRadius: '24px',
                cursor: 'pointer',
                boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
                transition: 'all 0.15s ease',
              }}
              title="Click to view full user profile & settings"
            >
              <div
                style={{
                  width: 30,
                  height: 30,
                  borderRadius: '50%',
                  background: 'linear-gradient(135deg, #2563eb, #1d4ed8)',
                  color: '#ffffff',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: 800,
                  fontSize: 12,
                }}
              >
                {user?.full_name?.[0] || 'U'}
              </div>
              <div style={{ textAlign: 'left' }}>
                <div style={{ fontSize: 12, fontWeight: 700, color: '#0f172a', lineHeight: 1.2 }}>
                  {user?.full_name || 'My Profile'}
                </div>
                <div style={{ fontSize: 10, color: '#64748b', fontWeight: 500 }}>
                  {currentRole.replace('_', ' ')}
                </div>
              </div>
            </button>
          </div>
        </header>

        {/* Page Content */}
        <div className="page-content">
          {children}
        </div>
      </div>

      {/* Global Profile Modal */}
      <ProfileModal isOpen={profileOpen} onClose={() => setProfileOpen(false)} />

      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: '#ffffff',
            color: '#0f172a',
            border: '1px solid #e2e8f0',
            boxShadow: '0 10px 15px -3px rgba(0,0,0,0.08)',
            fontSize: '13px',
            fontWeight: '600',
          },
        }}
      />
    </div>
  );
}
