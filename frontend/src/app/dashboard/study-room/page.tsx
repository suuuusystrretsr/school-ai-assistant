'use client';

import { useMemo, useState } from 'react';

import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { getWsBaseUrl } from '@/lib/api';

export default function StudyRoomPage() {
  const [roomId, setRoomId] = useState('1');
  const [connected, setConnected] = useState(false);
  const [messages, setMessages] = useState<string[]>([]);
  const [content, setContent] = useState('');
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [error, setError] = useState('');

  const wsUrl = useMemo(() => `${getWsBaseUrl()}/ws/rooms/${roomId}?user_id=student`, [roomId]);

  function connect() {
    setError('');
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      setConnected(true);
      setMessages((prev) => [...prev, 'Connected to room.']);
    };

    ws.onclose = () => {
      setConnected(false);
      setMessages((prev) => [...prev, 'Disconnected from room.']);
    };

    ws.onerror = () => {
      setError('WebSocket connection failed. Check backend /health and NEXT_PUBLIC_WS_URL.');
    };

    ws.onmessage = (evt) => {
      const payload = JSON.parse(evt.data);
      setMessages((prev) => [...prev, `${payload.user_id}: ${payload.content || payload.event}`]);
    };

    setSocket(ws);
  }

  function sendMessage() {
    if (!socket || socket.readyState !== WebSocket.OPEN) {
      setError('Connect to room first.');
      return;
    }
    socket.send(JSON.stringify({ type: 'chat', content }));
    setContent('');
  }

  return (
    <div className='grid gap-4 lg:grid-cols-3'>
      <Card className='lg:col-span-2' title='Study Rooms / Group Study' subtitle='Live collaboration - beta'>
        <div className='flex gap-2'>
          <input className='rounded-xl border p-2' value={roomId} onChange={(e) => setRoomId(e.target.value)} />
          <Button onClick={connect}>{connected ? 'Connected' : 'Connect WS'}</Button>
        </div>
        {error ? <p className='mt-2 text-sm text-rose-700'>{error}</p> : null}
        <div className='mt-4 h-64 overflow-auto rounded-xl border bg-white p-3 text-sm'>
          {messages.map((m, i) => <p key={i}>{m}</p>)}
        </div>
        <div className='mt-3 flex gap-2'>
          <input className='flex-1 rounded-xl border p-2' value={content} onChange={(e) => setContent(e.target.value)} />
          <Button onClick={sendMessage}>Send</Button>
        </div>
      </Card>

      <div className='space-y-4'>
        <Card title='Room Rules'>
          <p className='text-sm text-slate-700'>Host plus up to 4 invited users (max 5 participants).</p>
        </Card>
        <Card title='Collab Tools'>
          <ul className='list-disc pl-5 text-sm text-slate-700'>
            <li>Live chat</li>
            <li>Presence indicator</li>
            <li>Shared session notes</li>
            <li>Group task board</li>
            <li>AI group tutor</li>
          </ul>
        </Card>
      </div>
    </div>
  );
}
