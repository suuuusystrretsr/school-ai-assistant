'use client';

import { useState } from 'react';

import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { API_URL } from '@/lib/api';

export default function PlannerPage() {
  const [tasks, setTasks] = useState<any[]>([]);

  async function generatePlan() {
    const token = localStorage.getItem('schoolai_token');
    const res = await fetch(`${API_URL}/planner/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        exams: [
          { subject: 'Math', exam_date: '2026-04-08' },
          { subject: 'Biology', exam_date: '2026-04-15' }
        ],
        weekly_availability_minutes: 600,
        weak_topics: ['Quadratics', 'Cell respiration'],
        priorities: { Math: 10, Biology: 8 }
      }),
    });
    const data = await res.json();
    setTasks(Array.isArray(data) ? data : []);
  }

  return (
    <div className='space-y-4'>
      <Card title='Smart Study Planner' subtitle='Uses exams, weak topics, and availability to build plan'>
        <Button onClick={generatePlan}>Generate Personalized Plan</Button>
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
