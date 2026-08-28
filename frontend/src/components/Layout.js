import React, { useState } from 'react';
import Sidebar from './Sidebar';
import ProfileModal from './ProfileModal';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { Toaster } from 'react-hot-toast';
import { User, Sun, Moon } from 'lucide-react';

export default function Layout({ children, title }) {
  const { user, roleName, switchRole } = useAuth();
  const { theme, toggleTheme } = useTheme();
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

          <div className="topbar-actions" style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            {/* Dark / Light Mode Toggle Button */}
            <button
              onClick={toggleTheme}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                background: 'var(--bg-card)',
                border: '1px solid var(--border)',
                padding: '6px 12px',
                borderRadius: '20px',
                cursor: 'pointer',
                color: 'var(--text-primary)',
                fontSize: '12px',
                fontWeight: 600,
                boxShadow: 'var(--shadow-sm)',
                transition: 'all 0.15s ease',
              }}
              title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} Mode`}
            >
              {theme === 'dark' ? (
                <>
                  <Sun size={14} color="#f59e0b" />
                  <span>Light</span>
                </>
              ) : (
                <>
                  <Moon size={14} color="#6366f1" />
                  <span>Dark</span>
                </>
              )}
            </button>

            {/* Topbar Role Switcher Pills */}
            <div
              style={{
                display: 'flex',
                background: 'var(--bg-card)',
                padding: '3px',
                borderRadius: '8px',
                border: '1px solid var(--border)',
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
                      background: isActive ? 'var(--accent)' : 'transparent',
                      color: isActive ? '#ffffff' : 'var(--text-secondary)',
                      fontWeight: isActive ? 700 : 500,
                      fontSize: '12px',
                      padding: '5px 12px',
                      borderRadius: '6px',
                      cursor: 'pointer',
                      boxShadow: isActive ? '0 1px 3px rgba(0,0,0,0.2)' : 'none',
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
                background: 'var(--bg-card)',
                border: '1px solid var(--border)',
                padding: '4px 12px 4px 6px',
                borderRadius: '24px',
                cursor: 'pointer',
                boxShadow: 'var(--shadow-sm)',
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
                <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1.2 }}>
                  {user?.full_name || 'My Profile'}
                </div>
                <div style={{ fontSize: 10, color: 'var(--text-muted)', fontWeight: 500 }}>
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
            background: 'var(--bg-card)',
            color: 'var(--text-primary)',
            border: '1px solid var(--border)',
            boxShadow: 'var(--shadow-lg)',
            fontSize: '13px',
            fontWeight: '600',
          },
        }}
      />
    </div>
  );
}
