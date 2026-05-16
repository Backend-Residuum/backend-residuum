import { useEffect, useState } from 'react';
import { QrCode } from 'lucide-react';
import { getApiError, pontosService, qrCodeService } from '../services/api';
import { asArray, formatDate } from '../utils/format';
import Message from '../components/Message';

export default function QrCodePage() {
  const [pontos, setPontos] = useState([]);
  const [pontoId, setPontoId] = useState('');
  const [tokens, setTokens] = useState([]);
  const [token, setToken] = useState('');
  const [validation, setValidation] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  useEffect(() => { pontosService.list().then(({ data }) => setPontos(asArray(data))).catch((err) => setError(getApiError(err))); }, []);

  async function loadTokens(id = pontoId) {
    if (!id) return;
    const { data } = await qrCodeService.listByPoint(id);
    setTokens(asArray(data));
  }

  async function generate() {
    setError(''); setMessage('');
    try {
      const { data } = await qrCodeService.create(pontoId);
      setMessage(`Token gerado: ${data.token}`);
      await loadTokens(pontoId);
    } catch (err) { setError(getApiError(err)); }
  }

  async function validate() {
    setError(''); setValidation('');
    try {
      const { data } = await qrCodeService.validate(token);
      setValidation(typeof data === 'string' ? data : JSON.stringify(data));
    } catch (err) { setError(getApiError(err)); }
  }

  return (
    <section className="page-stack">
      <div className="section-title"><QrCode /><div><h1>QR Code</h1><p>Gere, liste e valide tokens de presença.</p></div></div>
      <Message type="success">{message}</Message><Message type="error">{error}</Message><Message type="success">{validation && `Validação: ${validation}`}</Message>
      <div className="two-columns">
        <div className="panel form-grid">
          <h3>Gerar token</h3>
          <label><span>Ponto de coleta</span><select value={pontoId} onChange={(e) => { setPontoId(e.target.value); loadTokens(e.target.value).catch(() => {}); }}><option value="">Selecione</option>{pontos.map((p) => <option value={p.id} key={p.id}>{p.nome}</option>)}</select></label>
          <button className="primary-button" disabled={!pontoId} onClick={generate}>Gerar QR Code</button>
        </div>
        <div className="panel form-grid">
          <h3>Validar token</h3>
          <label><span>Token</span><input value={token} onChange={(e) => setToken(e.target.value)} placeholder="Cole o token" /></label>
          <button className="secondary-button" disabled={!token} onClick={validate}>Validar</button>
        </div>
      </div>
      <div className="panel table-wrap">
        <h3>Tokens ativos</h3>
        <table><thead><tr><th>ID</th><th>Token</th><th>Ponto</th><th>Ativo</th><th>Expiração</th></tr></thead><tbody>{tokens.map((t) => <tr key={t.id}><td>{t.id}</td><td><code>{t.token}</code></td><td>{t.ponto_coleta_id}</td><td>{t.ativo}</td><td>{formatDate(t.data_expiracao)}</td></tr>)}</tbody></table>
        {!tokens.length && <p className="empty">Selecione um ponto para listar tokens.</p>}
      </div>
    </section>
  );
}
