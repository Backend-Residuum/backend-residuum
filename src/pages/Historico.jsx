import { useEffect, useMemo, useState } from 'react';
import { History } from 'lucide-react';
import { descarteService, getApiError, pontosService } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { asArray, formatDate } from '../utils/format';
import Message from '../components/Message';

function getId(value) {
  return value?.id_descarte ?? value?.id;
}

function getUsuarioNome(desc, currentUser, view) {
  const possibleName =
    desc.usuario_nome ||
    desc.nome_usuario ||
    desc.nome_descartante ||
    desc.descartante_nome ||
    desc.usuario?.nome ||
    desc.user?.nome ||
    desc.nome;

  if (possibleName) return possibleName;

  const descUserId = desc.usuario_id ?? desc.user_id ?? desc.id_usuario;
  if (view === 'me' || Number(descUserId) === Number(currentUser?.id)) {
    return currentUser?.nome || 'Você';
  }

  return descUserId ? `Usuário #${descUserId}` : '-';
}

function getPontoNome(desc, pontosById) {
  const possibleName =
    desc.ponto_nome ||
    desc.nome_ponto ||
    desc.ponto_coleta_nome ||
    desc.local_descarte ||
    desc.local_nome ||
    desc.ponto_coleta?.nome ||
    desc.ponto?.nome;

  if (possibleName) return possibleName;

  const pontoId = desc.ponto_coleta_id ?? desc.ponto_id ?? desc.id_ponto;
  return pontosById[pontoId]?.nome || (pontoId ? `Ponto #${pontoId}` : '-');
}

export default function Historico() {
  const { user } = useAuth();
  const isAdmin = String(user?.role).toLowerCase() === 'admin';
  const [items, setItems] = useState([]);
  const [pontos, setPontos] = useState([]);
  const [view, setView] = useState('me');
  const [error, setError] = useState('');

  const pontosById = useMemo(() => {
    return asArray(pontos).reduce((acc, ponto) => {
      if (ponto?.id !== undefined && ponto?.id !== null) acc[ponto.id] = ponto;
      return acc;
    }, {});
  }, [pontos]);

  async function load(target = view) {
    setError('');
    try {
      const [historyResponse, pontosResponse] = await Promise.all([
        target === 'geral' ? descarteService.generalHistory() : descarteService.myHistory(),
        pontosService.list().catch(() => ({ data: [] }))
      ]);
      setItems(asArray(historyResponse.data));
      setPontos(asArray(pontosResponse.data));
    } catch (err) {
      setError(getApiError(err));
    }
  }

  useEffect(() => { load(); }, [view]);

  return (
    <section className="page-stack">
      <div className="section-title"><History /><div><h1>Histórico de descartes</h1><p>Acompanhe registros confirmados e pendentes.</p></div></div>
      <Message type="error">{error}</Message>
      {isAdmin && <div className="tabs"><button className={view === 'me' ? 'active' : ''} onClick={() => setView('me')}>Meu histórico</button><button className={view === 'geral' ? 'active' : ''} onClick={() => setView('geral')}>Histórico geral</button></div>}
      <div className="panel table-wrap">
        <table>
          <thead><tr><th>ID</th><th>Descartante</th><th>Tipo</th><th>Quantidade</th><th>Confirmada</th><th>Status</th><th>Local de descarte</th><th>Data</th></tr></thead>
          <tbody>{items.map((d) => <tr key={getId(d)}><td>{getId(d)}</td><td>{getUsuarioNome(d, user, view)}</td><td>{d.tipo_residuo}</td><td>{d.quantidade}</td><td>{d.quantidade_confirmada || '-'}</td><td><span className="badge">{d.status}</span></td><td>{getPontoNome(d, pontosById)}</td><td>{formatDate(d.data_desc)}</td></tr>)}</tbody>
        </table>
        {!items.length && <p className="empty">Nenhum registro encontrado.</p>}
      </div>
    </section>
  );
}
