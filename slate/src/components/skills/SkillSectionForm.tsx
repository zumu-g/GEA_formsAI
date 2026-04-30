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

/** Convert a stored dd/mm/yyyy value to the ISO YYYY-MM-DD format that
 *  <input type="date"> expects. Returns '' for any blank or invalid input. */
function toIsoDate(ddmmyyyy: string): string {
  if (!ddmmyyyy) return '';
  const parts = ddmmyyyy.split('/');
  if (parts.length !== 3) return '';
  const [dd, mm, yyyy] = parts;
  return `${yyyy}-${mm.padStart(2, '0')}-${dd.padStart(2, '0')}`;
}

/** Convert a browser-returned ISO YYYY-MM-DD value to stored dd/mm/yyyy. */
function fromIsoDate(iso: string): string {
  if (!iso) return '';
  const parts = iso.split('-');
  if (parts.length !== 3) return '';
  const [yyyy, mm, dd] = parts;
  return `${dd}/${mm}/${yyyy}`;
}

/** Map a SkillField type to an HTML input type. */
function htmlInputType(
  fieldType: string
): 'text' | 'date' | 'tel' | 'email' | 'number' {
  switch (fieldType) {
    case 'date':
      return 'date';
    case 'phone':
      return 'tel';
    case 'email':
      return 'email';
    case 'number':
      return 'number';
    default:
      return 'text';
  }
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

  const hasRequiredFields = section.fields.some((f) => f.required);
  const errorCount = Object.keys(errors).length;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-[#1D1D1F]">{section.title}</h2>
        {section.description && (
          <p className="mt-1 text-sm text-[#86868B]">{section.description}</p>
        )}
      </div>

      {/* FIX 5 — Validation error banner */}
      {errorCount > 0 && (
        <div className="px-4 py-3 rounded-xl bg-red-50 border border-red-200 text-sm text-red-700">
          {errorCount} field{errorCount !== 1 ? 's' : ''} need{errorCount === 1 ? 's' : ''} attention — check below
        </div>
      )}

      <div className="space-y-4">
        {/* FIX 4 — Required field legend (once, before first field) */}
        {hasRequiredFields && (
          <p className="text-xs text-[#86868B] mb-4">
            Fields marked <span className="text-red-500 font-medium">*</span> are required
          </p>
        )}

        {section.fields.map((field) => {
          const value = values[field.id] ?? field.defaultValue ?? '';
          const error = errors[field.id];
          const isComputed = computedFieldIds.has(field.id);

          // FIX 2 — checkbox: connect label via htmlFor/id
          if (field.type === 'checkbox') {
            return (
              <div key={field.id} className="flex items-start gap-3 py-2">
                <input
                  type="checkbox"
                  id={field.id}
                  checked={value === 'true'}
                  onChange={(e) =>
                    onValueChange(field.id, e.target.checked ? 'true' : 'false')
                  }
                  className="mt-0.5 w-5 h-5 rounded border-[#D1D1D6] text-[#5856D6] focus:ring-[#5856D6] focus:ring-offset-0 cursor-pointer"
                />
                <div className="flex-1">
                  <label
                    htmlFor={field.id}
                    className="text-sm font-medium text-[#1D1D1F] hover:text-[#5856D6] transition-colors cursor-pointer"
                  >
                    {field.label}
                  </label>
                  {field.helpText && (
                    <p className="text-xs text-[#86868B] mt-0.5">{field.helpText}</p>
                  )}
                </div>
              </div>
            );
          }

          // Formatted value for computed display
          const formattedComputedValue =
            isComputed && value
              ? `$${parseFloat(value).toLocaleString('en-AU', { minimumFractionDigits: 2 })}`
              : value;

          return (
            <div key={field.id}>
              {/* FIX 2 — label connected via htmlFor */}
              <label
                htmlFor={field.id}
                className="block text-sm font-medium text-[#1D1D1F] mb-1.5"
              >
                {field.label}
                {field.required && <span className="text-red-500 ml-0.5">*</span>}
                {isComputed && (
                  <span className="ml-2 text-xs font-normal text-[#86868B] bg-[#F5F5F7] px-2 py-0.5 rounded-full">
                    Auto-calculated
                  </span>
                )}
              </label>

              {/* FIX 3 — Computed fields rendered as static display, not an input */}
              {isComputed ? (
                <div className="px-3 py-2 rounded-xl bg-[#F5F5F7] border border-[#E5E5EA] text-sm text-[#1D1D1F]">
                  {formattedComputedValue || <span className="text-[#C7C7CC]">—</span>}
                </div>
              ) : (
                <div className="flex gap-2">
                  {field.type === 'textarea' ? (
                    <textarea
                      id={field.id}
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
                      {field.type === 'currency' && (
                        <span className="absolute left-3 top-1/2 -translate-y-1/2 text-sm text-[#86868B]">
                          $
                        </span>
                      )}
                      {/* FIX 1 — correct input type + date format conversion */}
                      <input
                        id={field.id}
                        type={htmlInputType(field.type)}
                        value={
                          field.type === 'date' ? toIsoDate(value) : value
                        }
                        onChange={(e) => {
                          if (field.type === 'date') {
                            onValueChange(field.id, fromIsoDate(e.target.value));
                          } else {
                            onValueChange(field.id, e.target.value);
                          }
                        }}
                        placeholder={field.placeholder}
                        className={`
                          w-full rounded-lg border px-3 py-2.5 text-sm text-[#1D1D1F]
                          placeholder:text-[#C7C7CC] transition-all duration-200
                          focus:outline-none focus:ring-2 focus:ring-[#5856D6]/30 focus:border-[#5856D6]
                          ${field.type === 'currency' ? 'pl-7' : ''}
                          ${error ? 'border-red-300 bg-red-50/50' : 'border-[#E5E5EA] bg-white'}
                        `}
                      />
                    </div>
                  )}

                  <VoiceInputButton onResult={handleVoiceResult(field.id)} />
                </div>
              )}

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
