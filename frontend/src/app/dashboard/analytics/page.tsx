'use client';

import { useEffect, useState } from 'react';

import { Card } from '@/components/ui/card';
import { ProgressBar } from '@/components/ui/progress-bar';
import { getWithAuth } from '@/lib/request';

type DashboardData = {
  subject_progress: Record<string, number>;
  practice_accuracy: number;
  readiness_score: number;
  streak_days: number;
  recent_performance: {
    completed_exams: number;
    homework_solved: number;
    flashcard_decks: number;
    study_plans_generated: number;
    active_days_last_14: number;
  };
};

export default function AnalyticsPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    async function load() {
      const token = typeof window !== 'undefined' ? localStorage.getItem('schoolai_token') : null;
      if (!token) {
        setLoading(false);
        return;
      }

      setError('');
      setLoading(true);
      try {
        const analytics = await getWithAuth('/analytics/dashboard');
        setData(analytics);
      } catch (err) {
        setData(null);
        setError(err instanceof Error ? err.message : 'Failed to load analytics.');
      } finally {
        setLoading(false);
      }
    }

    load();
  }, []);

  const subjectEntries = Object.entries(data?.subject_progress || {});

  return (
    <div className='space-y-4'>
      {!loading && !error && !data ? (
        <p className='text-sm text-slate-600'>Log in to load analytics.</p>
      ) : null}

      <Card title='Learning Analytics Dashboard' subtitle='Live metrics from your account activity'>
        {loading ? <p className='text-sm text-slate-600'>Loading analytics...</p> : null}
        {error ? <p className='text-sm text-rose-700'>{error}</p> : null}

        <div className='grid gap-4 md:grid-cols-3'>
          <div className='rounded-xl bg-slate-50 p-4'>
            <p className='text-sm text-slate-600'>Estimated Exam Readiness</p>
            <p className='text-3xl font-bold'>{Math.round(data?.readiness_score || 0)}%</p>
          </div>
          <div className='rounded-xl bg-slate-50 p-4'>
            <p className='text-sm text-slate-600'>Practice Accuracy</p>
            <p className='text-3xl font-bold'>{Math.round(data?.practice_accuracy || 0)}%</p>
          </div>
          <div className='rounded-xl bg-slate-50 p-4'>
            <p className='text-sm text-slate-600'>Streak</p>
            <p className='text-3xl font-bold'>{Math.round(data?.streak_days || 0)} days</p>
          </div>
        </div>
      </Card>

      <Card title='Subject Progress'>
        {subjectEntries.length === 0 ? (
          <p className='text-sm text-slate-600'>No subject progress yet. Complete an exam to create tracked progress.</p>
        ) : (
          <div className='space-y-3'>
            {subjectEntries.map(([subject, progress]) => (
              <div key={subject}>
                <p className='mb-1 text-sm text-slate-700'>{subject}</p>
                <ProgressBar value={Math.round(progress)} />
              </div>
            ))}
          </div>
        )}
      </Card>

      <Card title='Recent Activity Summary'>
        <ul className='space-y-2 text-sm text-slate-700'>
          <li>Completed exams: {data?.recent_performance?.completed_exams || 0}</li>
          <li>Homework solved: {data?.recent_performance?.homework_solved || 0}</li>
          <li>Flashcard decks generated: {data?.recent_performance?.flashcard_decks || 0}</li>
          <li>Study plans generated: {data?.recent_performance?.study_plans_generated || 0}</li>
          <li>Active days in last 14: {data?.recent_performance?.active_days_last_14 || 0}</li>
        </ul>
      </Card>

      <Card title='Focus & Distraction Detection'>
        <p className='text-sm text-slate-700'>If repeated tab switches are detected, the app prompts: "Still studying?".</p>
      </Card>
    </div>
  );
}
