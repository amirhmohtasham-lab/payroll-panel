// Chat — order a custom report from the assistant, view history.

import { type KeyboardEvent, useEffect, useRef, useState } from 'react';
import { Layout } from '../components/Layout';
import { api } from '../api/client';
import type { ChatMessageOut, ChatResponse } from '../api/types';
import { ACCOUNTANT_NAV } from '../lib/nav';
import { ChatRobot, Export } from '../ui/icons';

interface DisplayMessage {
  role: 'user' | 'assistant';
  text: string;
  chart?: string;
}

export function ChatPage() {
  const [messages, setMessages] = useState<DisplayMessage[]>([]);
  const [input, setInput] = useState('');
  const [loaded, setLoaded] = useState(false);
  const boxRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api
      .get<{ messages: ChatMessageOut[] }>('/api/chat/history')
      .then((d) => {
        const msgs: DisplayMessage[] = [];
        for (const m of d.messages) {
          if (m.role === 'user') msgs.push({ role: 'user', text: m.message ?? '' });
          else msgs.push({ role: 'assistant', text: m.reply ?? '', chart: m.chart ?? undefined });
        }
        setMessages(msgs);
      })
      .finally(() => setLoaded(true));
  }, []);

  useEffect(() => {
    boxRef.current?.scrollTo({ top: boxRef.current.scrollHeight });
  }, [messages]);

  async function send() {
    const msg = input.trim();
    if (!msg) return;
    setInput('');
    setMessages((prev) => [...prev, { role: 'user', text: msg }]);
    try {
      const res = await api.post<ChatResponse>('/api/chat', { message: msg });
      setMessages((prev) => [...prev, { role: 'assistant', text: res.reply, chart: res.chart }]);
    } catch {
      setMessages((prev) => [...prev, { role: 'assistant', text: 'خطا در پردازش درخواست.' }]);
    }
  }

  function handleKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter') send();
  }

  return (
    <Layout title="چت سفارش گزارش" navItems={ACCOUNTANT_NAV}>
      <div className="card">
        <h2><ChatRobot size={18} /> چت سفارش گزارش</h2>
        <div className="chat-box" ref={boxRef}>
          {loaded && messages.length === 0 && (
            <p style={{ color: 'var(--text-muted)' }}>تاریخچه خالی است.</p>
          )}
          {messages.map((m, i) => (
            <div key={i} className={`chat-msg ${m.role === 'user' ? 'user' : 'bot'}`}>
              <strong>{m.role === 'user' ? 'شما:' : <><ChatRobot size={18} /> ربات گزارش:</>}</strong>
              <br />
              {m.text.split('\n').map((line, li) => (
                <span key={li}>
                  {line}
                  <br />
                </span>
              ))}
              {m.chart && <div dangerouslySetInnerHTML={{ __html: m.chart }} />}
            </div>
          ))}
        </div>
        <div className="chat-input-row">
          <input
            placeholder="نوع گزارش…"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
          />
          <button className="primary" onClick={send} style={{ display: 'inline-flex', alignItems: 'center', gap: '.35rem' }}>
            <Export size={16} /> ارسال
          </button>
        </div>
      </div>
    </Layout>
  );
}
