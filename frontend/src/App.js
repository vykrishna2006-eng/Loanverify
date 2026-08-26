import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';

import Login         from './pages/Login';
import Dashboard     from './pages/Dashboard';
import Uploads       from './pages/Uploads';
import Loans         from './pages/Loans';
import Exceptions    from './pages/Exceptions';
import AIAssistant   from './pages/AIAssistant';
import VerifiedLoans from './pages/VerifiedLoans';
import AuditTrail    from './pages/AuditTrail';
import Rules         from './pages/Rules';
import Exports       from './pages/Exports';

function ProtectedRoute({ children, roles }) {
  const { user, roleName } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  if (roles && !roles.includes(roleName)) return <Navigate to="/dashboard" replace />;
  return children;
}

function AppRoutes() {
  const { user } = useAuth();
  return (
    <Routes>
      <Route path="/login" element={user ? <Navigate to="/dashboard" replace /> : <Login />} />
      <Route path="/" element={<Navigate to="/dashboard" replace />} />

      <Route path="/dashboard"     element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
      <Route path="/uploads"       element={<ProtectedRoute roles={['DATA_OPERATOR']}><Uploads /></ProtectedRoute>} />
      <Route path="/loans"         element={<ProtectedRoute><Loans /></ProtectedRoute>} />
      <Route path="/exceptions"    element={<ProtectedRoute><Exceptions /></ProtectedRoute>} />
      <Route path="/exceptions/:id" element={<ProtectedRoute><Exceptions /></ProtectedRoute>} />
      <Route path="/ai-assistant"  element={<ProtectedRoute><AIAssistant /></ProtectedRoute>} />
      <Route path="/verified-loans" element={<ProtectedRoute><VerifiedLoans /></ProtectedRoute>} />
      <Route path="/audit"         element={<ProtectedRoute><AuditTrail /></ProtectedRoute>} />
      <Route path="/rules"         element={<ProtectedRoute roles={['DATA_OPERATOR','REVIEWER']}><Rules /></ProtectedRoute>} />
      <Route path="/exports"       element={<ProtectedRoute><Exports /></ProtectedRoute>} />

      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </AuthProvider>
  );
}
