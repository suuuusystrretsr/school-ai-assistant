'use client';

import type { ReactNode } from 'react';
import { useEffect, useState } from 'react';

import { DashboardSidebar } from '@/components/layout/dashboard-sidebar';

export default function DashboardLayout({ children }: { children: ReactNode }) {
  const [hasToken, setHasToken] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('schoolai_token');
    setHasToken(Boolean(token));
  }, []);

  return (
    <div className='mx-auto flex min-h-screen max-w-[1600px] gap-6 px-4 py-4'>
      <DashboardSidebar />
      <main className='flex-1'>
        {!hasToken ? (
          <div className='mb-4 rounded-xl border border-amber-300 bg-amber-50 p-3 text-sm text-amber-800'>
            You are not logged in. Interactive features call the backend and will fail until you sign up/login.
          </div>
        ) : null}
        {children}
      </main>
    </div>
  );
}
