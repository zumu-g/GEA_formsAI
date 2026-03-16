'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Globe } from 'lucide-react';
import { PDFUploader } from '@/components/pdf/PDFUploader';

export default function FillPage() {
  const [isUploading, setIsUploading] = useState(false);
  const [activeTab, setActiveTab] = useState<'pdf' | 'web'>('pdf');
  const [webUrl, setWebUrl] = useState('');
  const [webInstructions, setWebInstructions] = useState('');
  const [isSubmittingWeb, setIsSubmittingWeb] = useState(false);
  const router = useRouter();

  const handleUpload = async (file: File) => {
    setIsUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('/api/forms/upload', {
        method: 'POST',
        body: formData,
      });

      const { success, data, error } = await response.json();

      if (!success) {
        throw new Error(error?.message || 'Upload failed');
      }

      router.push(`/fill/${data.id}`);
    } catch (err) {
      console.error('Upload error:', err);
      setIsUploading(false);
    }
  };

  const handleWebFill = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!webUrl || !webInstructions) return;

    setIsSubmittingWeb(true);
    try {
      const response = await fetch('/api/forms/web-fill', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: webUrl, instructions: webInstructions }),
      });

      const { success, data, error } = await response.json();
      if (!success) throw new Error(error?.message || 'Failed to start web fill');

      // For now, alert with task ID — later build a status page
      alert(`Web fill task started! Task ID: ${data.taskId}`);
    } catch (err) {
      console.error('Web fill error:', err);
      alert(err instanceof Error ? err.message : 'Web fill failed');
    } finally {
      setIsSubmittingWeb(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto">
      <div className="text-center mb-10">
        <h1 className="text-2xl font-bold text-[#1D1D1F]">Fill a Form</h1>
        <p className="text-sm text-[#86868B] mt-2">
          Upload a PDF or provide a web form URL — AI fills it for you.
        </p>
      </div>

      {/* Tab switcher */}
      <div className="flex items-center justify-center gap-1 mb-8 p-1 bg-[#F5F5F7] rounded-lg w-fit mx-auto">
        <button
          onClick={() => setActiveTab('pdf')}
          className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
            activeTab === 'pdf'
              ? 'bg-white text-[#1D1D1F] shadow-sm'
              : 'text-[#86868B] hover:text-[#1D1D1F]'
          }`}
        >
          PDF Form
        </button>
        <button
          onClick={() => setActiveTab('web')}
          className={`flex items-center gap-1.5 px-4 py-2 text-sm font-medium rounded-md transition-colors ${
            activeTab === 'web'
              ? 'bg-white text-[#1D1D1F] shadow-sm'
              : 'text-[#86868B] hover:text-[#1D1D1F]'
          }`}
        >
          <Globe className="w-3.5 h-3.5" />
          Web Form
        </button>
      </div>

      {/* PDF Upload */}
      {activeTab === 'pdf' && (
        <>
          <PDFUploader onUpload={handleUpload} isUploading={isUploading} />
          <div className="mt-10 text-center">
            <p className="text-xs text-[#AEAEB2]">
              Supported: PDF files up to 25MB, up to 100 pages.
              <br />
              Your documents are encrypted and never used for AI training.
            </p>
          </div>
        </>
      )}

      {/* Web Form */}
      {activeTab === 'web' && (
        <form onSubmit={handleWebFill} className="space-y-4">
          <div className="p-6 rounded-xl border border-[#E5E5EA] bg-white space-y-4">
            <div>
              <label className="block text-sm font-medium text-[#1D1D1F] mb-1">
                Web Form URL
              </label>
              <input
                type="url"
                value={webUrl}
                onChange={(e) => setWebUrl(e.target.value)}
                placeholder="https://example.com/application-form"
                required
                className="w-full px-3 py-2 text-sm rounded-lg border border-[#E5E5EA] focus:outline-none focus:border-[#5856D6] focus:ring-1 focus:ring-[#5856D6]"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-[#1D1D1F] mb-1">
                Instructions
              </label>
              <textarea
                value={webInstructions}
                onChange={(e) => setWebInstructions(e.target.value)}
                placeholder="Fill in the application form with: Name: John Doe, Email: john@example.com..."
                required
                rows={4}
                className="w-full px-3 py-2 text-sm rounded-lg border border-[#E5E5EA] focus:outline-none focus:border-[#5856D6] focus:ring-1 focus:ring-[#5856D6] resize-none"
              />
            </div>
            <button
              type="submit"
              disabled={isSubmittingWeb}
              className="w-full py-2.5 text-sm font-medium text-white bg-[#5856D6] rounded-lg hover:bg-[#4B49B6] disabled:opacity-50 transition-colors"
            >
              {isSubmittingWeb ? 'Starting...' : 'Fill Web Form with AI'}
            </button>
          </div>
          <div className="text-center">
            <p className="text-xs text-[#AEAEB2]">
              Powered by Skyvern — AI browser automation.
              <br />
              The AI will navigate to the URL and fill the form for you.
            </p>
          </div>
        </form>
      )}
    </div>
  );
}
