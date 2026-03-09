'use client';

import { useEffect, useMemo, useState } from 'react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { getWithAuth, postWithAuth } from '@/lib/request';

type ClassroomState = {
  session_id: number;
  status: string;
  setup: {
    subject: string;
    topic: string;
    grade_level: string;
    duration_minutes: number;
    difficulty: string;
    learning_goal?: string;
    teacher_style: string;
    custom_teacher_style?: string;
  };
  lesson_plan: Array<{ name: string; minutes: number }>;
  current_phase_index: number;
  current_phase: { name: string; minutes: number } | null;
  adaptive_difficulty: string;
  teacher_turn: {
    phase?: string;
    message?: string;
    question?: string;
    feedback?: string;
  };
  visuals: {
    slides?: string[];
    diagram?: { nodes?: string[]; edges?: string[] };
    timeline?: Array<{ step: number; phase: string; minutes: number }>;
    whiteboard_steps?: string[];
  };
  transcript: Array<Record<string, any>>;
  transcript_compacted: boolean;
  report: {
    class_summary?: string;
    key_concepts?: string[];
    weak_areas?: string[];
    suggested_next_topic?: string;
    recommended_practice_tasks?: string[];
  };
};

type ClassroomHistoryItem = {
  id: number;
  subject: string;
  topic: string;
  grade_level: string;
  status: string;
  duration_minutes: number;
  started_at?: string;
  completed_at?: string;
  transcript_compacted?: boolean;
};

const teacherStyles = ['Standard teacher', 'Exam-focused teacher', 'Visual explainer', 'Fast crash-course teacher', 'Custom'];
const gradeOptions = ['3rd Grade', '4th Grade', '5th Grade', '6th Grade', '7th Grade', '8th Grade', '9th Grade', '10th Grade', '11th Grade', '12th Grade'];
const durationOptions = [15, 30, 45, 60, 75, 90];

export default function ClassroomPage() {
  const [subject, setSubject] = useState('History');
  const [topic, setTopic] = useState('World War II');
  const [gradeLevel, setGradeLevel] = useState('6th Grade');
  const [durationMinutes, setDurationMinutes] = useState(45);
  const [difficulty, setDifficulty] = useState('standard');
  const [learningGoal, setLearningGoal] = useState('exam preparation');
  const [teacherStyle, setTeacherStyle] = useState('Standard teacher');
  const [customTeacherStyle, setCustomTeacherStyle] = useState('');

  const [session, setSession] = useState<ClassroomState | null>(null);
  const [history, setHistory] = useState<ClassroomHistoryItem[]>([]);
  const [studentResponse, setStudentResponse] = useState('');
  const [confidence, setConfidence] = useState(60);

  const [loadingStart, setLoadingStart] = useState(false);
  const [loadingRespond, setLoadingRespond] = useState(false);
  const [loadingEnd, setLoadingEnd] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [status, setStatus] = useState('');
  const [error, setError] = useState('');

  const progress = useMemo(() => {
    if (!session || !session.lesson_plan?.length) return 0;
    return Math.round(((session.current_phase_index + 1) / session.lesson_plan.length) * 100);
  }, [session]);

  const currentSessionId = session?.session_id;

  function formatStamp(value?: string) {
    if (!value) return 'n/a';
    const dt = new Date(value);
    if (Number.isNaN(dt.getTime())) return value;
    return dt.toLocaleString();
  }

  async function loadHistory() {
    setLoadingHistory(true);
    try {
      const data = await getWithAuth('/classroom/history');
      setHistory(Array.isArray(data?.sessions) ? data.sessions : []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load classroom history.');
    } finally {
      setLoadingHistory(false);
    }
  }

  useEffect(() => {
    loadHistory();
  }, []);

  async function startClass() {
    setError('');
    setStatus('Starting class...');
    setLoadingStart(true);
    try {
      const data = await postWithAuth('/classroom/start', {
        subject,
        topic,
        grade_level: gradeLevel,
        duration_minutes: durationMinutes,
        difficulty,
        learning_goal: learningGoal || undefined,
        teacher_style: teacherStyle === 'Custom' ? 'Custom' : teacherStyle,
        custom_teacher_style: teacherStyle === 'Custom' ? customTeacherStyle : undefined,
      });
      setSession(data);
      setStudentResponse('');
      setStatus('Class started. Answer the teacher question to continue.');
      await loadHistory();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start class.');
      setStatus('');
    } finally {
      setLoadingStart(false);
    }
  }

  async function submitResponse() {
    if (!currentSessionId) {
      setError('Start a class first.');
      return;
    }
    if (!studentResponse.trim()) {
      setError('Enter your response before sending.');
      return;
    }

    setError('');
    setStatus('Teacher is reviewing your response...');
    setLoadingRespond(true);
    try {
      const data = await postWithAuth(`/classroom/${currentSessionId}/respond`, {
        student_response: studentResponse,
        self_confidence: confidence,
      });
      setSession(data);
      setStudentResponse('');
      setStatus('Response processed. Continue to the next prompt.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit response.');
      setStatus('');
    } finally {
      setLoadingRespond(false);
    }
  }

  async function endClass() {
    if (!currentSessionId) {
      setError('No active class session to end.');
      return;
    }

    setError('');
    setStatus('Finalizing class report...');
    setLoadingEnd(true);
    try {
      const data = await postWithAuth(`/classroom/${currentSessionId}/end`, {
        reason: 'user-ended-session',
      });
      setSession(data);
      setStatus('Class completed. Report generated.');
      await loadHistory();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to end class.');
      setStatus('');
    } finally {
      setLoadingEnd(false);
    }
  }

  async function openSession(sessionId: number) {
    setError('');
    setStatus('Loading selected class session...');
    try {
      const data = await getWithAuth(`/classroom/${sessionId}`);
      setSession(data);
      setStatus('Session loaded.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to open selected session.');
      setStatus('');
    }
  }

  return (
    <div className='space-y-4'>
      <div className='grid gap-4 xl:grid-cols-3'>
        <Card className='xl:col-span-2' title='AI Classroom Setup' subtitle='Configure a teacher-led class session'>
          <div className='grid gap-2 md:grid-cols-2'>
            <label className='text-sm'>
              Subject
              <input className='mt-1 w-full rounded-xl border p-2' value={subject} onChange={(e) => setSubject(e.target.value)} />
            </label>
            <label className='text-sm'>
              Topic
              <input className='mt-1 w-full rounded-xl border p-2' value={topic} onChange={(e) => setTopic(e.target.value)} />
            </label>
            <label className='text-sm'>
              Grade Level
              <select className='mt-1 w-full rounded-xl border p-2' value={gradeLevel} onChange={(e) => setGradeLevel(e.target.value)}>
                {gradeOptions.map((item) => <option key={item}>{item}</option>)}
              </select>
            </label>
            <label className='text-sm'>
              Class Duration
              <select className='mt-1 w-full rounded-xl border p-2' value={durationMinutes} onChange={(e) => setDurationMinutes(Number(e.target.value))}>
                {durationOptions.map((item) => <option key={item} value={item}>{item} minutes</option>)}
              </select>
            </label>
            <label className='text-sm'>
              Difficulty
              <select className='mt-1 w-full rounded-xl border p-2' value={difficulty} onChange={(e) => setDifficulty(e.target.value)}>
                <option value='easy'>Easy</option>
                <option value='standard'>Standard</option>
                <option value='hard'>Hard</option>
              </select>
            </label>
            <label className='text-sm'>
              Learning Goal (optional)
              <input className='mt-1 w-full rounded-xl border p-2' value={learningGoal} onChange={(e) => setLearningGoal(e.target.value)} placeholder='exam preparation / first time learning / review mode' />
            </label>
            <label className='text-sm md:col-span-2'>
              Teacher Style
              <select className='mt-1 w-full rounded-xl border p-2' value={teacherStyle} onChange={(e) => setTeacherStyle(e.target.value)}>
                {teacherStyles.map((style) => <option key={style}>{style}</option>)}
              </select>
            </label>
          </div>

          {teacherStyle === 'Custom' ? (
            <label className='mt-3 block text-sm'>
              Custom Teacher Style
              <input
                className='mt-1 w-full rounded-xl border p-2'
                value={customTeacherStyle}
                onChange={(e) => setCustomTeacherStyle(e.target.value)}
                placeholder='Teach like a strict exam teacher who asks lots of questions'
              />
            </label>
          ) : null}

          <div className='mt-3 flex flex-wrap gap-2'>
            <Button onClick={startClass} disabled={loadingStart}>{loadingStart ? 'Starting...' : 'Start Class'}</Button>
            <Button variant='secondary' onClick={endClass} disabled={!currentSessionId || loadingEnd || session?.status === 'completed'}>
              {loadingEnd ? 'Ending...' : 'End Class'}
            </Button>
          </div>
        </Card>

        <Card title='Class Status' subtitle='Adaptive teacher behavior and progression'>
          <div className='space-y-3 text-sm'>
            <div className='flex flex-wrap gap-2'>
              <Badge label={`Progress ${progress}%`} tone='brand' />
              <Badge label={`Difficulty ${session?.adaptive_difficulty || difficulty}`} tone='warn' />
              <Badge label={session?.status === 'completed' ? 'Completed' : 'In Progress'} tone={session?.status === 'completed' ? 'good' : 'neutral'} />
            </div>
            <p><strong>Current phase:</strong> {session?.current_phase?.name || 'Not started'}</p>
            <p><strong>Session:</strong> {currentSessionId ? `#${currentSessionId}` : 'n/a'}</p>
            <p className='text-slate-600'>
              Duration-aware planning automatically scales for 15, 30, 45, 60+ minute classes.
            </p>
          </div>
        </Card>
      </div>

      <div className='grid gap-4 xl:grid-cols-3'>
        <Card className='xl:col-span-2' title='Live Class Session' subtitle='Teacher explains, asks, evaluates, and adapts'>
          <div className='rounded-xl border bg-white p-3 text-sm'>
            <p><strong>Teacher:</strong> {session?.teacher_turn?.message || 'Start a class to begin live teaching.'}</p>
            <p className='mt-2'><strong>Question:</strong> {session?.teacher_turn?.question || 'No question yet.'}</p>
            {session?.teacher_turn?.feedback ? <p className='mt-2'><strong>Feedback:</strong> {session.teacher_turn.feedback}</p> : null}
          </div>

          <textarea
            className='mt-3 h-24 w-full rounded-xl border p-3'
            value={studentResponse}
            onChange={(e) => setStudentResponse(e.target.value)}
            placeholder='Type your answer to the teacher here...'
          />
          <label className='mt-2 block text-sm text-slate-700'>
            Self-confidence: {confidence}%
            <input className='mt-1 w-full' type='range' min={0} max={100} value={confidence} onChange={(e) => setConfidence(Number(e.target.value))} />
          </label>

          <div className='mt-3 flex flex-wrap gap-2'>
            <Button onClick={submitResponse} disabled={!currentSessionId || loadingRespond || session?.status === 'completed'}>
              {loadingRespond ? 'Submitting...' : 'Submit Response'}
            </Button>
          </div>
        </Card>

        <Card title='Teaching Visuals' subtitle='Slides, diagram, timeline, and whiteboard mode'>
          <div className='space-y-3 text-sm'>
            <div className='rounded-xl border bg-white p-3'>
              <p className='font-semibold'>Slides</p>
              <ul className='mt-2 list-disc pl-5'>
                {(session?.visuals?.slides || []).map((item, idx) => <li key={idx}>{item}</li>)}
              </ul>
            </div>
            <div className='rounded-xl border bg-white p-3'>
              <p className='font-semibold'>Diagram</p>
              <p className='mt-2'>Nodes: {(session?.visuals?.diagram?.nodes || []).join(' | ') || 'n/a'}</p>
              <p className='mt-1'>Edges: {(session?.visuals?.diagram?.edges || []).join(' | ') || 'n/a'}</p>
            </div>
            <div className='rounded-xl border bg-white p-3'>
              <p className='font-semibold'>Timeline</p>
              <ul className='mt-2 list-disc pl-5'>
                {(session?.visuals?.timeline || []).map((item, idx) => (
                  <li key={idx}>{item.step}. {item.phase} ({item.minutes}m)</li>
                ))}
              </ul>
            </div>
            <div className='rounded-xl border bg-white p-3'>
              <p className='font-semibold'>Whiteboard Steps</p>
              <ul className='mt-2 list-disc pl-5'>
                {(session?.visuals?.whiteboard_steps || []).map((item, idx) => <li key={idx}>{item}</li>)}
              </ul>
            </div>
          </div>
        </Card>
      </div>

      <div className='grid gap-4 xl:grid-cols-3'>
        <Card className='xl:col-span-2' title='Class History' subtitle='Open previous sessions and continue where needed'>
          <div className='space-y-2'>
            <div className='flex gap-2'>
              <Button variant='secondary' onClick={loadHistory} disabled={loadingHistory}>{loadingHistory ? 'Refreshing...' : 'Refresh History'}</Button>
            </div>
            {history.length === 0 ? <p className='text-sm text-slate-600'>No classroom sessions yet.</p> : null}
            {history.map((item) => (
              <div key={item.id} className='flex flex-wrap items-center justify-between gap-2 rounded-xl border bg-white p-3 text-sm'>
                <div>
                  <p className='font-semibold'>{item.subject} - {item.topic}</p>
                  <p className='text-slate-600'>Grade {item.grade_level} | {item.duration_minutes}m | {item.status}</p>
                  <p className='text-xs text-slate-500'>Started: {formatStamp(item.started_at)}</p>
                </div>
                <div className='flex gap-2'>
                  {item.transcript_compacted ? <Badge label='Summary Only' tone='warn' /> : null}
                  <Button variant='secondary' onClick={() => openSession(item.id)}>Open</Button>
                </div>
              </div>
            ))}
          </div>
        </Card>

        <Card title='End of Class Report' subtitle='Summary and next best actions'>
          {session?.report?.class_summary ? (
            <div className='space-y-2 text-sm'>
              <p><strong>Summary:</strong> {session.report.class_summary}</p>
              <p><strong>Key Concepts:</strong> {(session.report.key_concepts || []).join(', ')}</p>
              <p><strong>Weak Areas:</strong> {(session.report.weak_areas || []).join(', ')}</p>
              <p><strong>Next Class Topic:</strong> {session.report.suggested_next_topic || 'n/a'}</p>
              <p><strong>Practice Tasks:</strong> {(session.report.recommended_practice_tasks || []).join(', ')}</p>
            </div>
          ) : (
            <p className='text-sm text-slate-600'>Complete a class to generate the report.</p>
          )}
        </Card>
      </div>

      {status ? <p className='text-sm text-emerald-700'>{status}</p> : null}
      {error ? <p className='text-sm text-rose-700'>{error}</p> : null}
    </div>
  );
}
