import { apiFetch } from '@/lib/api';
import { clearAuthToken, getAuthToken } from '@/lib/auth';
import { toReadableError } from '@/lib/error-message';

function requireToken(): string {
  const token = getAuthToken();
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
  const token = requireToken();

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
    throw new Error('Cannot reach backend API. Open Render /health, wait for wake-up, then retry.');
  }

  const data = await parseJsonSafe(res);
  if (!res.ok) {
    if (res.status === 401) {
      clearAuthToken();
      throw new Error('Session expired. Log in again.');
    }
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
