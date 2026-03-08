import { apiFetch } from '@/lib/api';
import { toReadableError } from '@/lib/error-message';

function getToken(): string {
  const token = typeof window !== 'undefined' ? localStorage.getItem('schoolai_token') : null;
  if (!token) {
    throw new Error('Please create an account and log in first.');
  }
  return token;
}

async function parseJsonSafe(res: Response): Promise<any> {
  try {
    return await res.json();
  } catch {
    return null;
  }
}

export async function requestWithAuth(path: string, method: string = 'GET', body?: Record<string, unknown>): Promise<any> {
  const token = getToken();

  let res: Response;
  try {
    res = await apiFetch(path, {
      method,
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new Error('Cannot reach backend API. Open the Render /health URL and retry in 30 seconds.');
  }

  const data = await parseJsonSafe(res);
  if (!res.ok) {
    throw new Error(toReadableError(data?.detail, `Request failed (${res.status})`));
  }

  return data;
}

export async function postWithAuth(path: string, body: Record<string, unknown>): Promise<any> {
  return requestWithAuth(path, 'POST', body);
}

export async function getWithAuth(path: string): Promise<any> {
  return requestWithAuth(path, 'GET');
}

export async function patchWithAuth(path: string, body: Record<string, unknown>): Promise<any> {
  return requestWithAuth(path, 'PATCH', body);
}