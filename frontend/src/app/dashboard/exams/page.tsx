'use client';

import { useEffect, useMemo, useState } from 'react';

import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { postWithAuth } from '@/lib/request';

type ExamQuestion = {
  id: number;
  prompt: string;
  choices: string[];
};

type ExamReview = {
  question_id: number;
  prompt: string;
  choices: string[];
  selected_answer: string | null;
  correct_answer: string;
  is_correct: boolean;
  explanation: string;
};

const teacherStyles = [
  'strict teacher',
  'tricky teacher',
  'short-answer teacher',
  'reasoning-heavy teacher',
  'exam-board style',
  'custom',
];

export default function ExamsPage() {
  const [subject, setSubject] = useState('Math');
  const [topic, setTopic] = useState('quadratics');
  const [difficulty, setDifficulty] = useState('medium');
  const [duration, setDuration] = useState(20);
  const [questionCount, setQuestionCount] = useState(5);
  const [teacherStyle, setTeacherStyle] = useState('exam-board style');
  const [customTeacherStyle, setCustomTeacherStyle] = useState('');

  const [exam, setExam] = useState<any>(null);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [confidence, setConfidence] = useState<Record<number, number>>({});
  const [secondsLeft, setSecondsLeft] = useState(0);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (secondsLeft <= 0) return;
    const timer = setInterval(() => setSecondsLeft((prev) => prev - 1), 1000);
    return () => clearInterval(timer);
  }, [secondsLeft]);

  const timerLabel = useMemo(
    () => `${Math.floor(secondsLeft / 60)}:${String(secondsLeft % 60).padStart(2, '0')}`,
    [secondsLeft]
  );

  async function generateExam() {
    setError('');
    setResult(null);
    setAnswers({});
    setConfidence({});
    setLoading(true);

    try {
      const data = await postWithAuth('/exams/generate', {
        subject,
        topic,
        difficulty,
        duration_minutes: duration,
        question_count: questionCount,
        teacher_style: teacherStyle,
        custom_teacher_style: customTeacherStyle,
      }, 70000);
      if (!data?.exam_id || !Array.isArray(data?.questions)) {
        throw new Error('Invalid exam response from API.');
      }
      setExam(data);
      setSecondsLeft((data.duration_minutes || duration) * 60);

      try {
        await postWithAuth('/analytics/session-signal', {
          page: 'exams',
          event_type: 'interaction',
          action: 'generate-exam',
          topic,
          task_difficulty: difficulty,
          dwell_seconds: 45,
        });
      } catch {
        // Best-effort analytics only; do not fail exam generation.
      }
    } catch (err) {
      setExam(null);
      setError(err instanceof Error ? err.message : 'Failed to generate exam.');
    } finally {
      setLoading(false);
    }
  }

  function setAnswer(questionId: number, option: string) {
    setAnswers((prev) => ({ ...prev, [questionId]: option }));
  }

  function setConfidenceValue(questionId: number, value: number) {
    setConfidence((prev) => ({ ...prev, [questionId]: value }));
  }

  async function submitExam() {
    if (!exam) {
      setError('Generate and start an exam first.');
      return;
    }

    const total = Array.isArray(exam.questions) ? exam.questions.length : 0;
    const answered = Object.keys(answers).length;
    if (answered < total) {
      setError(`Answer all questions first (${answered}/${total} answered).`);
      return;
    }

    setError('');
    setSubmitting(true);
    try {
      const data = await postWithAuth(`/exams/${exam.exam_id}/submit`, {
        answers,
        confidence_by_question: confidence,
      }, 30000);
      setResult(data);

      try {
        await postWithAuth('/analytics/session-signal', {
          page: 'exams',
          event_type: 'interaction',
          action: 'submit-exam',
          topic,
          task_difficulty: difficulty,
          dwell_seconds: 120,
        });
      } catch {
        // Best-effort analytics only; do not fail exam submission.
      }
    } catch (err) {
      setResult(null);
      setError(err instanceof Error ? err.message : 'Failed to submit exam.');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className='space-y-4'>
      <Card title='AI Exam Simulator' subtitle='Build, start, submit, and review complete test flow'>
        <div className='grid gap-2 md:grid-cols-3'>
          <label className='text-sm'>
            Subject
            <select className='mt-1 w-full rounded-xl border p-2' value={subject} onChange={(e) => setSubject(e.target.value)}>
              <option>Math</option>
              <option>Biology</option>
              <option>History</option>
              <option>Chemistry</option>
              <option>Physics</option>
            </select>
          </label>
          <label className='text-sm'>
            Topic (custom)
            <input className='mt-1 w-full rounded-xl border p-2' value={topic} onChange={(e) => setTopic(e.target.value)} />
          </label>
          <label className='text-sm'>
            Difficulty
            <select className='mt-1 w-full rounded-xl border p-2' value={difficulty} onChange={(e) => setDifficulty(e.target.value)}>
              <option value='easy'>Easy</option>
              <option value='medium'>Medium</option>
              <option value='hard'>Hard</option>
            </select>
          </label>
          <label className='text-sm'>
            Number of questions
            <input
              className='mt-1 w-full rounded-xl border p-2'
              type='number'
              min={3}
              max={25}
              value={questionCount}
              onChange={(e) => setQuestionCount(Number(e.target.value) || 5)}
            />
          </label>
          <label className='text-sm'>
            Duration (minutes)
            <input
              className='mt-1 w-full rounded-xl border p-2'
              type='number'
              min={5}
              max={180}
              value={duration}
              onChange={(e) => setDuration(Number(e.target.value) || 20)}
            />
          </label>
          <label className='text-sm'>
            Teacher style simulator
            <select className='mt-1 w-full rounded-xl border p-2' value={teacherStyle} onChange={(e) => setTeacherStyle(e.target.value)}>
              {teacherStyles.map((item) => <option key={item}>{item}</option>)}
            </select>
          </label>
        </div>

        {teacherStyle === 'custom' ? (
          <label className='mt-3 block text-sm'>
            Custom style instruction
            <input
              className='mt-1 w-full rounded-xl border p-2'
              value={customTeacherStyle}
              onChange={(e) => setCustomTeacherStyle(e.target.value)}
              placeholder='e.g., like a hard IB examiner'
            />
          </label>
        ) : null}

        <div className='mt-3 flex flex-wrap items-center gap-2'>
          <Button onClick={generateExam} disabled={loading}>{loading ? 'Generating...' : 'Start Test'}</Button>
          <Button variant='secondary' onClick={submitExam} disabled={submitting || !exam}>{submitting ? 'Submitting...' : 'Submit Test'}</Button>
          <span className='rounded-lg bg-slate-100 px-3 py-2 text-sm font-semibold'>Timer: {timerLabel}</span>
        </div>

        {error ? <p className='mt-2 text-sm text-rose-700'>{error}</p> : null}
      </Card>

      {exam ? (
        <Card
          title={`Exam: ${exam.subject} (${exam.topic})`}
          subtitle={`Predicted score: ${exam.predicted_score > 0 ? `${exam.predicted_score}%` : 'No prior exam history yet'} | Style: ${exam.teacher_style}`}
        >
          <div className='space-y-4'>
            {(exam.questions as ExamQuestion[]).map((q, idx) => (
              <div key={q.id} className='rounded-xl border bg-white p-3'>
                <p className='font-semibold'>Q{idx + 1}. {q.prompt}</p>
                <div className='mt-2 grid gap-2 sm:grid-cols-2'>
                  {q.choices.map((choice, cIdx) => {
                    const option = ['A', 'B', 'C', 'D'][cIdx] || choice;
                    const selected = answers[q.id] === option;
                    return (
                      <button
                        key={`${q.id}-${option}`}
                        className={`rounded-lg border px-3 py-2 text-left text-sm ${selected ? 'border-brand-500 bg-brand-50' : 'border-slate-200 bg-white'}`}
                        onClick={() => setAnswer(q.id, option)}
                      >
                        <strong>{option}.</strong> {choice}
                      </button>
                    );
                  })}
                </div>
                <label className='mt-2 block text-xs text-slate-600'>
                  Confidence for this answer: {confidence[q.id] ?? 50}%
                  <input
                    className='mt-1 w-full'
                    type='range'
                    min={0}
                    max={100}
                    value={confidence[q.id] ?? 50}
                    onChange={(e) => setConfidenceValue(q.id, Number(e.target.value))}
                  />
                </label>
              </div>
            ))}
          </div>
        </Card>
      ) : null}

      {result ? (
        <Card title='Test Review Mode' subtitle='Selected answer is red if wrong, correct answer is green with explanation'>
          <p><strong>Actual score:</strong> {result.actual_score}%</p>
          <p className='mt-1'><strong>Confidence gap:</strong> {result.confidence_gap}%</p>
          <p className='mt-1'><strong>Weak areas:</strong> {result.weak_areas?.join(', ') || 'None'}</p>

          <div className='mt-3 space-y-3'>
            {(result.reviews as ExamReview[])?.map((review, idx) => (
              <div key={review.question_id} className='rounded-xl border bg-white p-3'>
                <p className='font-semibold'>Review Q{idx + 1}: {review.prompt}</p>
                <div className='mt-2 grid gap-2 sm:grid-cols-2'>
                  {review.choices.map((choice, cIdx) => {
                    const option = ['A', 'B', 'C', 'D'][cIdx] || choice;
                    const isSelected = review.selected_answer === option;
                    const isCorrect = review.correct_answer === option;
                    const classes = isCorrect
                      ? 'border-emerald-400 bg-emerald-50 text-emerald-800'
                      : isSelected && !review.is_correct
                      ? 'border-rose-400 bg-rose-50 text-rose-800'
                      : 'border-slate-200 bg-white';

                    return (
                      <div key={`${review.question_id}-${option}`} className={`rounded-lg border px-3 py-2 text-sm ${classes}`}>
                        <strong>{option}.</strong> {choice}
                      </div>
                    );
                  })}
                </div>
                <p className='mt-2 text-sm'><strong>Explanation:</strong> {review.explanation}</p>
              </div>
            ))}
          </div>

          <div className='mt-4 rounded-xl border bg-slate-50 p-3 text-sm'>
            <p className='font-semibold'>Exam Outcome Simulator</p>
            <ul className='mt-2 list-disc pl-5'>
              <li>If exam happened today: {result.outcome_simulation?.if_exam_today}%</li>
              <li>If studied 30 minutes more: {result.outcome_simulation?.if_study_30_more_minutes}%</li>
              <li>If fixed one weak area: {result.outcome_simulation?.if_fix_one_weak_area}%</li>
              <li>If retention risk ignored: {result.outcome_simulation?.if_ignore_retention_risk}%</li>
            </ul>
          </div>
        </Card>
      ) : null}
    </div>
  );
}
