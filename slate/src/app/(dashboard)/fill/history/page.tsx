'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { FileText, CheckCircle2, XCircle, ArrowLeft, Trash2 } from 'lucide-react';
import { getFillHistory, clearFillHistory } from '@/lib/fillHistory';
import type { FillHistoryEntry } from '@/lib/fillHistory';

// ─── Relative time helper ────────────────────────────────────────────────────

function formatRelativeDate(timestamp: number): string {
  const now = new Date();
  const date = new Date(timestamp);

  const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
  const yesterdayStart = todayStart - 86_400_000;
  const dateStart = new Date(date.getFullYear(), date.getMonth(), date.getDate()).getTime();

  const timeStr = date.toLocaleTimeString('en-AU', { hour: 'numeric', minute: '2-digit' });

  if (dateStart === todayStart) return `Today, ${timeStr}`;
  if (dateStart === yesterdayStart) return `Yesterday, ${timeStr}`;

  return date.toLocaleDateString('en-AU', {
    day: 'numeric',
    month: 'short',
    year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined,
  }) + `, ${timeStr}`;
}

// ─── Component ────────────────────────────────────────────────────────────────

export default function FillHistoryPage() {
  const [history, setHistory] = useState<FillHistoryEntry[]>([]);
  const [confirmClear, setConfirmClear] = useState(false);

  useEffect(() => {
    setHistory(getFillHistory());
  }, []);

  const handleClear = () => {
    if (!confirmClear) {
      setConfirmClear(true);
      return;
    }
    clearFillHistory();
    setHistory([]);
    setConfirmClear(false);
  };

  const handleClearCancel = () => setConfirmClear(false);

  return (
    <div className="max-w-2xl mx-auto">
      {/* Page header */}
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-3">
          <Link
            href="/fill"
            className="flex items-center justify-center w-8 h-8 rounded-lg bg-[#F5F5F7] hover:bg-[#E5E5EA] text-[#86868B] transition-colors"
            title="Back to Fill"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <h1 className="text-xl font-semibold text-[#1D1D1F]">Recent Fills</h1>
            <p className="text-xs text-[#86868B] mt-0.5">
              {history.length > 0
                ? `${history.length} fill${history.length === 1 ? '' : 's'} recorded`
                : 'No fills recorded yet'}
            </p>
          </div>
        </div>

        {history.length > 0 && (
          <div className="flex items-center gap-2">
            {confirmClear && (
              <span className="text-xs text-[#FF3B30]">
                Are you sure?
              </span>
            )}
            {confirmClear && (
              <button
                onClick={handleClearCancel}
                className="px-3 py-1.5 text-xs font-medium text-[#86868B] bg-[#F5F5F7] rounded-lg hover:bg-[#E5E5EA] transition-colors"
              >
                Cancel
              </button>
            )}
            <button
              onClick={handleClear}
              className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg transition-colors ${
                confirmClear
                  ? 'text-white bg-[#FF3B30] hover:bg-[#E0352B]'
                  : 'text-[#FF3B30] bg-[#FF3B30]/10 hover:bg-[#FF3B30]/20'
              }`}
            >
              <Trash2 className="w-3.5 h-3.5" />
              {confirmClear ? 'Yes, clear all' : 'Clear all'}
            </button>
          </div>
        )}
      </div>

      {/* Empty state */}
      {history.length === 0 && (
        <div className="flex flex-col items-center justify-center py-24 text-center">
          <div className="w-14 h-14 rounded-2xl bg-[#F5F5F7] flex items-center justify-center mb-4">
            <FileText className="w-7 h-7 text-[#C7C7CC]" />
          </div>
          <p className="text-[#1D1D1F] font-medium mb-1">No fills yet</p>
          <p className="text-sm text-[#86868B] mb-6">Upload a PDF to get started.</p>
          <Link
            href="/fill"
            className="px-4 py-2 text-sm font-medium text-white bg-[#1D1D1F] rounded-lg hover:bg-[#3A3A3C] transition-colors"
          >
            Fill a form
          </Link>
        </div>
      )}

      {/* History list */}
      {history.length > 0 && (
        <div className="space-y-2">
          {history.map((entry) => (
            <HistoryCard key={entry.id} entry={entry} />
          ))}
        </div>
      )}
    </div>
  );
}

// ─── History card ─────────────────────────────────────────────────────────────

function HistoryCard({ entry }: { entry: FillHistoryEntry }) {
  const isComplete = entry.status === 'complete';

  return (
    <div className="bg-white border border-[#E5E5EA] rounded-xl p-4 flex items-start gap-3">
      {/* Status icon */}
      <div className="mt-0.5 shrink-0">
        {isComplete ? (
          <CheckCircle2 className="w-4 h-4 text-[#34C759]" />
        ) : (
          <XCircle className="w-4 h-4 text-[#FF3B30]" />
        )}
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-[#1D1D1F] truncate">{entry.formName}</p>
        <p className="text-xs text-[#86868B] mt-0.5 line-clamp-1">
          &ldquo;{entry.instructions}{entry.instructions.length === 120 ? '…' : ''}&rdquo;
        </p>
        <div className="flex items-center gap-2 mt-1.5">
          <span className="text-xs text-[#AEAEB2]">{formatRelativeDate(entry.timestamp)}</span>
          {isComplete && typeof entry.fieldsFilled === 'number' && (
            <>
              <span className="text-xs text-[#D1D1D6]">·</span>
              <span className="text-xs text-[#AEAEB2]">{entry.fieldsFilled} field{entry.fieldsFilled === 1 ? '' : 's'} filled</span>
            </>
          )}
          {!isComplete && (
            <>
              <span className="text-xs text-[#D1D1D6]">·</span>
              <span className="text-xs text-[#FF3B30]">Error</span>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
