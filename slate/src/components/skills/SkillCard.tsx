'use client';

import Link from 'next/link';
import { FileSignature, Scale, FileText, Calculator } from 'lucide-react';
import type { SkillDefinition } from '@/types/skill';

const ICON_MAP: Record<string, React.ComponentType<{ size?: number; className?: string }>> = {
  FileSignature,
  Scale,
  FileText,
  Calculator,
};

interface SkillCardProps {
  skill: SkillDefinition;
}

export function SkillCard({ skill }: SkillCardProps) {
  const Icon = ICON_MAP[skill.icon] ?? FileText;
  const totalFields = skill.sections.reduce((sum, s) => sum + s.fields.length, 0);
  const isDraft = skill.version.includes('draft');

  return (
    <Link
      href={`/skills/${skill.id}`}
      className="group block bg-white border border-[#E5E5EA] rounded-2xl p-6 hover:shadow-md hover:border-[#D1D1D6] transition-all duration-200 hover:-translate-y-0.5"
    >
      <div className="flex items-start gap-4">
        <div className="w-11 h-11 rounded-xl bg-[#5856D6]/10 flex items-center justify-center shrink-0 group-hover:bg-[#5856D6]/15 transition-colors">
          <Icon size={22} className="text-[#5856D6]" />
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <h3 className="text-base font-semibold text-[#1D1D1F] truncate">
              {skill.name}
            </h3>
            {isDraft && (
              <span className="text-[10px] font-medium text-amber-600 bg-amber-50 px-1.5 py-0.5 rounded-full shrink-0">
                Draft
              </span>
            )}
          </div>
          <p className="text-sm text-[#86868B] mt-1 line-clamp-2">{skill.description}</p>

          <div className="flex items-center gap-3 mt-3">
            {skill.jurisdiction && (
              <span className="text-xs font-medium text-[#5856D6] bg-[#5856D6]/8 px-2 py-0.5 rounded-full">
                {skill.jurisdiction}
              </span>
            )}
            <span className="text-xs text-[#86868B]">
              {skill.sections.length} sections
            </span>
            <span className="text-xs text-[#86868B]">{totalFields} fields</span>
          </div>
        </div>
      </div>
    </Link>
  );
}
