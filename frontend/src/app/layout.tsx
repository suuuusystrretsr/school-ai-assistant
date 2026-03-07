import type { Metadata } from 'next';
import { Manrope, Sora } from 'next/font/google';
import type { ReactNode } from 'react';

import './globals.css';

const bodyFont = Manrope({
  variable: '--font-body',
  subsets: ['latin'],
});

const displayFont = Sora({
  variable: '--font-display',
  subsets: ['latin'],
});

export const metadata: Metadata = {
  title: 'SCHOOL AI ASSISTANT',
  description: 'Next-generation AI-powered education platform for study, tutoring, and exam prep.',
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang='en'>
      <body className={`${bodyFont.variable} ${displayFont.variable}`}>
        <div className='app-shell'>{children}</div>
      </body>
    </html>
  );
}
