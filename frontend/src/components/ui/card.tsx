import clsx from 'clsx';
import { ComponentProps, ReactNode } from 'react';

interface CardProps extends ComponentProps<'section'> {
  title?: string;
  subtitle?: string;
  children: ReactNode;
}

export function Card({ title, subtitle, children, className, ...props }: CardProps) {
  return (
    <section className={clsx('glass rounded-2xl p-5 shadow-sm', className)} {...props}>
      {title ? <h3 className='text-lg font-semibold text-ink'>{title}</h3> : null}
      {subtitle ? <p className='mt-1 text-sm text-slate-600'>{subtitle}</p> : null}
      <div className={clsx(title || subtitle ? 'mt-4' : '')}>{children}</div>
    </section>
  );
}
