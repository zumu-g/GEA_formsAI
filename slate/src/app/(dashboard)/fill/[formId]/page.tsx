'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { Download, RotateCcw, Clock } from 'lucide-react';
import { PDFViewer } from '@/components/fill/PDFViewer';
import { StreamingFillChat } from '@/components/fill/StreamingFillChat';
import { FieldsPanel, type FieldEntry } from '@/components/fill/FieldsPanel';
import { useStreamingFill } from '@/hooks/useStreamingFill';
import { addFillEntry } from '@/lib/fillHistory';

export default function FillWorkspacePage() {
  const params = useParams();
  const formId = params.formId as string;

  const [formName, setFormName] = useState<string>('');
  const [originalPdfUrl, setOriginalPdfUrl] = useState<string | null>(null);
  const [fields, setFields] = useState<FieldEntry[]>([]);
  const [isDetecting, setIsDetecting] = useState(true);
  const [contextFiles, setContextFiles] = useState<File[]>([]);

  const lastInstructionsRef = useRef<string>('');
  const historyRecordedRef = useRef<boolean>(false);

  const { events, status, filledPdfUrl, sessionId, error, startFill, reset } = useStreamingFill();

  useEffect(() => {
    async function init() {
      try {
        setFormName('Uploaded Form');
        setOriginalPdfUrl(`/api/forms/${formId}/pdf`);

        const detectRes = await fetch('/api/forms/detect', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ formId }),
        });

        const detectData = await detectRes.json();
        if (detectData.success && detectData.data.fields.length > 0) {
          setFields(
            detectData.data.fields.map(
              (f: { id: string; fieldName: string; fieldType: string; pageNumber?: number }) => ({
                id: f.id,
                fieldName: f.fieldName,
                fieldType: (f.fieldType as FieldEntry['fieldType']) || 'text',
                value: '',
                manual: false,
                pageNumber: f.pageNumber,
              })
            )
          );
        }
      } catch (err) {
        console.error('Init error:', err);
      } finally {
        setIsDetecting(false);
      }
    }

    init();
  }, [formId]);

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

      // Prepend any pre-filled field values as context for the AI
      const filledFields = fields.filter((f) => f.value.trim());
      let fullMessage = message;
      if (filledFields.length > 0) {
        const fieldContext = filledFields
          .map((f) => `- ${f.fieldName}: ${f.value}`)
          .join('\n');
        fullMessage = `Field values to use:\n${fieldContext}\n\n${message}`;
      }

      lastInstructionsRef.current = message;
      startFill(formId, fullMessage, sessionId ?? undefined, contextFiles.length > 0 ? contextFiles : undefined);
    },
    [formId, sessionId, startFill, contextFiles, fields]
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
          {!isDetecting && (
            <p className="text-xs text-[#86868B]">
              {fields.length > 0 ? `${fields.length} fields detected` : 'No fields detected'}
            </p>
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

      {/* Main workspace: PDF viewer + right panel */}
      <div className="flex-1 flex gap-4 p-4 overflow-hidden">
        {/* Left: PDF Viewer */}
        <div className="flex-1 min-w-0">
          <PDFViewer
            pdfUrl={displayPdfUrl}
            title={filledPdfUrl ? 'Filled PDF' : formName}
          />
        </div>

        {/* Right: Fields + Chat */}
        <div className="w-96 shrink-0 flex flex-col gap-3 overflow-y-auto">
          <FieldsPanel
            fields={fields}
            isDetecting={isDetecting}
            onChange={setFields}
          />

          <StreamingFillChat
            events={events}
            status={status}
            error={error}
            onSend={handleSend}
            onContextFilesChange={setContextFiles}
          />
        </div>
      </div>
    </div>
  );
}
