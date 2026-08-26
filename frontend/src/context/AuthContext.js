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
      return { ok: false, error: err.response?.data?.detail || 'Login failed' };
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
      return { ok: false, error: err.response?.data?.detail || 'Registration failed' };
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('lv_token');
    localStorage.removeItem('lv_user');
    setUser(null);
  };

  const roleName = user?.role?.name || '';

  return (
    <AuthContext.Provider value={{ user, login, register, logout, loading, roleName }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
