'use client';

import { FileText } from 'lucide-react';

interface PDFViewerProps {
  pdfUrl: string | null;
  title?: string;
}

export function PDFViewer({ pdfUrl, title }: PDFViewerProps) {
  if (!pdfUrl) {
    return (
      <div className="flex flex-col items-center justify-center h-full bg-[#F5F5F7] rounded-xl border border-[#E5E5EA]">
        <FileText className="w-12 h-12 text-[#AEAEB2] mb-3" />
        <p className="text-sm text-[#86868B]">No PDF loaded</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full rounded-xl border border-[#E5E5EA] overflow-hidden">
      {title && (
        <div className="px-4 py-2 bg-[#F5F5F7] border-b border-[#E5E5EA]">
          <p className="text-xs font-medium text-[#86868B] truncate">{title}</p>
        </div>
      )}
      <iframe
        src={`${pdfUrl}#toolbar=1&navpanes=0`}
        className="flex-1 w-full"
        title="PDF Viewer"
      />
    </div>
  );
}
