import { useEffect, useMemo, useRef, useState } from 'react';
import { Edit3, ExternalLink, Filter, LocateFixed, MapPin, Plus, Search, X } from 'lucide-react';
import { getApiError, pontosService } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { asArray, formatCoordinate, formatKg, isValidCoordinatePair, mapsQueryUrl, parseCoordinate, parseDecimal } from '../utils/format';
import Message from '../components/Message';
import Inventory from '../components/Inventory';
import LeafletMap from '../components/LeafletMap';

const tipos = ['', 'plastico', 'papel', 'papelao', 'metal', 'vidro', 'aluminio', 'cobre', 'pilhas', 'baterias'];
const statusOptions = ['ativo', 'cheio', 'inativo'];
const emptyForm = {
  nome: '',
  endereco: '',
  latitude: '',
  longitude: '',
  raio_operacao: 1000,
  capacidade_maxima: 500,
  tipos_residuos_aceitos: ['plastico'],
  horario_funcionamento: '',
  status: 'ativo',
  ativo: 1
};

function normalizeStatus(ponto) {
  return String(ponto?.status_calculado || ponto?.status || (ponto?.ativo ? 'ativo' : 'inativo')).toLowerCase();
}

function statusLabel(status) {
  const value = String(status || '').toLowerCase();
  if (value === 'cheio') return 'Cheio';
  if (value === 'inativo') return 'Inativo';
  return 'Ativo';
}

function statusClass(status) {
  const value = String(status || '').toLowerCase();
  if (value === 'cheio') return 'warning';
  if (value === 'inativo') return 'danger';
  return 'ok';
}

function formatPercent(value) {
  const number = Number(value || 0);
  if (!Number.isFinite(number)) return '0%';
  return `${number.toLocaleString('pt-BR', { maximumFractionDigits: 1 })}%`;
}

function getTiposAceitos(ponto) {
  if (Array.isArray(ponto?.tipos_residuos_aceitos)) return ponto.tipos_residuos_aceitos;
  if (typeof ponto?.tipos_residuos_aceitos === 'string') {
    try {
      const parsed = JSON.parse(ponto.tipos_residuos_aceitos);
      if (Array.isArray(parsed)) return parsed;
    } catch {
      return ponto.tipos_residuos_aceitos.split(',').map((item) => item.trim()).filter(Boolean);
    }
  }
  return [];
}

export default function Pontos() {
  const { user } = useAuth();
  const isAdmin = String(user?.role).toLowerCase() === 'admin';
  const [pontos, setPontos] = useState([]);
  const [form, setForm] = useState(emptyForm);
  const [filters, setFilters] = useState({ tipo_residuo: '', distancia_km: '', lat: '', long: '' });
  const [editingId, setEditingId] = useState(null);
  const [selectedPoint, setSelectedPoint] = useState(null);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [locating, setLocating] = useState(false);
  const [accuracy, setAccuracy] = useState(null);
  const mapPanelRef = useRef(null);

  async function load(customFilters = filters) {
    const params = {};
    if (customFilters.tipo_residuo) params.tipo_residuo = customFilters.tipo_residuo;
    const lat = parseCoordinate(customFilters.lat);
    const lng = parseCoordinate(customFilters.long);
    const distancia = parseDecimal(customFilters.distancia_km);
    if (Number.isFinite(lat) && Number.isFinite(lng)) {
      params.lat = lat;
      params.long = lng;
    }
    if (Number.isFinite(distancia) && distancia > 0) params.distancia_km = distancia;
    if (isAdmin) params.incluir_inativos = true;

    const { data } = await pontosService.list(params);
    const list = asArray(data);
    setPontos(list);
    if (selectedPoint) {
      const updated = list.find((p) => Number(p.id) === Number(selectedPoint.id));
      setSelectedPoint(updated || null);
    }
  }

  useEffect(() => { load().catch((err) => setError(getApiError(err))); }, [isAdmin]);

  function update(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  function updateFilter(field, value) {
    setFilters((prev) => ({ ...prev, [field]: value }));
  }

  function updateTipos(tipo, checked) {
    setForm((prev) => {
      const current = Array.isArray(prev.tipos_residuos_aceitos) ? prev.tipos_residuos_aceitos : [];
      const next = checked ? [...new Set([...current, tipo])] : current.filter((item) => item !== tipo);
      return { ...prev, tipos_residuos_aceitos: next };
    });
  }

  function edit(ponto) {
    setEditingId(ponto.id);
    setForm({
      nome: ponto.nome || '',
      endereco: ponto.endereco || '',
      latitude: formatCoordinate(ponto.latitude),
      longitude: formatCoordinate(ponto.longitude),
      raio_operacao: ponto.raio_operacao || 1000,
      capacidade_maxima: ponto.capacidade_maxima || 500,
      tipos_residuos_aceitos: getTiposAceitos(ponto).length ? getTiposAceitos(ponto) : ['plastico'],
      horario_funcionamento: ponto.horario_funcionamento || '',
      status: ponto.status || (ponto.ativo ? 'ativo' : 'inativo'),
      ativo: ponto.ativo ?? 1
    });
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  async function submit(e) {
    e.preventDefault();
    setError(''); setMessage('');

    const latitude = parseCoordinate(form.latitude);
    const longitude = parseCoordinate(form.longitude);
    const raioOperacao = parseDecimal(form.raio_operacao);
    const capacidadeMaxima = parseDecimal(form.capacidade_maxima);

    if (!isValidCoordinatePair(latitude, longitude)) {
      setError('Coordenadas inválidas. Use latitude e longitude em formato decimal, por exemplo: -3.075900 e -60.060000.');
      return;
    }

    if (!Array.isArray(form.tipos_residuos_aceitos) || form.tipos_residuos_aceitos.length === 0) {
      setError('Selecione pelo menos um tipo de resíduo aceito pelo ponto.');
      return;
    }

    const payload = {
      nome: form.nome,
      endereco: form.endereco || null,
      latitude,
      longitude,
      raio_operacao: Number.isFinite(raioOperacao) ? raioOperacao : 1000,
      capacidade_maxima: Number.isFinite(capacidadeMaxima) ? capacidadeMaxima : 500,
      tipos_residuos_aceitos: form.tipos_residuos_aceitos,
      horario_funcionamento: form.horario_funcionamento || null,
      status: form.status || 'ativo',
      ativo: form.status === 'inativo' ? 0 : Number(form.ativo)
    };
    try {
      if (editingId) {
        await pontosService.update(editingId, payload);
        setMessage('Ponto atualizado com sucesso.');
      } else {
        await pontosService.create(payload);
        setMessage('Ponto criado com sucesso.');
      }
      setForm(emptyForm);
      setEditingId(null);
      await load();
    } catch (err) { setError(getApiError(err)); }
  }

  async function applyFilters(e) {
    e?.preventDefault?.();
    setError(''); setMessage('');
    try {
      await load(filters);
      setMessage('Filtros aplicados.');
    } catch (err) {
      setError(getApiError(err));
    }
  }

  async function clearFilters() {
    const empty = { tipo_residuo: '', distancia_km: '', lat: '', long: '' };
    setFilters(empty);
    setAccuracy(null);
    setError(''); setMessage('');
    await load(empty).catch((err) => setError(getApiError(err)));
  }

  function useMyLocation() {
    if (!navigator.geolocation) {
      setError('Seu navegador não oferece suporte à geolocalização.');
      return;
    }
    setLocating(true);
    setError('');
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const lat = Number(position.coords.latitude.toFixed(6));
        const lng = Number(position.coords.longitude.toFixed(6));
        setFilters((prev) => ({ ...prev, lat, long: lng }));
        setAccuracy(position.coords.accuracy || null);
        setLocating(false);
      },
      () => {
        setLocating(false);
        setError('Não foi possível capturar sua localização. Verifique a permissão do navegador.');
      },
      { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 }
    );
  }

  function selectPointOnMap(point) {
    setSelectedPoint(point);
    setTimeout(() => {
      mapPanelRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 80);
  }

  const selectedExternalUrl = useMemo(() => selectedPoint ? mapsQueryUrl(selectedPoint.latitude, selectedPoint.longitude) : '', [selectedPoint]);

  return (
    <section className="page-stack">
      <div className="section-title"><MapPin /><div><h1>Pontos de coleta</h1><p>Consulte pontos disponíveis, filtre por material e distância, e veja os detalhes no mapa.</p></div></div>
      <Message type="success">{message}</Message><Message type="error">{error}</Message>
      {isAdmin && (
        <form className="panel form-grid wide" onSubmit={submit}>
          <h3>{editingId ? 'Editar ponto de coleta' : 'Criar ponto de coleta'}</h3>
          <label><span>Nome</span><input required value={form.nome} onChange={(e) => update('nome', e.target.value)} /></label>
          <label><span>Endereço</span><input value={form.endereco} onChange={(e) => update('endereco', e.target.value)} /></label>
          <label><span>Latitude</span><input required type="text" inputMode="decimal" placeholder="Ex: -3.075900" value={form.latitude} onChange={(e) => update('latitude', e.target.value)} /></label>
          <label><span>Longitude</span><input required type="text" inputMode="decimal" placeholder="Ex: -60.060000" value={form.longitude} onChange={(e) => update('longitude', e.target.value)} /></label>
          <label><span>Raio de operação</span><input type="text" inputMode="decimal" value={form.raio_operacao} onChange={(e) => update('raio_operacao', e.target.value)} /></label>
          <label><span>Capacidade máxima (kg)</span><input type="text" inputMode="decimal" value={form.capacidade_maxima} onChange={(e) => update('capacidade_maxima', e.target.value)} /></label>
          <label><span>Horário de funcionamento</span><input placeholder="Ex: Segunda a sábado, 08h às 18h" value={form.horario_funcionamento} onChange={(e) => update('horario_funcionamento', e.target.value)} /></label>
          <label><span>Status</span><select value={form.status} onChange={(e) => update('status', e.target.value)}>{statusOptions.map((status) => <option key={status} value={status}>{statusLabel(status)}</option>)}</select></label>
          <div className="form-field-full checkbox-group">
            <strong>Tipos de resíduos aceitos</strong>
            <div className="chips-grid">
              {tipos.filter(Boolean).map((tipo) => (
                <label className="check-chip" key={tipo}>
                  <input type="checkbox" checked={form.tipos_residuos_aceitos.includes(tipo)} onChange={(e) => updateTipos(tipo, e.target.checked)} />
                  <span>{tipo}</span>
                </label>
              ))}
            </div>
          </div>
          <button className="primary-button"><Plus size={16} /> {editingId ? 'Salvar alterações' : 'Criar ponto'}</button>
        </form>
      )}

      <form className="panel filter-panel" onSubmit={applyFilters}>
        <div className="filter-title"><Filter size={18} /><div><h3>Filtrar pontos</h3><p>{isAdmin ? 'Você está vendo pontos ativos, cheios e inativos para poder editar ou reativar cadastros.' : 'Use filtros para encontrar pontos que aceitam seu material e estão próximos.'}</p></div></div>
        <label><span>Tipo de resíduo</span><select value={filters.tipo_residuo} onChange={(e) => updateFilter('tipo_residuo', e.target.value)}>{tipos.map((tipo) => <option key={tipo || 'todos'} value={tipo}>{tipo ? tipo : 'Todos os tipos'}</option>)}</select></label>
        <label><span>Distância máxima (km)</span><input type="text" inputMode="decimal" placeholder="Ex: 5" value={filters.distancia_km} onChange={(e) => updateFilter('distancia_km', e.target.value)} /></label>
        <label><span>Latitude atual</span><input type="text" inputMode="decimal" value={filters.lat} onChange={(e) => updateFilter('lat', e.target.value)} /></label>
        <label><span>Longitude atual</span><input type="text" inputMode="decimal" value={filters.long} onChange={(e) => updateFilter('long', e.target.value)} /></label>
        <div className="filter-actions">
          <button type="button" className="secondary-button" onClick={useMyLocation} disabled={locating}><LocateFixed size={16} /> {locating ? 'Capturando...' : 'Usar minha localização'}</button>
          <button className="primary-button"><Search size={16} /> Aplicar filtros</button>
          <button type="button" className="secondary-button" onClick={clearFilters}><X size={16} /> Limpar</button>
          {accuracy ? <small>Precisão aproximada da localização: {Math.round(accuracy)}m</small> : null}
        </div>
      </form>

      {selectedPoint && (
        <div className="panel map-panel" ref={mapPanelRef}>
          <div className="map-panel-header">
            <div>
              <h3>{selectedPoint.nome}</h3>
              <p>{selectedPoint.endereco || 'Sem endereço informado'}</p>
              <small>Latitude {formatCoordinate(selectedPoint.latitude)} • Longitude {formatCoordinate(selectedPoint.longitude)}</small>
            </div>
            <div className="map-actions">
              {selectedExternalUrl && <a className="secondary-button" href={selectedExternalUrl} target="_blank" rel="noreferrer"><ExternalLink size={15} /> Abrir no OpenStreetMap</a>}
              <button className="icon-button" onClick={() => setSelectedPoint(null)} aria-label="Fechar mapa"><X size={18} /></button>
            </div>
          </div>
          <div className="point-details-grid">
            <span><strong>Status:</strong> <em className={`badge ${statusClass(normalizeStatus(selectedPoint))}`}>{statusLabel(normalizeStatus(selectedPoint))}</em></span>
            <span><strong>Horário:</strong> {selectedPoint.horario_funcionamento || 'Não informado'}</span>
            <span><strong>Capacidade:</strong> {formatKg(selectedPoint.capacidade_maxima)}</span>
            <span><strong>Ocupação:</strong> {formatKg(selectedPoint.total_inventario)} / {formatPercent(selectedPoint.percentual_ocupacao)}</span>
            <span><strong>Tipos aceitos:</strong> {getTiposAceitos(selectedPoint).join(', ') || 'Não informado'}</span>
          </div>
          {isValidCoordinatePair(selectedPoint.latitude, selectedPoint.longitude) ? (
            <LeafletMap
              points={pontos}
              selectedPoint={selectedPoint}
              onSelectPoint={selectPointOnMap}
              height={420}
              focusSelected
              selectedZoom={18}
            />
          ) : (
            <Message type="error">Este ponto não possui coordenadas válidas.</Message>
          )}
        </div>
      )}
      <div className="cards-grid">
        {pontos.map((p) => {
          const status = normalizeStatus(p);
          const tiposAceitos = getTiposAceitos(p);
          return (
            <article className={`point-card clickable ${selectedPoint?.id === p.id ? 'selected' : ''}`} key={p.id} onClick={() => selectPointOnMap(p)}>
              <div className="point-head"><h3>{p.nome}</h3><span className={`badge ${statusClass(status)}`}>{statusLabel(status)}</span></div>
              <p>{p.endereco || 'Sem endereço informado'}</p>
              <small>Lat: {formatCoordinate(p.latitude)} | Long: {formatCoordinate(p.longitude)} | Raio: {p.raio_operacao}m</small>
              <div className="point-meta-grid">
                <span><strong>Horário</strong>{p.horario_funcionamento || 'Não informado'}</span>
                <span><strong>Capacidade</strong>{formatKg(p.capacidade_maxima)}</span>
                <span><strong>Ocupação</strong>{formatKg(p.total_inventario)} • {formatPercent(p.percentual_ocupacao)}</span>
              </div>
              <div className="accepted-tags">
                {tiposAceitos.length ? tiposAceitos.map((tipo) => <span key={tipo}>{tipo}</span>) : <span>Tipos não informados</span>}
              </div>
              <Inventory inventario={p.inventario} />
              <div className="card-actions">
                <button type="button" className="secondary-button" onClick={(e) => { e.stopPropagation(); selectPointOnMap(p); }}><MapPin size={15} /> Ver no mapa</button>
                {isAdmin && <button type="button" className="secondary-button" onClick={(e) => { e.stopPropagation(); edit(p); }}><Edit3 size={15} /> Editar</button>}
              </div>
            </article>
          );
        })}
        {!pontos.length && <p className="empty">Nenhum ponto encontrado com os filtros selecionados.</p>}
      </div>
    </section>
  );
}
