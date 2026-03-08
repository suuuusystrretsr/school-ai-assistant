'use client';

import { useEffect, useState } from 'react';

import { Card } from '@/components/ui/card';
import { ProgressBar } from '@/components/ui/progress-bar';
import { getWithAuth } from '@/lib/request';

export default function AnalyticsPage() {
  const [dashboard, setDashboard] = useState<any>(null);
  const [intel, setIntel] = useState<any>(null);
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
        const [analytics, intelligence] = await Promise.all([
          getWithAuth('/analytics/dashboard'),
          getWithAuth('/analytics/intelligence'),
        ]);
        setDashboard(analytics);
        setIntel(intelligence);
      } catch (err) {
        setDashboard(null);
        setIntel(null);
        setError(err instanceof Error ? err.message : 'Failed to load analytics.');
      } finally {
        setLoading(false);
      }
    }

    load();
  }, []);

  const subjectEntries = Object.entries(dashboard?.subject_progress || {});

  return (
    <div className='space-y-4'>
      {!loading && !error && !dashboard ? <p className='text-sm text-slate-600'>Log in to load analytics.</p> : null}

      <Card title='Learning Analytics Dashboard' subtitle='Mastery, confidence, retention, and execution intelligence'>
        {loading ? <p className='text-sm text-slate-600'>Loading analytics...</p> : null}
        {error ? <p className='text-sm text-rose-700'>{error}</p> : null}

        <div className='grid gap-4 md:grid-cols-4'>
          <div className='rounded-xl bg-slate-50 p-4'>
            <p className='text-sm text-slate-600'>Outcome Forecast</p>
            <p className='text-3xl font-bold'>{Math.round(intel?.exam_outcome_simulator?.if_exam_today || dashboard?.readiness_score || 0)}%</p>
          </div>
          <div className='rounded-xl bg-slate-50 p-4'>
            <p className='text-sm text-slate-600'>Practice Accuracy</p>
            <p className='text-3xl font-bold'>{Math.round(dashboard?.practice_accuracy || 0)}%</p>
          </div>
          <div className='rounded-xl bg-slate-50 p-4'>
            <p className='text-sm text-slate-600'>Execution Stability</p>
            <p className='text-3xl font-bold'>{Math.round(dashboard?.learning_consistency || 0)}%</p>
          </div>
          <div className='rounded-xl bg-slate-50 p-4'>
            <p className='text-sm text-slate-600'>Identity Model</p>
            <p className='text-3xl font-bold'>{intel?.study_identity_model?.identity || 'n/a'}</p>
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
                <ProgressBar value={Math.round(progress as number)} />
              </div>
            ))}
          </div>
        )}
      </Card>

      <div className='grid gap-4 lg:grid-cols-2'>
        <Card title='Understanding Confidence Map'>
          <p className='text-sm'>Overall confidence: <strong>{intel?.confidence_map?.overall_confidence ?? 0}%</strong></p>
          <p className='text-sm mt-1'>Actual mastery: <strong>{intel?.confidence_map?.overall_actual ?? 0}%</strong></p>
          <p className='text-sm mt-2'>Overconfidence: {(intel?.confidence_map?.overconfidence || []).join(', ') || 'None'}</p>
          <p className='text-sm'>Hidden strengths: {(intel?.confidence_map?.hidden_strength || []).join(', ') || 'None'}</p>
          <p className='text-sm'>Uncertainty zones: {(intel?.confidence_map?.uncertainty_zones || []).join(', ') || 'None'}</p>
        </Card>

        <Card title='Cognitive Breakdown Engine'>
          <p className='text-sm'>Dominant issue: <strong>{intel?.cognitive_breakdown?.dominant || 'n/a'}</strong></p>
          <ul className='mt-2 list-disc pl-5 text-sm'>
            {(intel?.cognitive_breakdown?.breakdown || []).map((item: any) => (
              <li key={item.type}>{item.type}: {item.count}</li>
            ))}
          </ul>
        </Card>
      </div>

      <div className='grid gap-4 lg:grid-cols-2'>
        <Card title='AI Why You Are Stuck'>
          <ul className='list-disc pl-5 text-sm'>
            {(intel?.why_stuck?.insights || []).map((item: string) => <li key={item}>{item}</li>)}
          </ul>
        </Card>

        <Card title='Knowledge Dependency Scanner'>
          <ul className='list-disc pl-5 text-sm'>
            {(intel?.knowledge_dependencies || []).map((item: any, idx: number) => (
              <li key={idx}>{item.weak_topic}: depends on {(item.depends_on || []).join(', ')}</li>
            ))}
          </ul>
        </Card>
      </div>

      <div className='grid gap-4 lg:grid-cols-2'>
        <Card title='Friction Detector'>
          <p className='text-sm'>Score: <strong>{intel?.friction_detector?.score ?? 0}</strong></p>
          <p className='text-sm mt-1'>{intel?.friction_detector?.prompt}</p>
          <ul className='mt-2 list-disc pl-5 text-sm'>
            {(intel?.friction_detector?.patterns || []).map((item: string) => <li key={item}>{item}</li>)}
          </ul>
        </Card>

        <Card title='Mistake Pattern Intelligence'>
          <p className='text-sm'>Likely grade impact: <strong>{intel?.mistake_pattern_intelligence?.likely_grade_impact || 'n/a'}</strong></p>
          <ul className='mt-2 list-disc pl-5 text-sm'>
            {(intel?.mistake_pattern_intelligence?.common_error_types || []).map((item: string) => <li key={item}>{item}</li>)}
          </ul>
        </Card>
      </div>

      <div className='grid gap-4 lg:grid-cols-2'>
        <Card title='AI Session Replay'>
          <p className='text-sm'><strong>Strongest moment:</strong> {intel?.session_replay?.strongest_moment || 'n/a'}</p>
          <p className='text-sm mt-1'><strong>Most wasted time:</strong> {intel?.session_replay?.most_wasted_time || 'n/a'}</p>
          <p className='text-sm mt-1'><strong>Most valuable concept:</strong> {intel?.session_replay?.most_valuable_concept || 'n/a'}</p>
          <p className='text-sm mt-1'><strong>Most fragile concept:</strong> {intel?.session_replay?.most_fragile_concept || 'n/a'}</p>
          <p className='text-sm mt-1'><strong>Recommended next action:</strong> {intel?.session_replay?.recommended_next_action || 'n/a'}</p>
        </Card>

        <Card title='Exam Outcome Simulator + Priority Distortion'>
          <ul className='list-disc pl-5 text-sm'>
            <li>If exam today: {intel?.exam_outcome_simulator?.if_exam_today ?? 0}%</li>
            <li>If study 30 more minutes: {intel?.exam_outcome_simulator?.if_study_30_more_minutes ?? 0}%</li>
            <li>If fix one weak area: {intel?.exam_outcome_simulator?.if_fix_one_weak_area ?? 0}%</li>
            <li>If ignore retention risk: {intel?.exam_outcome_simulator?.if_ignore_retention_risk ?? 0}%</li>
          </ul>
          <p className='mt-3 text-sm'>{intel?.priority_distortion?.message || 'n/a'}</p>
        </Card>
      </div>
    </div>
  );
}
