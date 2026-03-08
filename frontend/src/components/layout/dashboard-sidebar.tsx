'use client';

import clsx from 'clsx';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useEffect, useState } from 'react';

import { clearAuthToken, isLoggedIn } from '@/lib/auth';

const nav = [
  { href: '/dashboard', label: 'Dashboard' },
  { href: '/dashboard/homework', label: 'Homework Solver' },
  { href: '/dashboard/flashcards', label: 'Flashcards' },
  { href: '/dashboard/tutor', label: 'AI Tutor' },
  { href: '/dashboard/planner', label: 'Study Planner' },
  { href: '/dashboard/exams', label: 'Exam Simulator' },
  { href: '/dashboard/analytics', label: 'Analytics' },
  { href: '/dashboard/study-room', label: 'Study Rooms' },
  { href: '/dashboard/settings', label: 'Settings' },
];

type Props = {
  onAuthStateChange?: (hasToken: boolean) => void;
};

export function DashboardSidebar({ onAuthStateChange }: Props) {
  const pathname = usePathname();
  const [loggedIn, setLoggedIn] = useState(false);

  useEffect(() => {
    setLoggedIn(isLoggedIn());
  }, []);

  function logout() {
    clearAuthToken();
    setLoggedIn(false);
    onAuthStateChange?.(false);
    window.location.href = '/login';
  }

  return (
    <aside className='glass hidden w-72 shrink-0 rounded-r-3xl border-l-0 border-y-0 border-r p-5 lg:block'>
      <p className='px-3 text-xs font-semibold uppercase tracking-[0.15em] text-slate-500'>SCHOOL AI ASSISTANT</p>
      <nav className='mt-4 space-y-1'>
        {nav.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={clsx('block rounded-xl px-3 py-2 text-sm font-medium transition', {
              'bg-brand-500 text-white shadow-float': pathname === item.href,
              'text-slate-700 hover:bg-brand-50': pathname !== item.href,
            })}
          >
            {item.label}
          </Link>
        ))}
      </nav>

      <div className='mt-6 rounded-xl border bg-white/70 p-3 text-sm'>
        <p className='font-semibold text-slate-700'>{loggedIn ? 'Signed in on this device' : 'Demo mode'}</p>
        <p className='mt-1 text-xs text-slate-600'>Session persists until you log out.</p>
        {loggedIn ? (
          <button className='mt-3 rounded-lg border px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50' onClick={logout}>
            Log out
          </button>
        ) : (
          <Link href='/login' className='mt-3 inline-block text-xs font-semibold text-brand-700'>Log in</Link>
        )}
      </div>
    </aside>
  );
}
