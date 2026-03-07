'use client';

import { useEffect, useMemo, useState } from 'react';

import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { postWithAuth } from '@/lib/request';

export default function ExamsPage() {
  const [exam, setExam] = useState<any>(null);
  const [secondsLeft, setSecondsLeft] = useState(0);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    if (secondsLeft <= 0) return;
    const timer = setInterval(() => setSecondsLeft((prev) => prev - 1), 1000);
    return () => clearInterval(timer);
  }, [secondsLeft]);

  const timerLabel = useMemo(
    () => `${Math.floor(secondsLeft / 60)}:${String(secondsLeft % 60).padStart(2, '0')}`,
    [secondsLeft]
  );

  async function generateExam() {
    setError('');
    setResult(null);
    try {
      const data = await postWithAuth('/exams/generate', { subject: 'Math', difficulty: 'medium', duration_minutes: 20 });
      if (!data?.exam_id || !data?.subject) {
        throw new Error('Invalid exam response from API.');
      }
      setExam(data);
      setSecondsLeft((data.duration_minutes || 20) * 60);
    } catch (err) {
      setExam(null);
      setError(err instanceof Error ? err.message : 'Failed to generate exam.');
    }
  }

  async function submitExam() {
    if (!exam) {
      setError('Generate an exam first.');
      return;
    }

    setError('');
    try {
      const answers: Record<number, string> = {};
      exam.questions?.forEach((q: any) => {
        answers[q.id] = 'B';
      });
      const data = await postWithAuth(`/exams/${exam.exam_id}/submit`, { answers });
      setResult(data);
    } catch (err) {
      setResult(null);
      setError(err instanceof Error ? err.message : 'Failed to submit exam.');
    }
  }

  return (
    <div className='space-y-4'>
      <Card title='AI Exam Simulator' subtitle='Generate, time, grade, and review performance breakdown'>
        <div className='flex items-center gap-2'>
          <Button onClick={generateExam}>Generate Exam</Button>
          <Button variant='secondary' onClick={submitExam}>Submit Exam</Button>
          <span className='rounded-lg bg-slate-100 px-3 py-2 text-sm font-semibold'>Timer: {timerLabel}</span>
        </div>
        {error ? <p className='mt-2 text-sm text-rose-700'>{error}</p> : null}
      </Card>

      {exam ? (
        <Card title={`Exam: ${exam.subject}`} subtitle={`Predicted score: ${exam.predicted_score}%`}>
          <ul className='space-y-2 text-sm'>
            {exam.questions?.slice(0, 5).map((q: any) => <li key={q.id}>{q.prompt}</li>)}
          </ul>
        </Card>
      ) : null}

      {result ? (
        <Card title='Performance Review'>
          <p>Actual score: <strong>{result.actual_score}%</strong></p>
          <p className='mt-2'>Weak areas: {result.weak_areas?.join(', ')}</p>
          <p className='mt-2'>Next review topics: {result.next_topics?.join(', ')}</p>
        </Card>
      ) : null}
    </div>
  );
}
