'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { Upload, Loader2, CheckCircle2, AlertCircle, Download, X, Sparkles } from 'lucide-react';
import { SmartPDFViewer } from '@/components/fill/SmartPDFViewer';
import { SmartFillPanel } from '@/components/fill/SmartFillPanel';
import type { DetectedField, SmartDetectResult } from '@/types/smartFill';
import type { DataProfile } from '@/types/profile';

// ─── Stage type ───────────────────────────────────────────────────────────────

type Stage = 'upload' | 'detecting' | 'fill' | 'no-fields' | 'generating' | 'done';

// ─── Upload zone ──────────────────────────────────────────────────────────────

interface UploadZoneProps {
  onUpload: (file: File) => void;
}

function UploadZone({ onUpload }: UploadZoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback(
    (file: File) => {
      const isPdf =
        file.type === 'application/pdf' ||
        ((!file.type || file.type === 'application/octet-stream') &&
          file.name.toLowerCase().endsWith('.pdf'));
      if (!isPdf) return;
      if (file.size > 25 * 1024 * 1024) return;
      onUpload(file);
    },
    [onUpload]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  return (
    <div className="max-w-lg mx-auto">
      {/* Icon + title */}
      <div className="text-center mb-6">
        <div className="w-14 h-14 rounded-2xl bg-[#5856D6]/10 flex items-center justify-center mx-auto mb-4">
          <Sparkles size={28} className="text-[#5856D6]" />
        </div>
        <h2 className="text-xl font-semibold text-gray-100">Upload Your Form</h2>
        <p className="text-sm text-gray-400 mt-1">
          AI will detect all fillable fields automatically.
        </p>
      </div>

      <input
        ref={inputRef}
        type="file"
        accept=".pdf"
        className="hidden"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) handleFile(file);
        }}
      />

      {/* Drop zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className={`
          border-2 border-dashed rounded-2xl p-10 text-center
          transition-all duration-200 cursor-pointer
          ${isDragging
            ? 'border-[#5856D6] bg-[#5856D6]/5'
            : 'border-gray-700 hover:border-[#5856D6]/60 bg-gray-900'
          }
        `}
      >
        <div className="flex flex-col items-center gap-3">
          <Upload size={32} className="text-gray-500" />
          <div>
            <p className="text-sm font-medium text-gray-100">
              Drop your PDF here or click to browse
            </p>
            <p className="text-xs text-gray-400 mt-1">PDF only, max 25MB, up to 100 pages</p>
          </div>
        </div>
      </div>

      <p className="mt-6 text-center text-xs text-gray-500">
        Your documents are encrypted and never used for AI training.
      </p>
    </div>
  );
}

// ─── Detecting screen ─────────────────────────────────────────────────────────

const DETECTING_MESSAGES = ['Analysing form…', 'Detecting fields…', 'Processing pages…'];

interface DetectingScreenProps {
  pageCount?: number;
}

function DetectingScreen({ pageCount }: DetectingScreenProps) {
  const [msgIndex, setMsgIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setMsgIndex((i) => (i + 1) % DETECTING_MESSAGES.length);
    }, 1500);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex flex-col items-center justify-center h-80 gap-4">
      <Loader2 size={40} className="text-[#5856D6] animate-spin" />
      <div className="text-center">
        <p className="text-base font-medium text-gray-100">{DETECTING_MESSAGES[msgIndex]}</p>
        {pageCount !== undefined && pageCount > 0 && (
          <p className="text-sm text-gray-400 mt-1">
            {pageCount} {pageCount === 1 ? 'page' : 'pages'} found
          </p>
        )}
        <p className="text-xs text-gray-500 mt-2">
          This may take 15–30 seconds for multi-page forms
        </p>
      </div>
    </div>
  );
}

// ─── Done screen ──────────────────────────────────────────────────────────────

interface DoneScreenProps {
  pdfUrl: string;
  onStartOver: () => void;
}

function DoneScreen({ pdfUrl, onStartOver }: DoneScreenProps) {
  return (
    <div className="max-w-md mx-auto text-center py-16">
      <div className="w-16 h-16 rounded-full bg-green-900/30 flex items-center justify-center mx-auto mb-5">
        <CheckCircle2 size={32} className="text-green-400" />
      </div>
      <h2 className="text-xl font-semibold text-gray-100 mb-2">PDF Ready</h2>
      <p className="text-sm text-gray-400 mb-8">
        Your filled PDF has been generated and is ready to download.
      </p>
      <div className="flex flex-col sm:flex-row gap-3 justify-center">
        <a
          href={pdfUrl}
          download="filled-form.pdf"
          className="
            inline-flex items-center justify-center gap-2
            px-6 py-3 rounded-xl text-sm font-semibold text-white
            bg-[#5856D6] hover:bg-[#4644C4]
            transition-colors duration-150
          "
        >
          <Download size={16} />
          Download PDF
        </a>
        <button
          onClick={onStartOver}
          className="
            px-6 py-3 rounded-xl text-sm font-medium text-gray-300
            bg-gray-800 hover:bg-gray-700
            transition-colors duration-150
          "
        >
          Fill Another Form
        </button>
      </div>
    </div>
  );
}

// ─── No-fields screen ─────────────────────────────────────────────────────────

interface NoFieldsScreenProps {
  onRetry: () => void;
  onAddManually: () => void;
  onDetectFromText: (description: string) => void;
}

function NoFieldsScreen({ onRetry, onAddManually, onDetectFromText }: NoFieldsScreenProps) {
  const [description, setDescription] = useState('');

  return (
    <div className="max-w-md mx-auto text-center py-12 px-4">
      <div className="w-16 h-16 rounded-full bg-amber-900/30 flex items-center justify-center mx-auto mb-5">
        <AlertCircle size={32} className="text-amber-400" />
      </div>
      <h2 className="text-xl font-semibold text-gray-100 mb-2">No Fields Detected</h2>
      <p className="text-sm text-gray-400 mb-4">AI couldn&apos;t find fillable fields. This PDF may be:</p>
      <ul className="text-left text-sm text-gray-500 space-y-1 mb-6 mx-auto max-w-xs">
        <li className="flex items-start gap-2"><span className="text-gray-600 mt-0.5">•</span>A scanned image without a digital text layer</li>
        <li className="flex items-start gap-2"><span className="text-gray-600 mt-0.5">•</span>A flat PDF with no form fields embedded</li>
        <li className="flex items-start gap-2"><span className="text-gray-600 mt-0.5">•</span>A document rather than a form</li>
      </ul>

      {/* Describe fields shortcut */}
      <div className="mb-5 text-left">
        <p className="text-xs font-medium text-gray-400 mb-2">Or describe the fields this form needs:</p>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="e.g. Full Name, Date of Birth, Address, Signature, ABN..."
          rows={3}
          className="w-full bg-gray-800 border border-gray-700 rounded-xl px-3 py-2.5 text-sm text-gray-100 placeholder-gray-600 focus:outline-none focus:border-[#5856D6]/70 focus:ring-1 focus:ring-[#5856D6]/30 transition-colors resize-none"
        />
        <button
          onClick={() => description.trim() && onDetectFromText(description)}
          disabled={!description.trim()}
          className="mt-2 w-full py-2.5 rounded-xl text-sm font-semibold text-white bg-[#5856D6] hover:bg-[#4644C4] disabled:opacity-40 disabled:cursor-not-allowed transition-colors duration-150"
        >
          Detect Fields from Description →
        </button>
      </div>

      <div className="flex flex-col sm:flex-row gap-3 justify-center">
        <button onClick={onRetry} className="px-5 py-2.5 rounded-xl text-sm font-medium text-gray-300 bg-gray-800 hover:bg-gray-700 transition-colors duration-150">
          Try Again
        </button>
        <button onClick={onAddManually} className="px-5 py-2.5 rounded-xl text-sm font-medium text-gray-300 bg-gray-800 hover:bg-gray-700 transition-colors duration-150">
          Add Fields Manually
        </button>
      </div>
    </div>
  );
}

// ─── SmartFillPage ────────────────────────────────────────────────────────────

export default function SmartFillPage() {
  const [stage, setStage] = useState<Stage>('upload');
  const [formId, setFormId] = useState<string | null>(null);
  const [detectResult, setDetectResult] = useState<SmartDetectResult | null>(null);
  const [fields, setFields] = useState<DetectedField[]>([]);
  const [values, setValues] = useState<Record<string, string>>({});
  const [activeFieldId, setActiveFieldId] = useState<string | null>(null);
  const [profiles, setProfiles] = useState<DataProfile[]>([]);
  const [filledPdfUrl, setFilledPdfUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // ── Load profiles on mount ──
  useEffect(() => {
    fetch('/api/profiles')
      .then((res) => {
        if (!res.ok) return null;
        return res.json();
      })
      .then((data) => {
        if (data?.success && Array.isArray(data.data)) {
          setProfiles(data.data as DataProfile[]);
        }
      })
      .catch(() => {
        // Profiles are optional; fail silently
      });
  }, []);

  useEffect(() => {
    document.title = 'Smart Fill — Slate';
  }, []);

  // ── Value change handler ──
  const handleValueChange = useCallback((fieldId: string, value: string) => {
    setValues((prev) => ({ ...prev, [fieldId]: value }));
  }, []);

  // ── Upload + detect handler ──
  const handleUpload = useCallback(
    async (file: File) => {
      setStage('detecting');
      setError(null);

      try {
        // 1. Upload PDF
        const fd = new FormData();
        fd.append('file', file);
        const uploadRes = await fetch('/api/forms/upload', { method: 'POST', body: fd });
        const uploadData = await uploadRes.json();

        if (!uploadData.success) {
          throw new Error(uploadData.error?.message ?? 'Upload failed.');
        }

        const id: string = uploadData.data.id;
        setFormId(id);

        // 2. Run smart detection
        const detectRes = await fetch('/api/forms/detect-smart', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ formId: id }),
        });
        const result: SmartDetectResult = await detectRes.json();

        setDetectResult(result);
        setFields(result.fields);

        if (result.fields.length === 0) {
          // No fields detected by any method — show recovery screen
          setStage('no-fields');
        } else {
          // Pre-fill from default profile where profileKey matches
          const defaultProfile = profiles.find((p) => p.isDefault);
          if (defaultProfile) {
            const prefilled: Record<string, string> = {};
            result.fields.forEach((f) => {
              if (f.profileKey && defaultProfile.data[f.profileKey]) {
                prefilled[f.id] = defaultProfile.data[f.profileKey];
              }
            });
            setValues(prefilled);
          } else {
            setValues({});
          }
          setActiveFieldId(result.fields[0]?.id ?? null);
          setStage('fill');
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Something went wrong. Please try again.');
        setStage('upload');
      }
    },
    [profiles]
  );

  // ── Detect from text description handler ──
  const handleDetectFromText = useCallback(async (description: string) => {
    setStage('detecting');
    setError(null);

    try {
      const res = await fetch('/api/forms/detect-from-text', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ description }),
      });
      const data = await res.json();

      if (!res.ok || !Array.isArray(data.fields)) {
        throw new Error(data.error ?? 'Detection failed.');
      }

      const detectedFields: DetectedField[] = data.fields;

      if (detectedFields.length === 0) {
        setError('No fields could be inferred from your description. Try adding more detail.');
        setStage('no-fields');
        return;
      }

      // Build a minimal SmartDetectResult so the fill stage has what it needs
      const syntheticResult: SmartDetectResult = {
        fields: detectedFields,
        pageImages: detectResult?.pageImages ?? [],
        pageCount: detectResult?.pageCount ?? 1,
        pageDimensions: detectResult?.pageDimensions ?? [{ width: 595.28, height: 841.89 }],
        detectionMethod: 'empty',
      };

      setDetectResult(syntheticResult);
      setFields(detectedFields);

      // Pre-fill from default profile where profileKey matches
      const defaultProfile = profiles.find((p) => p.isDefault);
      if (defaultProfile) {
        const prefilled: Record<string, string> = {};
        detectedFields.forEach((f) => {
          if (f.profileKey && defaultProfile.data[f.profileKey]) {
            prefilled[f.id] = defaultProfile.data[f.profileKey];
          }
        });
        setValues(prefilled);
      } else {
        setValues({});
      }

      setActiveFieldId(detectedFields[0]?.id ?? null);
      setStage('fill');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong. Please try again.');
      setStage('no-fields');
    }
  }, [detectResult, profiles]);

  // ── Generate PDF handler ──
  const handleGenerate = useCallback(async () => {
    if (!formId || !detectResult) return;
    setStage('generating');
    setError(null);

    try {
      const PTS_TO_MM = 25.4 / 72;

      const mappings = fields.map((field) => {
        const dim = detectResult.pageDimensions[field.page - 1] ?? { width: 595.28, height: 841.89 };
        const pageW = dim.width * PTS_TO_MM;
        const pageH = dim.height * PTS_TO_MM;
        return {
          skillFieldId: field.id,
          schemaName: field.id,
          page: field.page - 1,  // pdfme is 0-indexed
          position: {
            x: Math.max(0, field.bbox.x * pageW),
            y: Math.max(0, field.bbox.y * pageH),
          },
          width: Math.max(5, field.bbox.w * pageW),
          height: Math.max(4, field.bbox.h * pageH),
          type: field.type === 'checkbox' ? 'checkbox' as const : 'text' as const,
          fontSize: 9,
        };
      });

      // Only include fields that have values
      const filledValues: Record<string, string> = {};
      fields.forEach((f) => {
        if (values[f.id]?.trim()) filledValues[f.id] = values[f.id];
      });

      const res = await fetch('/api/forms/fill', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          formId,
          pdfmePayload: { mappings, values: filledValues },
        }),
      });

      if (!res.ok) throw new Error(`Fill failed: ${res.status}`);

      const data = await res.json();
      if (!data.pdfBase64) throw new Error('No PDF returned');

      const bytes = Uint8Array.from(atob(data.pdfBase64), (c) => c.charCodeAt(0));
      const blob = new Blob([bytes], { type: 'application/pdf' });
      setFilledPdfUrl(URL.createObjectURL(blob));
      setStage('done');
    } catch (e) {
      console.error('Generate failed:', e);
      setError('Failed to generate PDF. Please try again.');
      setStage('fill');
    }
  }, [formId, detectResult, fields, values]);

  // ── Reset ──
  const handleStartOver = useCallback(() => {
    if (filledPdfUrl) URL.revokeObjectURL(filledPdfUrl);
    setStage('upload');
    setFormId(null);
    setDetectResult(null);
    setFields([]);
    setValues({});
    setActiveFieldId(null);
    setFilledPdfUrl(null);
    setError(null);
  }, [filledPdfUrl]);

  // ─── Render ───────────────────────────────────────────────────────────────

  return (
    <div className="flex flex-col h-full">
      {/* Page header */}
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-xl bg-[#5856D6]/10 flex items-center justify-center shrink-0">
          <Sparkles size={20} className="text-[#5856D6]" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-gray-100">Smart Fill</h1>
          <p className="text-sm text-gray-400">
            Upload a form — AI detects the fields
          </p>
        </div>
      </div>

      {/* Error banner */}
      {error && (
        <div className="flex items-center gap-3 mb-4 px-4 py-3 rounded-xl bg-red-900/20 border border-red-800/50">
          <AlertCircle size={16} className="text-red-400 shrink-0" />
          <p className="text-sm text-red-400 flex-1">{error}</p>
          <button
            onClick={() => setError(null)}
            className="shrink-0 text-red-400 hover:text-red-300 transition-colors"
            aria-label="Dismiss error"
          >
            <X size={16} />
          </button>
        </div>
      )}

      {/* ── Stage: Upload ── */}
      {stage === 'upload' && (
        <div className="flex-1 flex items-center justify-center">
          <UploadZone onUpload={handleUpload} />
        </div>
      )}

      {/* ── Stage: Detecting ── */}
      {stage === 'detecting' && (
        <div className="flex-1 flex items-center justify-center">
          <DetectingScreen pageCount={detectResult?.pageCount} />
        </div>
      )}

      {/* ── Stage: No Fields ── */}
      {stage === 'no-fields' && (
        <div className="flex-1 flex items-center justify-center">
          <NoFieldsScreen
            onRetry={handleStartOver}
            onAddManually={() => {
              setStage('fill');
              setActiveFieldId(null);
            }}
            onDetectFromText={handleDetectFromText}
          />
        </div>
      )}

      {/* ── Stage: Fill ── */}
      {(stage === 'fill' || stage === 'generating') && detectResult && (
        <div className="flex flex-col lg:flex-row gap-4" style={{ height: 'calc(100vh - 160px)' }}>
          {/* Left: PDF viewer (60%) */}
          <div className="w-full lg:w-[60%] h-full overflow-hidden rounded-xl">
            <SmartPDFViewer
              pageImages={detectResult.pageImages}
              fields={fields}
              activeFieldId={activeFieldId}
              filledFields={values}
              onFieldClick={setActiveFieldId}
              formId={formId ?? undefined}
            />
          </div>

          {/* Right: Fill panel (40%) */}
          <div className="w-full lg:w-[40%] h-full overflow-hidden rounded-xl">
            <SmartFillPanel
              fields={fields}
              values={values}
              activeFieldId={activeFieldId}
              profiles={profiles}
              onValueChange={handleValueChange}
              onFieldFocus={setActiveFieldId}
              onGenerate={handleGenerate}
              isGenerating={stage === 'generating'}
              onFieldsChange={setFields}
              detectionMethod={detectResult?.detectionMethod}
            />
          </div>
        </div>
      )}

      {/* ── Stage: Done ── */}
      {stage === 'done' && filledPdfUrl && (
        <div className="flex-1 flex items-center justify-center">
          <DoneScreen pdfUrl={filledPdfUrl} onStartOver={handleStartOver} />
        </div>
      )}
    </div>
  );
}
