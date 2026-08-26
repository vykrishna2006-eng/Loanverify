import React, { createContext, useContext, useState } from 'react';
import { authAPI } from '../api/client';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try { return JSON.parse(localStorage.getItem('lv_user')); } catch { return null; }
  });
  const [loading, setLoading] = useState(false);

  const login = async (email, password) => {
    setLoading(true);
    try {
      const res = await authAPI.login(email, password);
      const { access_token, user: u } = res.data;
      localStorage.setItem('lv_token', access_token);
      localStorage.setItem('lv_user', JSON.stringify(u));
      setUser(u);
      return { ok: true };
    } catch (err) {
      const errorMsg =
        err.response?.data?.detail ||
        (typeof err.response?.data === 'string' ? err.response?.data : null) ||
        (err.response?.status === 404 ? 'Backend server not reachable. Please verify backend URL.' : 'Login failed');
      return { ok: false, error: errorMsg };
    } finally {
      setLoading(false);
    }
  };

  const register = async (fullName, email, password, roleName = "DATA_OPERATOR") => {
    setLoading(true);
    try {
      await authAPI.register({
        full_name: fullName,
        email: email,
        password: password,
        role_name: roleName,
      });
      // After registration, automatically log in
      return await login(email, password);
    } catch (err) {
      const errorMsg =
        err.response?.data?.detail ||
        (typeof err.response?.data === 'string' ? err.response?.data : null) ||
        (err.response?.status === 404 ? 'Backend server not reachable. Please verify backend URL.' : 'Registration failed');
      return { ok: false, error: errorMsg };
    } finally {
      setLoading(false);
    }
  };

  const switchRole = (newRole) => {
    if (!user) return;
    const updatedUser = {
      ...user,
      role: { ...(user.role || {}), name: newRole },
      role_name: newRole,
    };
    localStorage.setItem('lv_user', JSON.stringify(updatedUser));
    setUser(updatedUser);
  };

  const logout = () => {
    localStorage.removeItem('lv_token');
    localStorage.removeItem('lv_user');
    setUser(null);
  };

  const roleName = user?.role?.name || user?.role_name || '';

  return (
    <AuthContext.Provider value={{ user, login, register, switchRole, logout, loading, roleName }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
