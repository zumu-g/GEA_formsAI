'use client';

import { useCallback, useEffect } from 'react';
import type { SkillSection } from '@/types/skill';
import { VoiceInputButton } from './VoiceInputButton';

interface SkillSectionFormProps {
  section: SkillSection;
  values: Record<string, string>;
  errors: Record<string, string>;
  computedFieldIds: Set<string>;
  onValueChange: (fieldId: string, value: string) => void;
}

export function SkillSectionForm({
  section,
  values,
  errors,
  computedFieldIds,
  onValueChange,
}: SkillSectionFormProps) {
  const handleVoiceResult = useCallback(
    (fieldId: string) => (transcript: string) => {
      onValueChange(fieldId, transcript);
    },
    [onValueChange]
  );

  // Initialize fields that have defaultValue but no stored value yet
  useEffect(() => {
    const defaults: Record<string, string> = {};
    for (const field of section.fields) {
      if (field.defaultValue && !values[field.id]) {
        defaults[field.id] = field.defaultValue;
      }
    }
    if (Object.keys(defaults).length > 0) {
      Object.entries(defaults).forEach(([id, val]) => onValueChange(id, val));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [section.id]); // Only run when section changes

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-[#1D1D1F]">{section.title}</h2>
        {section.description && (
          <p className="mt-1 text-sm text-[#86868B]">{section.description}</p>
        )}
      </div>

      <div className="space-y-4">
        {section.fields.map((field) => {
          const value = values[field.id] ?? field.defaultValue ?? '';
          const error = errors[field.id];
          const isComputed = computedFieldIds.has(field.id);

          if (field.type === 'checkbox') {
            return (
              <label
                key={field.id}
                className="flex items-start gap-3 py-2 cursor-pointer group"
              >
                <input
                  type="checkbox"
                  checked={value === 'true'}
                  onChange={(e) =>
                    onValueChange(field.id, e.target.checked ? 'true' : 'false')
                  }
                  className="mt-0.5 w-5 h-5 rounded border-[#D1D1D6] text-[#5856D6] focus:ring-[#5856D6] focus:ring-offset-0 cursor-pointer"
                />
                <div className="flex-1">
                  <span className="text-sm font-medium text-[#1D1D1F] group-hover:text-[#5856D6] transition-colors">
                    {field.label}
                  </span>
                  {field.helpText && (
                    <p className="text-xs text-[#86868B] mt-0.5">{field.helpText}</p>
                  )}
                </div>
              </label>
            );
          }

          return (
            <div key={field.id}>
              <label className="block text-sm font-medium text-[#1D1D1F] mb-1.5">
                {field.label}
                {field.required && <span className="text-red-500 ml-0.5">*</span>}
                {isComputed && (
                  <span className="ml-2 text-xs font-normal text-[#86868B] bg-[#F5F5F7] px-2 py-0.5 rounded-full">
                    Auto-calculated
                  </span>
                )}
              </label>

              <div className="flex gap-2">
                {field.type === 'textarea' ? (
                  <textarea
                    value={value}
                    onChange={(e) => onValueChange(field.id, e.target.value)}
                    placeholder={field.placeholder}
                    rows={4}
                    className={`
                      flex-1 rounded-lg border px-3 py-2 text-sm text-[#1D1D1F]
                      placeholder:text-[#C7C7CC] transition-all duration-200
                      focus:outline-none focus:ring-2 focus:ring-[#5856D6]/30 focus:border-[#5856D6]
                      ${error ? 'border-red-300 bg-red-50/50' : 'border-[#E5E5EA] bg-white'}
                    `}
                  />
                ) : (
                  <div className="flex-1 relative">
                    {field.type === 'currency' && !isComputed && (
                      <span className="absolute left-3 top-1/2 -translate-y-1/2 text-sm text-[#86868B]">
                        $
                      </span>
                    )}
                    <input
                      type="text"
                      value={isComputed && value ? `$${parseFloat(value).toLocaleString('en-AU', { minimumFractionDigits: 2 })}` : value}
                      onChange={(e) => onValueChange(field.id, e.target.value)}
                      placeholder={field.placeholder}
                      readOnly={isComputed}
                      className={`
                        w-full rounded-lg border px-3 py-2.5 text-sm text-[#1D1D1F]
                        placeholder:text-[#C7C7CC] transition-all duration-200
                        focus:outline-none focus:ring-2 focus:ring-[#5856D6]/30 focus:border-[#5856D6]
                        ${field.type === 'currency' && !isComputed ? 'pl-7' : ''}
                        ${isComputed ? 'bg-[#F5F5F7] text-[#86868B] cursor-default' : ''}
                        ${error ? 'border-red-300 bg-red-50/50' : 'border-[#E5E5EA] bg-white'}
                      `}
                    />
                  </div>
                )}

                {!isComputed && (
                  <VoiceInputButton
                    onResult={handleVoiceResult(field.id)}
                  />
                )}
              </div>

              {field.helpText && !error && (
                <p className="mt-1 text-xs text-[#86868B]">{field.helpText}</p>
              )}
              {error && (
                <p className="mt-1 text-xs text-red-600">{error}</p>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
