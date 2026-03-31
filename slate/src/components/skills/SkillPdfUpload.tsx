'use client';

import { useState, useCallback } from 'react';
import { Upload, FileText, Loader2 } from 'lucide-react';

interface SkillPdfUploadProps {
  skillName: string;
  onUploaded: (formId: string) => void;
}

export function SkillPdfUpload({ skillName, onUploaded }: SkillPdfUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);

  const handleFile = useCallback(
    async (file: File) => {
      if (file.type !== 'application/pdf') {
        setError('Please upload a PDF file.');
        return;
      }

      if (file.size > 25 * 1024 * 1024) {
        setError('File must be under 25MB.');
        return;
      }

      setError(null);
      setFileName(file.name);
      setIsUploading(true);

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

        onUploaded(data.data.id);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Upload failed.');
        setFileName(null);
      } finally {
        setIsUploading(false);
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

      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        className={`
          relative border-2 border-dashed rounded-2xl p-10 text-center
          transition-all duration-200 cursor-pointer
          ${isDragging ? 'border-[#5856D6] bg-[#5856D6]/5' : 'border-[#E5E5EA] hover:border-[#C7C7CC] bg-[#FAFAFA]'}
        `}
      >
        <input
          type="file"
          accept=".pdf"
          onChange={handleInputChange}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
          disabled={isUploading}
        />

        {isUploading ? (
          <div className="flex flex-col items-center gap-3">
            <Loader2 size={32} className="text-[#5856D6] animate-spin" />
            <p className="text-sm text-[#86868B]">
              Uploading <span className="font-medium text-[#1D1D1F]">{fileName}</span>...
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
