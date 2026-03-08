'use client';

import Link from 'next/link';
import { FormEvent, useEffect, useState } from 'react';

import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { apiFetch } from '@/lib/api';
import { isLoggedIn, setAuthToken } from '@/lib/auth';
import { toReadableError } from '@/lib/error-message';

export default function LoginPage() {
  const [email, setEmail] = useState('student@example.com');
  const [password, setPassword] = useState('password123');
  const [status, setStatus] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isLoggedIn()) {
      window.location.href = '/dashboard';
    }
  }, []);

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setStatus('Signing in...');
    setLoading(true);

    try {
      const res = await apiFetch('/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });

      let data: any = null;
      try {
        data = await res.json();
      } catch {
        data = null;
      }

      if (!res.ok) {
        throw new Error(toReadableError(data?.detail, `Login failed (${res.status})`));
      }

      setAuthToken(data.access_token);
      setStatus('Success. Redirecting...');
      window.location.href = '/dashboard';
    } catch (err) {
      if (err instanceof DOMException && err.name === 'AbortError') {
        setStatus('Login request timed out. Wake Render /health and retry.');
      } else if (err instanceof TypeError) {
        setStatus('Cannot reach backend API. Open Render /health, wait for wake-up, then retry.');
      } else {
        setStatus(err instanceof Error ? err.message : 'Login failed.');
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className='mx-auto flex min-h-screen max-w-md items-center px-6'>
      <Card className='w-full'>
        <h1 className='text-2xl font-bold'>Welcome back</h1>
        <p className='mt-1 text-sm text-slate-600'>Log in to SCHOOL AI ASSISTANT</p>
        <form className='mt-5 space-y-3' onSubmit={onSubmit}>
          <input
            className='w-full rounded-xl border p-3'
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            disabled={loading}
          />
          <input
            type='password'
            className='w-full rounded-xl border p-3'
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            disabled={loading}
          />
          <Button className='w-full' disabled={loading}>{loading ? 'Logging in...' : 'Log In'}</Button>
          <p className='text-xs text-rose-700'>{status}</p>
        </form>
        <p className='mt-4 text-sm'>No account? <Link href='/signup' className='text-brand-700'>Create one</Link></p>
      </Card>
    </main>
  );
}
