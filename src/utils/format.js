export function formatDate(value) {
  if (!value) return '-';
  try {
    return new Date(value).toLocaleString('pt-BR');
  } catch {
    return value;
  }
}

export function formatKg(value) {
  const n = Number(value || 0);
  return `${n.toLocaleString('pt-BR', { maximumFractionDigits: 2 })} kg`;
}

export function asArray(value) {
  if (!value) return [];
  if (Array.isArray(value)) return value;
  if (Array.isArray(value?.items)) return value.items;
  if (Array.isArray(value?.data)) return value.data;
  if (typeof value === 'object') return Object.values(value).filter((v) => typeof v === 'object');
  return [];
}

export function normalizeRole(role) {
  return String(role || 'usuario').toLowerCase();
}

export function parseDecimal(value) {
  if (typeof value === 'number') return value;
  const normalized = String(value ?? '')
    .trim()
    .replace(/\s/g, '')
    .replace(',', '.');

  const number = Number(normalized);
  return Number.isFinite(number) ? number : NaN;
}

export function parseCoordinate(value) {
  return parseDecimal(value);
}

export function isValidCoordinatePair(latitude, longitude) {
  const lat = parseCoordinate(latitude);
  const lng = parseCoordinate(longitude);
  return Number.isFinite(lat) && Number.isFinite(lng) && lat >= -90 && lat <= 90 && lng >= -180 && lng <= 180;
}

export function mapsQueryUrl(latitude, longitude) {
  const lat = parseCoordinate(latitude);
  const lng = parseCoordinate(longitude);
  if (!Number.isFinite(lat) || !Number.isFinite(lng)) return '';
  return `https://www.openstreetmap.org/?mlat=${lat}&mlon=${lng}#map=17/${lat}/${lng}`;
}

export function mapsEmbedUrl(latitude, longitude) {
  const lat = parseCoordinate(latitude);
  const lng = parseCoordinate(longitude);
  if (!Number.isFinite(lat) || !Number.isFinite(lng)) return '';
  return `https://www.openstreetmap.org/export/embed.html?bbox=${lng - 0.01}%2C${lat - 0.01}%2C${lng + 0.01}%2C${lat + 0.01}&layer=mapnik&marker=${lat}%2C${lng}`;
}

export function formatCoordinate(value) {
  const number = parseCoordinate(value);
  if (!Number.isFinite(number)) return '-';
  return number.toFixed(6);
}
