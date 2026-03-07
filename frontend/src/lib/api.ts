const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

function normalizeBase(url: string) {
  return url.endsWith('/') ? url.slice(0, -1) : url;
}

export function getWsBaseUrl() {
  const explicitWs = process.env.NEXT_PUBLIC_WS_URL;
  if (explicitWs) {
    return normalizeBase(explicitWs);
  }

  // Derive websocket base from API URL, stripping /api/v1 if present.
  const cleanApi = normalizeBase(API_URL).replace(/\/api\/v1$/, '');
  if (cleanApi.startsWith('https://')) return cleanApi.replace('https://', 'wss://');
  if (cleanApi.startsWith('http://')) return cleanApi.replace('http://', 'ws://');
  return cleanApi;
}

export async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${normalizeBase(API_URL)}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
  });

  if (!res.ok) {
    throw new Error(`API request failed: ${res.status}`);
  }

  return res.json() as Promise<T>;
}

export { API_URL };
