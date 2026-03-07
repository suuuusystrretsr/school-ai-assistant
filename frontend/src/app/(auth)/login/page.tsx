'use client';

import Link from 'next/link';
import { FormEvent, useState } from 'react';

import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { API_URL } from '@/lib/api';
import { toReadableError } from '@/lib/error-message';

export default function LoginPage() {
  const [email, setEmail] = useState('student@example.com');
  const [password, setPassword] = useState('password123');
  const [message, setMessage] = useState('');

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setMessage('Signing in...');
    try {
      const res = await fetch(`${API_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(toReadableError(data?.detail, 'Login failed'));
      }
      localStorage.setItem('schoolai_token', data.access_token);
      window.location.href = '/dashboard';
    } catch {
      setMessage('Cannot reach backend API. Open the Render /health URL, wait for wake-up, then retry.');
    }
  }

  return (
    <main className='mx-auto flex min-h-screen max-w-md items-center px-6'>
      <Card className='w-full'>
        <h1 className='text-2xl font-bold'>Welcome back</h1>
        <p className='mt-1 text-sm text-slate-600'>Log in to SCHOOL AI ASSISTANT</p>
        <form className='mt-5 space-y-3' onSubmit={onSubmit}>
          <input className='w-full rounded-xl border p-3' value={email} onChange={(e) => setEmail(e.target.value)} />
          <input
            type='password'
            className='w-full rounded-xl border p-3'
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <Button className='w-full'>Log In</Button>
          <p className='text-xs text-rose-700'>{message}</p>
        </form>
        <p className='mt-4 text-sm'>No account? <Link href='/signup' className='text-brand-700'>Create one</Link></p>
      </Card>
    </main>
  );
}
