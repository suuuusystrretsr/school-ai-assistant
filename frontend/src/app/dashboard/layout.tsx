import type { ReactNode } from 'react';

import { DashboardSidebar } from '@/components/layout/dashboard-sidebar';

export default function DashboardLayout({ children }: { children: ReactNode }) {
  return (
    <div className='mx-auto flex min-h-screen max-w-[1600px] gap-6 px-4 py-4'>
      <DashboardSidebar />
      <main className='flex-1'>{children}</main>
    </div>
  );
}
