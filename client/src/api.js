export const API_BASE_URL = (import.meta.env.VITE_API_URL || 'http://localhost:5000').replace(/\/$/, '');

export function getStoredAuthToken() {
  return localStorage.getItem('ifhe_kpi_token') || '';
}

export function setStoredAuthToken(token) {
  if (token) {
    localStorage.setItem('ifhe_kpi_token', token);
  } else {
    localStorage.removeItem('ifhe_kpi_token');
  }
}

export async function apiFetch(url, options = {}) {
  const token = getStoredAuthToken();
  const headers = new Headers(options.headers || {});

  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  if (!(options.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  return fetch(url, { ...options, headers });
}
