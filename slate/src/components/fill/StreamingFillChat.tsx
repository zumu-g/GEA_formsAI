'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, Bot, Wrench, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import type { StreamEvent } from '@/types/formFillingBackend';

interface StreamingFillChatProps {
  events: StreamEvent[];
  status: 'idle' | 'streaming' | 'complete' | 'error';
  error: string | null;
  onSend: (message: string) => void;
  disabled?: boolean;
}

export function StreamingFillChat({ events, status, error, onSend, disabled }: StreamingFillChatProps) {
  const [input, setInput] = useState('');
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [events]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setInput('');
  };

  return (
    <div className="flex flex-col h-full rounded-xl border border-[#E5E5EA] overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 bg-[#F5F5F7] border-b border-[#E5E5EA] flex items-center gap-2">
        <Bot className="w-4 h-4 text-[#5856D6]" />
        <span className="text-sm font-medium text-[#1D1D1F]">AI Form Filler</span>
        {status === 'streaming' && (
          <span className="ml-auto flex items-center gap-1 text-xs text-[#5856D6]">
            <Loader2 className="w-3 h-3 animate-spin" />
            Working...
          </span>
        )}
        {status === 'complete' && (
          <span className="ml-auto flex items-center gap-1 text-xs text-[#34C759]">
            <CheckCircle className="w-3 h-3" />
            Done
          </span>
        )}
      </div>

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-3">
        {events.length === 0 && status === 'idle' && (
          <div className="text-center py-8">
            <Bot className="w-10 h-10 text-[#AEAEB2] mx-auto mb-3" />
            <p className="text-sm text-[#86868B]">
              Tell me how to fill out this form.
            </p>
            <p className="text-xs text-[#AEAEB2] mt-1">
              e.g. &quot;Fill in John Doe, 123 Main St, phone 555-1234&quot;
            </p>
          </div>
        )}

        {events.map((event, i) => (
          <EventBubble key={i} event={event} />
        ))}

        {error && (
          <div className="flex items-start gap-2 p-3 bg-red-50 rounded-lg">
            <AlertCircle className="w-4 h-4 text-[#FF3B30] mt-0.5 shrink-0" />
            <p className="text-sm text-[#FF3B30]">{error}</p>
          </div>
        )}
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="p-3 border-t border-[#E5E5EA] bg-white">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={status === 'complete' ? 'Send follow-up instructions...' : 'Type your instructions...'}
            disabled={disabled || status === 'streaming'}
            className="flex-1 px-3 py-2 text-sm rounded-lg border border-[#E5E5EA] focus:outline-none focus:border-[#5856D6] focus:ring-1 focus:ring-[#5856D6] disabled:opacity-50 disabled:bg-[#F5F5F7]"
          />
          <button
            type="submit"
            disabled={disabled || status === 'streaming' || !input.trim()}
            className="px-3 py-2 bg-[#5856D6] text-white rounded-lg hover:bg-[#4B49B6] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </form>
    </div>
  );
}

function EventBubble({ event }: { event: StreamEvent }) {
  const { type, data } = event;

  if (type === 'text') {
    const text = (data.text as string) || (data.content as string) || '';
    if (!text) return null;
    return (
      <div className="flex items-start gap-2">
        <Bot className="w-4 h-4 text-[#5856D6] mt-0.5 shrink-0" />
        <p className="text-sm text-[#1D1D1F] whitespace-pre-wrap">{text}</p>
      </div>
    );
  }

  if (type === 'tool_start') {
    const name = (data.tool_name as string) || (data.name as string) || 'tool';
    return (
      <div className="flex items-center gap-2 text-xs text-[#86868B]">
        <Wrench className="w-3 h-3" />
        <span>Using {name}...</span>
      </div>
    );
  }

  if (type === 'tool_end') {
    const name = (data.tool_name as string) || (data.name as string) || 'tool';
    const result = (data.result as string) || '';
    return (
      <div className="ml-5 p-2 bg-[#F5F5F7] rounded-lg">
        <p className="text-xs font-medium text-[#86868B] mb-1">{name}</p>
        {result && <p className="text-xs text-[#1D1D1F] font-mono whitespace-pre-wrap line-clamp-4">{result}</p>}
      </div>
    );
  }

  if (type === 'complete') {
    const summary = (data.summary as string) || `Filled ${data.fields_filled || 0} fields`;
    return (
      <div className="flex items-start gap-2 p-3 bg-green-50 rounded-lg">
        <CheckCircle className="w-4 h-4 text-[#34C759] mt-0.5 shrink-0" />
        <p className="text-sm text-[#1D1D1F]">{summary}</p>
      </div>
    );
  }

  if (type === 'error') {
    return (
      <div className="flex items-start gap-2 p-3 bg-red-50 rounded-lg">
        <AlertCircle className="w-4 h-4 text-[#FF3B30] mt-0.5 shrink-0" />
        <p className="text-sm text-[#FF3B30]">{(data.message as string) || 'An error occurred'}</p>
      </div>
    );
  }

  return null;
}
