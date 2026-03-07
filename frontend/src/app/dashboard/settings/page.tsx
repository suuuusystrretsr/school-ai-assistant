'use client';

import { useState } from 'react';

import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';

export default function SettingsPage() {
  const [siteUrl, setSiteUrl] = useState(process.env.NEXT_PUBLIC_SITE_URL || 'https://schoolaiassistant.local');
  const [apiUrl, setApiUrl] = useState(process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1');

  return (
    <div className='space-y-4'>
      <Card title='Settings (Placeholder)' subtitle='This page is currently display-only for MVP.'>
        <div className='space-y-3'>
          <label className='block text-sm'>
            Site URL
            <input className='mt-1 w-full rounded-xl border p-3' value={siteUrl} onChange={(e) => setSiteUrl(e.target.value)} />
          </label>
          <label className='block text-sm'>
            API URL
            <input className='mt-1 w-full rounded-xl border p-3' value={apiUrl} onChange={(e) => setApiUrl(e.target.value)} />
          </label>
          <Button disabled className='cursor-not-allowed opacity-70'>Save Preferences (Coming Soon)</Button>
        </div>
      </Card>

      <Card title='Future OAuth Placeholder'>
        <p className='text-sm text-slate-700'>Google, Microsoft, and GitHub OAuth providers can be added without refactoring core auth flows.</p>
      </Card>
    </div>
  );
}
