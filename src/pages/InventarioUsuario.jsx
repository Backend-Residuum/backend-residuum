import { useEffect, useMemo, useState } from 'react';
import {
  AlertTriangle,
  CheckCircle2,
  Edit3,
  ExternalLink,
  LocateFixed,
  MapPin,
  Navigation,
  PackageOpen,
  Plus,
  Recycle,
  Save,
  Trash2,
  X
} from 'lucide-react';
import { getApiError, descarteService, inventarioService, pontosService, qrCodeService } from '../services/api';
import {
  asArray,
  formatCoordinate,
  formatDate,
  formatKg,
  isValidCoordinatePair,
  mapsQueryUrl,
  parseCoordinate,
  parseDecimal
} from '../utils/format';
import Message from '../components/Message';
import LeafletMap from '../components/LeafletMap';

const tipos = ['plastico', 'papel', 'papelao', 'metal', 'vidro', 'aluminio', 'cobre', 'pilhas', 'baterias'];


function isVisibleInventoryItem(item) {
  return String(item?.status || '').toLowerCase() !== 'cancelado';
}

function quantidadeDisponivel(item) {
  const fromApi = Number(item?.quantidade_disponivel);
  if (Number.isFinite(fromApi)) return fromApi;
  return Math.max(Number(item?.quantidade || 0) - Number(item?.quantidade_reservada || 0), 0);
}

function statusLabel(status) {
  const labels = {
    disponivel: 'Disponível',
    em_transferencia: 'Em transferência',
    finalizado: 'Finalizado',
    cancelado: 'Cancelado'
  };
  return labels[status] || status || '-';
}

function statusClass(status) {
  if (status === 'disponivel') return 'ok';
  if (status === 'cancelado' || status === 'finalizado') return 'danger';
  return '';
}

function calcularDistanciaMetros(lat1, lon1, lat2, lon2) {
  const aLat = parseCoordinate(lat1);
  const aLon = parseCoordinate(lon1);
  const bLat = parseCoordinate(lat2);
  const bLon = parseCoordinate(lon2);

  if (!isValidCoordinatePair(aLat, aLon) || !isValidCoordinatePair(bLat, bLon)) return null;

  const R = 6371000;
  const toRad = (value) => (value * Math.PI) / 180;
  const dLat = toRad(bLat - aLat);
  const dLon = toRad(bLon - aLon);

  const h =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(toRad(aLat)) * Math.cos(toRad(bLat)) *
    Math.sin(dLon / 2) * Math.sin(dLon / 2);

  return 2 * R * Math.atan2(Math.sqrt(h), Math.sqrt(1 - h));
}

function formatMeters(value) {
  if (!Number.isFinite(value)) return '-';
  if (value >= 1000) return `${(value / 1000).toFixed(2)} km`;
  return `${Math.round(value)} m`;
}

export default function InventarioUsuario() {
  const [items, setItems] = useState([]);
  const [pontos, setPontos] = useState([]);
  const [pendentes, setPendentes] = useState([]);
  const [form, setForm] = useState({ tipo_residuo: 'plastico', quantidade: '', descricao: '', observacao: '' });
  const [editId, setEditId] = useState(null);
  const [editForm, setEditForm] = useState({ tipo_residuo: 'plastico', quantidade: '', descricao: '', observacao: '' });
  const [selectedItem, setSelectedItem] = useState(null);
  const [discardForm, setDiscardForm] = useState({ quantidade: '', ponto_coleta_id: '', usuario_lat: '', usuario_long: '', observacao: 'Transferência via inventário do usuário', qrcode_token: '' });
  const [locationInfo, setLocationInfo] = useState(null);
  const [locating, setLocating] = useState(false);
  const [qrValidation, setQrValidation] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  async function loadPendentes() {
    try {
      const { data } = await descarteService.myHistory();
      setPendentes(asArray(data).filter((item) => String(item.status || '').toLowerCase() === 'pendente'));
    } catch {
      setPendentes([]);
    }
  }

  async function loadInventario() {
    const { data } = await inventarioService.list();
    setItems(asArray(data).filter(isVisibleInventoryItem));
  }

  async function loadAll() {
    const [inventarioResp, pontosResp] = await Promise.all([
      inventarioService.list(),
      pontosService.list()
    ]);
    setItems(asArray(inventarioResp.data).filter(isVisibleInventoryItem));
    setPontos(asArray(pontosResp.data));
    await loadPendentes();
  }

  useEffect(() => {
    loadAll().catch((err) => setError(getApiError(err)));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function updateForm(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  function updateDiscard(field, value) {
    setDiscardForm((prev) => ({ ...prev, [field]: value }));
  }

  const activeItems = items.filter((item) => !['cancelado', 'finalizado'].includes(String(item.status).toLowerCase()));
  const totalDisponivel = activeItems.reduce((acc, item) => acc + quantidadeDisponivel(item), 0);
  const totalReservado = activeItems.reduce((acc, item) => acc + Number(item.quantidade_reservada || 0), 0);
  const itensDisponiveis = activeItems.filter((item) => item.status === 'disponivel' || quantidadeDisponivel(item) > 0).length;

  const selectedPoint = useMemo(() => pontos.find((p) => Number(p.id) === Number(discardForm.ponto_coleta_id)), [pontos, discardForm.ponto_coleta_id]);
  const selectedPointExternal = selectedPoint ? mapsQueryUrl(selectedPoint.latitude, selectedPoint.longitude) : '';
  const userMapsUrl = discardForm.usuario_lat && discardForm.usuario_long ? mapsQueryUrl(discardForm.usuario_lat, discardForm.usuario_long) : '';

  const userLocation = useMemo(() => {
    if (!isValidCoordinatePair(discardForm.usuario_lat, discardForm.usuario_long)) return null;
    return {
      latitude: parseCoordinate(discardForm.usuario_lat),
      longitude: parseCoordinate(discardForm.usuario_long),
      accuracy: Number(locationInfo?.accuracy || 0)
    };
  }, [discardForm.usuario_lat, discardForm.usuario_long, locationInfo]);

  const distanceToPoint = useMemo(() => {
    if (!selectedPoint || !discardForm.usuario_lat || !discardForm.usuario_long) return null;
    return calcularDistanciaMetros(discardForm.usuario_lat, discardForm.usuario_long, selectedPoint.latitude, selectedPoint.longitude);
  }, [selectedPoint, discardForm.usuario_lat, discardForm.usuario_long]);

  const isOutsideSelectedRadius = selectedPoint && Number.isFinite(distanceToPoint) && distanceToPoint > Number(selectedPoint.raio_operacao || 1000);

  async function createItem(e) {
    e.preventDefault();
    setError('');
    setMessage('');

    const quantidade = parseDecimal(form.quantidade);
    if (!Number.isFinite(quantidade) || quantidade < 1) {
      setError('Quantidade inválida. Informe um valor maior ou igual a 1.');
      return;
    }

    try {
      await inventarioService.create({
        tipo_residuo: form.tipo_residuo,
        quantidade,
        descricao: form.descricao || null,
        observacao: form.observacao || null
      });
      setMessage('Item cadastrado no seu inventário.');
      setForm({ tipo_residuo: 'plastico', quantidade: '', descricao: '', observacao: '' });
      await loadInventario();
    } catch (err) {
      setError(getApiError(err));
    }
  }

  function startEdit(item) {
    setEditId(item.id);
    setEditForm({
      tipo_residuo: item.tipo_residuo || 'plastico',
      quantidade: String(item.quantidade ?? ''),
      descricao: item.descricao || '',
      observacao: item.observacao || ''
    });
  }

  async function saveEdit(itemId) {
    setError('');
    setMessage('');
    const quantidade = parseDecimal(editForm.quantidade);
    if (!Number.isFinite(quantidade) || quantidade < 1) {
      setError('Quantidade inválida. Informe um valor maior ou igual a 1.');
      return;
    }

    try {
      await inventarioService.update(itemId, {
        tipo_residuo: editForm.tipo_residuo,
        quantidade,
        descricao: editForm.descricao || null,
        observacao: editForm.observacao || null
      });
      setMessage('Item atualizado.');
      setEditId(null);
      await loadInventario();
    } catch (err) {
      setError(getApiError(err));
    }
  }

  async function removeItem(itemId) {
    setError('');
    setMessage('');
    const confirmRemove = window.confirm('Remover este item do inventário? Itens com quantidade reservada em descarte pendente não podem ser removidos.');
    if (!confirmRemove) return;

    try {
      await inventarioService.remove(itemId);
      setMessage('Item removido do inventário.');
      if (selectedItem?.id === itemId) setSelectedItem(null);
      setItems((prev) => prev.filter((item) => Number(item.id) !== Number(itemId)));
      await loadInventario();
    } catch (err) {
      setError(getApiError(err));
    }
  }

  function startDiscard(item) {
    const disponivel = quantidadeDisponivel(item);
    setSelectedItem(item);
    setQrValidation('');
    setError('');
    setMessage('');
    setDiscardForm((prev) => ({
      ...prev,
      quantidade: disponivel > 0 ? String(disponivel) : '',
      observacao: `Descarte de ${item.tipo_residuo} a partir do inventário`,
      qrcode_token: ''
    }));
    setTimeout(() => {
      document.getElementById('inventario-descartar-panel')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 80);
  }

  function useBrowserLocation() {
    setError('');
    setLocationInfo(null);

    if (!navigator.geolocation) {
      setError('Seu navegador não tem suporte a geolocalização. Preencha latitude e longitude manualmente.');
      return;
    }

    setLocating(true);

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const latitude = Number(pos.coords.latitude.toFixed(6));
        const longitude = Number(pos.coords.longitude.toFixed(6));
        const accuracy = Math.round(pos.coords.accuracy || 0);

        setDiscardForm((prev) => ({ ...prev, usuario_lat: latitude, usuario_long: longitude }));
        setLocationInfo({ accuracy, capturedAt: new Date().toLocaleTimeString('pt-BR'), source: 'browser' });

        if (accuracy > 1000) {
          setError(`Sua localização foi capturada, mas a precisão está baixa: aproximadamente ${formatMeters(accuracy)}. No computador isso pode acontecer por causa da rede/IP.`);
        }
        setLocating(false);
      },
      (err) => {
        let msg = 'Não foi possível obter a localização. Preencha manualmente.';
        if (err.code === 1) msg = 'Permissão de localização negada. Libere a localização no navegador ou preencha manualmente.';
        if (err.code === 2) msg = 'Localização indisponível no momento. Tente novamente ou preencha manualmente.';
        if (err.code === 3) msg = 'Tempo esgotado ao buscar localização. Tente novamente ou preencha manualmente.';
        setError(msg);
        setLocating(false);
      },
      { enableHighAccuracy: true, timeout: 20000, maximumAge: 0 }
    );
  }

  function usarCoordenadasDoPontoParaTeste() {
    if (!selectedPoint) {
      setError('Selecione um ponto de coleta antes de usar as coordenadas de teste.');
      return;
    }

    setDiscardForm((prev) => ({
      ...prev,
      usuario_lat: Number(parseCoordinate(selectedPoint.latitude).toFixed(6)),
      usuario_long: Number(parseCoordinate(selectedPoint.longitude).toFixed(6))
    }));
    setLocationInfo({ accuracy: 0, capturedAt: new Date().toLocaleTimeString('pt-BR'), source: 'manual-test' });
    setError('');
  }

  async function validateQr() {
    setError('');
    setQrValidation('');
    if (!discardForm.qrcode_token) return;
    try {
      const { data } = await qrCodeService.validate(discardForm.qrcode_token);
      setQrValidation(typeof data === 'string' ? data : JSON.stringify(data));
    } catch (err) {
      setError(getApiError(err));
    }
  }

  async function submitDiscard(e) {
    e.preventDefault();
    setError('');
    setMessage('');

    if (!selectedItem) {
      setError('Selecione um item do inventário para descartar.');
      return;
    }

    const quantidade = parseDecimal(discardForm.quantidade);
    const disponivel = quantidadeDisponivel(selectedItem);
    const usuarioLat = parseCoordinate(discardForm.usuario_lat);
    const usuarioLong = parseCoordinate(discardForm.usuario_long);

    if (!Number.isFinite(quantidade) || quantidade < 1) {
      setError('Quantidade inválida. Informe um valor maior ou igual a 1.');
      return;
    }

    if (quantidade > disponivel) {
      setError(`Quantidade maior do que o disponível no inventário. Disponível: ${formatKg(disponivel)}.`);
      return;
    }

    if (!discardForm.ponto_coleta_id) {
      setError('Selecione um ponto de coleta.');
      return;
    }

    if (!isValidCoordinatePair(usuarioLat, usuarioLong)) {
      setError('Localização inválida. Use latitude e longitude em formato decimal, por exemplo: -3.075900 e -60.060000.');
      return;
    }

    try {
      const { data } = await inventarioService.discard(selectedItem.id, {
        quantidade,
        ponto_coleta_id: Number(discardForm.ponto_coleta_id),
        usuario_lat: usuarioLat,
        usuario_long: usuarioLong,
        observacao: discardForm.observacao || 'Transferência via inventário do usuário',
        qrcode_token: discardForm.qrcode_token || null
      });
      setMessage(`Descarte criado como pendente. ID: ${data.id_descarte} | A baixa no inventário ocorrerá somente após a confirmação da cooperativa/admin.`);
      setSelectedItem(null);
      setDiscardForm((prev) => ({ ...prev, quantidade: '', observacao: 'Transferência via inventário do usuário', qrcode_token: '' }));
      await loadInventario();
      await loadPendentes();
    } catch (err) {
      setError(getApiError(err));
    }
  }

  return (
    <section className="page-stack">
      <div className="section-title">
        <PackageOpen />
        <div>
          <h1>Meu inventário</h1>
          <p>Cadastre os resíduos que você possui e transfira uma parte para um ponto de coleta quando for descartar.</p>
        </div>
      </div>

      <Message type="success">{message}</Message>
      <Message type="error">{error}</Message>

      <div className="stats-grid">
        <article className="stat-card"><PackageOpen /><span>Itens listados</span><strong>{items.length}</strong></article>
        <article className="stat-card"><CheckCircle2 /><span>Disponíveis</span><strong>{itensDisponiveis}</strong></article>
        <article className="stat-card"><Recycle /><span>Total disponível</span><strong>{formatKg(totalDisponivel)}</strong></article>
        <article className="stat-card"><AlertTriangle /><span>Reservado</span><strong>{formatKg(totalReservado)}</strong></article>
      </div>

      <div className="two-columns inventory-layout">
        <form className="panel form-grid" onSubmit={createItem}>
          <h3><Plus size={18} /> Cadastrar resíduo</h3>
          <label><span>Tipo de resíduo</span><select value={form.tipo_residuo} onChange={(e) => updateForm('tipo_residuo', e.target.value)}>{tipos.map((t) => <option key={t} value={t}>{t}</option>)}</select></label>
          <label><span>Quantidade total kg</span><input required type="text" inputMode="decimal" placeholder="Ex: 6 ou 6,5" value={form.quantidade} onChange={(e) => updateForm('quantidade', e.target.value)} /></label>
          <label><span>Descrição</span><input value={form.descricao} onChange={(e) => updateForm('descricao', e.target.value)} placeholder="Ex: garrafas PET acumuladas em casa" /></label>
          <label><span>Observação</span><input value={form.observacao} onChange={(e) => updateForm('observacao', e.target.value)} placeholder="Opcional" /></label>
          <button className="primary-button"><Plus size={16} /> Adicionar ao inventário</button>
        </form>

        <div className="panel">
          <div className="inventory-header">
            <div>
              <h3>Resíduos cadastrados</h3>
              <p className="muted">A lista mostra apenas itens ativos. Itens removidos não aparecem e não entram nas contagens. Descartes pendentes aparecem na seção abaixo.</p>
            </div>
          </div>
          <div className="inventory-user-list">
            {items.map((item) => {
              const disponivel = quantidadeDisponivel(item);
              const isEditing = editId === item.id;
              const canDiscard = disponivel >= 1 && !['cancelado', 'finalizado'].includes(item.status);

              return (
                <article className="inventory-user-card" key={item.id}>
                  {!isEditing ? (
                    <>
                      <div className="inventory-card-main">
                        <div>
                          <div className="inventory-title-row">
                            <h4>{item.tipo_residuo}</h4>
                            <span className={`badge ${statusClass(item.status)}`}>{statusLabel(item.status)}</span>
                          </div>
                          <p>{item.descricao || 'Sem descrição'}</p>
                          {item.observacao && <small>{item.observacao}</small>}
                        </div>
                        <div className="inventory-amounts">
                          <span>Total <strong>{formatKg(item.quantidade)}</strong></span>
                          <span>Reservado <strong>{formatKg(item.quantidade_reservada)}</strong></span>
                          <span>Disponível <strong>{formatKg(disponivel)}</strong></span>
                        </div>
                      </div>
                      <div className="inventory-card-footer">
                        <small>Cadastrado em {formatDate(item.data_cadastro)}</small>
                        <div className="card-actions">
                          <button className="secondary-button small" type="button" onClick={() => startEdit(item)}><Edit3 size={15} /> Editar</button>
                          <button className="secondary-button small" type="button" disabled={!canDiscard} onClick={() => startDiscard(item)}><Recycle size={15} /> Descartar</button>
                          <button className="icon-button danger" type="button" onClick={() => removeItem(item.id)} title="Remover"><Trash2 size={16} /></button>
                        </div>
                      </div>
                    </>
                  ) : (
                    <div className="edit-inventory-grid">
                      <label><span>Tipo</span><select value={editForm.tipo_residuo} onChange={(e) => setEditForm((prev) => ({ ...prev, tipo_residuo: e.target.value }))}>{tipos.map((t) => <option key={t} value={t}>{t}</option>)}</select></label>
                      <label><span>Quantidade</span><input type="text" inputMode="decimal" value={editForm.quantidade} onChange={(e) => setEditForm((prev) => ({ ...prev, quantidade: e.target.value }))} /></label>
                      <label><span>Descrição</span><input value={editForm.descricao} onChange={(e) => setEditForm((prev) => ({ ...prev, descricao: e.target.value }))} /></label>
                      <label><span>Observação</span><input value={editForm.observacao} onChange={(e) => setEditForm((prev) => ({ ...prev, observacao: e.target.value }))} /></label>
                      <div className="card-actions">
                        <button className="primary-button small" type="button" onClick={() => saveEdit(item.id)}><Save size={15} /> Salvar</button>
                        <button className="secondary-button small" type="button" onClick={() => setEditId(null)}><X size={15} /> Cancelar</button>
                      </div>
                    </div>
                  )}
                </article>
              );
            })}
            {!items.length && <p className="empty">Nenhum item encontrado no inventário.</p>}
          </div>
        </div>
      </div>

      <div className="panel">
        <div className="inventory-header">
          <div>
            <h3>Descartes pendentes do inventário</h3>
            <p className="muted">Estes descartes ainda aguardam confirmação do admin/cooperativa. A baixa no inventário só acontece pela quantidade confirmada.</p>
          </div>
          <button className="secondary-button small" type="button" onClick={loadPendentes}>Atualizar</button>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr><th>ID</th><th>Tipo</th><th>Qtd. declarada</th><th>Ponto</th><th>Status</th><th>Data</th></tr>
            </thead>
            <tbody>
              {pendentes.map((d) => (
                <tr key={d.id_descarte || d.id}>
                  <td>{d.id_descarte || d.id}</td>
                  <td>{d.tipo_residuo || '-'}</td>
                  <td>{formatKg(d.quantidade)}</td>
                  <td>{d.ponto_coleta_id || '-'}</td>
                  <td><span className="badge">{d.status}</span></td>
                  <td>{formatDate(d.data_desc)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {!pendentes.length && <p className="empty">Nenhum descarte pendente no momento.</p>}
        </div>
      </div>

      {selectedItem && (
        <form className="panel form-grid wide" id="inventario-descartar-panel" onSubmit={submitDiscard}>
          <h3><Recycle size={18} /> Descartar item do inventário</h3>
          <div className="inventory-selected-summary">
            <strong>{selectedItem.tipo_residuo}</strong>
            <span>Total: {formatKg(selectedItem.quantidade)}</span>
            <span>Reservado: {formatKg(selectedItem.quantidade_reservada)}</span>
            <span>Disponível: {formatKg(quantidadeDisponivel(selectedItem))}</span>
          </div>

          <label><span>Ponto de coleta</span><select required value={discardForm.ponto_coleta_id} onChange={(e) => updateDiscard('ponto_coleta_id', e.target.value)}><option value="">Selecione</option>{pontos.map((p) => <option key={p.id} value={p.id}>{p.nome}</option>)}</select></label>
          <label><span>Quantidade que deseja descartar kg</span><input required type="text" inputMode="decimal" value={discardForm.quantidade} onChange={(e) => updateDiscard('quantidade', e.target.value)} placeholder="Ex: 2 ou 2,5" /></label>
          <label><span>Latitude usuário</span><input required type="text" inputMode="decimal" value={discardForm.usuario_lat} onChange={(e) => updateDiscard('usuario_lat', e.target.value)} placeholder="Ex: -3.075900" /></label>
          <label><span>Longitude usuário</span><input required type="text" inputMode="decimal" value={discardForm.usuario_long} onChange={(e) => updateDiscard('usuario_long', e.target.value)} placeholder="Ex: -60.060000" /></label>
          <label><span>Observação</span><input maxLength="50" value={discardForm.observacao} onChange={(e) => updateDiscard('observacao', e.target.value)} /></label>
          <label><span>Token QR Code opcional</span><input value={discardForm.qrcode_token} onChange={(e) => updateDiscard('qrcode_token', e.target.value)} placeholder="Cole o token se houver" /></label>

          <div className="location-actions">
            <button type="button" className="secondary-button" onClick={useBrowserLocation} disabled={locating}><LocateFixed size={16} /> {locating ? 'Buscando localização...' : 'Usar minha localização'}</button>
            <button type="button" className="secondary-button" onClick={usarCoordenadasDoPontoParaTeste} disabled={!selectedPoint}><Navigation size={16} /> Usar coordenada do ponto para teste</button>
            <button type="button" className="secondary-button" disabled={!discardForm.qrcode_token} onClick={validateQr}>Validar QR Code</button>
            {userMapsUrl && <a className="secondary-button" href={userMapsUrl} target="_blank" rel="noreferrer"><ExternalLink size={15} /> Ver minha coordenada</a>}
          </div>

          {qrValidation && <Message type="success">QR validado: {qrValidation}</Message>}

          {(locationInfo || Number.isFinite(distanceToPoint)) && (
            <div className={`location-debug ${isOutsideSelectedRadius ? 'warning' : 'ok'}`}>
              <div>
                <strong>Validação de presença</strong>
                <p>Latitude {formatCoordinate(discardForm.usuario_lat)} • Longitude {formatCoordinate(discardForm.usuario_long)}{locationInfo?.capturedAt ? ` • Capturada às ${locationInfo.capturedAt}` : ''}</p>
                {locationInfo?.source === 'browser' && <p>Precisão estimada pelo navegador: <strong>{formatMeters(locationInfo.accuracy)}</strong></p>}
                {locationInfo?.source === 'manual-test' && <p>Coordenada copiada do ponto de coleta apenas para facilitar testes no computador.</p>}
                {Number.isFinite(distanceToPoint) && selectedPoint && <p>Distância até o ponto: <strong>{formatMeters(distanceToPoint)}</strong> • Raio permitido: <strong>{formatMeters(Number(selectedPoint.raio_operacao || 1000))}</strong></p>}
              </div>
              {isOutsideSelectedRadius && <div className="location-warning"><AlertTriangle size={18} /> Sua coordenada parece estar fora do raio do ponto.</div>}
            </div>
          )}

          <div className="form-actions-line">
            <button className="primary-button"><Recycle size={16} /> Criar descarte pendente</button>
            <button type="button" className="secondary-button" onClick={() => setSelectedItem(null)}><X size={16} /> Cancelar</button>
          </div>
        </form>
      )}

      {selectedPoint && selectedItem && (
        <div className="panel map-panel compact-map">
          <div className="map-panel-header">
            <div>
              <h3><MapPin size={18} /> {selectedPoint.nome}</h3>
              <p>{selectedPoint.endereco || 'Sem endereço informado'}</p>
              <small>Latitude {formatCoordinate(selectedPoint.latitude)} • Longitude {formatCoordinate(selectedPoint.longitude)}</small>
            </div>
            {selectedPointExternal && <a className="secondary-button" href={selectedPointExternal} target="_blank" rel="noreferrer"><ExternalLink size={15} /> Abrir no OpenStreetMap</a>}
          </div>
          <LeafletMap
            points={[selectedPoint]}
            selectedPoint={selectedPoint}
            userLocation={userLocation}
            height={340}
            focusSelected
            selectedZoom={18}
          />
        </div>
      )}
    </section>
  );
}
