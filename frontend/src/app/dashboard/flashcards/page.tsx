'use client';

import { useState } from 'react';

import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { postWithAuth } from '@/lib/request';

type Flashcard = {
  question: string;
  answer: string;
  topic_tags: string[];
  difficulty_tag: string;
};

export default function FlashcardsPage() {
  const [notes, setNotes] = useState('Photosynthesis converts light energy into chemical energy. Chlorophyll absorbs light.');
  const [cards, setCards] = useState<Flashcard[]>([]);
  const [userAnswers, setUserAnswers] = useState<Record<number, string>>({});
  const [revealed, setRevealed] = useState<Record<number, boolean>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function generate() {
    if (!notes.trim()) {
      setError('Paste notes first.');
      return;
    }

    setError('');
    setUserAnswers({});
    setRevealed({});
    setLoading(true);

    try {
      const data = await postWithAuth('/flashcards/generate', {
        title: 'Revision Deck',
        source_text: notes,
        source_type: 'lecture-notes',
      });
      setCards(Array.isArray(data.cards) ? data.cards : []);
    } catch (err) {
      setCards([]);
      setError(err instanceof Error ? err.message : 'Failed to generate flashcards.');
    } finally {
      setLoading(false);
    }
  }

  function updateAnswer(idx: number, value: string) {
    setUserAnswers((prev) => ({ ...prev, [idx]: value }));
  }

  function reveal(idx: number) {
    setRevealed((prev) => ({ ...prev, [idx]: true }));
  }

  return (
    <div className='space-y-4'>
      <Card title='Flashcard Generator' subtitle='Generate cards from your text, attempt answer first, then reveal'>
        <textarea className='h-36 w-full rounded-xl border p-3' value={notes} onChange={(e) => setNotes(e.target.value)} />
        <Button className='mt-3' onClick={generate} disabled={loading}>{loading ? 'Generating...' : 'Generate Flashcards'}</Button>
        {error ? <p className='mt-2 text-sm text-rose-700'>{error}</p> : null}
      </Card>

      {!loading && cards.length === 0 ? <p className='text-sm text-slate-600'>No cards yet. Generate from your notes.</p> : null}

      <div className='grid gap-3 md:grid-cols-2'>
        {cards.map((card, idx) => {
          const isRevealed = Boolean(revealed[idx]);
          return (
            <Card key={idx} title={`Card ${idx + 1}`}>
              <p className='text-sm'><strong>Q:</strong> {card.question}</p>
              <label className='mt-3 block text-sm'>
                Your answer
                <textarea
                  className='mt-1 h-20 w-full rounded-lg border p-2'
                  value={userAnswers[idx] || ''}
                  onChange={(e) => updateAnswer(idx, e.target.value)}
                />
              </label>
              <div className='mt-2 flex gap-2'>
                <Button variant='secondary' onClick={() => reveal(idx)}>Reveal Correct Answer</Button>
              </div>
              {isRevealed ? (
                <p className='mt-3 text-sm'><strong>Correct answer:</strong> {card.answer}</p>
              ) : null}
              <p className='mt-2 text-xs text-slate-500'>Tags: {card.topic_tags?.join(', ')} | {card.difficulty_tag}</p>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
