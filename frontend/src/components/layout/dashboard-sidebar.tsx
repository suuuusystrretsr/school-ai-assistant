'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import clsx from 'clsx';

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

export function DashboardSidebar() {
  const pathname = usePathname();

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
    </aside>
  );
}
