'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { Download, RotateCcw, Clock } from 'lucide-react';
import { PDFViewer } from '@/components/fill/PDFViewer';
import { StreamingFillChat } from '@/components/fill/StreamingFillChat';
import { useStreamingFill } from '@/hooks/useStreamingFill';
import { addFillEntry } from '@/lib/fillHistory';

export default function FillWorkspacePage() {
  const params = useParams();
  const formId = params.formId as string;

  const [formName, setFormName] = useState<string>('');
  const [originalPdfUrl, setOriginalPdfUrl] = useState<string | null>(null);
  const [fields, setFields] = useState<{ id: string; fieldName: string; fieldType: string }[]>([]);
  const [isDetecting, setIsDetecting] = useState(true);
  const [contextFiles, setContextFiles] = useState<File[]>([]);

  // Track last instructions sent and whether this fill has been logged
  const lastInstructionsRef = useRef<string>('');
  const historyRecordedRef = useRef<boolean>(false);

  const { events, status, filledPdfUrl, sessionId, error, startFill, reset } = useStreamingFill();

  // Load form metadata and detect fields on mount
  useEffect(() => {
    async function init() {
      try {
        setFormName('Uploaded Form');
        setOriginalPdfUrl(`/api/forms/${formId}/pdf`);

        // Detect fields via backend
        const detectRes = await fetch('/api/forms/detect', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ formId }),
        });

        const detectData = await detectRes.json();
        if (detectData.success) {
          setFields(detectData.data.fields);
        }
      } catch (err) {
        console.error('Init error:', err);
      } finally {
        setIsDetecting(false);
      }
    }

    init();
  }, [formId]);

  // Record fill history when streaming completes or errors
  useEffect(() => {
    if (status !== 'complete' && status !== 'error') return;
    if (historyRecordedRef.current) return;
    if (!lastInstructionsRef.current) return;

    historyRecordedRef.current = true;

    let fieldsFilled: number | undefined;
    if (status === 'complete') {
      const completeEvent = [...events].reverse().find((e) => e.type === 'complete');
      if (completeEvent) {
        const val = completeEvent.data.fields_filled;
        if (typeof val === 'number') fieldsFilled = val;
      }
    }

    addFillEntry({
      formName: formName || 'Unnamed Form',
      instructions: lastInstructionsRef.current.slice(0, 120),
      timestamp: Date.now(),
      status: status === 'complete' ? 'complete' : 'error',
      fieldsFilled,
      formId,
    });
  }, [status, events, formName, formId]);

  const handleSend = useCallback(
    (message: string) => {
      historyRecordedRef.current = false;
      lastInstructionsRef.current = message;
      startFill(formId, message, sessionId ?? undefined, contextFiles.length > 0 ? contextFiles : undefined);
    },
    [formId, sessionId, startFill, contextFiles]
  );

  const handleDownload = useCallback(() => {
    if (!filledPdfUrl) return;
    const a = document.createElement('a');
    a.href = filledPdfUrl;
    a.download = `filled_${formName || 'form'}.pdf`;
    a.click();
  }, [filledPdfUrl, formName]);

  const handleReset = useCallback(() => {
    historyRecordedRef.current = false;
    lastInstructionsRef.current = '';
    reset();
  }, [reset]);

  const displayPdfUrl = filledPdfUrl || originalPdfUrl;

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)]">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-6 py-3 border-b border-[#E5E5EA]">
        <div>
          <h1 className="text-lg font-semibold text-[#1D1D1F]">{formName || 'Form Workspace'}</h1>
          {fields.length > 0 && (
            <p className="text-xs text-[#86868B]">{fields.length} fields detected</p>
          )}
          {isDetecting && (
            <p className="text-xs text-[#5856D6]">Detecting fields...</p>
          )}
        </div>
        <div className="flex items-center gap-2">
          {filledPdfUrl && (
            <button
              onClick={handleDownload}
              className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-white bg-[#34C759] rounded-lg hover:bg-[#2DB84E] transition-colors"
            >
              <Download className="w-4 h-4" />
              Download
            </button>
          )}
          <button
            onClick={handleReset}
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-[#86868B] bg-[#F5F5F7] rounded-lg hover:bg-[#E5E5EA] transition-colors"
          >
            <RotateCcw className="w-4 h-4" />
            Reset
          </button>
          <Link
            href="/fill/history"
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-[#86868B] bg-[#F5F5F7] rounded-lg hover:bg-[#E5E5EA] transition-colors"
            title="Fill history"
          >
            <Clock className="w-4 h-4" />
            History
          </Link>
        </div>
      </div>

      {/* Main workspace: PDF viewer + Chat side by side */}
      <div className="flex-1 flex gap-4 p-4 overflow-hidden">
        {/* Left: PDF Viewer */}
        <div className="flex-1 min-w-0">
          <PDFViewer
            pdfUrl={displayPdfUrl}
            title={filledPdfUrl ? 'Filled PDF' : formName}
          />
        </div>

        {/* Right: Chat / Instructions */}
        <div className="w-96 shrink-0 flex flex-col gap-3">
          <StreamingFillChat
            events={events}
            status={status}
            error={error}
            onSend={handleSend}
            onContextFilesChange={setContextFiles}
          />

          {/* Field summary */}
          {fields.length > 0 && (
            <div className="rounded-xl border border-[#E5E5EA] p-3 max-h-48 overflow-y-auto">
              <p className="text-xs font-medium text-[#86868B] mb-2">Detected Fields</p>
              <div className="space-y-1">
                {fields.map((f) => (
                  <div key={f.id} className="flex items-center justify-between text-xs">
                    <span className="text-[#1D1D1F] truncate">{f.fieldName}</span>
                    <span className="text-[#AEAEB2] ml-2 shrink-0">{f.fieldType}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
