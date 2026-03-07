import { Card } from '@/components/ui/card';
import { ProgressBar } from '@/components/ui/progress-bar';

const analytics = [
  { subject: 'Math', progress: 64 },
  { subject: 'Biology', progress: 58 },
  { subject: 'History', progress: 72 },
];

export default function AnalyticsPage() {
  return (
    <div className='space-y-4'>
      <Card title='Learning Analytics Dashboard' subtitle='Mastery, readiness, retention, and consistency'>
        <div className='grid gap-4 md:grid-cols-3'>
          <div className='rounded-xl bg-slate-50 p-4'>
            <p className='text-sm text-slate-600'>Estimated Exam Readiness</p>
            <p className='text-3xl font-bold'>69%</p>
          </div>
          <div className='rounded-xl bg-slate-50 p-4'>
            <p className='text-sm text-slate-600'>Practice Accuracy</p>
            <p className='text-3xl font-bold'>71%</p>
          </div>
          <div className='rounded-xl bg-slate-50 p-4'>
            <p className='text-sm text-slate-600'>Streak</p>
            <p className='text-3xl font-bold'>9 days</p>
          </div>
        </div>
      </Card>
      <Card title='Subject Progress'>
        <div className='space-y-3'>
          {analytics.map((item) => (
            <div key={item.subject}>
              <p className='mb-1 text-sm text-slate-700'>{item.subject}</p>
              <ProgressBar value={item.progress} />
            </div>
          ))}
        </div>
      </Card>
      <Card title='Focus & Distraction Detection'>
        <p className='text-sm text-slate-700'>If repeated tab switches are detected, the app prompts: "Still studying?".</p>
      </Card>
    </div>
  );
}
