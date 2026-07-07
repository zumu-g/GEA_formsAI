'use client';

import { FileText } from 'lucide-react';

interface PDFViewerProps {
  pdfUrl: string | null;
  title?: string;
}

export function PDFViewer({ pdfUrl, title }: PDFViewerProps) {
  if (!pdfUrl) {
    return (
      <div className="flex flex-col items-center justify-center h-full bg-[#F2F4F7] rounded-xl border border-[#E2E4EA]">
        <FileText className="w-12 h-12 text-[#A2A6B0] mb-3" />
        <p className="text-sm text-[#767A85]">No PDF loaded</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full rounded-xl border border-[#E2E4EA] overflow-hidden">
      {title && (
        <div className="px-4 py-2 bg-[#F2F4F7] border-b border-[#E2E4EA]">
          <p className="text-xs font-medium text-[#767A85] truncate">{title}</p>
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
