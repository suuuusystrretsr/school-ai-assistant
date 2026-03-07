import clsx from 'clsx';
import { ButtonHTMLAttributes } from 'react';

type ButtonVariant = 'primary' | 'secondary' | 'ghost';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
}

export function Button({ className, variant = 'primary', ...props }: ButtonProps) {
  return (
    <button
      className={clsx(
        'inline-flex items-center justify-center rounded-xl px-4 py-2 text-sm font-semibold transition',
        {
          'bg-brand-500 text-white hover:bg-brand-600 shadow-float': variant === 'primary',
          'bg-white text-ink border border-brand-100 hover:bg-brand-50': variant === 'secondary',
          'bg-transparent text-brand-700 hover:bg-brand-50': variant === 'ghost',
        },
        className
      )}
      {...props}
    />
  );
}
