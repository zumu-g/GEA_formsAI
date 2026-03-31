'use client';

import { useState, useMemo, useCallback, useEffect } from 'react';
import { Check, ChevronLeft, ChevronRight, Download, Circle } from 'lucide-react';
import type { SkillDefinition } from '@/types/skill';
import { useSkillStore } from '@/stores/skillStore';
import { applyComputedFields, validateSection, mapSkillValuesToPdfFields, mapSkillValuesToPdfmeInputs } from '@/lib/skills/utils';
import { SkillPdfUpload } from './SkillPdfUpload';
import { SkillSectionForm } from './SkillSectionForm';
import { SkillReview } from './SkillReview';

interface SkillWizardProps {
  skill: SkillDefinition;
}

export function SkillWizard({ skill }: SkillWizardProps) {
  const session = useSkillStore((s) => s.session);
  const setValue = useSkillStore((s) => s.setValue);
  const setValues = useSkillStore((s) => s.setValues);
  const setFormId = useSkillStore((s) => s.setFormId);
  const goToSection = useSkillStore((s) => s.goToSection);
  const nextSection = useSkillStore((s) => s.nextSection);
  const prevSection = useSkillStore((s) => s.prevSection);
  const markSectionComplete = useSkillStore((s) => s.markSectionComplete);
  const setStatus = useSkillStore((s) => s.setStatus);

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isGenerating, setIsGenerating] = useState(false);
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [genError, setGenError] = useState<string | null>(null);

  // Clean up blob URL on change or unmount to prevent memory leaks
  useEffect(() => {
    return () => {
      if (pdfUrl) URL.revokeObjectURL(pdfUrl);
    };
  }, [pdfUrl]);

  const computedFieldIds = useMemo(() => {
    const ids = new Set<string>();
    for (const c of skill.computedFields ?? []) {
      ids.add(c.skillFieldId);
    }
    return ids;
  }, [skill.computedFields]);

  // Auto-compute derived fields whenever values change
  const valuesWithComputed = useMemo(() => {
    if (!session) return {};
    return applyComputedFields(skill, session.values);
  }, [skill, session?.values]);

  const handleValueChange = useCallback(
    (fieldId: string, value: string) => {
      setValue(fieldId, value);
      // Clear error for this field
      setErrors((prev) => {
        const next = { ...prev };
        delete next[fieldId];
        return next;
      });
    },
    [setValue]
  );

  const handleNext = useCallback(() => {
    if (!session) return;
    const currentSection = skill.sections[session.currentSectionIndex];
    const sectionErrors = validateSection(currentSection, valuesWithComputed);

    if (Object.keys(sectionErrors).length > 0) {
      setErrors(sectionErrors);
      return;
    }

    setErrors({});
    markSectionComplete(currentSection.id);

    if (session.currentSectionIndex === skill.sections.length - 1) {
      // Last section — go to review
      setStatus('review');
    } else {
      nextSection();
    }
  }, [session, skill, valuesWithComputed, markSectionComplete, nextSection, setStatus]);

  const handleBack = useCallback(() => {
    if (!session) return;
    if (session.status === 'review') {
      setStatus('in_progress');
    } else {
      prevSection();
    }
  }, [session, prevSection, setStatus]);

  const handleEditFromReview = useCallback(
    (sectionIndex: number) => {
      setStatus('in_progress');
      goToSection(sectionIndex);
    },
    [setStatus, goToSection]
  );

  const handleGenerate = useCallback(async () => {
    if (!session?.formId) return;

    setIsGenerating(true);
    setGenError(null);

    try {
      // Apply computed fields, then build request body
      const finalValues = applyComputedFields(skill, session.values);

      let requestBody: Record<string, unknown>;

      if (skill.pdfmeFieldMappings?.length) {
        // Coordinate-based pdfme path (preferred)
        const pdfmeValues = mapSkillValuesToPdfmeInputs(
          skill.pdfmeFieldMappings,
          finalValues,
          skill.sections
        );
        requestBody = {
          formId: session.formId,
          pdfmePayload: {
            mappings: skill.pdfmeFieldMappings,
            values: pdfmeValues,
          },
        };
      } else {
        // Fallback: AcroForm field name path
        const pdfFieldValues = mapSkillValuesToPdfFields(skill, finalValues);
        requestBody = {
          formId: session.formId,
          fieldValues: pdfFieldValues,
        };
      }

      const res = await fetch('/api/forms/fill', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody),
      });

      const data = await res.json();

      if (!data.success) {
        throw new Error(data.error?.message ?? 'Fill failed.');
      }

      // Convert base64 PDF to blob URL
      const byteChars = atob(data.data.pdfBase64);
      const byteArray = new Uint8Array(byteChars.length);
      for (let i = 0; i < byteChars.length; i++) {
        byteArray[i] = byteChars.charCodeAt(i);
      }
      const blob = new Blob([byteArray], { type: 'application/pdf' });
      const url = URL.createObjectURL(blob);
      setPdfUrl(url);
      setStatus('complete');
    } catch (err) {
      setGenError(err instanceof Error ? err.message : 'Generation failed.');
    } finally {
      setIsGenerating(false);
    }
  }, [session, skill, setStatus]);

  if (!session) return null;

  // Upload step
  if (session.status === 'upload') {
    return (
      <div className="py-12">
        <SkillPdfUpload
          skillName={skill.documentType}
          onUploaded={(formId) => setFormId(formId)}
        />
      </div>
    );
  }

  // Complete step — show download
  if (session.status === 'complete' && pdfUrl) {
    return (
      <div className="py-12 text-center max-w-md mx-auto">
        <div className="w-16 h-16 rounded-2xl bg-green-100 flex items-center justify-center mx-auto mb-4">
          <Check size={32} className="text-green-600" />
        </div>
        <h2 className="text-xl font-semibold text-[#1D1D1F] mb-2">PDF Generated</h2>
        <p className="text-sm text-[#86868B] mb-6">
          Your filled {skill.documentType} is ready to download.
        </p>
        <div className="flex flex-col gap-3">
          <a
            href={pdfUrl}
            download={`${skill.name.replace(/\s+/g, '_')}_filled.pdf`}
            className="inline-flex items-center justify-center gap-2 py-3 px-6 rounded-xl bg-[#5856D6] text-white text-sm font-semibold hover:bg-[#4240B0] transition-all duration-200 active:scale-[0.98]"
          >
            <Download size={18} />
            Download Filled PDF
          </a>
          <a
            href={pdfUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-[#5856D6] hover:text-[#4240B0] transition-colors"
          >
            Preview in new tab
          </a>
        </div>
      </div>
    );
  }

  const currentSection = skill.sections[session.currentSectionIndex];
  const isReview = session.status === 'review';
  const isFirstSection = session.currentSectionIndex === 0;

  return (
    <div className="flex gap-8 min-h-[500px]">
      {/* Section nav sidebar */}
      <div className="w-56 shrink-0">
        <nav className="sticky top-4 space-y-1">
          {skill.sections.map((section, idx) => {
            const isActive = !isReview && session.currentSectionIndex === idx;
            const isCompleted = session.completedSections.includes(section.id);
            // Allow clicking: current section, completed sections, or the next uncompleted section
            const canNavigate =
              isReview ||
              isActive ||
              isCompleted ||
              idx <= session.currentSectionIndex + 1;

            return (
              <button
                key={section.id}
                disabled={!canNavigate}
                onClick={() => {
                  if (!canNavigate) return;
                  if (isReview) {
                    handleEditFromReview(idx);
                  } else {
                    goToSection(idx);
                  }
                }}
                className={`
                  w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm text-left
                  transition-all duration-150
                  ${
                    !canNavigate
                      ? 'text-[#D1D1D6] cursor-not-allowed opacity-50'
                      : isActive
                        ? 'bg-white text-[#1D1D1F] shadow-sm border border-[#E5E5EA]/60 font-medium cursor-pointer'
                        : 'text-[#86868B] hover:bg-white/60 hover:text-[#1D1D1F] cursor-pointer'
                  }
                `}
              >
                {isCompleted ? (
                  <Check size={16} className="text-green-500 shrink-0" />
                ) : (
                  <Circle
                    size={16}
                    className={`shrink-0 ${isActive ? 'text-[#5856D6]' : 'text-[#D1D1D6]'}`}
                  />
                )}
                <span className="truncate">{section.title}</span>
              </button>
            );
          })}

          {/* Review step in nav */}
          {(() => {
            const allComplete = session.completedSections.length === skill.sections.length;
            return (
              <button
                disabled={!allComplete && !isReview}
                onClick={() => {
                  if (allComplete) {
                    setStatus('review');
                  }
                }}
                className={`
                  w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm text-left
                  transition-all duration-150
                  ${
                    !allComplete && !isReview
                      ? 'text-[#D1D1D6] cursor-not-allowed opacity-50'
                      : isReview
                        ? 'bg-white text-[#1D1D1F] shadow-sm border border-[#E5E5EA]/60 font-medium cursor-pointer'
                        : 'text-[#86868B] hover:bg-white/60 hover:text-[#1D1D1F] cursor-pointer'
                  }
                `}
              >
                <Circle
                  size={16}
                  className={`shrink-0 ${isReview ? 'text-[#5856D6]' : 'text-[#D1D1D6]'}`}
                />
                <span className="truncate">Review & Generate</span>
              </button>
            );
          })()}
        </nav>
      </div>

      {/* Main content */}
      <div className="flex-1 max-w-xl">
        {isReview ? (
          <SkillReview
            skill={skill}
            values={valuesWithComputed}
            onEditSection={handleEditFromReview}
            onGenerate={handleGenerate}
            isGenerating={isGenerating}
          />
        ) : (
          <>
            {/* Progress */}
            <div className="flex items-center justify-between mb-6">
              <span className="text-xs text-[#86868B] font-medium">
                Step {session.currentSectionIndex + 1} of {skill.sections.length}
              </span>
              <div className="flex gap-1">
                {skill.sections.map((_, idx) => (
                  <div
                    key={idx}
                    className={`h-1 w-6 rounded-full transition-colors ${
                      idx <= session.currentSectionIndex ? 'bg-[#5856D6]' : 'bg-[#E5E5EA]'
                    }`}
                  />
                ))}
              </div>
            </div>

            <SkillSectionForm
              section={currentSection}
              values={valuesWithComputed}
              errors={errors}
              computedFieldIds={computedFieldIds}
              onValueChange={handleValueChange}
            />

            {/* Navigation */}
            <div className="flex items-center justify-between mt-8 pt-6 border-t border-[#E5E5EA]/60">
              <button
                onClick={handleBack}
                disabled={isFirstSection}
                className={`
                  flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium
                  transition-all duration-150 cursor-pointer
                  ${
                    isFirstSection
                      ? 'text-[#D1D1D6] cursor-not-allowed'
                      : 'text-[#86868B] hover:text-[#1D1D1F] hover:bg-[#F5F5F7]'
                  }
                `}
              >
                <ChevronLeft size={16} />
                Back
              </button>

              <button
                onClick={handleNext}
                className="flex items-center gap-2 px-6 py-2.5 rounded-xl text-sm font-semibold text-white bg-[#5856D6] hover:bg-[#4240B0] active:scale-[0.98] transition-all duration-200 cursor-pointer"
              >
                {session.currentSectionIndex === skill.sections.length - 1
                  ? 'Review'
                  : 'Next'}
                <ChevronRight size={16} />
              </button>
            </div>
          </>
        )}

        {genError && (
          <p className="mt-4 text-sm text-red-600 text-center">{genError}</p>
        )}
      </div>
    </div>
  );
}
