'use client';

import { useEffect, useRef, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ArrowLeft } from 'lucide-react';
import Link from 'next/link';
import { getSkillById } from '@/lib/skills';
import { useSkillStore } from '@/stores/skillStore';
import { autoFillFromProfile } from '@/lib/skills/utils';
import { SkillWizard } from '@/components/skills/SkillWizard';

export default function SkillExecutionPage() {
  const params = useParams();
  const router = useRouter();
  const skillId = params.skillId as string;
  const skill = getSkillById(skillId);

  const session = useSkillStore((s) => s.session);
  const startSession = useSkillStore((s) => s.startSession);
  const setValues = useSkillStore((s) => s.setValues);
  const reset = useSkillStore((s) => s.reset);
  const hasAutoFilled = useRef(false);
  const [showStartOverConfirm, setShowStartOverConfirm] = useState(false);
  const [autoFillCount, setAutoFillCount] = useState(0);
  const [showAutoFillToast, setShowAutoFillToast] = useState(false);

  useEffect(() => {
    if (!skill) {
      router.push('/skills');
      return;
    }

    // Start a new session if none exists or if it's for a different skill
    if (!session || session.skillId !== skillId) {
      startSession(skillId);
    }
  }, [skill, skillId, session, startSession, router]);

  // Auto-fill from default profile when session transitions to in_progress
  useEffect(() => {
    if (!skill || !session || session.status !== 'in_progress' || hasAutoFilled.current) return;
    hasAutoFilled.current = true;

    (async () => {
      try {
        const res = await fetch('/api/profiles');
        if (!res.ok) return;
        const profiles = await res.json();
        const profile = profiles.find((p: { isDefault?: boolean }) => p.isDefault) ?? profiles[0];
        if (!profile) return;
        const autoValues = autoFillFromProfile(skill, profile);
        if (Object.keys(autoValues).length > 0) {
          setValues(autoValues);
          setAutoFillCount(Object.keys(autoValues).length);
          setShowAutoFillToast(true);
          setTimeout(() => setShowAutoFillToast(false), 4000);
        }
      } catch {
        // Silently ignore — auto-fill is best-effort
      }
    })();
  }, [skill, session, setValues]);

  if (!skill) return null;

  return (
    <div className="max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-3">
          <Link
            href="/skills"
            onClick={() => reset()}
            aria-label="Back to Skills"
            className="flex items-center justify-center w-9 h-9 rounded-xl border border-[#E2E4EA] text-[#767A85] hover:text-[#1B1D24] hover:border-[#C4C8D1] transition-all duration-150"
          >
            <ArrowLeft size={16} />
          </Link>
          <div>
            <h1 className="text-xl font-bold text-[#1B1D24]">{skill.name}</h1>
            {skill.jurisdiction && (
              <span className="text-xs font-medium text-[#5856D6]">
                {skill.jurisdiction}
              </span>
            )}
          </div>
        </div>

        {session && session.status !== 'upload' && (
          showStartOverConfirm ? (
            <div className="flex items-center gap-2">
              <span className="text-xs text-[#767A85]">Discard all progress?</span>
              <button
                onClick={() => {
                  setShowStartOverConfirm(false);
                  hasAutoFilled.current = false;
                  reset();
                  startSession(skillId);
                }}
                className="text-xs font-medium text-red-600 hover:text-red-700 cursor-pointer"
              >
                Yes, start over
              </button>
              <button
                onClick={() => setShowStartOverConfirm(false)}
                className="text-xs text-[#767A85] hover:text-[#1B1D24] cursor-pointer"
              >
                Cancel
              </button>
            </div>
          ) : (
            <button
              onClick={() => setShowStartOverConfirm(true)}
              className="text-xs text-[#767A85] hover:text-[#1B1D24] transition-colors cursor-pointer"
            >
              Start over
            </button>
          )
        )}
      </div>

      {/* Auto-fill toast */}
      {showAutoFillToast && autoFillCount > 0 && (
        <div className="mb-4 px-4 py-2.5 rounded-xl bg-[#5856D6]/10 border border-[#5856D6]/20 text-sm text-[#5856D6] flex items-center justify-between">
          <span>Pre-filled {autoFillCount} field{autoFillCount !== 1 ? 's' : ''} from your profile</span>
          <button onClick={() => setShowAutoFillToast(false)} className="text-[#5856D6]/60 hover:text-[#5856D6] text-xs cursor-pointer">Dismiss</button>
        </div>
      )}

      {/* Wizard */}
      <SkillWizard key={session?.formId ?? 'no-session'} skill={skill} />
    </div>
  );
}
