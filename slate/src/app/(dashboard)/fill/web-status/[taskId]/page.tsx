'use client';

import { useEffect, useState, useCallback, useRef } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { motion } from 'framer-motion';
import {
  ArrowLeft,
  Clock,
  CheckCircle2,
  XCircle,
  Loader2,
  Globe,
  ExternalLink,
  AlertTriangle,
} from 'lucide-react';
import type { SkyvernTask, SkyvernTaskStatus } from '@/types/skyvern';

const POLL_INTERVAL = 3000;

const STEPS = ['created', 'queued', 'running', 'completed'] as const;

const STEP_LABELS: Record<string, string> = {
  created: 'Created',
  queued: 'Queued',
  running: 'Filling Form',
  completed: 'Completed',
};

function getStepIndex(status: SkyvernTaskStatus): number {
  if (status === 'failed' || status === 'terminated') return 2; // stop at running
  const idx = STEPS.indexOf(status as (typeof STEPS)[number]);
  return idx === -1 ? 0 : idx;
}

function statusColor(status: SkyvernTaskStatus) {
  switch (status) {
    case 'completed':
      return { bg: 'bg-emerald-50', text: 'text-emerald-600', border: 'border-emerald-200', dot: 'bg-emerald-500' };
    case 'failed':
    case 'terminated':
      return { bg: 'bg-red-50', text: 'text-red-600', border: 'border-red-200', dot: 'bg-red-500' };
    case 'running':
      return { bg: 'bg-amber-50', text: 'text-amber-600', border: 'border-amber-200', dot: 'bg-amber-500' };
    default:
      return { bg: 'bg-[#F5F5F7]', text: 'text-[#86868B]', border: 'border-[#E5E5EA]', dot: 'bg-[#86868B]' };
  }
}

function StatusIcon({ status }: { status: SkyvernTaskStatus }) {
  switch (status) {
    case 'completed':
      return <CheckCircle2 className="w-6 h-6 text-emerald-500" />;
    case 'failed':
    case 'terminated':
      return <XCircle className="w-6 h-6 text-red-500" />;
    case 'running':
      return <Loader2 className="w-6 h-6 text-amber-500 animate-spin" />;
    default:
      return <Clock className="w-6 h-6 text-[#86868B]" />;
  }
}

function formatElapsed(startISO: string): string {
  const elapsed = Math.floor((Date.now() - new Date(startISO).getTime()) / 1000);
  if (elapsed < 60) return `${elapsed}s`;
  const mins = Math.floor(elapsed / 60);
  const secs = elapsed % 60;
  return `${mins}m ${secs}s`;
}

const prefersReducedMotion =
  typeof window !== 'undefined'
    ? window.matchMedia('(prefers-reduced-motion: reduce)').matches
    : false;

const fadeUp = prefersReducedMotion
  ? {}
  : { initial: { opacity: 0, y: 20 }, animate: { opacity: 1, y: 0 } };

export default function WebFillStatusPage() {
  const { taskId } = useParams<{ taskId: string }>();
  const [task, setTask] = useState<SkyvernTask | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [elapsed, setElapsed] = useState('0s');
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  const isTerminal = task?.status === 'completed' || task?.status === 'failed' || task?.status === 'terminated';

  const fetchStatus = useCallback(async () => {
    try {
      const res = await fetch(`/api/forms/web-fill/${taskId}`);
      const json = await res.json();
      if (!json.success) throw new Error(json.error?.message || 'Failed to fetch status');
      setTask(json.data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong');
    }
  }, [taskId]);

  // Polling
  useEffect(() => {
    fetchStatus();
    intervalRef.current = setInterval(fetchStatus, POLL_INTERVAL);
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [fetchStatus]);

  // Stop polling on terminal status
  useEffect(() => {
    if (isTerminal && intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, [isTerminal]);

  // Elapsed time ticker
  useEffect(() => {
    if (!task?.created_at) return;
    const tick = () => setElapsed(formatElapsed(task.created_at));
    tick();
    if (!isTerminal) {
      timerRef.current = setInterval(tick, 1000);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [task?.created_at, isTerminal]);

  const currentStepIndex = task ? getStepIndex(task.status) : 0;
  const colors = task ? statusColor(task.status) : statusColor('created');

  return (
    <div className="max-w-2xl mx-auto">
      {/* Back link */}
      <motion.div {...fadeUp} transition={{ duration: 0.3 }}>
        <Link
          href="/fill"
          className="inline-flex items-center gap-1.5 text-sm text-[#86868B] hover:text-[#1D1D1F] transition-colors duration-200 mb-8"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Fill
        </Link>
      </motion.div>

      {/* Header */}
      <motion.div
        {...fadeUp}
        transition={{ duration: 0.4, delay: 0.05 }}
        className="text-center mb-10"
      >
        <h1 className="text-2xl font-bold text-[#1D1D1F]">Web Form Fill</h1>
        <p className="text-sm text-[#86868B] mt-2">
          Task <span className="font-mono text-xs bg-[#F5F5F7] px-2 py-0.5 rounded">{taskId}</span>
        </p>
      </motion.div>

      {/* Error banner */}
      {error && !task && (
        <motion.div
          {...fadeUp}
          transition={{ duration: 0.3 }}
          className="mb-6 p-4 rounded-xl bg-red-50 border border-red-200 flex items-start gap-3"
        >
          <AlertTriangle className="w-5 h-5 text-red-500 mt-0.5 shrink-0" />
          <div>
            <p className="text-sm font-medium text-red-700">Failed to load task</p>
            <p className="text-xs text-red-600 mt-0.5">{error}</p>
          </div>
        </motion.div>
      )}

      {/* Status card */}
      {task && (
        <motion.div
          {...fadeUp}
          transition={{ duration: 0.4, delay: 0.1 }}
          className={`p-6 rounded-xl border ${colors.border} ${colors.bg} mb-6`}
        >
          <div className="flex items-center justify-between mb-1">
            <div className="flex items-center gap-3">
              <StatusIcon status={task.status} />
              <div>
                <p className={`text-lg font-semibold ${colors.text}`}>
                  {task.status === 'completed'
                    ? 'Form Filled Successfully'
                    : task.status === 'failed' || task.status === 'terminated'
                    ? 'Task Failed'
                    : 'Filling Form...'}
                </p>
                <p className="text-xs text-[#86868B] mt-0.5">
                  Elapsed: {elapsed}
                </p>
              </div>
            </div>
            {!isTerminal && (
              <div className="flex items-center gap-1.5 text-xs text-[#86868B]">
                <span className="relative flex h-2 w-2">
                  <span className={`animate-ping absolute inline-flex h-full w-full rounded-full ${colors.dot} opacity-75`} />
                  <span className={`relative inline-flex rounded-full h-2 w-2 ${colors.dot}`} />
                </span>
                Live
              </div>
            )}
          </div>
        </motion.div>
      )}

      {/* Progress stepper */}
      {task && (
        <motion.div
          {...fadeUp}
          transition={{ duration: 0.4, delay: 0.15 }}
          className="p-6 rounded-xl border border-[#E5E5EA] bg-white mb-6"
        >
          <p className="text-sm font-medium text-[#1D1D1F] mb-5">Progress</p>
          <div className="relative flex items-start justify-between">
            {/* Connecting line (background) */}
            <div className="absolute top-3 left-3 right-3 h-0.5 bg-[#E5E5EA]" />
            {/* Connecting line (filled) */}
            <motion.div
              className="absolute top-3 left-3 h-0.5 bg-[#5856D6]"
              initial={{ width: 0 }}
              animate={{
                width: `${(currentStepIndex / (STEPS.length - 1)) * 100}%`,
              }}
              transition={{ duration: 0.5, ease: 'easeOut' }}
              style={{ maxWidth: 'calc(100% - 24px)' }}
            />

            {STEPS.map((step, i) => {
              const isActive = i === currentStepIndex;
              const isDone = i < currentStepIndex || (i === currentStepIndex && task.status === 'completed');
              const isFailed = (task.status === 'failed' || task.status === 'terminated') && i === currentStepIndex;

              let dotClasses = 'bg-[#E5E5EA] border-[#E5E5EA]';
              if (isDone) dotClasses = 'bg-[#5856D6] border-[#5856D6]';
              else if (isFailed) dotClasses = 'bg-red-500 border-red-500';
              else if (isActive) dotClasses = 'bg-amber-400 border-amber-400';

              return (
                <div key={step} className="relative flex flex-col items-center z-10" style={{ flex: 1 }}>
                  <div
                    className={`w-6 h-6 rounded-full border-2 flex items-center justify-center ${dotClasses} transition-colors duration-300`}
                  >
                    {isDone && (
                      <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                      </svg>
                    )}
                    {isActive && !isDone && !isFailed && (
                      <div className="w-2 h-2 rounded-full bg-white" />
                    )}
                    {isFailed && (
                      <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    )}
                  </div>
                  <span
                    className={`text-xs mt-2 text-center ${
                      isDone || isActive ? 'text-[#1D1D1F] font-medium' : 'text-[#AEAEB2]'
                    }`}
                  >
                    {STEP_LABELS[step]}
                  </span>
                </div>
              );
            })}
          </div>
        </motion.div>
      )}

      {/* Details card */}
      {task && (
        <motion.div
          {...fadeUp}
          transition={{ duration: 0.4, delay: 0.2 }}
          className="p-6 rounded-xl border border-[#E5E5EA] bg-white mb-6 space-y-4"
        >
          <p className="text-sm font-medium text-[#1D1D1F]">Details</p>

          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-xs text-[#86868B] mb-0.5">Target URL</p>
              <a
                href={task.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-[#5856D6] hover:underline inline-flex items-center gap-1 text-sm break-all"
              >
                <Globe className="w-3.5 h-3.5 shrink-0" />
                {task.url}
                <ExternalLink className="w-3 h-3 shrink-0" />
              </a>
            </div>
            <div>
              <p className="text-xs text-[#86868B] mb-0.5">Status</p>
              <span className={`inline-flex items-center gap-1.5 text-sm font-medium ${colors.text}`}>
                <span className={`w-1.5 h-1.5 rounded-full ${colors.dot}`} />
                {task.status.charAt(0).toUpperCase() + task.status.slice(1)}
              </span>
            </div>
            <div>
              <p className="text-xs text-[#86868B] mb-0.5">Created</p>
              <p className="text-[#1D1D1F]">
                {new Date(task.created_at).toLocaleString()}
              </p>
            </div>
            {task.completed_at && (
              <div>
                <p className="text-xs text-[#86868B] mb-0.5">Completed</p>
                <p className="text-[#1D1D1F]">
                  {new Date(task.completed_at).toLocaleString()}
                </p>
              </div>
            )}
          </div>

          {task.navigation_goal && (
            <div>
              <p className="text-xs text-[#86868B] mb-1">Instructions</p>
              <p className="text-sm text-[#1D1D1F] bg-[#F5F5F7] rounded-lg px-3 py-2">
                {task.navigation_goal}
              </p>
            </div>
          )}

          {/* Failure reason */}
          {task.failure_reason && (
            <div className="p-3 rounded-lg bg-red-50 border border-red-200">
              <p className="text-xs text-red-500 font-medium mb-0.5">Failure Reason</p>
              <p className="text-sm text-red-700">{task.failure_reason}</p>
            </div>
          )}
        </motion.div>
      )}

      {/* Extracted information */}
      {task?.extracted_information && Object.keys(task.extracted_information).length > 0 && (
        <motion.div
          {...fadeUp}
          transition={{ duration: 0.4, delay: 0.25 }}
          className="p-6 rounded-xl border border-[#E5E5EA] bg-white mb-6"
        >
          <p className="text-sm font-medium text-[#1D1D1F] mb-3">Extracted Information</p>
          <pre className="text-xs text-[#1D1D1F] bg-[#F5F5F7] rounded-lg p-4 overflow-x-auto font-mono">
            {JSON.stringify(task.extracted_information, null, 2)}
          </pre>
        </motion.div>
      )}

      {/* Footer actions */}
      <motion.div
        {...fadeUp}
        transition={{ duration: 0.4, delay: 0.3 }}
        className="flex items-center justify-center gap-3 mt-8"
      >
        <Link
          href="/fill"
          className="px-5 py-2.5 text-sm font-medium text-[#1D1D1F] bg-[#F5F5F7] rounded-lg hover:bg-[#E5E5EA] transition-colors duration-200"
        >
          Fill Another Form
        </Link>
        {task?.status === 'completed' && task.url && (
          <a
            href={task.url}
            target="_blank"
            rel="noopener noreferrer"
            className="px-5 py-2.5 text-sm font-medium text-white bg-[#5856D6] rounded-lg hover:bg-[#4B49B6] transition-colors duration-200 inline-flex items-center gap-1.5"
          >
            Visit Form
            <ExternalLink className="w-3.5 h-3.5" />
          </a>
        )}
      </motion.div>
    </div>
  );
}
