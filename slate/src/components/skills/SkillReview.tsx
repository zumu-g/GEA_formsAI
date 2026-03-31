'use client';

import type { SkillDefinition } from '@/types/skill';
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
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-[#1D1D1F]">Review & Generate</h2>
        <p className="mt-1 text-sm text-[#86868B]">
          Review your entries below, then generate the filled PDF.
        </p>
      </div>

      <div className="space-y-4">
        {skill.sections.map((section, sectionIndex) => {
          const filledFields = section.fields.filter(
            (f) =>
              (values[f.id] && values[f.id].trim() !== '') ||
              (f.type === 'checkbox' && values[f.id] === 'false')
          );

          return (
            <div
              key={section.id}
              className="bg-white border border-[#E5E5EA] rounded-xl p-4"
            >
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-semibold text-[#1D1D1F]">
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
                <p className="text-xs text-[#C7C7CC] italic">No fields filled</p>
              ) : (
                <div className="space-y-2">
                  {filledFields.map((field) => (
                    <div key={field.id} className="flex items-start gap-2">
                      <Check size={14} className="text-green-500 mt-0.5 shrink-0" />
                      <div className="min-w-0">
                        <span className="text-xs text-[#86868B]">{field.label}: </span>
                        <span className="text-sm text-[#1D1D1F]">
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
