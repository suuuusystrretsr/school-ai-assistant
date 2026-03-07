'use client';

import { useState } from 'react';

import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { API_URL } from '@/lib/api';

export default function TutorPage() {
  const [message, setMessage] = useState('Teach me algebra step by step.');
  const [reply, setReply] = useState<any>(null);

  async function askTutor() {
    const token = localStorage.getItem('schoolai_token');
    const res = await fetch(`${API_URL}/tutor/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ message, subject: 'Math', mode: 'normal' }),
    });
    const data = await res.json();
    setReply(data);
  }

  return (
    <div className='grid gap-4 lg:grid-cols-3'>
      <Card className='lg:col-span-2' title='AI Tutor Mode' subtitle='Conversational tutor with adaptive path'>
        <textarea className='h-28 w-full rounded-xl border p-3' value={message} onChange={(e) => setMessage(e.target.value)} />
        <Button className='mt-3' onClick={askTutor}>Ask Tutor</Button>

        {reply ? (
          <div className='mt-4 rounded-xl border bg-white p-4 text-sm'>
            <p><strong>Tutor:</strong> {reply.reply}</p>
            <p className='mt-2'><strong>Follow-up:</strong> {reply.follow_up_question}</p>
            <p className='mt-2'><strong>Adaptive Path:</strong> {reply.adaptive_path?.join(' -> ')}</p>
          </div>
        ) : null}
      </Card>

      <Card title='Study Buddy'>
        <p className='text-sm text-slate-700'>"You are 1 session away from a 10-day streak."</p>
      </Card>
    </div>
  );
}
