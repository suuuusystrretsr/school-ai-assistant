'use client';

import Link from 'next/link';
import type { ReactNode } from 'react';
import { useEffect, useState } from 'react';

import { DashboardSidebar } from '@/components/layout/dashboard-sidebar';
import { isLoggedIn } from '@/lib/auth';

export default function DashboardLayout({ children }: { children: ReactNode }) {
  const [hasToken, setHasToken] = useState(true);

  useEffect(() => {
    setHasToken(isLoggedIn());
  }, []);

  return (
    <div className='mx-auto flex min-h-screen max-w-[1600px] gap-6 px-4 py-4'>
      <DashboardSidebar onAuthStateChange={setHasToken} />
      <main className='flex-1'>
        {!hasToken ? (
          <div className='mb-4 rounded-xl border border-amber-300 bg-amber-50 p-3 text-sm text-amber-800'>
            You are viewing product pages in demo mode. For live AI actions, please <Link className='underline' href='/login'>log in</Link>.
          </div>
        ) : null}
        {children}
      </main>
    </div>
  );
}
