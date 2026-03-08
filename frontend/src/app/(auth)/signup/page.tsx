'use client';

import Link from 'next/link';
import { FormEvent, useState } from 'react';

import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { apiFetch } from '@/lib/api';
import { toReadableError } from '@/lib/error-message';

export default function SignupPage() {
  const [fullName, setFullName] = useState('Student Name');
  const [email, setEmail] = useState('student@example.com');
  const [password, setPassword] = useState('password123');
  const [message, setMessage] = useState('');

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setMessage('Creating account...');

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

      localStorage.setItem('schoolai_token', data.access_token);
      window.location.href = '/dashboard';
    } catch (err) {
      if (err instanceof DOMException && err.name === 'AbortError') {
        setMessage('Signup request timed out. Wake Render /health and retry.');
        return;
      }
      if (err instanceof TypeError) {
        setMessage('Cannot reach backend API. Open the Render /health URL, wait for wake-up, then retry.');
        return;
      }
      setMessage(err instanceof Error ? err.message : 'Signup failed.');
    }
  }

  return (
    <main className='mx-auto flex min-h-screen max-w-md items-center px-6'>
      <Card className='w-full'>
        <h1 className='text-2xl font-bold'>Create your account</h1>
        <p className='mt-1 text-sm text-slate-600'>Start using SCHOOL AI ASSISTANT for free.</p>
        <form className='mt-5 space-y-3' onSubmit={onSubmit}>
          <input className='w-full rounded-xl border p-3' value={fullName} onChange={(e) => setFullName(e.target.value)} />
          <input className='w-full rounded-xl border p-3' value={email} onChange={(e) => setEmail(e.target.value)} />
          <input
            type='password'
            className='w-full rounded-xl border p-3'
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <Button className='w-full'>Create Account</Button>
          <p className='text-xs text-rose-700'>{message}</p>
        </form>
        <p className='mt-4 text-sm'>Already have one? <Link href='/login' className='text-brand-700'>Log in</Link></p>
      </Card>
    </main>
  );
}