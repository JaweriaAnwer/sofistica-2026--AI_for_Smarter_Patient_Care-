export const API_BASE_URL = 'http://localhost:8000';

/**
 * Thin fetch wrapper. Member C's endpoints should live under API_BASE_URL.
 * Every page uses this so swapping the base URL (e.g. for deployment)
 * only happens in one place.
 */
export async function apiGet(path, options = {}) {
  const res = await fetch(`${API_BASE_URL}${path}`, options);
  if (!res.ok) {
    throw new Error(`API ${path} failed with status ${res.status}`);
  }
  return res.json();
}

export async function apiPost(path, body) {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const err = new Error(data.detail || `API ${path} failed with status ${res.status}`);
    err.status = res.status;
    err.body = data;
    throw err;
  }
  return data;
}
