'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, Bot, Wrench, CheckCircle, AlertCircle, Loader2, Paperclip, X } from 'lucide-react';
import type { StreamEvent } from '@/types/formFillingBackend';

interface StreamingFillChatProps {
  events: StreamEvent[];
  status: 'idle' | 'streaming' | 'complete' | 'error';
  error: string | null;
  onSend: (message: string) => void;
  onContextFilesChange?: (files: File[]) => void;
  disabled?: boolean;
}

export function StreamingFillChat({ events, status, error, onSend, onContextFilesChange, disabled }: StreamingFillChatProps) {
  const [input, setInput] = useState('');
  const [attachedFiles, setAttachedFiles] = useState<File[]>([]);
  const scrollRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

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

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files;
    if (!selected) return;
    const newFiles = Array.from(selected);
    const merged = [...attachedFiles, ...newFiles].filter(
      (file, idx, arr) => arr.findIndex((f) => f.name === file.name && f.size === file.size) === idx
    );
    setAttachedFiles(merged);
    onContextFilesChange?.(merged);
    // Reset input so the same file can be re-selected after removal
    e.target.value = '';
  };

  const removeFile = (index: number) => {
    const updated = attachedFiles.filter((_, i) => i !== index);
    setAttachedFiles(updated);
    onContextFilesChange?.(updated);
  };

  const hasFiles = attachedFiles.length > 0;

  return (
    <div className="flex flex-col h-full rounded-xl border border-[#E2E4EA] overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 bg-[#F2F4F7] border-b border-[#E2E4EA] flex items-center gap-2">
        <Bot className="w-4 h-4 text-[#5856D6]" />
        <span className="text-sm font-medium text-[#1B1D24]">AI Form Filler</span>
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
            <Bot className="w-10 h-10 text-[#A2A6B0] mx-auto mb-3" />
            <p className="text-sm text-[#767A85]">
              Tell me how to fill out this form.
            </p>
            <p className="text-xs text-[#A2A6B0] mt-1">
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
      <form onSubmit={handleSubmit} className="p-3 border-t border-[#E2E4EA] bg-white">
        {/* Attached file chips */}
        {hasFiles && (
          <div className="flex flex-wrap gap-1.5 mb-2">
            {attachedFiles.map((file, i) => (
              <span
                key={i}
                className="bg-[#F2F4F7] border border-[#E2E4EA] text-xs px-2 py-0.5 rounded-full flex items-center gap-1"
              >
                <span className="text-[#1B1D24] max-w-[140px] truncate">{file.name}</span>
                <button
                  type="button"
                  onClick={() => removeFile(i)}
                  className="text-[#A2A6B0] hover:text-[#FF3B30] transition-colors"
                  aria-label={`Remove ${file.name}`}
                >
                  <X className="w-3 h-3" />
                </button>
              </span>
            ))}
          </div>
        )}

        <div className="flex gap-2">
          {/* Hidden file input */}
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.doc,.docx,.txt"
            multiple
            onChange={handleFileChange}
            className="hidden"
            aria-label="Attach context files"
          />

          {/* Paperclip button */}
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={disabled || status === 'streaming'}
            title="Attach context files (CV, resume, etc.)"
            className={
              `relative px-3 py-2 rounded-lg border transition-colors disabled:opacity-50 disabled:cursor-not-allowed ` +
              (hasFiles
                ? 'bg-[#5856D6]/10 border-[#5856D6]/30 text-[#5856D6]'
                : 'bg-[#F2F4F7] border-[#E2E4EA] text-[#767A85] hover:bg-[#E2E4EA]')
            }
          >
            <Paperclip className="w-4 h-4" />
            {hasFiles && (
              <span className="absolute -top-1.5 -right-1.5 w-4 h-4 bg-[#5856D6] text-white text-[10px] font-semibold rounded-full flex items-center justify-center leading-none">
                {attachedFiles.length}
              </span>
            )}
          </button>

          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={status === 'complete' ? 'Send follow-up instructions...' : 'Type your instructions...'}
            disabled={disabled || status === 'streaming'}
            className="flex-1 px-3 py-2 text-sm rounded-lg border border-[#E2E4EA] focus:outline-none focus:border-[#5856D6] focus:ring-1 focus:ring-[#5856D6] disabled:opacity-50 disabled:bg-[#F2F4F7]"
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

const TOOL_LABELS: Record<string, string> = {
  fill_fields_smart: 'Writing to form',
  fill_pdf_form: 'Writing to form',
  extract_field_values: 'Reading field values',
  analyze_form: 'Analysing the form',
  detect_fields: 'Detecting fields',
};

function friendlyToolName(name: string): string {
  if (TOOL_LABELS[name]) return TOOL_LABELS[name];
  // Fall back: humanise snake_case tool names (e.g. "do_thing" → "Do thing")
  const spaced = name.replace(/_/g, ' ').trim();
  return spaced.charAt(0).toUpperCase() + spaced.slice(1);
}

function EventBubble({ event }: { event: StreamEvent }) {
  const { type, data } = event;

  if (type === 'text') {
    const text = (data.text as string) || (data.content as string) || '';
    if (!text) return null;
    return (
      <div className="flex items-start gap-2">
        <Bot className="w-4 h-4 text-[#5856D6] mt-0.5 shrink-0" />
        <p className="text-sm text-[#1B1D24] whitespace-pre-wrap">{text}</p>
      </div>
    );
  }

  if (type === 'tool_start') {
    const name = friendlyToolName((data.tool_name as string) || (data.name as string) || 'tool');
    return (
      <div className="flex items-center gap-2 text-xs text-[#767A85]">
        <Wrench className="w-3 h-3" />
        <span>{name}…</span>
      </div>
    );
  }

  if (type === 'tool_end') {
    const name = friendlyToolName((data.tool_name as string) || (data.name as string) || 'tool');
    const result = (data.result as string) || '';
    return (
      <div className="ml-5 p-2 bg-[#F2F4F7] rounded-lg">
        <p className="text-xs font-medium text-[#767A85] mb-1">{name}</p>
        {result && <p className="text-xs text-[#1B1D24] font-mono whitespace-pre-wrap line-clamp-4">{result}</p>}
      </div>
    );
  }

  if (type === 'complete') {
    const summary = (data.summary as string) || `Filled ${data.fields_filled || 0} fields`;
    return (
      <div className="flex items-start gap-2 p-3 bg-green-50 rounded-lg">
        <CheckCircle className="w-4 h-4 text-[#34C759] mt-0.5 shrink-0" />
        <p className="text-sm text-[#1B1D24]">{summary}</p>
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
