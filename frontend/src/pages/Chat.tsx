import { useState, useRef, useEffect } from 'react';
import { api } from '@/api/client';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([
    { role: 'assistant', content: '你好！我是 FinWatch AI 分析助手。你可以问我关于消费习惯、异常支出、预算建议等问题。' },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [usage, setUsage] = useState<{ chat: { used: number; limit: number }; llm_enabled: boolean } | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api.get('/llm/usage').then((r) => setUsage(r.data)).catch(() => {});
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const send = async () => {
    if (!input.trim() || loading) return;
    const userMsg = input.trim();
    setInput('');
    setMessages((prev) => [...prev, { role: 'user', content: userMsg }]);
    setLoading(true);

    try {
      const res = await api.post('/llm/chat', { message: userMsg });
      const reply = res.data.reply || 'AI 服务暂时不可用，请稍后重试。';
      setMessages((prev) => [...prev, { role: 'assistant', content: reply }]);
    } catch {
      setMessages((prev) => [...prev, {
        role: 'assistant',
        content: 'AI 分析服务暂时不可用。请确认已在 .env 中配置 DEEPSEEK_API_KEY 并将 LLM_ENABLED 设为 true。\n\n离线模式下，您可以查看 Reports 页面获取数据报表。',
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4 max-w-3xl mx-auto" style={{ height: 'calc(100vh - 120px)' }}>
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">AI 对话分析</h2>
        {usage && (
          <span className={`text-xs px-2 py-1 rounded ${usage.llm_enabled ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
            {usage.llm_enabled ? `DeepSeek · ${usage.chat.used}/${usage.chat.limit}次/小时` : '离线模式'}
          </span>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-4 bg-white rounded-xl p-4 shadow-sm border" style={{ height: 'calc(100% - 80px)' }}>
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[80%] rounded-xl px-4 py-3 text-sm ${
              m.role === 'user'
                ? 'bg-slate-900 text-white'
                : 'bg-slate-100 text-slate-800'
            }`}>
              <div style={{ whiteSpace: 'pre-wrap' }}>{m.content}</div>
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-slate-100 rounded-xl px-4 py-3 text-sm text-slate-400">
              思考中...
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && send()}
          placeholder="输入你想了解的分析问题，例如：本月我的主要支出在哪些方面？"
          className="flex-1 px-4 py-3 border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          disabled={loading}
        />
        <button
          onClick={send}
          disabled={loading || !input.trim()}
          className="px-6 py-3 bg-slate-900 text-white rounded-xl text-sm disabled:opacity-50 hover:bg-slate-800 transition-colors"
        >
          发送
        </button>
      </div>
    </div>
  );
}
