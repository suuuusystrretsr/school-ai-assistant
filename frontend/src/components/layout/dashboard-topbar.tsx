import { Badge } from '@/components/ui/badge';

export function DashboardTopbar() {
  return (
    <header className='glass flex items-center justify-between rounded-2xl p-4'>
      <div>
        <p className='text-xs font-semibold uppercase tracking-[0.1em] text-slate-500'>Today</p>
        <p className='text-lg font-semibold text-ink'>Your Smart Study Workspace</p>
      </div>
      <div className='flex items-center gap-2'>
        <Badge label='Focus Mode Ready' tone='good' />
        <Badge label='Free MVP' tone='brand' />
      </div>
    </header>
  );
}
