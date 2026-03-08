'use client';

import { useEffect, useMemo, useState } from 'react';

import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { postWithAuth } from '@/lib/request';

type ExamQuestion = {
  id: number;
  prompt: string;
  choices: string[];
};

export default function ExamsPage() {
  const [subject, setSubject] = useState('Math');
  const [difficulty, setDifficulty] = useState('medium');
  const [duration, setDuration] = useState(20);

  const [exam, setExam] = useState<any>(null);
  const [answers, setAnswers] = useState<Record<number, string>>({});
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
    setAnswers({});

    try {
      const data = await postWithAuth('/exams/generate', {
        subject,
        difficulty,
        duration_minutes: duration,
      });
      if (!data?.exam_id || !Array.isArray(data?.questions)) {
        throw new Error('Invalid exam response from API.');
      }
      setExam(data);
      setSecondsLeft((data.duration_minutes || duration) * 60);
    } catch (err) {
      setExam(null);
      setError(err instanceof Error ? err.message : 'Failed to generate exam.');
    }
  }

  function setAnswer(questionId: number, option: string) {
    setAnswers((prev) => ({ ...prev, [questionId]: option }));
  }

  async function submitExam() {
    if (!exam) {
      setError('Generate an exam first.');
      return;
    }

    const total = Array.isArray(exam.questions) ? exam.questions.length : 0;
    const answered = Object.keys(answers).length;
    if (answered < total) {
      setError(`Answer all questions first (${answered}/${total} answered).`);
      return;
    }

    setError('');
    try {
      const data = await postWithAuth(`/exams/${exam.exam_id}/submit`, { answers });
      setResult(data);
    } catch (err) {
      setResult(null);
      setError(err instanceof Error ? err.message : 'Failed to submit exam.');
    }
  }

  return (
    <div className='space-y-4'>
      <Card title='AI Exam Simulator' subtitle='Generate, answer, submit, and review real score breakdown'>
        <div className='grid gap-2 md:grid-cols-4'>
          <label className='text-sm'>
            Subject
            <select className='mt-1 w-full rounded-xl border p-2' value={subject} onChange={(e) => setSubject(e.target.value)}>
              <option>Math</option>
              <option>Biology</option>
              <option>History</option>
              <option>Chemistry</option>
            </select>
          </label>
          <label className='text-sm'>
            Difficulty
            <select className='mt-1 w-full rounded-xl border p-2' value={difficulty} onChange={(e) => setDifficulty(e.target.value)}>
              <option value='easy'>Easy</option>
              <option value='medium'>Medium</option>
              <option value='hard'>Hard</option>
            </select>
          </label>
          <label className='text-sm'>
            Minutes
            <input
              className='mt-1 w-full rounded-xl border p-2'
              type='number'
              min={5}
              max={180}
              value={duration}
              onChange={(e) => setDuration(Number(e.target.value) || 20)}
            />
          </label>
          <div className='flex items-end'>
            <span className='rounded-lg bg-slate-100 px-3 py-2 text-sm font-semibold w-full text-center'>Timer: {timerLabel}</span>
          </div>
        </div>

        <div className='mt-3 flex items-center gap-2'>
          <Button onClick={generateExam}>Generate Exam</Button>
          <Button variant='secondary' onClick={submitExam}>Submit Exam</Button>
        </div>

        {error ? <p className='mt-2 text-sm text-rose-700'>{error}</p> : null}
      </Card>

      {exam ? (
        <Card
          title={`Exam: ${exam.subject}`}
          subtitle={`Predicted score: ${exam.predicted_score > 0 ? `${exam.predicted_score}%` : 'N/A (no prior exam history yet)'}`}
        >
          <div className='space-y-4'>
            {(exam.questions as ExamQuestion[]).map((q, idx) => (
              <div key={q.id} className='rounded-xl border bg-white p-3'>
                <p className='font-semibold'>Q{idx + 1}. {q.prompt}</p>
                <div className='mt-2 grid gap-2 sm:grid-cols-2'>
                  {q.choices.map((choice, cIdx) => {
                    const option = ['A', 'B', 'C', 'D'][cIdx] || choice;
                    const selected = answers[q.id] === option;
                    return (
                      <button
                        key={`${q.id}-${option}`}
                        className={`rounded-lg border px-3 py-2 text-left text-sm ${selected ? 'border-brand-500 bg-brand-50' : 'border-slate-200 bg-white'}`}
                        onClick={() => setAnswer(q.id, option)}
                      >
                        <strong>{option}.</strong> {choice}
                      </button>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </Card>
      ) : null}

      {result ? (
        <Card title='Performance Review'>
          <p>Actual score: <strong>{result.actual_score}%</strong></p>
          <p className='mt-2'>Weak areas: {result.weak_areas?.join(', ') || 'None'}</p>
          <p className='mt-2'>Next review topics: {result.next_topics?.join(', ') || 'None'}</p>
        </Card>
      ) : null}
    </div>
  );
}