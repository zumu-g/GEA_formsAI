'use client';

import { useState, useCallback, useRef } from 'react';
import type { StreamEvent } from '@/types/formFillingBackend';

interface UseStreamingFillReturn {
  events: StreamEvent[];
  status: 'idle' | 'streaming' | 'complete' | 'error';
  filledPdfUrl: string | null;
  sessionId: string | null;
  error: string | null;
  startFill: (formId: string, instructions: string, resumeSessionId?: string) => void;
  reset: () => void;
}

export function useStreamingFill(): UseStreamingFillReturn {
  const [events, setEvents] = useState<StreamEvent[]>([]);
  const [status, setStatus] = useState<'idle' | 'streaming' | 'complete' | 'error'>('idle');
  const [filledPdfUrl, setFilledPdfUrl] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const startFill = useCallback(async (formId: string, instructions: string, resumeSessionId?: string) => {
    // Cleanup previous
    abortRef.current?.abort();
    if (filledPdfUrl) URL.revokeObjectURL(filledPdfUrl);

    const abort = new AbortController();
    abortRef.current = abort;

    setEvents([]);
    setStatus('streaming');
    setFilledPdfUrl(null);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('formId', formId);
      formData.append('instructions', instructions);
      if (resumeSessionId) formData.append('resumeSessionId', resumeSessionId);

      const res = await fetch('/api/forms/fill-stream', {
        method: 'POST',
        body: formData,
        signal: abort.signal,
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.error?.message || `Request failed: ${res.status}`);
      }

      const reader = res.body?.getReader();
      if (!reader) throw new Error('No stream reader');

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          const raw = line.slice(6).trim();
          if (!raw || raw === '[DONE]') continue;

          try {
            const parsed = JSON.parse(raw);
            const event: StreamEvent = {
              type: parsed.type || 'text',
              data: parsed,
              timestamp: Date.now(),
            };

            setEvents((prev) => [...prev, event]);

            if (parsed.type === 'complete' && parsed.session_id) {
              setSessionId(parsed.session_id);
            }

            if (parsed.type === 'pdf_ready' && parsed.pdf_hex) {
              const bytes = new Uint8Array(
                parsed.pdf_hex.match(/.{1,2}/g).map((b: string) => parseInt(b, 16))
              );
              const blob = new Blob([bytes], { type: 'application/pdf' });
              setFilledPdfUrl(URL.createObjectURL(blob));
            }
          } catch {
            // Skip malformed JSON
          }
        }
      }

      setStatus('complete');
    } catch (err) {
      if (abort.signal.aborted) return;
      const message = err instanceof Error ? err.message : 'Stream failed';
      setError(message);
      setStatus('error');
    }
  }, [filledPdfUrl]);

  const reset = useCallback(() => {
    abortRef.current?.abort();
    if (filledPdfUrl) URL.revokeObjectURL(filledPdfUrl);
    setEvents([]);
    setStatus('idle');
    setFilledPdfUrl(null);
    setSessionId(null);
    setError(null);
  }, [filledPdfUrl]);

  return { events, status, filledPdfUrl, sessionId, error, startFill, reset };
}
