'use client';

import { useEffect, useRef } from 'react';
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
            className="flex items-center justify-center w-9 h-9 rounded-xl border border-[#E5E5EA] text-[#86868B] hover:text-[#1D1D1F] hover:border-[#C7C7CC] transition-all duration-150"
          >
            <ArrowLeft size={16} />
          </Link>
          <div>
            <h1 className="text-xl font-bold text-[#1D1D1F]">{skill.name}</h1>
            {skill.jurisdiction && (
              <span className="text-xs font-medium text-[#5856D6]">
                {skill.jurisdiction}
              </span>
            )}
          </div>
        </div>

        {session && session.status !== 'upload' && (
          <button
            onClick={() => {
              reset();
              startSession(skillId);
            }}
            className="text-xs text-[#86868B] hover:text-[#1D1D1F] transition-colors cursor-pointer"
          >
            Start over
          </button>
        )}
      </div>

      {/* Wizard */}
      <SkillWizard skill={skill} />
    </div>
  );
}
