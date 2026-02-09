'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { PDFUploader } from '@/components/pdf/PDFUploader';

export default function FillPage() {
  const [isUploading, setIsUploading] = useState(false);
  const router = useRouter();

  const handleUpload = async (file: File) => {
    setIsUploading(true);
    try {
      // TODO: Upload to API and get form ID
      // const response = await fetch('/api/forms/upload', { ... });
      // const { data } = await response.json();
      // router.push(`/fill/${data.id}`);

      // Simulated delay for now
      await new Promise((resolve) => setTimeout(resolve, 1500));
      router.push('/fill/demo');
    } catch {
      setIsUploading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto">
      <div className="text-center mb-10">
        <h1 className="text-2xl font-bold text-[#1D1D1F]">Fill a Form</h1>
        <p className="text-sm text-[#86868B] mt-2">
          Upload any PDF form and we&apos;ll help you fill it out in seconds.
        </p>
      </div>

      <PDFUploader onUpload={handleUpload} isUploading={isUploading} />

      <div className="mt-10 text-center">
        <p className="text-xs text-[#AEAEB2]">
          Supported: PDF files up to 25MB, up to 100 pages.
          <br />
          Your documents are encrypted and never used for AI training.
        </p>
      </div>
    </div>
  );
}
