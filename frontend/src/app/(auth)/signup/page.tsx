'use client';

import Link from 'next/link';
import { FormEvent, useEffect, useState } from 'react';

import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { apiFetch } from '@/lib/api';
import { isLoggedIn, setAuthToken } from '@/lib/auth';
import { toReadableError } from '@/lib/error-message';

export default function SignupPage() {
  const [fullName, setFullName] = useState('Student Name');
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
    setStatus('Creating account...');
    setLoading(true);

    try {
      const res = await apiFetch('/auth/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, full_name: fullName, password }),
      });

      let data: any = null;
      try {
        data = await res.json();
      } catch {
        data = null;
      }

      if (!res.ok) {
        throw new Error(toReadableError(data?.detail, `Signup failed (${res.status})`));
      }

      setAuthToken(data.access_token);
      setStatus('Account created. Redirecting...');
      window.location.href = '/dashboard';
    } catch (err) {
      if (err instanceof DOMException && err.name === 'AbortError') {
        setStatus('Signup request timed out. Wake Render /health and retry.');
      } else if (err instanceof TypeError) {
        setStatus('Cannot reach backend API. Open Render /health, wait for wake-up, then retry.');
      } else {
        setStatus(err instanceof Error ? err.message : 'Signup failed.');
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className='mx-auto flex min-h-screen max-w-md items-center px-6'>
      <Card className='w-full'>
        <h1 className='text-2xl font-bold'>Create your account</h1>
        <p className='mt-1 text-sm text-slate-600'>Start using SCHOOL AI ASSISTANT for free.</p>
        <form className='mt-5 space-y-3' onSubmit={onSubmit}>
          <input
            className='w-full rounded-xl border p-3'
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            disabled={loading}
          />
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
          <Button className='w-full' disabled={loading}>{loading ? 'Creating...' : 'Create Account'}</Button>
          <p className='text-xs text-rose-700'>{status}</p>
        </form>
        <p className='mt-4 text-sm'>Already have one? <Link href='/login' className='text-brand-700'>Log in</Link></p>
      </Card>
    </main>
  );
}
