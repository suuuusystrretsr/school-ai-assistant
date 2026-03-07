import { DashboardTopbar } from '@/components/layout/dashboard-topbar';
import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';
import { ProgressBar } from '@/components/ui/progress-bar';

const metrics = [
  { label: 'Practice Accuracy', value: 71, delta: '+6%' },
  { label: 'Exam Readiness', value: 69, delta: '+4%' },
  { label: 'Learning Consistency', value: 62, delta: '+8%' },
  { label: 'Retention Health', value: 74, delta: '+2%' },
];

export default function DashboardPage() {
  return (
    <div className='space-y-4'>
      <DashboardTopbar />

      <div className='grid gap-4 md:grid-cols-2 xl:grid-cols-4'>
        {metrics.map((m) => (
          <Card key={m.label} title={m.label}>
            <div className='flex items-end justify-between'>
              <p className='text-3xl font-bold'>{m.value}%</p>
              <Badge label={m.delta} tone='good' />
            </div>
            <div className='mt-3'>
              <ProgressBar value={m.value} />
            </div>
          </Card>
        ))}
      </div>

      <div className='grid gap-4 lg:grid-cols-3'>
        <Card title='Knowledge Graph' subtitle='Mastery by topic'>
          <div className='space-y-2 text-sm'>
            <p>Linear Equations: <strong>Mastered</strong></p>
            <p>Quadratics: <strong className='text-amber-700'>Weak</strong></p>
            <p>Polynomials: <strong className='text-slate-600'>Not learned</strong></p>
          </div>
        </Card>
        <Card title='Review Urgency' subtitle='Memory decay prediction'>
          <ul className='space-y-2 text-sm'>
            <li>High: Quadratics</li>
            <li>Medium: Cell respiration</li>
            <li>Low: Photosynthesis</li>
          </ul>
        </Card>
        <Card title='Study Buddy' subtitle='Gamified consistency coach'>
          <p className='text-sm text-slate-700'>"Nice streak. Keep your 25-minute focus block going."</p>
          <div className='mt-3 flex gap-2'>
            <Badge label='Streak 9 days' tone='brand' />
            <Badge label='Mood: Focused' tone='good' />
          </div>
        </Card>
      </div>
    </div>
  );
}
