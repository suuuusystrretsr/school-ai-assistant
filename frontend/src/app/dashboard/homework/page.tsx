'use client';

import { useState } from 'react';

import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { postWithAuth } from '@/lib/request';
import { ExplanationMode } from '@/types/app';

const modes: ExplanationMode[] = ['eli5', 'normal', 'advanced', 'teacher'];

export default function HomeworkPage() {
  const [mode, setMode] = useState<ExplanationMode>('normal');
  const [question, setQuestion] = useState('Solve 2x + 8 = 20');
  const [result, setResult] = useState<any>(null);
  const [signalMessage, setSignalMessage] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const [practice, setPractice] = useState<any>(null);
  const [attempt, setAttempt] = useState('');
  const [mistakeExplain, setMistakeExplain] = useState<any>(null);

  async function solveHomework() {
    if (!question.trim()) {
      setError('Enter a homework question first.');
      return;
    }

    setError('');
    setLoading(true);
    setPractice(null);
    setMistakeExplain(null);

    try {
      const data = await postWithAuth('/homework/solve', { question_text: question, explanation_mode: mode });
      setResult(data);

      await postWithAuth('/analytics/session-signal', {
        page: 'homework',
        event_type: 'interaction',
        action: 'solve-homework',
        topic: question.slice(0, 60),
        task_difficulty: mode === 'advanced' ? 'hard' : 'medium',
        dwell_seconds: 75,
        self_confidence: 60,
      });
    } catch (err) {
      setResult(null);
      setError(err instanceof Error ? err.message : 'Failed to solve homework.');
    } finally {
      setLoading(false);
    }
  }

  async function triggerConfusionCheck() {
    setError('');
    try {
      const data = await postWithAuth('/analytics/signals', {
        activity_seconds: 350,
        wrong_attempts: 2,
        answer_changes: 3,
        tab_switches: 1,
      });
      setSignalMessage(data.suggested_message || 'No signal response.');
    } catch (err) {
      setSignalMessage('');
      setError(err instanceof Error ? err.message : 'Failed to check confusion signal.');
    }
  }

  async function generatePractice() {
    if (!result?.solution_id) {
      setError('Solve homework first to generate related practice.');
      return;
    }

    setError('');
    try {
      const data = await postWithAuth('/homework/practice', {
        source_solution_id: result.solution_id,
        difficulty: 'medium',
      });
      setPractice(data);
    } catch (err) {
      setPractice(null);
      setError(err instanceof Error ? err.message : 'Failed to generate practice.');
    }
  }

  async function explainMyMistake() {
    if (!attempt.trim() || !result?.final_answer) {
      setError('Enter your attempt after solving to analyze the mistake.');
      return;
    }

    setError('');
    try {
      const data = await postWithAuth('/learning/explain-mistake', {
        question,
        user_answer: attempt,
        correct_answer: result.final_answer,
      });
      setMistakeExplain(data);

      await postWithAuth('/analytics/session-signal', {
        page: 'homework',
        event_type: 'interaction',
        action: 'mistake-analysis',
        topic: question.slice(0, 60),
        task_difficulty: 'medium',
        self_confidence: 45,
        was_correct: attempt.trim().toLowerCase() === String(result.final_answer).trim().toLowerCase(),
        dwell_seconds: 90,
      });
    } catch (err) {
      setMistakeExplain(null);
      setError(err instanceof Error ? err.message : 'Failed to analyze mistake.');
    }
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
        <div className='mt-3 flex flex-wrap gap-2'>
          <Button onClick={solveHomework} disabled={loading}>{loading ? 'Solving...' : 'Solve'}</Button>
          <Button variant='secondary' onClick={triggerConfusionCheck}>Need Hint Detector</Button>
          <Button variant='secondary' onClick={generatePractice}>Generate Practice</Button>
        </div>
        {error ? <p className='mt-2 text-sm text-rose-700'>{error}</p> : null}
        {signalMessage ? <p className='mt-2 text-sm text-slate-600'>{signalMessage}</p> : null}

        {result ? (
          <div className='mt-4 rounded-xl border bg-white p-4 text-sm'>
            <p><strong>Final Answer:</strong> {result.final_answer}</p>
            <p className='mt-2'><strong>Steps:</strong></p>
            <ul className='list-disc pl-5'>
              {result.steps?.map((step: string) => <li key={step}>{step}</li>)}
            </ul>
            <p className='mt-2'><strong>{mode.toUpperCase()}:</strong> {result.explanation_by_mode?.[mode]}</p>

            <div className='mt-4 rounded-lg border bg-slate-50 p-3'>
              <p className='font-semibold'>Cognitive Breakdown Engine</p>
              <p className='text-xs text-slate-600 mt-1'>Enter your own attempt and get targeted mistake diagnosis.</p>
              <textarea
                className='mt-2 h-20 w-full rounded-lg border p-2'
                placeholder='Type your own answer attempt here...'
                value={attempt}
                onChange={(e) => setAttempt(e.target.value)}
              />
              <Button className='mt-2' variant='secondary' onClick={explainMyMistake}>Explain My Mistake</Button>
              {mistakeExplain ? (
                <div className='mt-2 space-y-1 text-xs text-slate-700'>
                  <p><strong>Why wrong:</strong> {mistakeExplain.why_wrong}</p>
                  <p><strong>Logic break:</strong> {mistakeExplain.logic_break}</p>
                  <p><strong>Correct thinking:</strong> {mistakeExplain.correct_thinking}</p>
                </div>
              ) : null}
            </div>
          </div>
        ) : null}

        {practice ? (
          <div className='mt-4 rounded-xl border bg-white p-4 text-sm'>
            <p><strong>Practice Pack:</strong> {practice.title}</p>
            <ul className='mt-2 list-disc pl-5'>
              {practice.questions?.map((item: any, idx: number) => <li key={idx}>{item.question}</li>)}
            </ul>
          </div>
        ) : null}
      </Card>

      <div className='space-y-4'>
        <Card title='Whiteboard Solver (MVP Placeholder)'>
          <div className='h-40 rounded-xl border border-dashed p-3 text-sm text-slate-600'>
            Drawing input area placeholder. Handwriting recognition is intentionally not implemented yet.
          </div>
        </Card>
        <Card title='Progressive Hints'>
          <p className='text-sm text-slate-600'>Hints are revealed in 4 levels only after user chooses "Need a hint?".</p>
        </Card>
      </div>
    </div>
  );
}
