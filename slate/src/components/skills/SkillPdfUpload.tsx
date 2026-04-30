'use client';

import { useState, useCallback, useRef } from 'react';
import { flushSync } from 'react-dom';
import { Upload, FileText, Loader2, CheckCircle2 } from 'lucide-react';

interface SkillPdfUploadProps {
  skillName: string;
  onUploaded: (formId: string) => void;
}

export function SkillPdfUpload({ skillName, onUploaded }: SkillPdfUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const pendingFormId = useRef<string | null>(null);

  const handleFile = useCallback(
    async (file: File) => {
      const isPdf =
        file.type === 'application/pdf' ||
        ((!file.type || file.type === 'application/octet-stream') &&
          file.name.toLowerCase().endsWith('.pdf'));

      if (!isPdf) {
        setError('Please upload a PDF file.');
        return;
      }

      if (file.size > 25 * 1024 * 1024) {
        setError('File must be under 25MB.');
        return;
      }

      // flushSync forces the loading state to paint before the async fetch starts,
      // preventing React 18 batching from skipping the intermediate loading render.
      flushSync(() => {
        setError(null);
        setFileName(file.name);
        setIsUploading(true);
        setIsSuccess(false);
      });

      try {
        const formData = new FormData();
        formData.append('file', file);

        const res = await fetch('/api/forms/upload', {
          method: 'POST',
          body: formData,
        });

        const data = await res.json();

        if (!data.success) {
          throw new Error(data.error?.message ?? 'Upload failed.');
        }

        // Show success state briefly so the user knows the upload worked
        pendingFormId.current = data.data.id;
        flushSync(() => {
          setIsUploading(false);
          setIsSuccess(true);
        });

        // Short pause so the success state is visible, then transition
        await new Promise((r) => setTimeout(r, 600));
        onUploaded(data.data.id);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Upload failed.');
        setFileName(null);
        setIsUploading(false);
        setIsSuccess(false);
      }
    },
    [onUploaded]
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

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  return (
    <div className="max-w-lg mx-auto">
      <div className="text-center mb-6">
        <div className="w-14 h-14 rounded-2xl bg-[#5856D6]/10 flex items-center justify-center mx-auto mb-4">
          <FileText size={28} className="text-[#5856D6]" />
        </div>
        <h2 className="text-xl font-semibold text-[#1D1D1F]">Upload Your PDF</h2>
        <p className="text-sm text-[#86868B] mt-1">
          Upload the <span className="font-medium text-[#1D1D1F]">{skillName}</span> document
          to begin filling.
        </p>
      </div>

      <input
        ref={inputRef}
        type="file"
        accept=".pdf"
        onChange={handleInputChange}
        className="hidden"
        disabled={isUploading}
      />

      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => !isUploading && !isSuccess && inputRef.current?.click()}
        className={`
          border-2 border-dashed rounded-2xl p-10 text-center
          transition-all duration-200 cursor-pointer
          ${isDragging ? 'border-[#5856D6] bg-[#5856D6]/5' : 'border-[#E5E5EA] hover:border-[#C7C7CC] bg-[#FAFAFA]'}
        `}
      >

        {isUploading ? (
          <div className="flex flex-col items-center gap-3">
            <Loader2 size={32} className="text-[#5856D6] animate-spin" />
            <p className="text-sm text-[#86868B]">
              Uploading <span className="font-medium text-[#1D1D1F]">{fileName}</span>…
            </p>
          </div>
        ) : isSuccess ? (
          <div className="flex flex-col items-center gap-3">
            <CheckCircle2 size={32} className="text-green-500" />
            <p className="text-sm text-[#86868B]">
              <span className="font-medium text-[#1D1D1F]">{fileName}</span> ready
            </p>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-3">
            <Upload size={32} className="text-[#C7C7CC]" />
            <div>
              <p className="text-sm font-medium text-[#1D1D1F]">
                Drop your PDF here or click to browse
              </p>
              <p className="text-xs text-[#86868B] mt-1">PDF only, max 25MB</p>
            </div>
          </div>
        )}
      </div>

      {error && (
        <p className="mt-3 text-sm text-red-600 text-center">{error}</p>
      )}
    </div>
  );
}
