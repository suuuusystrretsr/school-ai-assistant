'use client';

import { useEffect, useState } from 'react';

import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { getWithAuth, postWithAuth } from '@/lib/request';

type PlannerTask = {
  id: number;
  subject: string;
  topic: string;
  due_date: string;
  minutes: number;
  priority: string;
  recommendations: string[];
};

const energyOptions = ['very low', 'low', 'medium', 'high', 'very high'];

export default function PlannerPage() {
  const [subject, setSubject] = useState('Math');
  const [examDate, setExamDate] = useState('');
  const [weakTopicsInput, setWeakTopicsInput] = useState('Quadratics, Word problems');
  const [weeklyAvailability, setWeeklyAvailability] = useState(600);
  const [energyLevel, setEnergyLevel] = useState('medium');

  const [tasks, setTasks] = useState<PlannerTask[]>([]);
  const [autopilot, setAutopilot] = useState<any>(null);
  const [intelligence, setIntelligence] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const defaultDate = new Date();
    defaultDate.setDate(defaultDate.getDate() + 14);
    setExamDate(defaultDate.toISOString().slice(0, 10));

    async function loadData() {
      setError('');
      setLoading(true);
      try {
        const [existing, intel] = await Promise.all([
          getWithAuth('/planner/tasks'),
          getWithAuth('/analytics/intelligence'),
        ]);
        setTasks(Array.isArray(existing) ? existing : []);
        setIntelligence(intel);
      } catch (err) {
        setTasks([]);
        setIntelligence(null);
        setError(err instanceof Error ? err.message : 'Failed to load planner data.');
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, []);

  function parseWeakTopics() {
    const weakTopics = weakTopicsInput
      .split(',')
      .map((item) => item.trim())
      .filter(Boolean);
    return weakTopics.length > 0 ? weakTopics : ['Foundations'];
  }

  async function generatePlan() {
    setError('');
    try {
      const weakTopics = parseWeakTopics();

      const data = await postWithAuth('/planner/generate', {
        exams: [{ subject, exam_date: examDate }],
        weekly_availability_minutes: weeklyAvailability,
        weak_topics: weakTopics,
        priorities: { [subject]: 10 },
      });
      setTasks(Array.isArray(data) ? data : []);

      await postWithAuth('/analytics/session-signal', {
        page: 'planner',
        event_type: 'interaction',
        action: 'generate-plan',
        topic: weakTopics[0],
        task_difficulty: 'medium',
        energy_level: energyLevel,
        dwell_seconds: 45,
      });
    } catch (err) {
      setTasks([]);
      setError(err instanceof Error ? err.message : 'Failed to generate study plan.');
    }
  }

  async function runAutopilot() {
    setError('');
    try {
      const weakTopics = parseWeakTopics();
      const memoryRisk = intelligence?.memory_forecast?.forget_soon || [];
      const confidenceGaps = intelligence?.confidence_map?.overconfidence || [];
      const readinessScore = intelligence?.exam_outcome_simulator?.if_exam_today || 60;

      const data = await postWithAuth('/analytics/autopilot', {
        energy_level: energyLevel,
        available_minutes: Math.min(180, Math.max(30, Math.round(weeklyAvailability / 7))),
        weak_topics: weakTopics,
        retention_risk: memoryRisk,
        confidence_gaps: confidenceGaps,
        readiness_score: readinessScore,
      });
      setAutopilot(data);
    } catch (err) {
      setAutopilot(null);
      setError(err instanceof Error ? err.message : 'Failed to generate autopilot session.');
    }
  }

  return (
    <div className='space-y-4'>
      <Card title='Smart Study Planner' subtitle='Uses exams, weak topics, and availability to build plan'>
        <div className='grid gap-3 md:grid-cols-2'>
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
            Exam Date
            <input className='mt-1 w-full rounded-xl border p-2' type='date' value={examDate} onChange={(e) => setExamDate(e.target.value)} />
          </label>
          <label className='text-sm md:col-span-2'>
            Weak Topics (comma-separated)
            <input className='mt-1 w-full rounded-xl border p-2' value={weakTopicsInput} onChange={(e) => setWeakTopicsInput(e.target.value)} />
          </label>
          <label className='text-sm'>
            Weekly Availability (minutes)
            <input
              className='mt-1 w-full rounded-xl border p-2'
              type='number'
              min={60}
              max={3000}
              value={weeklyAvailability}
              onChange={(e) => setWeeklyAvailability(Number(e.target.value) || 600)}
            />
          </label>
          <label className='text-sm'>
            Mental Energy Level
            <select className='mt-1 w-full rounded-xl border p-2' value={energyLevel} onChange={(e) => setEnergyLevel(e.target.value)}>
              {energyOptions.map((item) => <option key={item}>{item}</option>)}
            </select>
          </label>
        </div>

        <div className='mt-3 flex flex-wrap gap-2'>
          <Button onClick={generatePlan}>Generate Personalized Plan</Button>
          <Button variant='secondary' onClick={runAutopilot}>Run AI Study Autopilot</Button>
        </div>
        {error ? <p className='mt-2 text-sm text-rose-700'>{error}</p> : null}
      </Card>

      {autopilot ? (
        <Card title='AI Study Autopilot' subtitle='Energy-aware routing and session control'>
          <p className='text-sm text-slate-700'><strong>Routing:</strong> {autopilot.routing}</p>
          <p className='mt-1 text-sm text-slate-700'><strong>Study identity:</strong> {autopilot.study_identity}</p>
          <div className='mt-3 grid gap-2 md:grid-cols-2'>
            {autopilot.plan?.map((step: any, idx: number) => (
              <div key={idx} className='rounded-xl border bg-white p-3 text-sm'>
                <p className='font-semibold'>Block {idx + 1}: {step.block_minutes} min</p>
                <p>{step.activity}</p>
                <p className='text-slate-600'>{step.reason}</p>
              </div>
            ))}
          </div>
          <p className='mt-3 text-sm text-slate-700'><strong>Skip for now:</strong> {autopilot.skip_for_now?.join(', ')}</p>
          <ul className='mt-2 list-disc pl-5 text-sm text-slate-700'>
            {autopilot.switch_rules?.map((rule: string) => <li key={rule}>{rule}</li>)}
          </ul>
        </Card>
      ) : null}

      <div className='grid gap-3 md:grid-cols-2'>
        {loading ? <p className='text-sm text-slate-600'>Loading saved tasks...</p> : null}
        {!loading && tasks.length === 0 ? <p className='text-sm text-slate-600'>No planner tasks yet. Generate your first plan.</p> : null}
        {tasks.map((task) => (
          <Card key={task.id} title={`${task.subject} - ${task.topic}`}>
            <p className='text-sm text-slate-700'>Due: {task.due_date}</p>
            <p className='text-sm text-slate-700'>Duration: {task.minutes} min</p>
            <p className='text-sm text-slate-700'>Priority: {task.priority}</p>
            {task.recommendations?.length ? (
              <p className='mt-2 text-sm text-slate-700'>Recommendations: {task.recommendations.join(', ')}</p>
            ) : null}
          </Card>
        ))}
      </div>
    </div>
  );
}
