'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { Download, RotateCcw, Clock } from 'lucide-react';
import { PDFViewer } from '@/components/fill/PDFViewer';
import { StreamingFillChat } from '@/components/fill/StreamingFillChat';
import { FieldsPanel, type FieldEntry } from '@/components/fill/FieldsPanel';
import { FavouritesPanel } from '@/components/fill/FavouritesPanel';
import { useStreamingFill } from '@/hooks/useStreamingFill';
import { addFillEntry } from '@/lib/fillHistory';
import {
  getFavourites,
  saveFavourite,
  removeFavourite,
  isFavourite,
  type FavouriteField,
} from '@/lib/favouriteFields';

export default function FillWorkspacePage() {
  const params = useParams();
  const formId = params.formId as string;

  const [formName, setFormName] = useState<string>('');
  const [originalPdfUrl, setOriginalPdfUrl] = useState<string | null>(null);
  const [fields, setFields] = useState<FieldEntry[]>([]);
  const [isDetecting, setIsDetecting] = useState(true);
  const [detectionMethod, setDetectionMethod] = useState<import('@/types/smartFill').DetectionMethod | undefined>(undefined);
  const [contextFiles, setContextFiles] = useState<File[]>([]);
  const [favourites, setFavourites] = useState<FavouriteField[]>([]);
  const [confirmingReset, setConfirmingReset] = useState(false);

  const lastInstructionsRef = useRef<string>('');
  const historyRecordedRef = useRef<boolean>(false);

  useEffect(() => {
    setFavourites(getFavourites());
  }, []);

  const { events, status, filledPdfUrl, sessionId, error, startFill, reset } = useStreamingFill();

  useEffect(() => {
    async function init() {
      try {
        setFormName('Uploaded Form');
        setOriginalPdfUrl(`/api/forms/${formId}/pdf`);

        const detectRes = await fetch('/api/forms/detect-smart', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ formId }),
        });

        const detectData = await detectRes.json();
        if (detectData.detectionMethod) {
          setDetectionMethod(detectData.detectionMethod);
        }
        if (Array.isArray(detectData.fields) && detectData.fields.length > 0) {
          setFields(
            detectData.fields.map(
              (f: { id: string; label: string; type: string; page?: number }) => ({
                id: f.id,
                fieldName: f.label,
                fieldType: (f.type as FieldEntry['fieldType']) || 'text',
                value: '',
                manual: false,
                pageNumber: f.page,
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

  const performReset = useCallback(() => {
    historyRecordedRef.current = false;
    lastInstructionsRef.current = '';
    reset();
    setConfirmingReset(false);
  }, [reset]);

  // Only worth confirming if the user has work that reset would destroy.
  const hasWorkToLose =
    events.length > 0 ||
    !!filledPdfUrl ||
    status === 'streaming' ||
    fields.some((f) => f.value.trim());

  const handleReset = useCallback(() => {
    if (hasWorkToLose) {
      setConfirmingReset(true);
    } else {
      performReset();
    }
  }, [hasWorkToLose, performReset]);

  const handleAddToFavourite = useCallback((field: FieldEntry) => {
    if (isFavourite(field.fieldName)) {
      const current = getFavourites();
      const match = current.find(
        (f) => f.fieldName.trim().toLowerCase() === field.fieldName.trim().toLowerCase()
      );
      if (match) removeFavourite(match.id);
    } else {
      saveFavourite(field);
    }
    setFavourites(getFavourites());
  }, []);

  const handleRemoveFavourite = useCallback((id: string) => {
    removeFavourite(id);
    setFavourites(getFavourites());
  }, []);

  const handleDropFavourite = useCallback((fav: FavouriteField) => {
    setFields((prev) => {
      const alreadyExists = prev.some(
        (f) => f.fieldName.trim().toLowerCase() === fav.fieldName.trim().toLowerCase()
      );
      if (alreadyExists) return prev;
      return [
        ...prev,
        {
          id: `fav_${Date.now()}`,
          fieldName: fav.fieldName,
          fieldType: fav.fieldType,
          value: fav.value,
          manual: true,
        },
      ];
    });
  }, []);

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
          <FavouritesPanel
            favourites={favourites}
            onRemove={handleRemoveFavourite}
          />

          <FieldsPanel
            fields={fields}
            isDetecting={isDetecting}
            detectionMethod={detectionMethod}
            onChange={setFields}
            onAddToFavourite={handleAddToFavourite}
            isFavourite={isFavourite}
            onDropFavourite={handleDropFavourite}
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

      {/* Reset confirmation */}
      {confirmingReset && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 p-4"
          onClick={() => setConfirmingReset(false)}
        >
          <div
            className="w-full max-w-sm rounded-2xl bg-white p-5 shadow-xl"
            onClick={(e) => e.stopPropagation()}
          >
            <h2 className="text-base font-semibold text-[#1D1D1F]">Reset this session?</h2>
            <p className="mt-1.5 text-sm text-[#86868B]">
              This clears the AI conversation and any filled PDF for this form. Field values you entered
              will remain. This can&apos;t be undone.
            </p>
            <div className="mt-4 flex justify-end gap-2">
              <button
                onClick={() => setConfirmingReset(false)}
                className="px-3 py-1.5 text-sm font-medium text-[#86868B] bg-[#F5F5F7] rounded-lg hover:bg-[#E5E5EA] transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={performReset}
                className="px-3 py-1.5 text-sm font-medium text-white bg-[#FF3B30] rounded-lg hover:bg-[#E0352B] transition-colors"
              >
                Reset
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
