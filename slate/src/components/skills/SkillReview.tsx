'use client';

import { useMemo } from 'react';
import type { SkillDefinition } from '@/types/skill';
import { validateSection } from '@/lib/skills/utils';
import { Check, Pencil } from 'lucide-react';

interface SkillReviewProps {
  skill: SkillDefinition;
  values: Record<string, string>;
  onEditSection: (sectionIndex: number) => void;
  onGenerate: () => void;
  isGenerating: boolean;
}

export function SkillReview({
  skill,
  values,
  onEditSection,
  onGenerate,
  isGenerating,
}: SkillReviewProps) {
  const allErrors = useMemo(() => {
    return skill.sections.reduce<Record<string, string>>((acc, section) => ({
      ...acc,
      ...validateSection(section, values),
    }), {});
  }, [skill, values]);
  const hasErrors = Object.keys(allErrors).length > 0;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-[#1B1D24]">Review & Generate</h2>
        <p className="mt-1 text-sm text-[#767A85]">
          Review your entries below, then generate the filled PDF.
        </p>
      </div>

      <div className="space-y-4">
        {skill.sections.map((section, sectionIndex) => {
          const filledFields = section.fields.filter((f) => {
            if (f.type === 'checkbox') return values[f.id] === 'true';
            return values[f.id] && values[f.id].trim() !== '';
          });

          return (
            <div
              key={section.id}
              className="bg-white border border-[#E2E4EA] rounded-xl p-4"
            >
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-semibold text-[#1B1D24]">
                  {section.title}
                </h3>
                <button
                  type="button"
                  onClick={() => onEditSection(sectionIndex)}
                  className="flex items-center gap-1 text-xs text-[#5856D6] hover:text-[#4240B0] transition-colors cursor-pointer"
                >
                  <Pencil size={12} />
                  Edit
                </button>
              </div>

              {filledFields.length === 0 ? (
                <p className="text-xs text-[#C4C8D1] italic">No fields filled</p>
              ) : (
                <div className="space-y-2">
                  {filledFields.map((field) => (
                    <div key={field.id} className="flex items-start gap-2">
                      <Check size={14} className="text-green-500 mt-0.5 shrink-0" />
                      <div className="min-w-0">
                        <span className="text-xs text-[#767A85]">{field.label}: </span>
                        <span className="text-sm text-[#1B1D24]">
                          {field.type === 'checkbox'
                            ? values[field.id] === 'true'
                              ? 'Yes'
                              : 'No'
                            : field.type === 'currency'
                              ? `$${parseFloat(values[field.id].replace(/[^0-9.]/g, '') || '0').toLocaleString('en-AU', { minimumFractionDigits: 2 })}`
                              : values[field.id]}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {hasErrors && (
        <div className="mb-6 px-4 py-3 rounded-xl bg-amber-50 border border-amber-200">
          <p className="text-sm font-medium text-amber-800 mb-2">
            {Object.keys(allErrors).length} required field{Object.keys(allErrors).length !== 1 ? 's' : ''} incomplete
          </p>
          <ul className="space-y-1">
            {skill.sections.map((section, idx) => {
              const sectionErrors = validateSection(section, values);
              if (Object.keys(sectionErrors).length === 0) return null;
              return (
                <li key={section.id} className="text-xs text-amber-700 flex items-center justify-between">
                  <span>{section.title}: {Object.keys(sectionErrors).length} field(s)</span>
                  <button
                    onClick={() => onEditSection(idx)}
                    className="text-[#5856D6] text-xs font-medium hover:underline"
                  >
                    Fill now →
                  </button>
                </li>
              );
            })}
          </ul>
        </div>
      )}

      <button
        onClick={onGenerate}
        disabled={isGenerating}
        className={`
          w-full py-3 px-6 rounded-xl text-sm font-semibold text-white
          transition-all duration-200 cursor-pointer
          ${
            isGenerating
              ? 'bg-[#5856D6]/60 cursor-wait'
              : 'bg-[#5856D6] hover:bg-[#4240B0] active:scale-[0.98]'
          }
        `}
      >
        {isGenerating ? 'Generating PDF...' : 'Generate Filled PDF'}
      </button>
    </div>
  );
}
