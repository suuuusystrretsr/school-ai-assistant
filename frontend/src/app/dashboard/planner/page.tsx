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

export default function PlannerPage() {
  const [subject, setSubject] = useState('Math');
  const [examDate, setExamDate] = useState('');
  const [weakTopicsInput, setWeakTopicsInput] = useState('Quadratics, Word problems');
  const [weeklyAvailability, setWeeklyAvailability] = useState(600);

  const [tasks, setTasks] = useState<PlannerTask[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const defaultDate = new Date();
    defaultDate.setDate(defaultDate.getDate() + 14);
    setExamDate(defaultDate.toISOString().slice(0, 10));

    async function loadTasks() {
      setError('');
      setLoading(true);
      try {
        const existing = await getWithAuth('/planner/tasks');
        setTasks(Array.isArray(existing) ? existing : []);
      } catch (err) {
        setTasks([]);
        setError(err instanceof Error ? err.message : 'Failed to load planner tasks.');
      } finally {
        setLoading(false);
      }
    }

    loadTasks();
  }, []);

  async function generatePlan() {
    setError('');
    try {
      const weakTopics = weakTopicsInput
        .split(',')
        .map((item) => item.trim())
        .filter(Boolean);

      const data = await postWithAuth('/planner/generate', {
        exams: [{ subject, exam_date: examDate }],
        weekly_availability_minutes: weeklyAvailability,
        weak_topics: weakTopics.length > 0 ? weakTopics : ['Foundations'],
        priorities: { [subject]: 10 },
      });
      setTasks(Array.isArray(data) ? data : []);
    } catch (err) {
      setTasks([]);
      setError(err instanceof Error ? err.message : 'Failed to generate study plan.');
    }
  }

  return (
    <div className='space-y-4'>
      <Card title='Smart Study Planner' subtitle='Build plan from your exam date, weak topics, and availability'>
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
            <input
              className='mt-1 w-full rounded-xl border p-2'
              value={weakTopicsInput}
              onChange={(e) => setWeakTopicsInput(e.target.value)}
            />
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
        </div>

        <Button className='mt-3' onClick={generatePlan}>Generate Personalized Plan</Button>
        {error ? <p className='mt-2 text-sm text-rose-700'>{error}</p> : null}
      </Card>

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
