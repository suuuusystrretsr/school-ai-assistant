'use client';

import { useEffect, useState } from 'react';

import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { getWithAuth, patchWithAuth } from '@/lib/request';

const gradeOptions = [
  '3rd Grade',
  '4th Grade',
  '5th Grade',
  '6th Grade',
  '7th Grade',
  '8th Grade',
  '9th Grade',
  '10th Grade',
  '11th Grade',
  '12th Grade',
];

const learningStyles = ['visual', 'practice-based', 'reading-based', 'explanation-first'];

export default function SettingsPage() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [loggedOutView, setLoggedOutView] = useState(false);

  const [gradeLevel, setGradeLevel] = useState('');
  const [learningStyle, setLearningStyle] = useState('explanation-first');
  const [studyMinutes, setStudyMinutes] = useState(90);
  const [focusMode, setFocusMode] = useState(false);

  const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || 'https://schoolaiassistant.local';
  const backendApiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

  useEffect(() => {
    async function loadProfile() {
      const token = typeof window !== 'undefined' ? localStorage.getItem('schoolai_token') : null;
      if (!token) {
        setLoggedOutView(true);
        setLoading(false);
        return;
      }

      setError('');
      setMessage('');
      setLoading(true);

      try {
        const profile = await getWithAuth('/users/me/profile');
        setGradeLevel(profile?.grade_level || '');
        setLearningStyle(profile?.preferred_learning_style || 'explanation-first');
        setStudyMinutes(profile?.study_minutes_per_day || 90);
        setFocusMode(Boolean(profile?.focus_mode_enabled));
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load settings.');
      } finally {
        setLoading(false);
      }
    }

    loadProfile();
  }, []);

  async function saveProfile() {
    setError('');
    setMessage('');
    setSaving(true);

    try {
      await patchWithAuth('/users/me/profile', {
        grade_level: gradeLevel || null,
        preferred_learning_style: learningStyle,
        study_minutes_per_day: studyMinutes,
        focus_mode_enabled: focusMode,
      });
      setMessage('Settings saved. Grade baseline will be used in future recommendations.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save settings.');
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className='space-y-4'>
      <Card title='Learning Preferences' subtitle='Set your baseline so recommendations match your level'>
        {loading ? <p className='text-sm text-slate-600'>Loading settings...</p> : null}
        {!loading && loggedOutView ? <p className='text-sm text-slate-600'>Log in to edit and save learning preferences.</p> : null}

        <div className='grid gap-3 md:grid-cols-2'>
          <label className='block text-sm'>
            Grade Level
            <select
              className='mt-1 w-full rounded-xl border p-3'
              value={gradeLevel}
              onChange={(e) => setGradeLevel(e.target.value)}
              disabled={loading || saving || loggedOutView}
            >
              <option value=''>Select grade</option>
              {gradeOptions.map((grade) => (
                <option key={grade} value={grade}>
                  {grade}
                </option>
              ))}
            </select>
          </label>

          <label className='block text-sm'>
            Learning Style
            <select
              className='mt-1 w-full rounded-xl border p-3'
              value={learningStyle}
              onChange={(e) => setLearningStyle(e.target.value)}
              disabled={loading || saving || loggedOutView}
            >
              {learningStyles.map((style) => (
                <option key={style} value={style}>
                  {style}
                </option>
              ))}
            </select>
          </label>

          <label className='block text-sm'>
            Daily Study Minutes
            <input
              className='mt-1 w-full rounded-xl border p-3'
              type='number'
              min={15}
              max={480}
              value={studyMinutes}
              onChange={(e) => setStudyMinutes(Number(e.target.value) || 90)}
              disabled={loading || saving || loggedOutView}
            />
          </label>

          <label className='mt-6 flex items-center gap-2 text-sm'>
            <input
              type='checkbox'
              checked={focusMode}
              onChange={(e) => setFocusMode(e.target.checked)}
              disabled={loading || saving || loggedOutView}
            />
            Enable Focus Mode prompts
          </label>
        </div>

        <div className='mt-3 flex items-center gap-3'>
          <Button onClick={saveProfile} disabled={loading || saving || loggedOutView}>
            {saving ? 'Saving...' : 'Save Preferences'}
          </Button>
          {message ? <p className='text-sm text-emerald-700'>{message}</p> : null}
          {error ? <p className='text-sm text-rose-700'>{error}</p> : null}
        </div>
      </Card>

      <Card title='Deployment Configuration (Read-only)'>
        <div className='space-y-3'>
          <label className='block text-sm'>
            Public Site URL
            <input className='mt-1 w-full rounded-xl border p-3 bg-slate-50' value={siteUrl} readOnly />
          </label>
          <label className='block text-sm'>
            Frontend API Proxy
            <input className='mt-1 w-full rounded-xl border p-3 bg-slate-50' value='/api/proxy' readOnly />
          </label>
          <label className='block text-sm'>
            Backend API URL (proxy target)
            <input className='mt-1 w-full rounded-xl border p-3 bg-slate-50' value={backendApiUrl} readOnly />
          </label>
        </div>
      </Card>
    </div>
  );
}
