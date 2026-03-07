'use client';

import { useState } from 'react';

import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { API_URL } from '@/lib/api';
import { ExplanationMode } from '@/types/app';

const modes: ExplanationMode[] = ['eli5', 'normal', 'advanced', 'teacher'];

export default function HomeworkPage() {
  const [mode, setMode] = useState<ExplanationMode>('normal');
  const [question, setQuestion] = useState('Solve 2x + 8 = 20');
  const [result, setResult] = useState<any>(null);
  const [signalMessage, setSignalMessage] = useState('');

  async function solveHomework() {
    const token = localStorage.getItem('schoolai_token');
    const res = await fetch(`${API_URL}/homework/solve`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ question_text: question, explanation_mode: mode }),
    });
    const data = await res.json();
    setResult(data);
  }

  async function triggerConfusionCheck() {
    const token = localStorage.getItem('schoolai_token');
    const res = await fetch(`${API_URL}/analytics/signals`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ activity_seconds: 350, wrong_attempts: 2, answer_changes: 3, tab_switches: 1 }),
    });
    const data = await res.json();
    setSignalMessage(data.suggested_message);
  }

  return (
    <div className='grid gap-4 lg:grid-cols-3'>
      <Card className='lg:col-span-2' title='Homework Solver' subtitle='Text, image, and PDF-ready API flow'>
        <textarea className='h-32 w-full rounded-xl border p-3' value={question} onChange={(e) => setQuestion(e.target.value)} />
        <div className='mt-3 flex flex-wrap gap-2'>
          {modes.map((item) => (
            <Button key={item} variant={item === mode ? 'primary' : 'secondary'} onClick={() => setMode(item)}>
              {item.toUpperCase()}
            </Button>
          ))}
        </div>
        <div className='mt-3 flex gap-2'>
          <Button onClick={solveHomework}>Solve</Button>
          <Button variant='secondary' onClick={triggerConfusionCheck}>Need Hint Detector</Button>
        </div>
        <p className='mt-2 text-sm text-slate-600'>{signalMessage}</p>
        {result ? (
          <div className='mt-4 rounded-xl border bg-white p-4 text-sm'>
            <p><strong>Final Answer:</strong> {result.final_answer}</p>
            <p className='mt-2'><strong>Steps:</strong></p>
            <ul className='list-disc pl-5'>
              {result.steps?.map((step: string) => <li key={step}>{step}</li>)}
            </ul>
            <p className='mt-2'><strong>{mode.toUpperCase()}:</strong> {result.explanation_by_mode?.[mode]}</p>
          </div>
        ) : null}
      </Card>

      <div className='space-y-4'>
        <Card title='Whiteboard Solver (MVP)'>
          <div className='h-40 rounded-xl border border-dashed p-3 text-sm text-slate-600'>
            Drawing input area placeholder. API route exists for stroke payload ingestion.
          </div>
        </Card>
        <Card title='Progressive Hints'>
          <p className='text-sm text-slate-600'>Hints are revealed in 4 levels only after user chooses "Need a hint?".</p>
        </Card>
      </div>
    </div>
  );
}
