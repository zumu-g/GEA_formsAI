'use client';

import { useRef, useEffect, useCallback, useState } from 'react';
import { Crosshair } from 'lucide-react';
import type { DetectedField } from '@/types/smartFill';

interface SmartPDFViewerProps {
  pageImages: string[]; // base64 PNG, index 0 = page 1
  fields: DetectedField[];
  activeFieldId: string | null;
  filledFields: Record<string, string>; // fieldId -> value
  onFieldClick: (fieldId: string) => void;
  formId?: string;
  onRegionDrawn?: (page: number, bbox: { x: number; y: number; w: number; h: number }, cropDataUrl: string) => void;
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

// ─── Crop helper ─────────────────────────────────────────────────────────────

async function cropPageImage(
  imgBase64: string,
  bbox: { x: number; y: number; w: number; h: number },
): Promise<string> {
  return new Promise((resolve) => {
    const img = new Image();
    img.onload = () => {
      const sx = img.width * bbox.x;
      const sy = img.height * bbox.y;
      const sw = Math.max(img.width * bbox.w, 1);
      const sh = Math.max(img.height * bbox.h, 1);
      const canvas = document.createElement('canvas');
      canvas.width = sw;
      canvas.height = sh;
      canvas.getContext('2d')!.drawImage(img, sx, sy, sw, sh, 0, 0, sw, sh);
      resolve(canvas.toDataURL('image/png').split(',')[1]);
    };
    img.src = `data:image/png;base64,${imgBase64}`;
  });
}

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
  drawMode: boolean;
  liveRect: { page: number; x: number; y: number; w: number; h: number } | null;
  onPageMouseDown: (e: React.MouseEvent<HTMLDivElement>, pageNum: number, el: HTMLDivElement) => void;
}

function PageView({
  pageNum,
  image,
  fields,
  activeFieldId,
  filledFields,
  onFieldClick,
  overlayRefs,
  drawMode,
  liveRect,
  onPageMouseDown,
}: PageViewProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  const showLiveRect = liveRect?.page === pageNum;
  const lx = showLiveRect ? Math.min(liveRect!.x, liveRect!.x + liveRect!.w) * 100 : 0;
  const ly = showLiveRect ? Math.min(liveRect!.y, liveRect!.y + liveRect!.h) * 100 : 0;
  const lw = showLiveRect ? Math.abs(liveRect!.w) * 100 : 0;
  const lh = showLiveRect ? Math.abs(liveRect!.h) * 100 : 0;

  return (
    <div
      ref={containerRef}
      className={`relative w-full rounded-xl overflow-hidden ${drawMode ? 'cursor-crosshair select-none' : ''}`}
      onMouseDown={drawMode && containerRef.current
        ? (e) => onPageMouseDown(e, pageNum, containerRef.current!)
        : undefined}
    >
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

      {/* Field overlays — hidden in draw mode to avoid click conflicts */}
      {!drawMode && fields.map((field) => (
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

      {/* Live draw rect */}
      {showLiveRect && lw > 0 && lh > 0 && (
        <div
          style={{
            position: 'absolute',
            left: `${lx}%`,
            top: `${ly}%`,
            width: `${lw}%`,
            height: `${lh}%`,
          }}
          className="border-2 border-[#5856D6] bg-[#5856D6]/10 rounded-sm pointer-events-none"
        />
      )}
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
  onRegionDrawn,
}: SmartPDFViewerProps) {
  const overlayRefs = useRef<Map<string, HTMLDivElement>>(new Map());
  const [drawMode, setDrawMode] = useState(false);
  const [liveRect, setLiveRect] = useState<{ page: number; x: number; y: number; w: number; h: number } | null>(null);

  const drawStateRef = useRef<{
    pageNum: number;
    imgBase64: string;
    startX: number;
    startY: number;
    pageEl: HTMLDivElement;
  } | null>(null);

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

  // ── Global mouse move/up for draw mode ──────────────────────────────────────
  useEffect(() => {
    if (!drawMode) return;

    const handleMouseMove = (e: MouseEvent) => {
      const ds = drawStateRef.current;
      if (!ds) return;
      const rect = ds.pageEl.getBoundingClientRect();
      const cx = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
      const cy = Math.max(0, Math.min(1, (e.clientY - rect.top) / rect.height));
      setLiveRect({
        page: ds.pageNum,
        x: ds.startX,
        y: ds.startY,
        w: cx - ds.startX,
        h: cy - ds.startY,
      });
    };

    const handleMouseUp = async (e: MouseEvent) => {
      const ds = drawStateRef.current;
      if (!ds) return;

      const rect = ds.pageEl.getBoundingClientRect();
      const cx = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
      const cy = Math.max(0, Math.min(1, (e.clientY - rect.top) / rect.height));

      const x = Math.min(ds.startX, cx);
      const y = Math.min(ds.startY, cy);
      const w = Math.abs(cx - ds.startX);
      const h = Math.abs(cy - ds.startY);

      drawStateRef.current = null;
      setLiveRect(null);
      setDrawMode(false);

      // Minimum size threshold — ignore accidental clicks
      if (w < 0.01 || h < 0.005) return;

      if (onRegionDrawn) {
        const cropDataUrl = await cropPageImage(ds.imgBase64, { x, y, w, h });
        onRegionDrawn(ds.pageNum, { x, y, w, h }, cropDataUrl);
      }
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [drawMode, onRegionDrawn]);

  const handlePageMouseDown = useCallback(
    (e: React.MouseEvent<HTMLDivElement>, pageNum: number, el: HTMLDivElement) => {
      e.preventDefault();
      const rect = el.getBoundingClientRect();
      const sx = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
      const sy = Math.max(0, Math.min(1, (e.clientY - rect.top) / rect.height));
      drawStateRef.current = {
        pageNum,
        imgBase64: pageImages[pageNum - 1] ?? '',
        startX: sx,
        startY: sy,
        pageEl: el,
      };
    },
    [pageImages],
  );

  const toggleDrawMode = useCallback(() => {
    setDrawMode((d) => !d);
    setLiveRect(null);
    drawStateRef.current = null;
  }, []);

  const showDrawToolbar = pageImages.length > 0 && Boolean(onRegionDrawn);

  return (
    <div className="w-full h-full bg-gray-950 rounded-xl overflow-hidden flex flex-col">
      {/* Draw mode toolbar */}
      {showDrawToolbar && (
        <div className="shrink-0 px-3 py-2 border-b border-gray-800 flex items-center gap-3">
          <button
            type="button"
            onClick={toggleDrawMode}
            className={`flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded-lg transition-colors duration-150 ${
              drawMode
                ? 'bg-[#5856D6] text-white'
                : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800'
            }`}
          >
            <Crosshair size={12} />
            {drawMode ? 'Drawing — drag to select' : 'Draw Field'}
          </button>
          {drawMode && (
            <span className="text-xs text-gray-500">Click and drag over a missed field</span>
          )}
        </div>
      )}

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
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
            drawMode={drawMode}
            liveRect={liveRect}
            onPageMouseDown={handlePageMouseDown}
          />
        ))}
      </div>
    </div>
  );
}
