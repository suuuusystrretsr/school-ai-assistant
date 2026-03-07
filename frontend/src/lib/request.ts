import { API_URL } from '@/lib/api';
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

export async function postWithAuth(path: string, body: Record<string, unknown>): Promise<any> {
  const token = getToken();

  let res: Response;
  try {
    res = await fetch(`${API_URL}${path}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(body),
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
