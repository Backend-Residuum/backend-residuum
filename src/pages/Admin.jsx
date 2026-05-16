import { useEffect, useMemo, useState } from 'react';
import { ShieldCheck } from 'lucide-react';
import { descarteService, getApiError, pontosService } from '../services/api';
import { asArray, formatDate } from '../utils/format';
import Message from '../components/Message';

function getUsuarioNome(desc) {
  return (
    desc.usuario_nome ||
    desc.nome_usuario ||
    desc.nome_descartante ||
    desc.descartante_nome ||
    desc.usuario?.nome ||
    desc.user?.nome ||
    (desc.usuario_id ? `Usuário #${desc.usuario_id}` : '-')
  );
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

export default function Admin() {
  const [pendentes, setPendentes] = useState([]);
  const [pontos, setPontos] = useState([]);
  const [quantidades, setQuantidades] = useState({});
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const pontosById = useMemo(() => {
    return asArray(pontos).reduce((acc, ponto) => {
      if (ponto?.id !== undefined && ponto?.id !== null) acc[ponto.id] = ponto;
      return acc;
    }, {});
  }, [pontos]);

  async function load() {
    const [pendentesResponse, pontosResponse] = await Promise.all([
      descarteService.pending(),
      pontosService.list().catch(() => ({ data: [] }))
    ]);
    setPendentes(asArray(pendentesResponse.data));
    setPontos(asArray(pontosResponse.data));
  }

  useEffect(() => { load().catch((err) => setError(getApiError(err))); }, []);

  async function confirmar(id, fallbackQtd) {
    setError(''); setMessage('');
    const qtd = Number(quantidades[id] || fallbackQtd);
    try {
      const { data } = await descarteService.confirm(id, qtd);
      setMessage(data?.mensagem || `Descarte ${id} confirmado com sucesso.`);
      await load();
    } catch (err) { setError(getApiError(err)); }
  }

  return (
    <section className="page-stack">
      <div className="section-title"><ShieldCheck /><div><h1>Administração</h1><p>Confirme descartes pendentes da cooperativa.</p></div></div>
      <Message type="success">{message}</Message><Message type="error">{error}</Message>
      <div className="panel table-wrap">
        <table>
          <thead><tr><th>ID</th><th>Descartante</th><th>Tipo</th><th>Qtd. informada</th><th>Qtd. confirmada</th><th>Local de descarte</th><th>Data</th><th>Ação</th></tr></thead>
          <tbody>{pendentes.map((d) => {
            const id = d.id_descarte || d.id;
            return <tr key={id}><td>{id}</td><td>{getUsuarioNome(d)}</td><td>{d.tipo_residuo}</td><td>{d.quantidade}</td><td><input className="table-input" type="number" step="any" value={quantidades[id] ?? d.quantidade} onChange={(e) => setQuantidades((prev) => ({ ...prev, [id]: e.target.value }))} /></td><td>{getPontoNome(d, pontosById)}</td><td>{formatDate(d.data_desc)}</td><td><button className="primary-button small" onClick={() => confirmar(id, d.quantidade)}>Confirmar</button></td></tr>;
          })}</tbody>
        </table>
        {!pendentes.length && <p className="empty">Nenhum descarte pendente.</p>}
      </div>
    </section>
  );
}
