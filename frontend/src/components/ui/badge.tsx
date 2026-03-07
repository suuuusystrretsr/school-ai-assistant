import clsx from 'clsx';

export function Badge({ label, tone = 'neutral' }: { label: string; tone?: 'neutral' | 'good' | 'warn' | 'brand' }) {
  return (
    <span
      className={clsx('rounded-full px-2.5 py-1 text-xs font-semibold', {
        'bg-slate-100 text-slate-700': tone === 'neutral',
        'bg-emerald-100 text-emerald-700': tone === 'good',
        'bg-amber-100 text-amber-700': tone === 'warn',
        'bg-brand-100 text-brand-700': tone === 'brand',
      })}
    >
      {label}
    </span>
  );
}
