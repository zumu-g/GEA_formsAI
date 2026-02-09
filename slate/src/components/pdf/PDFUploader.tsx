'use client';

import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, AlertCircle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface PDFUploaderProps {
  onUpload: (file: File) => void;
  isUploading?: boolean;
}

export function PDFUploader({ onUpload, isUploading = false }: PDFUploaderProps) {
  const [error, setError] = useState<string | null>(null);

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      setError(null);
      const file = acceptedFiles[0];
      if (!file) return;

      if (file.type !== 'application/pdf') {
        setError('Please upload a PDF file.');
        return;
      }

      if (file.size > 25 * 1024 * 1024) {
        setError('File size must be under 25MB.');
        return;
      }

      onUpload(file);
    },
    [onUpload]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] },
    maxFiles: 1,
    disabled: isUploading,
  });

  return (
    <div className="w-full max-w-xl mx-auto">
      <div
        {...getRootProps()}
        className={`
          relative flex flex-col items-center justify-center
          p-12 rounded-2xl border-2 border-dashed
          transition-all duration-200 cursor-pointer
          ${isDragActive
            ? 'border-[#5856D6] bg-[#5856D6]/5'
            : 'border-[#E5E5EA] bg-[#F5F5F7]/30 hover:border-[#C7C7CC] hover:bg-[#F5F5F7]/60'
          }
          ${isUploading ? 'opacity-60 cursor-not-allowed' : ''}
        `}
      >
        <input {...getInputProps()} />

        <AnimatePresence mode="wait">
          {isUploading ? (
            <motion.div
              key="uploading"
              initial={{ opacity: 0, y: 5 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -5 }}
              className="flex flex-col items-center gap-4"
            >
              <div className="w-12 h-12 rounded-2xl bg-[#5856D6]/10 flex items-center justify-center">
                <svg className="animate-spin h-6 w-6 text-[#5856D6]" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
              </div>
              <div className="text-center">
                <p className="text-sm font-medium text-[#1D1D1F]">Uploading your PDF...</p>
                <p className="text-xs text-[#86868B] mt-1">This will only take a moment</p>
              </div>
            </motion.div>
          ) : isDragActive ? (
            <motion.div
              key="drag"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="flex flex-col items-center gap-4"
            >
              <div className="w-12 h-12 rounded-2xl bg-[#5856D6]/10 flex items-center justify-center">
                <FileText size={24} className="text-[#5856D6]" />
              </div>
              <p className="text-sm font-medium text-[#5856D6]">Drop your PDF here</p>
            </motion.div>
          ) : (
            <motion.div
              key="idle"
              initial={{ opacity: 0, y: 5 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -5 }}
              className="flex flex-col items-center gap-4"
            >
              <div className="w-12 h-12 rounded-2xl bg-[#F5F5F7] flex items-center justify-center">
                <Upload size={24} className="text-[#86868B]" />
              </div>
              <div className="text-center">
                <p className="text-sm font-medium text-[#1D1D1F]">
                  Drop your PDF here, or <span className="text-[#5856D6]">browse</span>
                </p>
                <p className="text-xs text-[#AEAEB2] mt-1">PDF up to 25MB</p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {error && (
        <motion.div
          initial={{ opacity: 0, y: -5 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center gap-2 mt-3 px-3 py-2 rounded-xl bg-[#FF3B30]/5"
        >
          <AlertCircle size={14} className="text-[#FF3B30] flex-shrink-0" />
          <p className="text-xs text-[#FF3B30]">{error}</p>
        </motion.div>
      )}
    </div>
  );
}
