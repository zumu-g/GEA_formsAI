'use client';

import { useState, useCallback } from 'react';
import { Plus, X, Loader2, Sparkles, Star } from 'lucide-react';
import type { DetectionMethod } from '@/types/smartFill';
import type { FavouriteField } from '@/lib/favouriteFields';

export interface FieldEntry {
  id: string;
  fieldName: string;
  fieldType: 'text' | 'checkbox' | 'date' | 'radio' | 'signature' | 'dropdown';
  value: string;
  manual: boolean;
  pageNumber?: number;
}

const METHOD_LABELS: Partial<Record<DetectionMethod, string>> = {
  acroform: 'AcroForm',
  pdfplumber: 'pdfplumber',
  commonforms: 'CommonForms',
  docai: 'Document AI',
  docling: 'Docling',
  vision: 'AI Vision',
  zerox: 'OCR',
};

interface FieldsPanelProps {
  fields: FieldEntry[];
  isDetecting: boolean;
  detectionMethod?: DetectionMethod;
  onChange: (fields: FieldEntry[]) => void;
  onAddToFavourite?: (field: FieldEntry) => void;
  isFavourite?: (fieldName: string) => boolean;
  onDropFavourite?: (fav: FavouriteField) => void;
}

const TYPE_OPTIONS: FieldEntry['fieldType'][] = ['text', 'checkbox', 'date', 'dropdown', 'signature', 'radio'];

const TYPE_COLOURS: Record<FieldEntry['fieldType'], string> = {
  text: 'bg-[#F2F4F7] text-[#767A85]',
  checkbox: 'bg-blue-50 text-blue-600',
  date: 'bg-purple-50 text-purple-600',
  dropdown: 'bg-orange-50 text-orange-600',
  signature: 'bg-red-50 text-red-600',
  radio: 'bg-green-50 text-green-600',
};

function FieldRow({
  field,
  isFav,
  onValueChange,
  onRemove,
  onAddToFavourite,
}: {
  field: FieldEntry;
  isFav: boolean;
  onValueChange: (id: string, value: string) => void;
  onRemove: (id: string) => void;
  onAddToFavourite?: (field: FieldEntry) => void;
}) {
  return (
    <div className="group flex items-start gap-2 py-2 border-b border-[#F2F4F7] last:border-0">
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5 mb-1">
          <span className="text-xs font-medium text-[#1B1D24] truncate">{field.fieldName}</span>
          <span className={`shrink-0 text-[10px] font-medium px-1.5 py-0.5 rounded-full ${TYPE_COLOURS[field.fieldType]}`}>
            {field.fieldType}
          </span>
          {field.pageNumber != null && (
            <span className="shrink-0 text-[10px] text-[#A2A6B0]">p{field.pageNumber}</span>
          )}
        </div>
        {field.fieldType === 'checkbox' ? (
          <label className="flex items-center gap-1.5 cursor-pointer">
            <input
              type="checkbox"
              checked={field.value === 'true'}
              onChange={(e) => onValueChange(field.id, e.target.checked ? 'true' : 'false')}
              className="w-3.5 h-3.5 rounded accent-[#5856D6]"
            />
            <span className="text-xs text-[#767A85]">{field.value === 'true' ? 'Checked' : 'Unchecked'}</span>
          </label>
        ) : (
          <input
            type={field.fieldType === 'date' ? 'date' : 'text'}
            value={field.value}
            onChange={(e) => onValueChange(field.id, e.target.value)}
            placeholder="Enter value…"
            className="w-full text-xs px-2 py-1 rounded-md border border-[#E2E4EA] bg-[#F8F9FB] text-[#1B1D24] placeholder-[#C4C8D1] focus:outline-none focus:border-[#5856D6] focus:bg-white transition-colors"
          />
        )}
      </div>
      <div className="mt-1 flex items-center gap-0.5">
        {onAddToFavourite && (
          <button
            onClick={() => onAddToFavourite(field)}
            className={`p-0.5 rounded transition-colors ${
              isFav
                ? 'text-amber-400'
                : 'text-[#C4C8D1] hover:text-amber-400 opacity-0 group-hover:opacity-100'
            }`}
            aria-label={isFav ? 'Remove from favourites' : 'Add to favourites'}
            title={isFav ? 'Remove from favourites' : 'Save to favourites'}
          >
            <Star size={12} className={isFav ? 'fill-amber-400' : ''} />
          </button>
        )}
        <button
          onClick={() => onRemove(field.id)}
          className="p-0.5 rounded text-[#C4C8D1] hover:text-red-500 hover:bg-red-50 transition-colors opacity-0 group-hover:opacity-100"
          aria-label="Remove field"
          title="Remove field"
        >
          <X size={12} />
        </button>
      </div>
    </div>
  );
}

export function FieldsPanel({
  fields,
  isDetecting,
  detectionMethod,
  onChange,
  onAddToFavourite,
  isFavourite,
  onDropFavourite,
}: FieldsPanelProps) {
  const [isAdding, setIsAdding] = useState(false);
  const [newName, setNewName] = useState('');
  const [newType, setNewType] = useState<FieldEntry['fieldType']>('text');
  const [isDragOver, setIsDragOver] = useState(false);

  const handleValueChange = useCallback(
    (id: string, value: string) => {
      onChange(fields.map((f) => (f.id === id ? { ...f, value } : f)));
    },
    [fields, onChange]
  );

  const handleRemove = useCallback(
    (id: string) => {
      onChange(fields.filter((f) => f.id !== id));
    },
    [fields, onChange]
  );

  const handleAdd = useCallback(() => {
    const trimmed = newName.trim();
    if (!trimmed) return;
    const newField: FieldEntry = {
      id: `manual_${Date.now()}`,
      fieldName: trimmed,
      fieldType: newType,
      value: '',
      manual: true,
    };
    onChange([...fields, newField]);
    setNewName('');
    setNewType('text');
    setIsAdding(false);
  }, [fields, newName, newType, onChange]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    if (e.dataTransfer.types.includes('application/slate-favourite')) {
      e.preventDefault();
      setIsDragOver(true);
    }
  }, []);

  const handleDragLeave = useCallback(() => setIsDragOver(false), []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragOver(false);
      const raw = e.dataTransfer.getData('application/slate-favourite');
      if (!raw || !onDropFavourite) return;
      try {
        onDropFavourite(JSON.parse(raw));
      } catch {
        // malformed drag data — ignore
      }
    },
    [onDropFavourite]
  );

  return (
    <div
      className={`rounded-xl border bg-white flex flex-col overflow-hidden transition-colors ${
        isDragOver ? 'border-[#5856D6] border-dashed bg-[#5856D6]/5' : 'border-[#E2E4EA]'
      }`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2.5 border-b border-[#F2F4F7]">
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-[#1B1D24]">Form Fields</span>
          {isDetecting ? (
            <span className="flex items-center gap-1 text-[10px] text-[#5856D6]">
              <Loader2 size={10} className="animate-spin" />
              Detecting…
            </span>
          ) : fields.length > 0 ? (
            <span className="text-[10px] font-medium bg-[#5856D6]/10 text-[#5856D6] px-1.5 py-0.5 rounded-full">
              {fields.length}
            </span>
          ) : null}
          {!isDetecting && detectionMethod && detectionMethod !== 'empty' && fields.length > 0 && (
            <span className="flex items-center gap-0.5 text-[10px] text-[#A2A6B0]">
              <Sparkles size={9} />
              {METHOD_LABELS[detectionMethod] ?? detectionMethod}
            </span>
          )}
        </div>
        <button
          onClick={() => setIsAdding((v) => !v)}
          className="flex items-center gap-1 text-[11px] font-medium text-[#5856D6] hover:text-[#4644C4] transition-colors"
        >
          <Plus size={12} />
          Add Field
        </button>
      </div>

      {/* Field list */}
      <div className="flex-1 overflow-y-auto max-h-64 px-3">
        {isDetecting && fields.length === 0 ? (
          <div className="py-4 space-y-2">
            {[1, 2, 3].map((i) => (
              <div key={i} className="animate-pulse">
                <div className="h-2.5 bg-[#F2F4F7] rounded w-2/3 mb-1.5" />
                <div className="h-6 bg-[#F2F4F7] rounded w-full" />
              </div>
            ))}
          </div>
        ) : fields.length === 0 ? (
          <div className="py-5 text-center">
            <p className="text-xs text-[#767A85]">No fields detected automatically.</p>
            <p className="mt-0.5 text-[11px] text-[#A2A6B0]">Draw fields on the PDF or describe them to the AI.</p>
            <button
              onClick={() => setIsAdding(true)}
              className="mt-2 text-xs text-[#5856D6] hover:underline"
            >
              Add fields manually
            </button>
          </div>
        ) : (
          <div>
            {fields.map((f) => (
              <FieldRow
                key={f.id}
                field={f}
                isFav={isFavourite ? isFavourite(f.fieldName) : false}
                onValueChange={handleValueChange}
                onRemove={handleRemove}
                onAddToFavourite={onAddToFavourite}
              />
            ))}
          </div>
        )}
      </div>

      {/* Add Field inline form */}
      {isAdding && (
        <div className="border-t border-[#F2F4F7] px-3 py-2.5 bg-[#F8F9FB] space-y-2">
          <input
            autoFocus
            type="text"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') handleAdd();
              if (e.key === 'Escape') setIsAdding(false);
            }}
            placeholder="Field name…"
            className="w-full text-xs px-2.5 py-1.5 rounded-lg border border-[#E2E4EA] bg-white text-[#1B1D24] placeholder-[#C4C8D1] focus:outline-none focus:border-[#5856D6] transition-colors"
          />
          <div className="flex items-center gap-2">
            <select
              value={newType}
              onChange={(e) => setNewType(e.target.value as FieldEntry['fieldType'])}
              className="flex-1 text-xs px-2 py-1.5 rounded-lg border border-[#E2E4EA] bg-white text-[#1B1D24] focus:outline-none focus:border-[#5856D6] transition-colors"
            >
              {TYPE_OPTIONS.map((t) => (
                <option key={t} value={t}>
                  {t.charAt(0).toUpperCase() + t.slice(1)}
                </option>
              ))}
            </select>
            <button
              onClick={() => setIsAdding(false)}
              className="px-2.5 py-1.5 text-xs text-[#767A85] hover:text-[#1B1D24] transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleAdd}
              disabled={!newName.trim()}
              className="px-3 py-1.5 text-xs font-medium text-white bg-[#5856D6] rounded-lg hover:bg-[#4644C4] disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              Add
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
