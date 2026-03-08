'use client';

import { useEffect, useState } from 'react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { getWithAuth, postWithAuth } from '@/lib/request';

type TutorTurn = {
  role: 'student' | 'tutor';
  text: string;
};

export default function TutorPage() {
  const [subject, setSubject] = useState('Math');
  const [mode, setMode] = useState('normal');
  const [message, setMessage] = useState('Teach me algebra step by step.');
  const [reply, setReply] = useState<any>(null);
  const [buddy, setBuddy] = useState<any>(null);
  const [history, setHistory] = useState<TutorTurn[]>([]);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState('');

  useEffect(() => {
    async function loadBuddy() {
      try {
        const data = await getWithAuth('/analytics/study-buddy');
        setBuddy(data);
      } catch {
        setBuddy(null);
      }
    }
    loadBuddy();
  }, []);

  async function askTutor() {
    if (!message.trim()) {
      setStatus('Enter a question first.');
      return;
    }

    setLoading(true);
    setStatus('Tutor is thinking...');

    try {
      const data = await postWithAuth('/tutor/chat', { message, subject, mode });
      setReply(data);
      setHistory((prev) => [...prev, { role: 'student', text: message }, { role: 'tutor', text: data.reply }]);
      setStatus('Tutor response ready.');

      await postWithAuth('/analytics/session-signal', {
        page: 'tutor',
        event_type: 'interaction',
        action: 'ask-tutor',
        topic: subject,
        task_difficulty: mode === 'advanced' ? 'hard' : 'medium',
        dwell_seconds: 60,
        self_confidence: 55,
      });
    } catch (err) {
      setReply(null);
      setStatus(err instanceof Error ? err.message : 'Tutor request failed.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className='grid gap-4 lg:grid-cols-3'>
      <Card className='lg:col-span-2' title='AI Tutor Mode' subtitle='Conversational tutor with adaptive follow-up and mini-quiz'>
        <div className='grid gap-2 sm:grid-cols-2'>
          <label className='text-sm'>
            Subject
            <select className='mt-1 w-full rounded-xl border p-2' value={subject} onChange={(e) => setSubject(e.target.value)}>
              <option>Math</option>
              <option>Biology</option>
              <option>History</option>
              <option>Chemistry</option>
              <option>Physics</option>
            </select>
          </label>
          <label className='text-sm'>
            Mode
            <select className='mt-1 w-full rounded-xl border p-2' value={mode} onChange={(e) => setMode(e.target.value)}>
              <option value='eli5'>ELI5</option>
              <option value='normal'>Normal</option>
              <option value='advanced'>Advanced</option>
              <option value='teacher'>Teacher</option>
            </select>
          </label>
        </div>

        <textarea className='mt-3 h-28 w-full rounded-xl border p-3' value={message} onChange={(e) => setMessage(e.target.value)} />
        <div className='mt-3 flex flex-wrap gap-2'>
          <Button onClick={askTutor} disabled={loading}>{loading ? 'Thinking...' : 'Ask Tutor'}</Button>
          {reply?.follow_up_question ? (
            <Button variant='secondary' onClick={() => setMessage(reply.follow_up_question)}>
              Use Follow-up Prompt
            </Button>
          ) : null}
        </div>
        {status ? <p className='mt-2 text-sm text-rose-700'>{status}</p> : null}

        {history.length > 0 ? (
          <div className='mt-4 space-y-2 rounded-xl border bg-white p-4 text-sm'>
            {history.slice(-6).map((turn, idx) => (
              <p key={idx}><strong>{turn.role === 'student' ? 'You' : 'Tutor'}:</strong> {turn.text}</p>
            ))}
          </div>
        ) : null}

        {reply ? (
          <div className='mt-4 space-y-2 rounded-xl border bg-white p-4 text-sm'>
            <p><strong>Tutor:</strong> {reply.reply}</p>
            <p><strong>Follow-up:</strong> {reply.follow_up_question}</p>
            <p><strong>Adaptive Path:</strong> {reply.adaptive_path?.join(' -> ')}</p>
            <div>
              <p className='font-semibold'>Mini Quiz</p>
              <ul className='list-disc pl-5'>
                {reply.mini_quiz?.map((q: any, idx: number) => <li key={idx}>{q.question}</li>)}
              </ul>
            </div>
          </div>
        ) : null}
      </Card>

      <Card title='Study Buddy'>
        {buddy ? (
          <>
            <p className='text-sm text-slate-700'>Consistency score: <strong>{buddy.consistency_score}%</strong></p>
            <p className='text-sm text-slate-700 mt-1'>Mood: <strong>{buddy.mood}</strong></p>
            <div className='mt-3 flex gap-2'>
              <Badge label={`Streak ${buddy.streak_days} days`} tone='brand' />
              <Badge label='Buddy Active' tone='good' />
            </div>
            <p className='mt-3 text-sm text-slate-700'>{buddy.nudges?.[0]?.message || 'Complete one session to receive your next nudge.'}</p>
          </>
        ) : (
          <p className='text-sm text-slate-700'>Study buddy data unavailable right now.</p>
        )}
      </Card>
    </div>
  );
}
