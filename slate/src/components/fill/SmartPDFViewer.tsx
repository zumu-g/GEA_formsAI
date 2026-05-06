'use client';

import { useRef, useEffect, useCallback } from 'react';
import type { DetectedField } from '@/types/smartFill';

interface SmartPDFViewerProps {
  pageImages: string[]; // base64 PNG, index 0 = page 1
  fields: DetectedField[];
  activeFieldId: string | null;
  filledFields: Record<string, string>; // fieldId -> value
  onFieldClick: (fieldId: string) => void;
  formId?: string;
}

// ─── Colour coding by field type ────────────────────────────────────────────

const TYPE_BORDER_DEFAULT: Record<DetectedField['type'], string> = {
  text: 'border-blue-400/40',
  checkbox: 'border-purple-400/40',
  date: 'border-amber-400/40',
  currency: 'border-green-400/40',
  signature: 'border-red-400/40',
  textarea: 'border-blue-400/40',
};

const TYPE_BORDER_ACTIVE: Record<DetectedField['type'], string> = {
  text: 'border-blue-500 bg-blue-500/10 shadow-sm shadow-blue-500/20',
  checkbox: 'border-purple-500 bg-purple-500/10 shadow-sm shadow-purple-500/20',
  date: 'border-amber-500 bg-amber-500/10 shadow-sm shadow-amber-500/20',
  currency: 'border-green-500 bg-green-500/10 shadow-sm shadow-green-500/20',
  signature: 'border-red-500 bg-red-500/10 shadow-sm shadow-red-500/20',
  textarea: 'border-blue-500 bg-blue-500/10 shadow-sm shadow-blue-500/20',
};

// ─── FieldOverlay ────────────────────────────────────────────────────────────

interface FieldOverlayProps {
  field: DetectedField;
  isActive: boolean;
  isFilled: boolean;
  onFieldClick: (fieldId: string) => void;
  overlayRef: (el: HTMLDivElement | null) => void;
}

function FieldOverlay({ field, isActive, isFilled, onFieldClick, overlayRef }: FieldOverlayProps) {
  const { bbox, type, label, id } = field;

  const baseStyle: React.CSSProperties = {
    position: 'absolute',
    left: `${bbox.x * 100}%`,
    top: `${bbox.y * 100}%`,
    width: `${bbox.w * 100}%`,
    height: `${bbox.h * 100}%`,
  };

  let borderClasses: string;
  if (isActive) {
    borderClasses = `border-2 rounded-sm ${TYPE_BORDER_ACTIVE[type]}`;
  } else if (isFilled) {
    borderClasses = 'border border-green-500/50 bg-green-500/5 rounded-sm';
  } else {
    borderClasses = `border rounded-sm ${TYPE_BORDER_DEFAULT[type]}`;
  }

  return (
    <div
      ref={overlayRef}
      style={baseStyle}
      className={`group cursor-pointer transition-all duration-150 ${borderClasses}`}
      onClick={() => onFieldClick(id)}
      role="button"
      aria-label={label}
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onFieldClick(id);
        }
      }}
    >
      {/* Hover tooltip */}
      <span
        className="
          pointer-events-none
          absolute -top-6 left-0
          text-xs bg-gray-900 text-white
          px-1.5 py-0.5 rounded
          whitespace-nowrap z-10
          opacity-0 group-hover:opacity-100
          transition-opacity duration-100
        "
      >
        {label}
      </span>
    </div>
  );
}

// ─── PageView ────────────────────────────────────────────────────────────────

interface PageViewProps {
  pageNum: number;
  image: string;
  fields: DetectedField[];
  activeFieldId: string | null;
  filledFields: Record<string, string>;
  onFieldClick: (fieldId: string) => void;
  overlayRefs: React.MutableRefObject<Map<string, HTMLDivElement>>;
}

function PageView({
  pageNum,
  image,
  fields,
  activeFieldId,
  filledFields,
  onFieldClick,
  overlayRefs,
}: PageViewProps) {
  return (
    <div className="relative w-full rounded-xl overflow-hidden">
      {/* Page image */}
      <img
        src={`data:image/png;base64,${image}`}
        alt={`Page ${pageNum}`}
        className="block w-full h-auto"
        draggable={false}
      />

      {/* Page number badge */}
      <span className="absolute top-2 right-2 text-xs text-gray-500 select-none">
        {pageNum}
      </span>

      {/* Field overlays */}
      {fields.map((field) => (
        <FieldOverlay
          key={field.id}
          field={field}
          isActive={activeFieldId === field.id}
          isFilled={Boolean(filledFields[field.id])}
          onFieldClick={onFieldClick}
          overlayRef={(el) => {
            if (el) {
              overlayRefs.current.set(field.id, el);
            } else {
              overlayRefs.current.delete(field.id);
            }
          }}
        />
      ))}
    </div>
  );
}

// ─── SkeletonLoader ──────────────────────────────────────────────────────────

function SkeletonLoader() {
  return (
    <div className="space-y-4">
      {[1, 2, 3].map((i) => (
        <div
          key={i}
          className="w-full rounded-xl bg-gray-800 animate-pulse"
          style={{ aspectRatio: '1 / 1.4' }}
        />
      ))}
    </div>
  );
}

// ─── SmartPDFViewer ──────────────────────────────────────────────────────────

export function SmartPDFViewer({
  pageImages,
  fields,
  activeFieldId,
  filledFields,
  onFieldClick,
  formId,
}: SmartPDFViewerProps) {
  // Map of fieldId -> overlay DOM element, populated by PageView children
  const overlayRefs = useRef<Map<string, HTMLDivElement>>(new Map());

  // Scroll active field into view whenever activeFieldId changes
  const scrollToField = useCallback((fieldId: string | null) => {
    if (!fieldId) return;
    const el = overlayRefs.current.get(fieldId);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }, []);

  useEffect(() => {
    scrollToField(activeFieldId);
  }, [activeFieldId, scrollToField]);

  return (
    <div className="w-full h-full bg-gray-950 rounded-xl overflow-hidden">
      <div className="h-full overflow-y-auto p-4 space-y-4">
        {/* Three-way branch: skeleton | iframe | page images with overlays */}
        {pageImages.length === 0 && !formId && <SkeletonLoader />}

        {pageImages.length === 0 && formId && (
          <div className="w-full h-full rounded-xl overflow-hidden border border-gray-800">
            <iframe
              src={`/api/forms/${formId}/pdf#toolbar=1&navpanes=0`}
              className="w-full h-full"
              title="PDF Preview"
              style={{ border: 'none', display: 'block' }}
            />
          </div>
        )}

        {pageImages.length > 0 && pageImages.map((img, i) => (
          <PageView
            key={i}
            pageNum={i + 1}
            image={img}
            fields={fields.filter((f) => f.page === i + 1)}
            activeFieldId={activeFieldId}
            filledFields={filledFields}
            onFieldClick={onFieldClick}
            overlayRefs={overlayRefs}
          />
        ))}
      </div>
    </div>
  );
}
