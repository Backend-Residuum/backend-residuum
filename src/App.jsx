import { Navigate, Route, Routes } from 'react-router-dom';
import ProtectedRoute from './components/ProtectedRoute';
import Layout from './components/Layout';
import AuthPage from './pages/AuthPage';
import Dashboard from './pages/Dashboard';
import Pontos from './pages/Pontos';
import InventarioUsuario from './pages/InventarioUsuario';
import Historico from './pages/Historico';
import Perfil from './pages/Perfil';
import Admin from './pages/Admin';
import QrCodePage from './pages/QrCodePage';

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<AuthPage mode="login" />} />
      <Route path="/cadastro" element={<AuthPage mode="register" />} />
      <Route path="/" element={<Navigate to="/app" replace />} />
      <Route path="/app" element={<ProtectedRoute><Layout /></ProtectedRoute>}>
        <Route index element={<Dashboard />} />
        <Route path="descartar" element={<Navigate to="/app/inventario" replace />} />
        <Route path="pontos" element={<Pontos />} />
        <Route path="inventario" element={<InventarioUsuario />} />
        <Route path="historico" element={<Historico />} />
        <Route path="perfil" element={<Perfil />} />
        <Route path="admin" element={<Admin />} />
        <Route path="qrcode" element={<QrCodePage />} />
      </Route>
      <Route path="*" element={<Navigate to="/app" replace />} />
    </Routes>
  );
}
