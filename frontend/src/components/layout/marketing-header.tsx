import Link from 'next/link';

import { Button } from '@/components/ui/button';

export function MarketingHeader() {
  return (
    <header className='mx-auto flex w-full max-w-7xl items-center justify-between px-6 py-5'>
      <Link href='/' className='text-xl font-bold tracking-tight'>
        SCHOOL AI ASSISTANT
      </Link>
      <nav className='hidden gap-8 text-sm font-medium text-slate-700 md:flex'>
        <a href='#features'>Features</a>
        <a href='#how'>How It Works</a>
        <a href='#faq'>FAQ</a>
      </nav>
      <div className='flex items-center gap-2'>
        <Link href='/login'>
          <Button variant='ghost'>Log in</Button>
        </Link>
        <Link href='/signup'>
          <Button>Get Started</Button>
        </Link>
      </div>
    </header>
  );
}
