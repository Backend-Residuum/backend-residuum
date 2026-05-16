import { useEffect, useMemo, useState } from 'react';
import { AlertTriangle, ExternalLink, LocateFixed, MapPin, Navigation, Recycle } from 'lucide-react';
import { descarteService, getApiError, pontosService, qrCodeService } from '../services/api';
import { asArray, formatCoordinate, isValidCoordinatePair, mapsQueryUrl, parseCoordinate, parseDecimal } from '../utils/format';
import Message from '../components/Message';
import LeafletMap from '../components/LeafletMap';

const tipos = ['plastico', 'papel', 'papelao', 'metal', 'vidro', 'aluminio', 'cobre', 'pilhas', 'baterias'];

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

export default function Descartar() {
  const [pontos, setPontos] = useState([]);
  const [form, setForm] = useState({ quantidade: '', tipo_residuo: 'plastico', observacao: 'Descarte via APP', usuario_lat: '', usuario_long: '', ponto_coleta_id: '', qrcode_token: '' });
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [qrValidation, setQrValidation] = useState('');
  const [locationInfo, setLocationInfo] = useState(null);
  const [locating, setLocating] = useState(false);

  useEffect(() => { pontosService.list().then(({ data }) => setPontos(asArray(data))).catch((err) => setError(getApiError(err))); }, []);

  function update(field, value) { setForm((prev) => ({ ...prev, [field]: value })); }

  const selectedPoint = useMemo(() => pontos.find((p) => Number(p.id) === Number(form.ponto_coleta_id)), [pontos, form.ponto_coleta_id]);
  const selectedPointExternal = selectedPoint ? mapsQueryUrl(selectedPoint.latitude, selectedPoint.longitude) : '';
  const userMapsUrl = form.usuario_lat && form.usuario_long ? mapsQueryUrl(form.usuario_lat, form.usuario_long) : '';

  const userLocation = useMemo(() => {
    if (!isValidCoordinatePair(form.usuario_lat, form.usuario_long)) return null;
    return {
      latitude: parseCoordinate(form.usuario_lat),
      longitude: parseCoordinate(form.usuario_long),
      accuracy: Number(locationInfo?.accuracy || 0)
    };
  }, [form.usuario_lat, form.usuario_long, locationInfo]);

  const distanceToPoint = useMemo(() => {
    if (!selectedPoint || !form.usuario_lat || !form.usuario_long) return null;
    return calcularDistanciaMetros(form.usuario_lat, form.usuario_long, selectedPoint.latitude, selectedPoint.longitude);
  }, [selectedPoint, form.usuario_lat, form.usuario_long]);

  const isOutsideSelectedRadius = selectedPoint && Number.isFinite(distanceToPoint) && distanceToPoint > Number(selectedPoint.raio_operacao || 1000);

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

        setForm((prev) => ({
          ...prev,
          usuario_lat: latitude,
          usuario_long: longitude
        }));

        setLocationInfo({
          accuracy,
          capturedAt: new Date().toLocaleTimeString('pt-BR'),
          source: 'browser'
        });

        if (accuracy > 1000) {
          setError(`Sua localização foi capturada, mas a precisão está baixa: aproximadamente ${formatMeters(accuracy)}. No computador isso pode acontecer por causa da rede/IP. Para teste, use o celular ou ajuste manualmente as coordenadas.`);
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
      {
        enableHighAccuracy: true,
        timeout: 20000,
        maximumAge: 0
      }
    );
  }

  function usarCoordenadasDoPontoParaTeste() {
    if (!selectedPoint) {
      setError('Selecione um ponto de coleta antes de usar as coordenadas de teste.');
      return;
    }

    setForm((prev) => ({
      ...prev,
      usuario_lat: Number(parseCoordinate(selectedPoint.latitude).toFixed(6)),
      usuario_long: Number(parseCoordinate(selectedPoint.longitude).toFixed(6))
    }));

    setLocationInfo({
      accuracy: 0,
      capturedAt: new Date().toLocaleTimeString('pt-BR'),
      source: 'manual-test'
    });
    setError('');
  }

  async function validateQr() {
    setError(''); setQrValidation('');
    try {
      const { data } = await qrCodeService.validate(form.qrcode_token);
      setQrValidation(typeof data === 'string' ? data : JSON.stringify(data));
    } catch (err) { setError(getApiError(err)); }
  }

  async function submit(e) {
    e.preventDefault(); setError(''); setMessage('');

    const quantidade = parseDecimal(form.quantidade);
    const usuarioLat = parseCoordinate(form.usuario_lat);
    const usuarioLong = parseCoordinate(form.usuario_long);

    if (!Number.isFinite(quantidade) || quantidade < 1) {
      setError('Quantidade inválida. Informe um valor maior ou igual a 1.');
      return;
    }

    if (!form.ponto_coleta_id) {
      setError('Selecione um ponto de coleta.');
      return;
    }

    if (!isValidCoordinatePair(usuarioLat, usuarioLong)) {
      setError('Localização inválida. Use latitude e longitude em formato decimal, por exemplo: -3.075900 e -60.060000. Você também pode digitar com vírgula que o sistema converte automaticamente.');
      return;
    }

    const payload = {
      quantidade,
      tipo_residuo: form.tipo_residuo,
      observacao: form.observacao || 'Descarte via APP',
      usuario_lat: usuarioLat,
      usuario_long: usuarioLong,
      ponto_coleta_id: Number(form.ponto_coleta_id),
      qrcode_token: form.qrcode_token || null
    };
    try {
      const { data } = await descarteService.create(payload);
      setMessage(`Descarte registrado com sucesso. ID: ${data.id_descarte} | Status: ${data.status}`);
      setForm((prev) => ({ ...prev, quantidade: '', observacao: 'Descarte via APP', qrcode_token: '' }));
    } catch (err) { setError(getApiError(err)); }
  }

  return (
    <section className="page-stack">
      <div className="section-title"><Recycle /><div><h1>Registrar descarte</h1><p>Informe o resíduo, localização e ponto de coleta.</p></div></div>
      <Message type="success">{message}</Message><Message type="error">{error}</Message>
      <Message type="info">Dica: para seguir o fluxo oficial do projeto, cadastre seus resíduos em <strong>Meu inventário</strong> e descarte a partir de um item cadastrado. Esta tela continua disponível para descarte rápido/manual.</Message>
      <form className="panel form-grid wide" onSubmit={submit}>
        <label><span>Ponto de coleta</span><select required value={form.ponto_coleta_id} onChange={(e) => update('ponto_coleta_id', e.target.value)}><option value="">Selecione</option>{pontos.map((p) => <option key={p.id} value={p.id}>{p.nome}</option>)}</select></label>
        <label><span>Tipo de resíduo</span><select value={form.tipo_residuo} onChange={(e) => update('tipo_residuo', e.target.value)}>{tipos.map((t) => <option key={t} value={t}>{t}</option>)}</select></label>
        <label><span>Quantidade kg</span><input required type="text" inputMode="decimal" placeholder="Ex: 1.5 ou 1,5" value={form.quantidade} onChange={(e) => update('quantidade', e.target.value)} /></label>
        <label><span>Observação</span><input maxLength="50" value={form.observacao} onChange={(e) => update('observacao', e.target.value)} /></label>
        <label><span>Latitude usuário</span><input required type="text" inputMode="decimal" placeholder="Ex: -3.075900" value={form.usuario_lat} onChange={(e) => update('usuario_lat', e.target.value)} /></label>
        <label><span>Longitude usuário</span><input required type="text" inputMode="decimal" placeholder="Ex: -60.060000" value={form.usuario_long} onChange={(e) => update('usuario_long', e.target.value)} /></label>

        <div className="location-actions">
          <button type="button" className="secondary-button" onClick={useBrowserLocation} disabled={locating}><LocateFixed size={16} /> {locating ? 'Buscando localização...' : 'Usar minha localização'}</button>
          <button type="button" className="secondary-button" onClick={usarCoordenadasDoPontoParaTeste} disabled={!selectedPoint}><Navigation size={16} /> Usar coordenada do ponto para teste</button>
          {userMapsUrl && <a className="secondary-button" href={userMapsUrl} target="_blank" rel="noreferrer"><ExternalLink size={15} /> Ver minha coordenada no OpenStreetMap</a>}
        </div>

        {(locationInfo || Number.isFinite(distanceToPoint)) && (
          <div className={`location-debug ${isOutsideSelectedRadius ? 'warning' : 'ok'}`}>
            <div>
              <strong>Localização de teste</strong>
              <p>
                Latitude {formatCoordinate(form.usuario_lat)} • Longitude {formatCoordinate(form.usuario_long)}
                {locationInfo?.capturedAt ? ` • Capturada às ${locationInfo.capturedAt}` : ''}
              </p>
              {locationInfo?.source === 'browser' && <p>Precisão estimada pelo navegador: <strong>{formatMeters(locationInfo.accuracy)}</strong></p>}
              {locationInfo?.source === 'manual-test' && <p>Coordenada copiada do ponto de coleta apenas para facilitar testes no computador.</p>}
              {Number.isFinite(distanceToPoint) && selectedPoint && <p>Distância até o ponto selecionado: <strong>{formatMeters(distanceToPoint)}</strong> • Raio permitido: <strong>{formatMeters(Number(selectedPoint.raio_operacao || 1000))}</strong></p>}
            </div>
            {isOutsideSelectedRadius && <div className="location-warning"><AlertTriangle size={18} /> Sua coordenada parece estar fora do raio do ponto. O backend pode recusar o descarte.</div>}
          </div>
        )}

        <label><span>Token QR Code opcional</span><input value={form.qrcode_token} onChange={(e) => update('qrcode_token', e.target.value)} placeholder="Cole o token se houver" /></label>
        <button type="button" className="secondary-button" disabled={!form.qrcode_token} onClick={validateQr}>Validar QR Code</button>
        {qrValidation && <Message type="success">QR validado: {qrValidation}</Message>}
        <button className="primary-button">Registrar descarte</button>
      </form>

      {selectedPoint && (
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
