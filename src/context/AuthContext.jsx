import { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { authService, getApiError } from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('residuum_token'));
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(Boolean(token));
  const [error, setError] = useState('');

  async function loadMe() {
    if (!localStorage.getItem('residuum_token')) {
      setLoading(false);
      return null;
    }
    try {
      setLoading(true);
      const { data } = await authService.me();
      setUser(data);
      setError('');
      return data;
    } catch (err) {
      setError(getApiError(err));
      logout();
      return null;
    } finally {
      setLoading(false);
    }
  }

  async function login(credentials) {
    const { data } = await authService.login(credentials);
    localStorage.setItem('residuum_token', data.access_token);
    setToken(data.access_token);
    await loadMe();
    return data;
  }

  async function register(payload) {
    return authService.register(payload);
  }

  function logout() {
    localStorage.removeItem('residuum_token');
    setToken(null);
    setUser(null);
  }

  useEffect(() => {
    loadMe();
  }, []);

  const value = useMemo(() => ({ token, user, setUser, loading, error, login, register, logout, reloadUser: loadMe }), [token, user, loading, error]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}
