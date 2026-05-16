import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function ProtectedRoute({ children }) {
  const { token, loading } = useAuth();
  if (loading) return <div className="full-loader">Carregando sessão...</div>;
  if (!token) return <Navigate to="/login" replace />;
  return children;
}
