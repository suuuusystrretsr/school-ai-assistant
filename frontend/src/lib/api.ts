function sanitizeUrl(raw: string | undefined): string {
  if (!raw) return '';
  return raw.trim().replace(/^['\"]+|['\"]+$/g, '');
}

const DIRECT_API_URL = sanitizeUrl(process.env.NEXT_PUBLIC_API_URL);
const PROXY_API_URL = '/api/proxy';
const API_URL = DIRECT_API_URL || PROXY_API_URL;

function normalizeBase(url: string) {
  return url.endsWith('/') ? url.slice(0, -1) : url;
}

function getApiBases(): string[] {
  const bases = [DIRECT_API_URL, PROXY_API_URL].filter(Boolean).map(normalizeBase);
  return Array.from(new Set(bases));
}

async function fetchWithTimeout(url: string, init: RequestInit, timeoutMs: number): Promise<Response> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(url, { ...init, signal: controller.signal });
  } finally {
    clearTimeout(timer);
  }
}

export async function apiFetch(path: string, init: RequestInit = {}, timeoutMs = 15000): Promise<Response> {
  let lastError: unknown = null;

  for (const base of getApiBases()) {
    try {
      return await fetchWithTimeout(`${base}${path}`, init, timeoutMs);
    } catch (error) {
      lastError = error;
    }
  }

  if (lastError) {
    throw lastError;
  }

  throw new TypeError('No API base URL is configured.');
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
  const res = await apiFetch(path, {
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

export { API_URL, DIRECT_API_URL, PROXY_API_URL };