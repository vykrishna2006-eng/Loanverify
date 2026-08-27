import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import toast, { Toaster } from 'react-hot-toast';

const DEMO_CREDS = [
  { label: 'Data Operator', email: 'operator@loanverify.ai', password: 'password123', role: 'Upload & Validate' },
  { label: 'Reviewer',      email: 'reviewer@loanverify.ai', password: 'password123', role: 'Review & Approve' },
  { label: 'Data Consumer', email: 'consumer@loanverify.ai', password: 'password123', role: 'View & Export' },
];

export default function Login() {
  const [isRegister, setIsRegister] = useState(false);
  const [fullName, setFullName]     = useState('');
  const [email, setEmail]           = useState('');
  const [password, setPassword]     = useState('');
  const [roleName, setRoleName]     = useState('DATA_OPERATOR');
  const [err, setErr]               = useState('');
  const { login, register, loading } = useAuth();
  const navigate                    = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErr('');
    if (isRegister) {
      if (!fullName.trim()) {
        setErr('Please enter your full name');
        return;
      }
      const result = await register(fullName, email, password, roleName);
      if (result.ok) {
        toast.success(`Welcome to LoanVerify AI, ${fullName.split(' ')[0]}!`);
        navigate('/dashboard');
      } else {
        setErr(result.error);
      }
    } else {
      const result = await login(email, password);
      if (result.ok) {
        navigate('/dashboard');
      } else {
        setErr(result.error);
      }
    }
  };

  const quickLogin = async (cred) => {
    setErr('');
    setEmail(cred.email);
    setPassword(cred.password);
    const result = await login(cred.email, cred.password);
    if (result.ok) navigate('/dashboard');
    else {
      setErr(result.error);
      toast.error(result.error);
    }
  };

  return (
    <div className="login-page">
      <div style={{ width: '100%', maxWidth: 460, padding: '0 16px' }}>
        <div className="login-card">
          <div className="login-logo">
            <h1>🏦 LoanVerify AI</h1>
            <p>Loan Data Verification Copilot</p>
          </div>

          {/* Toggle Tabs */}
          <div style={{ display: 'flex', background: 'rgba(255, 255, 255, 0.05)', borderRadius: 8, padding: 4, marginBottom: 20 }}>
            <button
              type="button"
              onClick={() => { setIsRegister(false); setErr(''); }}
              style={{
                flex: 1,
                padding: '8px 12px',
                border: 'none',
                borderRadius: 6,
                background: !isRegister ? 'var(--accent, #3b82f6)' : 'transparent',
                color: !isRegister ? '#fff' : 'var(--text-muted, #94a3b8)',
                fontWeight: 600,
                fontSize: 13,
                cursor: 'pointer',
                transition: 'all 0.2s ease',
              }}
            >
              Sign In
            </button>
            <button
              type="button"
              onClick={() => { setIsRegister(true); setErr(''); }}
              style={{
                flex: 1,
                padding: '8px 12px',
                border: 'none',
                borderRadius: 6,
                background: isRegister ? 'var(--accent, #3b82f6)' : 'transparent',
                color: isRegister ? '#fff' : 'var(--text-muted, #94a3b8)',
                fontWeight: 600,
                fontSize: 13,
                cursor: 'pointer',
                transition: 'all 0.2s ease',
              }}
            >
              Create Account
            </button>
          </div>

          <form onSubmit={handleSubmit}>
            {isRegister && (
              <div className="form-group">
                <label className="form-label">Full Name</label>
                <input
                  className="form-input"
                  type="text"
                  placeholder="e.g. Alex Taylor"
                  value={fullName}
                  onChange={e => setFullName(e.target.value)}
                  required
                />
              </div>
            )}

            <div className="form-group">
              <label className="form-label">Email</label>
              <input
                className="form-input"
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={e => setEmail(e.target.value)}
                required
                autoFocus={!isRegister}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Password</label>
              <input
                className="form-input"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={e => setPassword(e.target.value)}
                required
              />
            </div>

            {isRegister && (
              <div className="form-group">
                <label className="form-label">Role</label>
                <select
                  className="form-input"
                  value={roleName}
                  onChange={e => setRoleName(e.target.value)}
                  style={{ background: '#ffffff', color: '#0f172a' }}
                >
                  <option value="DATA_OPERATOR">Data Operator (Upload, Ingest, Validate)</option>
                  <option value="REVIEWER">Reviewer (Exception Review & AI Copilot)</option>
                  <option value="DATA_CONSUMER">Data Consumer (Verified Records & Audits)</option>
                </select>
              </div>
            )}

            {err && <div className="alert alert-danger">{err}</div>}

            <button
              className="btn btn-primary btn-lg"
              style={{ width: '100%', marginTop: 8 }}
              type="submit"
              disabled={loading}
            >
              {loading ? <span className="spinner" /> : (isRegister ? 'Create Account & Sign In' : 'Sign In')}
            </button>
          </form>

          <div className="divider" style={{ margin: '24px 0' }} />

          <div style={{ marginBottom: 12 }}>
            <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '.06em', marginBottom: 10 }}>
              Quick Demo Login
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {DEMO_CREDS.map(c => (
                <button
                  key={c.email}
                  type="button"
                  className="btn btn-secondary"
                  style={{ justifyContent: 'flex-start', gap: 10 }}
                  onClick={() => quickLogin(c)}
                  disabled={loading}
                >
                  <div style={{ textAlign: 'left' }}>
                    <div style={{ fontWeight: 600, fontSize: 12 }}>{c.label}</div>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{c.role} · {c.email}</div>
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
      <Toaster position="top-right" toastOptions={{ style: { background: '#ffffff', color: '#0f172a', border: '1px solid #e2e8f0', boxShadow: '0 4px 12px rgba(0,0,0,0.08)' } }} />
    </div>
  );
}
