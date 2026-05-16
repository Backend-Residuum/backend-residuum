import axios from 'axios';

export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('residuum_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export function getApiError(error) {
  const detail = error?.response?.data?.detail;
  if (Array.isArray(detail)) {
    return detail.map((item) => `${item.loc?.join('.')}: ${item.msg}`).join(' | ');
  }
  if (typeof detail === 'string') return detail;
  if (typeof error?.response?.data === 'string') return error.response.data;
  return error?.message || 'Erro inesperado na comunicação com a API.';
}

export const authService = {
  register: (payload) => api.post('/usuarios', payload),
  login: (payload) => api.post('/login', payload),
  me: () => api.get('/me'),
  perfil: () => api.get('/perfil'),
  updateAddress: (payload) => api.put('/me/endereco', payload)
};


export const perfilService = {
  get: () => api.get('/perfil')
};

export const pontosService = {
  list: (params = {}) => api.get('/pontos', { params }),
  get: (id) => api.get(`/pontos-coleta/${id}`),
  create: (payload) => api.post('/pontos-coleta', payload),
  update: (id, payload) => api.put(`/pontos-coleta/${id}`, payload)
};


export const inventarioService = {
  list: (status = '') => api.get('/me/inventario', { params: status ? { status } : {} }),
  get: (id) => api.get(`/me/inventario/${id}`),
  create: (payload) => api.post('/me/inventario', payload),
  update: (id, payload) => api.put(`/me/inventario/${id}`, payload),
  remove: (id) => api.delete(`/me/inventario/${id}`),
  discard: (id, payload) => api.post(`/me/inventario/${id}/descartar`, payload)
};

export const descarteService = {
  create: (payload) => api.post('/descarte/', payload),
  myHistory: () => api.get('/descarte/historico'),
  generalHistory: () => api.get('/descarte/historico/geral'),
  pending: () => api.get('/descarte/pendentes'),
  confirm: (id, quantidade_confirmada) => api.put(`/descarte/${id}/confirmar`, { quantidade_confirmada })
};

export const qrCodeService = {
  create: (ponto_coleta_id) => api.post('/qrcode-tokens', { ponto_coleta_id: Number(ponto_coleta_id) }),
  listByPoint: (pontoId) => api.get(`/qrcode-tokens/${pontoId}`),
  validate: (token) => api.post('/qrcode-tokens/validar', { token })
};

export default api;
