import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { Home, LogOut, MapPin, PlusCircle, ShieldCheck, UserRound, QrCode, PackageOpen } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import logo from '../assets/logo.jpg';

export default function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const role = String(user?.role || 'usuario').toLowerCase();
  const isAdmin = role === 'admin';

  function handleLogout() {
    logout();
    navigate('/login');
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <img src={logo} alt="Residuum" />
          <div>
            <h1>Residuum</h1>
            <p>Sistema de reciclagem</p>
          </div>
        </div>
        <nav className="nav-list">
          <NavLink to="/app" end><Home size={18} /> Início</NavLink>
          <NavLink to="/app/pontos"><MapPin size={18} /> Pontos de coleta</NavLink>
          <NavLink to="/app/inventario"><PackageOpen size={18} /> Meu inventário</NavLink>
          <NavLink to="/app/historico"><PlusCircle size={18} /> Histórico</NavLink>
          <NavLink to="/app/perfil"><UserRound size={18} /> Perfil</NavLink>
          <NavLink to="/app/qrcode"><QrCode size={18} /> QR Code</NavLink>
          {isAdmin && <NavLink to="/app/admin"><ShieldCheck size={18} /> Administração</NavLink>}
        </nav>
        <button className="logout" onClick={handleLogout}><LogOut size={18} /> Sair</button>
      </aside>
      <main className="content">
        <header className="topbar">
          <div>
            <span className="muted">Usuário logado</span>
            <h2>{user?.nome || 'Carregando...'}</h2>
          </div>
          <div className="user-pill">
            <span>{role}</span>
            <strong>{user?.pontuacao_total ?? 0} pts</strong>
          </div>
        </header>
        <Outlet />
      </main>
    </div>
  );
}
