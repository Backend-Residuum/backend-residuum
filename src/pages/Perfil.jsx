import { useEffect, useMemo, useState } from 'react';
import { Clock, PackageOpen, Recycle, UserRound } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { authService, getApiError, perfilService } from '../services/api';
import { asArray, formatDate, formatKg } from '../utils/format';
import Message from '../components/Message';

function getPontoNome(desc) {
  return desc?.ponto_coleta_nome || desc?.ponto_nome || desc?.local_descarte || (desc?.ponto_coleta_id ? `Ponto #${desc.ponto_coleta_id}` : '-');
}

export default function Perfil() {
  const { user, reloadUser } = useAuth();
  const [perfil, setPerfil] = useState(null);
  const [form, setForm] = useState({ rua: '', bairro: '', numero: '', cep: '', cidade: '' });
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  async function loadPerfil() {
    setLoading(true);
    try {
      const { data } = await perfilService.get();
      setPerfil(data || null);
      const endereco = data?.endereco || data?.usuario?.endereco || {};
      setForm({
        rua: endereco?.rua || '',
        bairro: endereco?.bairro || '',
        numero: endereco?.numero ?? '',
        cep: endereco?.cep || '',
        cidade: endereco?.cidade || ''
      });
    } catch (err) {
      setError(getApiError(err));
      const endereco = user?.endereco || {};
      setForm({ rua: endereco.rua || '', bairro: endereco.bairro || '', numero: endereco.numero || '', cep: endereco.cep || '', cidade: endereco.cidade || '' });
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { loadPerfil(); }, []);

  const usuario = perfil?.usuario || perfil || user || {};
  const resumo = perfil?.resumo || {};
  const inventario = asArray(perfil?.inventario).filter((item) => !['cancelado', 'finalizado'].includes(String(item.status).toLowerCase()));
  const historico = asArray(perfil?.historico_resumido);
  const pendentes = asArray(perfil?.descartes_pendentes);

  const quantidadeInventario = Number(
    resumo.quantidade_disponivel_inventario ??
    inventario.reduce((acc, item) => acc + Number(item.quantidade_disponivel ?? item.quantidade ?? 0), 0)
  );

  const enderecoCompleto = useMemo(() => {
    const endereco = usuario?.endereco;
    if (!endereco) return 'Endereço não cadastrado';
    return `${endereco.rua || ''}${endereco.numero ? `, ${endereco.numero}` : ''} - ${endereco.bairro || ''}, ${endereco.cidade || ''} ${endereco.cep ? `• CEP ${endereco.cep}` : ''}`.replace(/\s+/g, ' ').trim();
  }, [usuario]);

  function update(field, value) { setForm((prev) => ({ ...prev, [field]: value })); }

  async function submit(e) {
    e.preventDefault();
    setError('');
    setMessage('');
    try {
      await authService.updateAddress({ ...form, numero: Number(form.numero) });
      await reloadUser();
      await loadPerfil();
      setMessage('Endereço atualizado com sucesso.');
    } catch (err) {
      setError(getApiError(err));
    }
  }

  return (
    <section className="page-stack">
      <div className="section-title"><UserRound /><div><h1>Perfil</h1><p>Dados pessoais, endereço, pontuação, inventário e histórico resumido.</p></div></div>
      {loading && <p className="muted">Carregando perfil...</p>}
      <Message type="success">{message}</Message><Message type="error">{error}</Message>

      <div className="two-columns">
        <div className="panel profile-panel">
          <h3>{usuario?.nome || '-'}</h3>
          <p>{usuario?.email || '-'}</p>
          <p>{usuario?.telefone || '-'}</p>
          <p className="muted">{enderecoCompleto}</p>
          <div className="profile-score"><strong>{usuario?.pontuacao_total ?? resumo.pontuacao_total ?? 0}</strong><span>pontos acumulados</span></div>
          <span className="badge ok">{usuario?.role || 'usuario'}</span>
        </div>

        <form className="panel form-grid" onSubmit={submit}>
          <h3>Endereço</h3>
          <label><span>Rua</span><input required value={form.rua} onChange={(e) => update('rua', e.target.value)} /></label>
          <label><span>Bairro</span><input required value={form.bairro} onChange={(e) => update('bairro', e.target.value)} /></label>
          <label><span>Número</span><input required type="number" value={form.numero} onChange={(e) => update('numero', e.target.value)} /></label>
          <label><span>CEP</span><input required value={form.cep} onChange={(e) => update('cep', e.target.value)} /></label>
          <label><span>Cidade</span><input required value={form.cidade} onChange={(e) => update('cidade', e.target.value)} /></label>
          <button className="primary-button">Salvar endereço</button>
        </form>
      </div>

      <div className="stats-grid dashboard-stats">
        <article className="stat-card"><PackageOpen /><span>Itens no inventário</span><strong>{resumo.total_itens_inventario ?? inventario.length}</strong></article>
        <article className="stat-card"><Recycle /><span>Quantidade disponível</span><strong>{formatKg(quantidadeInventario)}</strong></article>
        <article className="stat-card"><Clock /><span>Descartes pendentes</span><strong>{resumo.total_descartes_pendentes ?? pendentes.length}</strong></article>
        <article className="stat-card"><Recycle /><span>Últimos descartes</span><strong>{resumo.total_descartes_resumidos ?? historico.length}</strong></article>
      </div>

      <div className="two-columns">
        <div className="panel">
          <h3>Inventário ativo</h3>
          <div className="cards-list">
            {inventario.slice(0, 5).map((item) => (
              <div className="mini-card" key={item.id}>
                <strong style={{ textTransform: 'capitalize' }}>{item.tipo_residuo}</strong>
                <span>Disponível: {formatKg(item.quantidade_disponivel ?? item.quantidade)}</span>
                {item.descricao && <span>{item.descricao}</span>}
              </div>
            ))}
            {!inventario.length && <p className="empty">Nenhum item ativo no inventário.</p>}
          </div>
        </div>

        <div className="panel">
          <h3>Descartes pendentes</h3>
          <div className="cards-list">
            {pendentes.slice(0, 5).map((d) => (
              <div className="mini-card" key={d.id_descarte || d.id}>
                <strong>#{d.id_descarte || d.id} • {d.tipo_residuo}</strong>
                <span>{d.quantidade} kg • {getPontoNome(d)}</span>
                <span>{formatDate(d.data_desc)}</span>
              </div>
            ))}
            {!pendentes.length && <p className="empty">Nenhum descarte pendente.</p>}
          </div>
        </div>
      </div>

      <div className="panel table-wrap">
        <h3>Histórico resumido</h3>
        <table>
          <thead><tr><th>ID</th><th>Tipo</th><th>Quantidade</th><th>Confirmada</th><th>Status</th><th>Local</th><th>Data</th></tr></thead>
          <tbody>{historico.map((d) => (
            <tr key={d.id_descarte || d.id}>
              <td>{d.id_descarte || d.id}</td>
              <td>{d.tipo_residuo}</td>
              <td>{d.quantidade}</td>
              <td>{d.quantidade_confirmada || '-'}</td>
              <td><span className="badge">{d.status}</span></td>
              <td>{getPontoNome(d)}</td>
              <td>{formatDate(d.data_desc)}</td>
            </tr>
          ))}</tbody>
        </table>
        {!historico.length && <p className="empty">Nenhum descarte encontrado.</p>}
      </div>
    </section>
  );
}
