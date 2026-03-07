'use client';

import { useState } from 'react';

import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { postWithAuth } from '@/lib/request';

export default function PlannerPage() {
  const [tasks, setTasks] = useState<any[]>([]);
  const [error, setError] = useState('');

  async function generatePlan() {
    setError('');
    try {
      const data = await postWithAuth('/planner/generate', {
        exams: [
          { subject: 'Math', exam_date: '2026-04-08' },
          { subject: 'Biology', exam_date: '2026-04-15' },
        ],
        weekly_availability_minutes: 600,
        weak_topics: ['Quadratics', 'Cell respiration'],
        priorities: { Math: 10, Biology: 8 },
      });
      setTasks(Array.isArray(data) ? data : []);
    } catch (err) {
      setTasks([]);
      setError(err instanceof Error ? err.message : 'Failed to generate study plan.');
    }
  }

  return (
    <div className='space-y-4'>
      <Card title='Smart Study Planner' subtitle='Uses exams, weak topics, and availability to build plan'>
        <Button onClick={generatePlan}>Generate Personalized Plan</Button>
        {error ? <p className='mt-2 text-sm text-rose-700'>{error}</p> : null}
      </Card>
      <div className='grid gap-3 md:grid-cols-2'>
        {tasks.map((task) => (
          <Card key={task.id} title={`${task.subject} - ${task.topic}`}>
            <p className='text-sm text-slate-700'>Due: {task.due_date}</p>
            <p className='text-sm text-slate-700'>Duration: {task.minutes} min</p>
            <p className='text-sm text-slate-700'>Priority: {task.priority}</p>
          </Card>
        ))}
      </div>
    </div>
  );
}
