import { useEffect, useMemo } from 'react';
import { Circle, MapContainer, Marker, Popup, TileLayer, useMap } from 'react-leaflet';
import L from 'leaflet';
import { formatCoordinate, isValidCoordinatePair, parseCoordinate } from '../utils/format';

function makeMarkerIcon(type = 'point') {
  const className = type === 'user' ? 'leaflet-marker-dot user' : 'leaflet-marker-dot point';
  return L.divIcon({
    className,
    html: '<span></span>',
    iconSize: [26, 26],
    iconAnchor: [13, 13],
    popupAnchor: [0, -13]
  });
}

const pointIcon = makeMarkerIcon('point');
const userIcon = makeMarkerIcon('user');

function MapAutoFit({ points, selectedPoint, userLocation, focusSelected = false, selectedZoom = 18 }) {
  const map = useMap();

  useEffect(() => {
    if (focusSelected && selectedPoint && isValidCoordinatePair(selectedPoint.latitude, selectedPoint.longitude)) {
      const lat = parseCoordinate(selectedPoint.latitude);
      const lng = parseCoordinate(selectedPoint.longitude);
      map.setView([lat, lng], selectedZoom, { animate: true });
      return;
    }

    const coordinates = [];

    points.forEach((point) => {
      const lat = parseCoordinate(point.latitude);
      const lng = parseCoordinate(point.longitude);
      if (isValidCoordinatePair(lat, lng)) coordinates.push([lat, lng]);
    });

    if (userLocation && isValidCoordinatePair(userLocation.latitude, userLocation.longitude)) {
      coordinates.push([parseCoordinate(userLocation.latitude), parseCoordinate(userLocation.longitude)]);
    }

    if (coordinates.length > 1) {
      map.fitBounds(coordinates, { padding: [34, 34], maxZoom: 16 });
      return;
    }

    if (coordinates.length === 1) {
      map.setView(coordinates[0], selectedPoint ? 16 : 14);
    }
  }, [map, points, selectedPoint, userLocation, focusSelected, selectedZoom]);

  useEffect(() => {
    setTimeout(() => map.invalidateSize(), 120);
  }, [map]);

  return null;
}

export default function LeafletMap({
  points = [],
  selectedPoint = null,
  userLocation = null,
  onSelectPoint,
  height = 360,
  showRadius = true,
  focusSelected = false,
  selectedZoom = 18
}) {
  const validPoints = useMemo(() => {
    return points.filter((point) => isValidCoordinatePair(point.latitude, point.longitude));
  }, [points]);

  const fallbackCenter = useMemo(() => {
    if (selectedPoint && isValidCoordinatePair(selectedPoint.latitude, selectedPoint.longitude)) {
      return [parseCoordinate(selectedPoint.latitude), parseCoordinate(selectedPoint.longitude)];
    }
    if (validPoints.length) {
      return [parseCoordinate(validPoints[0].latitude), parseCoordinate(validPoints[0].longitude)];
    }
    if (userLocation && isValidCoordinatePair(userLocation.latitude, userLocation.longitude)) {
      return [parseCoordinate(userLocation.latitude), parseCoordinate(userLocation.longitude)];
    }
    return [-3.119027, -60.021731];
  }, [selectedPoint, validPoints, userLocation]);

  const validUserLocation = userLocation && isValidCoordinatePair(userLocation.latitude, userLocation.longitude)
    ? {
        latitude: parseCoordinate(userLocation.latitude),
        longitude: parseCoordinate(userLocation.longitude),
        accuracy: Number(userLocation.accuracy || 0)
      }
    : null;

  return (
    <div className="leaflet-map-wrap" style={{ minHeight: height }}>
      <MapContainer center={fallbackCenter} zoom={14} scrollWheelZoom className="leaflet-map">
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        <MapAutoFit points={validPoints} selectedPoint={selectedPoint} userLocation={validUserLocation} focusSelected={focusSelected} selectedZoom={selectedZoom} />

        {validPoints.map((point) => {
          const lat = parseCoordinate(point.latitude);
          const lng = parseCoordinate(point.longitude);
          const isSelected = selectedPoint && Number(selectedPoint.id) === Number(point.id);
          return (
            <Marker
              key={point.id || `${lat}-${lng}`}
              position={[lat, lng]}
              icon={pointIcon}
              eventHandlers={{ click: () => onSelectPoint?.(point) }}
            >
              <Popup>
                <strong>{point.nome || 'Ponto de coleta'}</strong><br />
                {point.endereco || 'Sem endereço informado'}<br />
                Lat: {formatCoordinate(lat)}<br />
                Long: {formatCoordinate(lng)}<br />
                Raio: {point.raio_operacao || 1000}m<br />
                Horário: {point.horario_funcionamento || 'Não informado'}<br />
                Capacidade: {point.capacidade_maxima || '-'} kg<br />
                Ocupação: {point.percentual_ocupacao || 0}%<br />
                Status: {point.status_calculado || point.status || (point.ativo ? 'ativo' : 'inativo')}
              </Popup>
              {isSelected && showRadius && (
                <Circle
                  center={[lat, lng]}
                  radius={Number(point.raio_operacao || 1000)}
                  pathOptions={{ weight: 2, fillOpacity: 0.08 }}
                />
              )}
            </Marker>
          );
        })}

        {validUserLocation && (
          <>
            <Marker position={[validUserLocation.latitude, validUserLocation.longitude]} icon={userIcon}>
              <Popup>
                <strong>Sua localização capturada</strong><br />
                Lat: {formatCoordinate(validUserLocation.latitude)}<br />
                Long: {formatCoordinate(validUserLocation.longitude)}<br />
                {validUserLocation.accuracy ? `Precisão: ${Math.round(validUserLocation.accuracy)}m` : 'Precisão não informada'}
              </Popup>
            </Marker>
            {validUserLocation.accuracy > 0 && validUserLocation.accuracy <= 3000 && (
              <Circle
                center={[validUserLocation.latitude, validUserLocation.longitude]}
                radius={validUserLocation.accuracy}
                pathOptions={{ weight: 1, fillOpacity: 0.05 }}
              />
            )}
          </>
        )}
      </MapContainer>
    </div>
  );
}
