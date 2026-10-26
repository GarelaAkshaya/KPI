const envApiUrl = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '');
let activeBaseUrl = envApiUrl || localStorage.getItem('ifhe_kpi_active_api_base') || 'http://localhost:5000';

export function getActiveApiBase() {
  return activeBaseUrl;
}

export function setActiveApiBase(url) {
  activeBaseUrl = url.replace(/\/$/, '');
  try {
    localStorage.setItem('ifhe_kpi_active_api_base', activeBaseUrl);
  } catch {
    // ignore
  }
}

export const API_BASE_URL = activeBaseUrl;

export function getStoredAuthToken() {
  const token = localStorage.getItem('ifhe_kpi_token') || '';
  if (!token) return '';
  try {
    const parts = token.split('.');
    if (parts.length === 3) {
      const payload = JSON.parse(atob(parts[1]));
      if (payload.exp && Date.now() >= payload.exp * 1000) {
        localStorage.removeItem('ifhe_kpi_token');
        return '';
      }
    }
  } catch {
    // If not standard JWT format, keep token
  }
  return token;
}

export function setStoredAuthToken(token) {
  if (token) {
    localStorage.setItem('ifhe_kpi_token', token);
  } else {
    localStorage.removeItem('ifhe_kpi_token');
  }
}

function resolveUrl(url) {
  if (/^http:\/\/localhost:(5000|5001)/i.test(url)) {
    return url.replace(/^http:\/\/localhost:(5000|5001)/i, activeBaseUrl);
  }
  return url;
}

function getAlternateUrl(url) {
  if (url.includes(':5000')) {
    return url.replace(':5000', ':5001');
  }
  if (url.includes(':5001')) {
    return url.replace(':5001', ':5000');
  }
  return null;
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

  const primaryUrl = resolveUrl(url);
  let response;

  try {
    response = await fetch(primaryUrl, { ...options, headers });
  } catch (err) {
    // Attempt fallback between ports 5000 and 5001 if connection fails
    const altUrl = getAlternateUrl(primaryUrl);
    if (altUrl) {
      try {
        response = await fetch(altUrl, { ...options, headers });
        const newBase = altUrl.includes(':5001') ? 'http://localhost:5001' : 'http://localhost:5000';
        setActiveApiBase(newBase);
      } catch {
        throw err;
      }
    } else {
      throw err;
    }
  }

  // Central 401 Unauthorized handling
  if (response.status === 401) {
    setStoredAuthToken('');
    if (typeof window !== 'undefined' && window.location.pathname !== '/') {
      window.location.href = '/';
    }
  }

  return response;
}
