import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Leaf, Lock, Mail, Phone, User } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { getApiError } from '../services/api';
import Message from '../components/Message';
import logo from '../assets/logo.jpg';

export default function AuthPage({ mode }) {
  const isRegister = mode === 'register';
  const navigate = useNavigate();
  const { login, register } = useAuth();
  const [form, setForm] = useState({ nome: '', email: '', telefone: '', senha: '' });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  function update(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setError('');
    setMessage('');
    try {
      if (isRegister) {
        await register(form);
        setMessage('Cadastro criado com sucesso. Entrando no sistema...');
      }
      await login({ email: form.email, senha: form.senha });
      navigate('/app');
    } catch (err) {
      setError(getApiError(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-page">
      <section className="auth-card">
        <div className="auth-logo">
          <img src={logo} alt="Residuum" />
          <div>
            <h1>{isRegister ? 'Criar conta' : 'Entrar no Residuum'}</h1>
            <p>{isRegister ? 'Cadastre seus dados para começar.' : 'Acesse sua conta para registrar descartes.'}</p>
          </div>
        </div>
        <Message type="success">{message}</Message>
        <Message type="error">{error}</Message>
        <form onSubmit={handleSubmit} className="form-grid">
          {isRegister && (
            <label><span><User size={16} /> Nome</span><input required value={form.nome} onChange={(e) => update('nome', e.target.value)} placeholder="Seu nome completo" /></label>
          )}
          <label><span><Mail size={16} /> E-mail</span><input required type="email" value={form.email} onChange={(e) => update('email', e.target.value)} placeholder="email@exemplo.com" /></label>
          {isRegister && (
            <label><span><Phone size={16} /> Telefone</span><input required value={form.telefone} onChange={(e) => update('telefone', e.target.value)} placeholder="92999999999" /></label>
          )}
          <label><span><Lock size={16} /> Senha</span><input required type="password" value={form.senha} onChange={(e) => update('senha', e.target.value)} placeholder="Sua senha" /></label>
          <button className="primary-button" disabled={loading}>{loading ? 'Processando...' : isRegister ? 'Cadastrar e entrar' : 'Entrar'}</button>
        </form>
        <p className="auth-switch">
          {isRegister ? 'Já possui conta?' : 'Ainda não possui conta?'}{' '}
          <Link to={isRegister ? '/login' : '/cadastro'}>{isRegister ? 'Entrar' : 'Cadastrar'}</Link>
        </p>
      </section>
      <aside className="auth-hero">
        <Leaf size={44} />
        <h2>Recicle, pontue e acompanhe seus descartes.</h2>
        <p>Frontend integrado aos endpoints reais do backend FastAPI.</p>
      </aside>
    </div>
  );
}
