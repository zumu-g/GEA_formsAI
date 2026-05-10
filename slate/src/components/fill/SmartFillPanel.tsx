'use client';

import { useRef, useEffect, useCallback, useState } from 'react';
import { User, FileText, Loader2, Plus, Sparkles } from 'lucide-react';
import { VoiceInputButton } from '@/components/skills/VoiceInputButton';
import type { DetectedField, DetectionMethod } from '@/types/smartFill';
import type { DataProfile } from '@/types/profile';

// ─── Props ────────────────────────────────────────────────────────────────────

interface SmartFillPanelProps {
  fields: DetectedField[];
  values: Record<string, string>;
  activeFieldId: string | null;
  profiles: DataProfile[];
  onValueChange: (fieldId: string, value: string) => void;
  onFieldFocus: (fieldId: string) => void;
  onGenerate: () => void;
  isGenerating: boolean;
  onFieldsChange?: (fields: DetectedField[]) => void;
  detectionMethod?: DetectionMethod;
}

// ─── Type badge colours ───────────────────────────────────────────────────────

const TYPE_BADGE: Record<DetectedField['type'], string> = {
  text: 'bg-gray-700 text-gray-300',
  textarea: 'bg-gray-700 text-gray-300',
  date: 'bg-purple-900/60 text-purple-300',
  currency: 'bg-green-900/60 text-green-300',
  checkbox: 'bg-blue-900/60 text-blue-300',
  signature: 'bg-red-900/60 text-red-300',
};

const TYPE_LABEL: Record<DetectedField['type'], string> = {
  text: 'Text',
  textarea: 'Text area',
  date: 'Date',
  currency: 'Currency',
  checkbox: 'Checkbox',
  signature: 'Signature',
};

// ─── Toggle switch for checkbox fields ───────────────────────────────────────

function ToggleSwitch({
  checked,
  onChange,
}: {
  checked: boolean;
  onChange: (value: boolean) => void;
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      onClick={() => onChange(!checked)}
      className={`
        relative inline-flex h-6 w-11 shrink-0 items-center rounded-full
        transition-colors duration-200 focus:outline-none focus-visible:ring-2
        focus-visible:ring-blue-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900
        ${checked ? 'bg-blue-600' : 'bg-gray-700'}
      `}
    >
      <span
        className={`
          inline-block h-4 w-4 rounded-full bg-white shadow-sm
          transition-transform duration-200
          ${checked ? 'translate-x-6' : 'translate-x-1'}
        `}
      />
    </button>
  );
}

// ─── Signature canvas drawing widget ─────────────────────────────────────────

interface SignatureCanvasProps {
  value: string;          // base64 PNG data URL string (empty = blank)
  onChange: (dataUrl: string) => void;
}

function SignatureCanvas({ value, onChange }: SignatureCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const isDrawing = useRef(false);
  const lastPos = useRef<{ x: number; y: number } | null>(null);
  const [typedName, setTypedName] = useState('');

  // Restore drawn signature from value (data URL) on mount / value change.
  // Plain text values (typed name fallback) are not drawn onto the canvas.
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    if (value && value.startsWith('data:image/')) {
      const img = new Image();
      img.onload = () => {
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
      };
      img.src = value;
    }
  // Only run when value changes externally (not while drawing).
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value]);

  const getPos = (
    e: React.MouseEvent<HTMLCanvasElement> | React.TouchEvent<HTMLCanvasElement>
  ): { x: number; y: number } | null => {
    const canvas = canvasRef.current;
    if (!canvas) return null;
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    if ('touches' in e) {
      const touch = e.touches[0];
      if (!touch) return null;
      return {
        x: (touch.clientX - rect.left) * scaleX,
        y: (touch.clientY - rect.top) * scaleY,
      };
    }
    return {
      x: (e.clientX - rect.left) * scaleX,
      y: (e.clientY - rect.top) * scaleY,
    };
  };

  const startDrawing = (
    e: React.MouseEvent<HTMLCanvasElement> | React.TouchEvent<HTMLCanvasElement>
  ) => {
    e.preventDefault();
    isDrawing.current = true;
    lastPos.current = getPos(e);
  };

  const draw = (
    e: React.MouseEvent<HTMLCanvasElement> | React.TouchEvent<HTMLCanvasElement>
  ) => {
    if (!isDrawing.current) return;
    e.preventDefault();
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    const pos = getPos(e);
    if (!pos || !lastPos.current) return;
    ctx.beginPath();
    ctx.moveTo(lastPos.current.x, lastPos.current.y);
    ctx.lineTo(pos.x, pos.y);
    ctx.strokeStyle = '#1a1a2e';
    ctx.lineWidth = 1.5;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.stroke();
    lastPos.current = pos;
  };

  const endDrawing = () => {
    if (!isDrawing.current) return;
    isDrawing.current = false;
    lastPos.current = null;
    const canvas = canvasRef.current;
    if (canvas) {
      onChange(canvas.toDataURL('image/png'));
    }
  };

  const handleClear = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    setTypedName('');
    onChange('');
  };

  const handleTypedName = (e: React.ChangeEvent<HTMLInputElement>) => {
    const name = e.target.value;
    setTypedName(name);
    onChange(name);
  };

  return (
    <div className="flex-1 min-w-0 space-y-2">
      {/* Canvas container */}
      <div className="relative w-full">
        <canvas
          ref={canvasRef}
          width={600}
          height={160}
          onMouseDown={startDrawing}
          onMouseMove={draw}
          onMouseUp={endDrawing}
          onMouseLeave={endDrawing}
          onTouchStart={startDrawing}
          onTouchMove={draw}
          onTouchEnd={endDrawing}
          className="rounded-lg border border-gray-700 bg-white cursor-crosshair w-full"
          style={{ touchAction: 'none' }}
          aria-label="Signature drawing area"
        />
        <button
          type="button"
          onClick={handleClear}
          className="absolute top-1.5 right-1.5 text-[10px] font-medium text-gray-500 hover:text-gray-800 bg-white/80 hover:bg-white px-1.5 py-0.5 rounded transition-colors duration-150"
        >
          Clear
        </button>
      </div>
      {/* Typed-name fallback */}
      <input
        type="text"
        value={typedName}
        onChange={handleTypedName}
        placeholder="or type name as text fallback…"
        className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-100 placeholder-gray-500 focus:outline-none focus:border-blue-500/70 focus:ring-1 focus:ring-blue-500/30 transition-colors duration-150"
      />
    </div>
  );
}

// ─── Individual field card ────────────────────────────────────────────────────

interface FieldCardProps {
  field: DetectedField;
  value: string;
  isActive: boolean;
  profiles: DataProfile[];
  cardRef: (el: HTMLDivElement | null) => void;
  inputRef: (el: HTMLInputElement | HTMLTextAreaElement | null) => void;
  onValueChange: (value: string) => void;
  onFocus: () => void;
}

function FieldCard({
  field,
  value,
  isActive,
  profiles,
  cardRef,
  inputRef,
  onValueChange,
  onFocus,
}: FieldCardProps) {
  // Profiles that have a value for this field's profileKey
  const profileMatches =
    field.profileKey
      ? profiles.filter((p) => {
          const v = p.data[field.profileKey as string];
          return v !== undefined && v !== '';
        })
      : [];

  const sharedInputClass = `
    flex-1 min-w-0 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2
    text-sm text-gray-100 placeholder-gray-500
    focus:outline-none focus:border-blue-500/70 focus:ring-1 focus:ring-blue-500/30
    transition-colors duration-150
    disabled:opacity-50 disabled:cursor-not-allowed
  `;

  const renderInput = () => {
    if (field.type === 'checkbox') {
      return (
        <div className="flex items-center gap-3">
          <ToggleSwitch
            checked={value === 'true'}
            onChange={(checked) => onValueChange(checked ? 'true' : 'false')}
          />
          <span className="text-sm text-gray-400">
            {value === 'true' ? 'Checked' : 'Unchecked'}
          </span>
        </div>
      );
    }

    if (field.type === 'signature') {
      return (
        <SignatureCanvas
          value={value}
          onChange={onValueChange}
        />
      );
    }

    if (field.type === 'textarea') {
      return (
        <textarea
          ref={inputRef as (el: HTMLTextAreaElement | null) => void}
          value={value}
          rows={3}
          placeholder="Enter value…"
          className={`${sharedInputClass} resize-none`}
          onChange={(e) => onValueChange(e.target.value)}
          onFocus={onFocus}
        />
      );
    }

    if (field.type === 'date') {
      return (
        <input
          ref={inputRef as (el: HTMLInputElement | null) => void}
          type="date"
          value={value}
          className={`${sharedInputClass} [color-scheme:dark]`}
          onChange={(e) => onValueChange(e.target.value)}
          onFocus={onFocus}
        />
      );
    }

    if (field.type === 'currency') {
      return (
        <div className="flex flex-1 items-center min-w-0 relative">
          <span className="absolute left-3 text-sm text-gray-400 select-none pointer-events-none">$</span>
          <input
            ref={inputRef as (el: HTMLInputElement | null) => void}
            type="text"
            inputMode="decimal"
            value={value}
            placeholder="0.00"
            className={`${sharedInputClass} pl-7`}
            onChange={(e) => onValueChange(e.target.value)}
            onFocus={onFocus}
          />
        </div>
      );
    }

    // Default: text
    return (
      <input
        ref={inputRef as (el: HTMLInputElement | null) => void}
        type="text"
        value={value}
        placeholder="Enter value…"
        className={sharedInputClass}
        onChange={(e) => onValueChange(e.target.value)}
        onFocus={onFocus}
      />
    );
  };

  return (
    <div
      ref={cardRef}
      className={`
        bg-gray-900 rounded-xl p-3 mb-2 border transition-colors duration-150
        ${isActive ? 'border-blue-500/50' : 'border-gray-800'}
      `}
    >
      {/* Header row */}
      <div className="flex items-center gap-2 mb-2">
        <span className="flex-1 text-sm font-medium text-gray-200 truncate">
          {field.label}
          {field.required && (
            <span className="ml-1 text-red-400 text-xs" aria-label="Required">*</span>
          )}
        </span>
        <span className={`shrink-0 text-[10px] font-medium px-2 py-0.5 rounded-full ${TYPE_BADGE[field.type]}`}>
          {TYPE_LABEL[field.type]}
        </span>
        {field.confidence === 0 && (
          <span className="text-[10px] text-gray-600 font-medium shrink-0">manual</span>
        )}
        <span className="text-xs text-gray-500 shrink-0">p{field.page}</span>
      </div>

      {/* Input row */}
      <div className="flex items-start gap-2">
        {renderInput()}
        {/* Voice input — not shown for checkbox or disabled signature */}
        {field.type !== 'checkbox' && field.type !== 'signature' && (
          <div className="shrink-0 mt-0.5">
            <VoiceInputButton onResult={(transcript) => onValueChange(transcript)} />
          </div>
        )}
      </div>

      {/* From profile chips */}
      {profileMatches.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1.5 items-center">
          <span className="flex items-center gap-1 text-xs text-gray-500">
            <User size={11} />
            From profile:
          </span>
          {profileMatches.map((profile) => {
            const profileValue = profile.data[field.profileKey as string];
            return (
              <button
                key={profile.id}
                type="button"
                onClick={() => onValueChange(profileValue)}
                className="text-xs bg-gray-800 hover:bg-gray-700 rounded-full px-2 py-0.5 cursor-pointer text-gray-300 transition-colors duration-150 max-w-[200px] truncate"
                title={`${profile.name}: "${profileValue}"`}
              >
                {profile.name}: &ldquo;{profileValue}&rdquo;
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}

// ─── SmartFillPanel ───────────────────────────────────────────────────────────

export function SmartFillPanel({
  fields,
  values,
  activeFieldId,
  profiles,
  onValueChange,
  onFieldFocus,
  onGenerate,
  isGenerating,
  onFieldsChange,
  detectionMethod,
}: SmartFillPanelProps) {
  const cardRefs = useRef<Record<string, HTMLDivElement | null>>({});
  const inputRefs = useRef<Record<string, HTMLInputElement | HTMLTextAreaElement | null>>({});

  const [isAddingField, setIsAddingField] = useState(false);
  const [newLabel, setNewLabel] = useState('');
  const [newType, setNewType] = useState<DetectedField['type']>('text');
  const [isAutoFilling, setIsAutoFilling] = useState(false);

  const setCardRef = useCallback(
    (id: string) => (el: HTMLDivElement | null) => {
      cardRefs.current[id] = el;
    },
    []
  );

  const setInputRef = useCallback(
    (id: string) => (el: HTMLInputElement | HTMLTextAreaElement | null) => {
      inputRefs.current[id] = el;
    },
    []
  );

  const handleAddField = useCallback(() => {
    const trimmed = newLabel.trim();
    if (!trimmed || !onFieldsChange) return;
    const id = `manual_${trimmed.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '').slice(0, 50)}_${Date.now()}`;
    const newField: DetectedField = {
      id,
      label: trimmed,
      type: newType,
      page: 1,
      bbox: { x: 0.05, y: 0, w: 0.90, h: 0.05 },
      required: false,
      value: '',
      confidence: 0,
    };
    onFieldsChange([...fields, newField]);
    setNewLabel('');
    setNewType('text');
    setIsAddingField(false);
  }, [fields, newLabel, newType, onFieldsChange]);

  const handleAutoFill = useCallback(async () => {
    if (profiles.length === 0 || isAutoFilling) return;
    const profile = profiles.find((p) => p.isDefault) ?? profiles[0];
    setIsAutoFilling(true);
    try {
      const res = await fetch('/api/forms/auto-fill', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fields, profileData: profile.data }),
      });
      if (!res.ok) return;
      const { values: suggested } = (await res.json()) as { values: Record<string, string> };
      for (const [fieldId, value] of Object.entries(suggested)) {
        if (value) onValueChange(fieldId, value);
      }
    } catch {
      // silently do nothing
    } finally {
      setIsAutoFilling(false);
    }
  }, [fields, profiles, isAutoFilling, onValueChange]);

  // Scroll active card into view and focus its input
  useEffect(() => {
    if (!activeFieldId) return;
    const card = cardRefs.current[activeFieldId];
    if (card) {
      card.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
    const input = inputRefs.current[activeFieldId];
    if (input) {
      input.focus({ preventScroll: true });
    }
  }, [activeFieldId]);

  const filled = fields.filter((f) => values[f.id]?.trim()).length;
  const total = fields.length;
  const progressPct = total > 0 ? (filled / total) * 100 : 0;
  const hasAnyValue = filled > 0;

  // ── Empty state ──
  if (fields.length === 0) {
    return (
      <div className="flex flex-col h-full bg-gray-950 text-gray-200">
        <div className="flex-1 flex flex-col items-center justify-center gap-3 px-6">
          <div className="w-12 h-12 rounded-full bg-gray-800 flex items-center justify-center">
            <FileText size={22} className="text-gray-500" />
          </div>
          <p className="text-sm text-gray-500 text-center">No fields detected yet.</p>
          {onFieldsChange && !isAddingField && (
            <button
              type="button"
              onClick={() => setIsAddingField(true)}
              className="text-sm text-[#5856D6] hover:text-[#4644C4] font-medium transition-colors duration-150"
            >
              + Add a field manually
            </button>
          )}
        </div>
        {isAddingField && onFieldsChange && (
          <div className="shrink-0 px-3 pt-3 pb-4 border-t border-gray-800 space-y-2">
            <p className="text-xs font-medium text-gray-400">New field</p>
            <input
              autoFocus
              type="text"
              value={newLabel}
              onChange={(e) => setNewLabel(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleAddField();
                if (e.key === 'Escape') { setIsAddingField(false); setNewLabel(''); }
              }}
              placeholder="Field label…"
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-100 placeholder-gray-500 focus:outline-none focus:border-[#5856D6]/70 focus:ring-1 focus:ring-[#5856D6]/30 transition-colors duration-150"
            />
            <div className="flex items-center gap-2">
              <select
                value={newType}
                onChange={(e) => setNewType(e.target.value as DetectedField['type'])}
                className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-2 py-2 text-sm text-gray-100 focus:outline-none focus:border-[#5856D6]/70 transition-colors duration-150"
              >
                {(['text', 'textarea', 'date', 'currency', 'checkbox', 'signature'] as DetectedField['type'][]).map((t) => (
                  <option key={t} value={t}>{TYPE_LABEL[t]}</option>
                ))}
              </select>
              <button
                type="button"
                onClick={() => { setIsAddingField(false); setNewLabel(''); }}
                className="px-3 py-2 text-xs text-gray-400 hover:text-gray-200 rounded-lg transition-colors duration-150"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleAddField}
                disabled={!newLabel.trim()}
                className="px-3 py-2 text-xs font-medium text-white bg-[#5856D6] hover:bg-[#4644C4] disabled:opacity-40 disabled:cursor-not-allowed rounded-lg transition-colors duration-150"
              >
                Add
              </button>
            </div>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-gray-950 text-gray-200">
      {/* Progress section */}
      <div className="px-4 pt-4 pb-3 border-b border-gray-800 shrink-0">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-medium text-gray-300">
            {filled} of {total} field{total !== 1 ? 's' : ''} filled
          </span>
          <div className="flex items-center gap-3">
            <span className="text-xs text-gray-500">{Math.round(progressPct)}%</span>
            {profiles.length > 0 && (
              <button
                type="button"
                onClick={handleAutoFill}
                disabled={isAutoFilling}
                className="text-xs font-medium text-[#5856D6] hover:text-[#4644C4] flex items-center gap-1 transition-colors duration-150 disabled:opacity-40 disabled:cursor-not-allowed"
              >
                {isAutoFilling ? (
                  <>
                    <Loader2 size={11} className="animate-spin" />
                    Filling…
                  </>
                ) : (
                  <>
                    <Sparkles size={11} />
                    Auto-fill
                  </>
                )}
              </button>
            )}
          </div>
        </div>
        <div className="h-1 w-full bg-gray-800 rounded-full overflow-hidden">
          <div
            className="h-full bg-blue-500 rounded-full transition-all duration-300 ease-out"
            style={{ width: `${progressPct}%` }}
          />
        </div>
      </div>

      {/* Scrollable field list */}
      <div className="flex-1 overflow-y-auto px-3 pt-3 pb-2">
        {fields.map((field) => (
          <FieldCard
            key={field.id}
            field={field}
            value={values[field.id] ?? ''}
            isActive={activeFieldId === field.id}
            profiles={profiles}
            cardRef={setCardRef(field.id)}
            inputRef={setInputRef(field.id)}
            onValueChange={(val) => onValueChange(field.id, val)}
            onFocus={() => onFieldFocus(field.id)}
          />
        ))}
        {onFieldsChange && !isAddingField && (
          <div className="pt-2 pb-1">
            <button
              type="button"
              onClick={() => setIsAddingField(true)}
              className="w-full flex items-center justify-center gap-1.5 py-2 text-xs font-medium text-gray-500 hover:text-[#5856D6] rounded-lg hover:bg-gray-900 transition-colors duration-150 border border-dashed border-gray-800 hover:border-[#5856D6]/40"
            >
              <Plus size={13} />
              Add Field
            </button>
          </div>
        )}
      </div>

      {/* Inline add-field form */}
      {isAddingField && onFieldsChange && (
        <div className="shrink-0 px-3 pt-3 pb-2 border-t border-gray-800 bg-gray-950 space-y-2">
          <p className="text-xs font-medium text-gray-400">New field</p>
          <input
            autoFocus
            type="text"
            value={newLabel}
            onChange={(e) => setNewLabel(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') handleAddField();
              if (e.key === 'Escape') { setIsAddingField(false); setNewLabel(''); }
            }}
            placeholder="Field label…"
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-100 placeholder-gray-500 focus:outline-none focus:border-[#5856D6]/70 focus:ring-1 focus:ring-[#5856D6]/30 transition-colors duration-150"
          />
          <div className="flex items-center gap-2">
            <select
              value={newType}
              onChange={(e) => setNewType(e.target.value as DetectedField['type'])}
              className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-2 py-2 text-sm text-gray-100 focus:outline-none focus:border-[#5856D6]/70 transition-colors duration-150"
            >
              {(['text', 'textarea', 'date', 'currency', 'checkbox', 'signature'] as DetectedField['type'][]).map((t) => (
                <option key={t} value={t}>{TYPE_LABEL[t]}</option>
              ))}
            </select>
            <button
              type="button"
              onClick={() => { setIsAddingField(false); setNewLabel(''); }}
              className="px-3 py-2 text-xs text-gray-400 hover:text-gray-200 rounded-lg transition-colors duration-150"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleAddField}
              disabled={!newLabel.trim()}
              className="px-3 py-2 text-xs font-medium text-white bg-[#5856D6] hover:bg-[#4644C4] disabled:opacity-40 disabled:cursor-not-allowed rounded-lg transition-colors duration-150"
            >
              Add
            </button>
          </div>
        </div>
      )}

      {/* Sticky generate button */}
      <div className="shrink-0 px-3 pb-4 pt-2 border-t border-gray-800">
        <button
          type="button"
          onClick={onGenerate}
          disabled={!hasAnyValue || isGenerating}
          className={`
            w-full flex items-center justify-center gap-2
            bg-blue-600 hover:bg-blue-500 disabled:opacity-40 disabled:cursor-not-allowed
            text-white rounded-xl py-3 font-medium text-sm
            transition-colors duration-150
          `}
        >
          {isGenerating && <Loader2 size={16} className="animate-spin" />}
          {isGenerating ? 'Generating…' : 'Generate Filled PDF'}
        </button>
      </div>

      {/* Detection method badge */}
      {detectionMethod && detectionMethod !== 'empty' && (
        <div className="shrink-0 px-3 py-2 flex items-center justify-center gap-1.5">
          {detectionMethod === 'docai' ? (
            <>
              <Sparkles size={11} className="text-blue-500" />
              <span className="text-[10px] text-gray-600">Detected via Google Document AI</span>
            </>
          ) : detectionMethod === 'acroform' ? (
            <>
              <FileText size={11} className="text-green-600" />
              <span className="text-[10px] text-gray-600">Detected via native form fields</span>
            </>
          ) : detectionMethod === 'vision' ? (
            <>
              <Sparkles size={11} className="text-blue-500" />
              <span className="text-[10px] text-gray-600">Detected via AI vision</span>
            </>
          ) : (
            <>
              <FileText size={11} className="text-green-600" />
              <span className="text-[10px] text-gray-600">Detected via OCR</span>
            </>
          )}
        </div>
      )}
    </div>
  );
}
