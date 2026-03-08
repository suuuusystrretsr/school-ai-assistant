'use client';

import { useEffect, useMemo, useState } from 'react';

import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { getWsBaseUrl } from '@/lib/api';
import { getWithAuth, postWithAuth } from '@/lib/request';

type StudyRoom = {
  id: number;
  title: string;
  subject: string;
  participant_count: number;
  max_participants: number;
};

export default function StudyRoomPage() {
  const [rooms, setRooms] = useState<StudyRoom[]>([]);
  const [roomTitle, setRoomTitle] = useState('After-school review room');
  const [subject, setSubject] = useState('Math');

  const [roomId, setRoomId] = useState('');
  const [connected, setConnected] = useState(false);
  const [messages, setMessages] = useState<string[]>([]);
  const [content, setContent] = useState('');
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [error, setError] = useState('');

  const [sharedNotes, setSharedNotes] = useState('');
  const [groupTask, setGroupTask] = useState('');
  const [groupTasks, setGroupTasks] = useState<string[]>([]);
  const [groupTutorPrompt, setGroupTutorPrompt] = useState('Help our group revise this topic in 3 steps.');
  const [groupTutorReply, setGroupTutorReply] = useState('');

  const wsUrl = useMemo(() => {
    if (!roomId) return '';
    return `${getWsBaseUrl()}/ws/rooms/${roomId}?user_id=student`;
  }, [roomId]);

  useEffect(() => {
    async function loadRooms() {
      try {
        const data = await getWithAuth('/study-rooms');
        setRooms(Array.isArray(data) ? data : []);
      } catch {
        setRooms([]);
      }
    }
    loadRooms();
  }, []);

  async function createRoom() {
    setError('');
    try {
      const room = await postWithAuth('/study-rooms', { title: roomTitle, subject });
      setRoomId(String(room.id));
      setRooms((prev) => [room, ...prev.filter((r) => r.id !== room.id)]);
      setMessages((prev) => [...prev, `Created room #${room.id}: ${room.title}`]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create room.');
    }
  }

  function connect() {
    if (!roomId) {
      setError('Create a room or select an existing room first.');
      return;
    }

    setError('');
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      setConnected(true);
      setMessages((prev) => [...prev, `Connected to room ${roomId}.`]);
    };

    ws.onclose = () => {
      setConnected(false);
      setMessages((prev) => [...prev, 'Disconnected from room.']);
    };

    ws.onerror = () => {
      setError('WebSocket connection failed. Live chat may be delayed on free-tier cold starts.');
    };

    ws.onmessage = (evt) => {
      try {
        const payload = JSON.parse(evt.data);
        setMessages((prev) => [...prev, `${payload.user_id}: ${payload.content || payload.event}`]);
      } catch {
        setMessages((prev) => [...prev, evt.data]);
      }
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

  function addGroupTask() {
    if (!groupTask.trim()) return;
    setGroupTasks((prev) => [...prev, groupTask]);
    setGroupTask('');
  }

  async function askGroupTutor() {
    try {
      const data = await postWithAuth('/tutor/chat', { message: groupTutorPrompt, subject, mode: 'teacher' });
      setGroupTutorReply(data.reply || 'No reply.');
    } catch (err) {
      setGroupTutorReply(err instanceof Error ? err.message : 'Group tutor unavailable.');
    }
  }

  return (
    <div className='grid gap-4 lg:grid-cols-3'>
      <Card className='lg:col-span-2' title='Study Rooms / Group Study' subtitle='Live chat implemented, collaborative board in active MVP'>
        <div className='grid gap-2 md:grid-cols-3'>
          <input className='rounded-xl border p-2' value={roomTitle} onChange={(e) => setRoomTitle(e.target.value)} placeholder='Room title' />
          <select className='rounded-xl border p-2' value={subject} onChange={(e) => setSubject(e.target.value)}>
            <option>Math</option>
            <option>Biology</option>
            <option>History</option>
            <option>Chemistry</option>
          </select>
          <Button onClick={createRoom}>Create Room</Button>
        </div>

        <div className='mt-3 flex flex-wrap gap-2'>
          {rooms.length === 0 ? <p className='text-sm text-slate-600'>No rooms yet.</p> : null}
          {rooms.map((room) => (
            <button
              key={room.id}
              className={`rounded-lg border px-3 py-2 text-sm ${roomId === String(room.id) ? 'border-brand-500 bg-brand-50' : 'border-slate-200 bg-white'}`}
              onClick={() => setRoomId(String(room.id))}
            >
              #{room.id} {room.title} ({room.participant_count}/{room.max_participants})
            </button>
          ))}
        </div>

        <div className='mt-3 flex gap-2'>
          <Button variant='secondary' onClick={connect}>{connected ? 'Connected' : 'Connect WS'}</Button>
          <p className='text-sm text-slate-600'>Selected room: {roomId || 'none'}</p>
        </div>

        {error ? <p className='mt-2 text-sm text-rose-700'>{error}</p> : null}

        <div className='mt-4 h-56 overflow-auto rounded-xl border bg-white p-3 text-sm'>
          {messages.length === 0 ? <p className='text-slate-500'>No messages yet.</p> : null}
          {messages.map((m, i) => <p key={i}>{m}</p>)}
        </div>

        <div className='mt-3 flex gap-2'>
          <input className='flex-1 rounded-xl border p-2' value={content} onChange={(e) => setContent(e.target.value)} placeholder='Message' />
          <Button onClick={sendMessage}>Send</Button>
        </div>
      </Card>

      <div className='space-y-4'>
        <Card title='Shared Session Notes (MVP)'>
          <textarea className='h-24 w-full rounded-xl border p-2' value={sharedNotes} onChange={(e) => setSharedNotes(e.target.value)} placeholder='Shared notes for room...' />
        </Card>

        <Card title='Group Task Board (MVP)'>
          <div className='flex gap-2'>
            <input className='flex-1 rounded-xl border p-2' value={groupTask} onChange={(e) => setGroupTask(e.target.value)} placeholder='Add group task' />
            <Button variant='secondary' onClick={addGroupTask}>Add</Button>
          </div>
          <ul className='mt-2 list-disc pl-5 text-sm'>
            {groupTasks.map((task) => <li key={task}>{task}</li>)}
          </ul>
        </Card>

        <Card title='AI Group Tutor'>
          <textarea className='h-20 w-full rounded-xl border p-2' value={groupTutorPrompt} onChange={(e) => setGroupTutorPrompt(e.target.value)} />
          <Button className='mt-2' variant='secondary' onClick={askGroupTutor}>Ask Group Tutor</Button>
          <p className='mt-2 text-sm text-slate-700'>{groupTutorReply || 'No group tutor output yet.'}</p>
        </Card>
      </div>
    </div>
  );
}
