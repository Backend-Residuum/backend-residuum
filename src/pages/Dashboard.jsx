import { useEffect, useMemo, useState } from 'react';
import { Award, Clock, MapPin, Recycle, UserRound } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { perfilService, pontosService } from '../services/api';
import { asArray, formatDate, formatKg } from '../utils/format';
import Inventory from '../components/Inventory';

function getPontoNome(desc) {
  return desc?.ponto_coleta_nome || desc?.ponto_nome || desc?.local_descarte || (desc?.ponto_coleta_id ? `Ponto #${desc.ponto_coleta_id}` : '-');
}

export default function Dashboard() {
  const { user } = useAuth();
  const [perfil, setPerfil] = useState(null);
  const [pontos, setPontos] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const [perfilResp, pontosResp] = await Promise.all([
          perfilService.get(),
          pontosService.list().catch(() => ({ data: [] }))
        ]);
        setPerfil(perfilResp.data || null);
        setPontos(asArray(pontosResp.data));
      } catch {
        setPerfil(null);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const usuario = perfil?.usuario || perfil || user || {};
  const resumo = perfil?.resumo || {};
  const historico = asArray(perfil?.historico_resumido);
  const pendentes = asArray(perfil?.descartes_pendentes);
  const inventario = asArray(perfil?.inventario).filter((item) => !['cancelado', 'finalizado'].includes(String(item.status).toLowerCase()));

  const totalInventario = Number(
    resumo.quantidade_disponivel_inventario ??
    inventario.reduce((acc, item) => acc + Math.max(Number(item.quantidade_disponivel ?? (Number(item.quantidade || 0) - Number(item.quantidade_reservada || 0))), 0), 0)
  );

  const totalItensInventario = Number(resumo.total_itens_inventario ?? inventario.length);
  const totalPendentes = Number(resumo.total_descartes_pendentes ?? pendentes.length);
  const totalDescartes = Number(resumo.total_descartes_resumidos ?? historico.length);

  const enderecoLabel = useMemo(() => {
    const endereco = usuario?.endereco;
    if (!endereco) return 'Endereço ainda não cadastrado';
    return `${endereco.rua || ''}${endereco.numero ? `, ${endereco.numero}` : ''} - ${endereco.bairro || ''}, ${endereco.cidade || ''}`.replace(/\s+/g, ' ').trim();
  }, [usuario]);

  return (
    <section className="page-stack">
      <div className="hero-card">
        <div>
          <span className="eyebrow">Bem-vindo</span>
          <h1>Olá, {usuario?.nome || 'usuário'}!</h1>
          <p>Acompanhe seus pontos, inventário, descartes pendentes e pontos de coleta disponíveis.</p>
        </div>
        <Award size={64} />
      </div>

      <div className="stats-grid dashboard-stats">
        <article className="stat-card"><Award /><span>Pontuação</span><strong>{usuario?.pontuacao_total ?? resumo.pontuacao_total ?? 0}</strong></article>
        <article className="stat-card"><Recycle /><span>Últimos descartes</span><strong>{totalDescartes}</strong></article>
        <article className="stat-card"><Clock /><span>Pendentes</span><strong>{totalPendentes}</strong></article>
        <article className="stat-card"><MapPin /><span>Pontos ativos</span><strong>{pontos.length}</strong></article>
        <article className="stat-card"><Recycle /><span>Inventário</span><strong>{formatKg(totalInventario)}</strong></article>
        <article className="stat-card"><UserRound /><span>Itens cadastrados</span><strong>{totalItensInventario}</strong></article>
      </div>

      {loading && <p className="muted">Carregando perfil...</p>}

      <div className="two-columns">
        <div className="panel">
          <h3>Resumo do perfil</h3>
          <div className="cards-list">
            <div className="mini-card">
              <strong>{usuario?.nome || '-'}</strong>
              <span>{usuario?.email || '-'}</span>
              <span>{usuario?.telefone || '-'}</span>
              <span>{enderecoLabel}</span>
              <span className="badge ok">{usuario?.role || 'usuario'}</span>
            </div>
          </div>
        </div>

        <div className="panel">
          <h3>Inventário pessoal</h3>
          <div className="cards-list">
            {inventario.slice(0, 4).map((item) => (
              <div className="mini-card" key={item.id}>
                <strong style={{ textTransform: 'capitalize' }}>{item.tipo_residuo}</strong>
                <span>Disponível: {formatKg(item.quantidade_disponivel ?? item.quantidade)}</span>
                {Number(item.quantidade_reservada || 0) > 0 && <span>Reservado: {formatKg(item.quantidade_reservada)}</span>}
              </div>
            ))}
            {!inventario.length && <p className="empty">Nenhum item ativo no inventário.</p>}
          </div>
        </div>
      </div>

      <div className="two-columns">
        <div className="panel">
          <h3>Últimos descartes</h3>
          <div className="table-wrap">
            <table>
              <thead><tr><th>ID</th><th>Tipo</th><th>Qtd.</th><th>Status</th><th>Local</th><th>Data</th></tr></thead>
              <tbody>{historico.slice(0, 5).map((d) => <tr key={d.id_descarte || d.id}><td>{d.id_descarte || d.id}</td><td>{d.tipo_residuo}</td><td>{d.quantidade}</td><td><span className="badge">{d.status}</span></td><td>{getPontoNome(d)}</td><td>{formatDate(d.data_desc)}</td></tr>)}</tbody>
            </table>
            {!historico.length && <p className="empty">Nenhum descarte encontrado.</p>}
          </div>
        </div>

        <div className="panel">
          <h3>Descartes pendentes</h3>
          <div className="table-wrap">
            <table>
              <thead><tr><th>ID</th><th>Tipo</th><th>Qtd.</th><th>Local</th><th>Data</th></tr></thead>
              <tbody>{pendentes.slice(0, 5).map((d) => <tr key={d.id_descarte || d.id}><td>{d.id_descarte || d.id}</td><td>{d.tipo_residuo}</td><td>{d.quantidade}</td><td>{getPontoNome(d)}</td><td>{formatDate(d.data_desc)}</td></tr>)}</tbody>
            </table>
            {!pendentes.length && <p className="empty">Nenhum descarte pendente.</p>}
          </div>
        </div>
      </div>

      <div className="panel">
        <h3>Pontos de coleta próximos/disponíveis</h3>
        <div className="cards-grid">
          {pontos.slice(0, 6).map((p) => (
            <div className="mini-card" key={p.id}>
              <strong>{p.nome}</strong>
              <span>{p.endereco || 'Sem endereço'}</span>
              <Inventory inventario={p.inventario} />
            </div>
          ))}
          {!pontos.length && <p className="empty">Nenhum ponto cadastrado.</p>}
        </div>
      </div>
    </section>
  );
}
