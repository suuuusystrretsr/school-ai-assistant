'use client';

import { useState } from 'react';

import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { API_URL } from '@/lib/api';

export default function FlashcardsPage() {
  const [notes, setNotes] = useState('Photosynthesis converts light energy into chemical energy. Chlorophyll absorbs light.');
  const [cards, setCards] = useState<any[]>([]);

  async function generate() {
    const token = localStorage.getItem('schoolai_token');
    const res = await fetch(`${API_URL}/flashcards/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ title: 'Biology Revision', source_text: notes, source_type: 'lecture-notes' }),
    });
    const data = await res.json();
    setCards(data.cards || []);
  }

  return (
    <div className='space-y-4'>
      <Card title='Flashcard Generator' subtitle='Upload notes or paste text to generate spaced-repetition-ready cards'>
        <textarea className='h-36 w-full rounded-xl border p-3' value={notes} onChange={(e) => setNotes(e.target.value)} />
        <Button className='mt-3' onClick={generate}>Generate Flashcards</Button>
      </Card>
      <div className='grid gap-3 md:grid-cols-2'>
        {cards.map((card, idx) => (
          <Card key={idx} title={`Card ${idx + 1}`}>
            <p className='text-sm'><strong>Q:</strong> {card.question}</p>
            <p className='mt-2 text-sm'><strong>A:</strong> {card.answer}</p>
            <p className='mt-2 text-xs text-slate-500'>Tags: {card.topic_tags?.join(', ')} | {card.difficulty_tag}</p>
          </Card>
        ))}
      </div>
    </div>
  );
}
