export function ProgressBar({ value }: { value: number }) {
  return (
    <div className='h-2 w-full rounded-full bg-slate-200'>
      <div
        className='h-2 rounded-full bg-gradient-to-r from-brand-500 to-cyan-500 transition-all'
        style={{ width: `${Math.max(0, Math.min(100, value))}%` }}
      />
    </div>
  );
}
