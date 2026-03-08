import Link from 'next/link';

import { MarketingFooter } from '@/components/layout/marketing-footer';
import { MarketingHeader } from '@/components/layout/marketing-header';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';

const features = [
  'Homework solver with explanation modes (ELI5, normal, advanced, teacher)',
  'AI tutor with adaptive mini-quizzes and revision paths',
  'Flashcard and lecture summarizer pipeline',
  'Knowledge graph, retention forecast, and confusion detection',
  'Live study rooms with WebSocket chat and presence',
  'Exam simulator with grading and weak-area predictions',
];

export default function LandingPage() {
  return (
    <main>
      <MarketingHeader />

      <section className='mx-auto grid max-w-7xl grid-cols-1 gap-8 px-6 pb-14 pt-6 lg:grid-cols-2'>
        <div className='animate-rise'>
          <Badge label='AI-Powered Learning Platform' tone='brand' />
          <h1 className='mt-5 text-4xl font-bold leading-tight text-ink md:text-6xl'>
            Study faster with a premium AI system built for real student outcomes.
          </h1>
          <p className='mt-5 max-w-xl text-lg text-slate-600'>
            SCHOOL AI ASSISTANT combines tutoring, planning, exam simulation, analytics, and collaboration in one polished workspace. Demo pages are visible without login, but live actions require account login.
          </p>
          <div className='mt-7 flex flex-wrap gap-3'>
            <Link href='/signup'>
              <Button className='px-6 py-3 text-base'>Create Free Account</Button>
            </Link>
            <Link href='/dashboard/homework'>
              <Button variant='secondary' className='px-6 py-3 text-base'>
                View Product (Homework Demo)
              </Button>
            </Link>
          </div>
        </div>

        <Card className='grid-bg animate-rise p-8'>
          <p className='text-sm font-semibold uppercase tracking-[0.1em] text-slate-500'>Learning Command Center</p>
          <div className='mt-4 grid gap-3 text-sm'>
            <div className='rounded-xl bg-white/90 p-3'>Homework solved today: <strong>14</strong></div>
            <div className='rounded-xl bg-white/90 p-3'>Current streak: <strong>9 days</strong></div>
            <div className='rounded-xl bg-white/90 p-3'>Readiness score: <strong>78%</strong></div>
            <div className='rounded-xl bg-white/90 p-3'>Urgent review: <strong>Quadratics, Cell Respiration</strong></div>
          </div>
        </Card>
      </section>

      <section id='features' className='mx-auto max-w-7xl px-6 py-10'>
        <h2 className='text-3xl font-bold text-ink'>Feature Highlights</h2>
        <div className='mt-5 grid gap-4 md:grid-cols-2'>
          {features.map((item) => (
            <Card key={item} className='animate-rise'>
              <p className='text-slate-700'>{item}</p>
            </Card>
          ))}
        </div>
      </section>

      <section id='how' className='mx-auto max-w-7xl px-6 py-10'>
        <h2 className='text-3xl font-bold text-ink'>How It Works</h2>
        <div className='mt-5 grid gap-4 md:grid-cols-3'>
          <Card title='1. Ask or Upload'>
            <p className='text-slate-600'>Submit text, image, PDF, lecture notes, or whiteboard input.</p>
          </Card>
          <Card title='2. Learn Adaptively'>
            <p className='text-slate-600'>Get explanations, hints, flashcards, practice sets, and tutor guidance.</p>
          </Card>
          <Card title='3. Improve Daily'>
            <p className='text-slate-600'>Track mastery, retention risk, weak areas, and progress streaks.</p>
          </Card>
        </div>
      </section>

      <section className='mx-auto max-w-7xl px-6 py-10'>
        <div className='grid gap-4 md:grid-cols-2'>
          <Card title='Testimonials (Placeholder)'>
            <p className='text-slate-600'>"This platform made exam prep actually structured."</p>
          </Card>
          <Card id='faq' title='FAQ (Placeholder)'>
            <p className='text-slate-600'>Q: Is this free? A: Yes, the MVP is fully free.</p>
          </Card>
        </div>
      </section>

      <MarketingFooter />
    </main>
  );
}

