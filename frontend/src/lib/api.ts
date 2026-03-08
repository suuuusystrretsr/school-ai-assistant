function sanitizeUrl(raw: string | undefined): string {
  if (!raw) return '';
  return raw.trim().replace(/^['\"]+|['\"]+$/g, '');
}

const DIRECT_API_URL = sanitizeUrl(process.env.NEXT_PUBLIC_API_URL);
const API_URL = DIRECT_API_URL || '/api/proxy';

function normalizeBase(url: string) {
  return url.endsWith('/') ? url.slice(0, -1) : url;
}

export function getWsBaseUrl() {
  const explicitWs = sanitizeUrl(process.env.NEXT_PUBLIC_WS_URL);
  if (explicitWs) {
    return normalizeBase(explicitWs);
  }

  const baseForWs = DIRECT_API_URL || API_URL;
  const cleanApi = normalizeBase(baseForWs).replace(/\/api\/v1$/, '');
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

export { API_URL, DIRECT_API_URL };