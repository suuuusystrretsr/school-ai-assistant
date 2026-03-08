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
  const [intel, setIntel] = useState<any>(null);

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
        const [analyticsData, buddyData, intelligence] = await Promise.all([
          getWithAuth('/analytics/dashboard'),
          getWithAuth('/analytics/study-buddy'),
          getWithAuth('/analytics/intelligence'),
        ]);
        setDashboard(analyticsData);
        setBuddy(buddyData);
        setIntel(intelligence);
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
    { label: 'Outcome Forecast', value: toPercent(intel?.exam_outcome_simulator?.if_exam_today ?? dashboard?.readiness_score) },
    { label: 'Execution Stability', value: toPercent(dashboard?.learning_consistency) },
    { label: 'Memory Forecast Health', value: toPercent(retentionHealth) },
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
        {metrics.map((metric) => (
          <Card key={metric.label} title={metric.label}>
            <div className='flex items-end justify-between'>
              <p className='text-3xl font-bold'>{metric.value}%</p>
              <Badge label={metric.value > 0 ? 'Live data' : 'No data yet'} tone={metric.value > 0 ? 'good' : 'neutral'} />
            </div>
            <div className='mt-3'>
              <ProgressBar value={metric.value} />
            </div>
          </Card>
        ))}
      </div>

      <div className='grid gap-4 lg:grid-cols-3'>
        <Card title='Knowledge Structure' subtitle='Mastery and dependencies'>
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
          {intel?.knowledge_dependencies?.length ? (
            <div className='mt-3 rounded-xl border bg-slate-50 p-3 text-xs'>
              <p className='font-semibold'>Dependency Scanner</p>
              {intel.knowledge_dependencies.slice(0, 2).map((dep: any, idx: number) => (
                <p key={idx} className='mt-1'>{dep.weak_topic}{' -> '}affects {(dep.impacts || []).join(', ') || 'nearby topics'}</p>
              ))}
            </div>
          ) : null}
        </Card>

        <Card title='Memory Forecast' subtitle='What you are about to forget'>
          <ul className='space-y-2 text-sm'>
            <li>Immediate: {(intel?.memory_forecast?.forget_soon || dashboard?.retention_forecast?.high || []).join(', ') || 'None'}</li>
            <li>Soon: {(intel?.memory_forecast?.review_soon || dashboard?.retention_forecast?.medium || []).join(', ') || 'None'}</li>
            <li>Stable: {(intel?.memory_forecast?.stable || dashboard?.retention_forecast?.low || []).join(', ') || 'None'}</li>
          </ul>
        </Card>

        <Card title='Performance Coach' subtitle='Friction + priority guidance'>
          {buddy ? (
            <>
              <p className='text-sm text-slate-700'>Mood: <strong>{buddy.mood}</strong></p>
              <div className='mt-3 flex gap-2'>
                <Badge label={`Streak ${buddy.streak_days} days`} tone='brand' />
                <Badge label={`Consistency ${toPercent(buddy.consistency_score)}%`} tone='good' />
              </div>
              <p className='mt-3 text-sm text-slate-700'>{buddy.nudges?.[0]?.message || 'Complete one study action to get your first personalized nudge.'}</p>
            </>
          ) : (
            <p className='text-sm text-slate-600'>Study coach data unavailable.</p>
          )}
          {intel?.friction_detector ? (
            <div className='mt-3 rounded-xl border bg-slate-50 p-3 text-xs'>
              <p><strong>Friction score:</strong> {intel.friction_detector.score}</p>
              <p>{intel.friction_detector.prompt}</p>
            </div>
          ) : null}
        </Card>
      </div>

      <div className='grid gap-4 lg:grid-cols-2'>
        <Card title='Understanding Confidence Map' subtitle='Confidence vs actual mastery'>
          <div className='space-y-2 text-sm'>
            <p>Overall confidence: <strong>{intel?.confidence_map?.overall_confidence ?? 0}%</strong></p>
            <p>Actual performance: <strong>{intel?.confidence_map?.overall_actual ?? 0}%</strong></p>
            <p>Overconfidence zones: {(intel?.confidence_map?.overconfidence || []).join(', ') || 'None'}</p>
            <p>Hidden strengths: {(intel?.confidence_map?.hidden_strength || []).join(', ') || 'None'}</p>
            <p>Uncertainty zones: {(intel?.confidence_map?.uncertainty_zones || []).join(', ') || 'None'}</p>
          </div>
        </Card>

        <Card title='Cognitive Breakdown + Next Action' subtitle='Why errors happen and what to do next'>
          <p className='text-sm'>Dominant breakdown: <strong>{intel?.cognitive_breakdown?.dominant || 'n/a'}</strong></p>
          <p className='mt-2 text-sm'>Why stuck: {(intel?.why_stuck?.insights || []).join(' | ') || 'n/a'}</p>
          <p className='mt-2 text-sm'>Priority distortion: {intel?.priority_distortion?.message || 'n/a'}</p>
          <p className='mt-2 text-sm'>Study identity: <strong>{intel?.study_identity_model?.identity || 'n/a'}</strong></p>
          <p className='mt-2 text-sm'>Next best action: <strong>{intel?.next_best_action?.title || 'n/a'}</strong></p>
        </Card>
      </div>
    </div>
  );
}

