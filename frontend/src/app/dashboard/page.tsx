'use client';

import { useEffect, useMemo, useState } from 'react';

import { DashboardTopbar } from '@/components/layout/dashboard-topbar';
import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';
import { ProgressBar } from '@/components/ui/progress-bar';
import { getWithAuth } from '@/lib/request';

type DashboardData = {
  practice_accuracy: number;
  readiness_score: number;
  learning_consistency: number;
  streak_days: number;
  mastery_by_topic: Record<string, Record<string, { status: string; score: number }>>;
  retention_forecast: {
    high: string[];
    medium: string[];
    low: string[];
    next_3_days_risk: string[];
  };
};

type BuddyData = {
  streak_days: number;
  consistency_score: number;
  mood: string;
  nudges: Array<{ type: string; message: string }>;
};

function toPercent(value: number | undefined): number {
  if (typeof value !== 'number' || Number.isNaN(value)) return 0;
  return Math.max(0, Math.min(100, Math.round(value)));
}

export default function DashboardPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [buddy, setBuddy] = useState<BuddyData | null>(null);

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
        const [analyticsData, buddyData] = await Promise.all([
          getWithAuth('/analytics/dashboard'),
          getWithAuth('/analytics/study-buddy'),
        ]);
        setDashboard(analyticsData);
        setBuddy(buddyData);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load dashboard data.');
      } finally {
        setLoading(false);
      }
    }

    load();
  }, []);

  const retentionHealth = useMemo(() => {
    if (!dashboard) return 0;
    const high = dashboard.retention_forecast?.high?.length || 0;
    const medium = dashboard.retention_forecast?.medium?.length || 0;
    return Math.max(0, 100 - high * 25 - medium * 10);
  }, [dashboard]);

  const metrics = [
    { label: 'Practice Accuracy', value: toPercent(dashboard?.practice_accuracy) },
    { label: 'Exam Readiness', value: toPercent(dashboard?.readiness_score) },
    { label: 'Learning Consistency', value: toPercent(dashboard?.learning_consistency) },
    { label: 'Retention Health', value: toPercent(retentionHealth) },
  ];

  const masteryEntries = Object.entries(dashboard?.mastery_by_topic || {});

  return (
    <div className='space-y-4'>
      <DashboardTopbar />

      {loading ? <p className='text-sm text-slate-600'>Loading dashboard...</p> : null}
      {error ? <p className='text-sm text-rose-700'>{error}</p> : null}
      {!loading && !error && !dashboard ? (
        <p className='text-sm text-slate-600'>Log in to load your live dashboard metrics.</p>
      ) : null}

      <div className='grid gap-4 md:grid-cols-2 xl:grid-cols-4'>
        {metrics.map((m) => (
          <Card key={m.label} title={m.label}>
            <div className='flex items-end justify-between'>
              <p className='text-3xl font-bold'>{m.value}%</p>
              <Badge label={m.value > 0 ? 'Live data' : 'No data yet'} tone={m.value > 0 ? 'good' : 'neutral'} />
            </div>
            <div className='mt-3'>
              <ProgressBar value={m.value} />
            </div>
          </Card>
        ))}
      </div>

      <div className='grid gap-4 lg:grid-cols-3'>
        <Card title='Knowledge Graph' subtitle='Mastery by topic from your activity'>
          {masteryEntries.length === 0 ? (
            <p className='text-sm text-slate-600'>No mastery data yet. Complete homework, exams, or tutor sessions to populate this.</p>
          ) : (
            <div className='space-y-3 text-sm'>
              {masteryEntries.map(([subject, topics]) => (
                <div key={subject}>
                  <p className='font-semibold'>{subject}</p>
                  <div className='mt-1 space-y-1'>
                    {Object.entries(topics).map(([topic, info]) => (
                      <p key={`${subject}-${topic}`}>
                        {topic}: <strong>{info.status}</strong> ({toPercent(info.score)}%)
                      </p>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>

        <Card title='Review Urgency' subtitle='Memory decay prediction'>
          <ul className='space-y-2 text-sm'>
            <li>High: {(dashboard?.retention_forecast?.high || []).join(', ') || 'None'}</li>
            <li>Medium: {(dashboard?.retention_forecast?.medium || []).join(', ') || 'None'}</li>
            <li>Low: {(dashboard?.retention_forecast?.low || []).join(', ') || 'None'}</li>
          </ul>
        </Card>

        <Card title='Study Buddy' subtitle='Gamified consistency coach'>
          {buddy ? (
            <>
              <p className='text-sm text-slate-700'>Mood: <strong>{buddy.mood}</strong></p>
              <div className='mt-3 flex gap-2'>
                <Badge label={`Streak ${buddy.streak_days} days`} tone='brand' />
                <Badge label={`Consistency ${toPercent(buddy.consistency_score)}%`} tone='good' />
              </div>
              <p className='mt-3 text-sm text-slate-700'>
                {buddy.nudges?.[0]?.message || 'Complete one study action to get your first personalized nudge.'}
              </p>
            </>
          ) : (
            <p className='text-sm text-slate-600'>Study buddy data unavailable.</p>
          )}
        </Card>
      </div>
    </div>
  );
}
