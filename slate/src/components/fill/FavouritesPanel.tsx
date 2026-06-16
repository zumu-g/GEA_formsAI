'use client';

import { useState } from 'react';
import { Star, X, GripVertical, ChevronDown, ChevronRight } from 'lucide-react';
import type { FavouriteField } from '@/lib/favouriteFields';

const TYPE_COLOURS: Record<FavouriteField['fieldType'], string> = {
  text: 'bg-[#F5F5F7] text-[#86868B]',
  checkbox: 'bg-blue-50 text-blue-600',
  date: 'bg-purple-50 text-purple-600',
  dropdown: 'bg-orange-50 text-orange-600',
  signature: 'bg-red-50 text-red-600',
  radio: 'bg-green-50 text-green-600',
};

interface FavouritesPanelProps {
  favourites: FavouriteField[];
  onRemove: (id: string) => void;
}

export function FavouritesPanel({ favourites, onRemove }: FavouritesPanelProps) {
  // Default collapsed when there's nothing saved — keep it out of the way until used.
  const [collapsed, setCollapsed] = useState(favourites.length === 0);

  const handleDragStart = (e: React.DragEvent, fav: FavouriteField) => {
    e.dataTransfer.setData('application/slate-favourite', JSON.stringify(fav));
    e.dataTransfer.effectAllowed = 'copy';
  };

  return (
    <div className="rounded-xl border border-[#E5E5EA] bg-white flex flex-col overflow-hidden">
      {/* Header */}
      <button
        onClick={() => setCollapsed((v) => !v)}
        className="flex items-center justify-between px-3 py-2.5 border-b border-[#F5F5F7] w-full text-left hover:bg-[#FAFAFA] transition-colors"
      >
        <div className="flex items-center gap-2">
          <Star size={13} className="text-amber-400 fill-amber-400" />
          <span className="text-xs font-semibold text-[#1D1D1F]">Favourites</span>
          {favourites.length > 0 && (
            <span className="text-[10px] font-medium bg-amber-100 text-amber-600 px-1.5 py-0.5 rounded-full">
              {favourites.length}
            </span>
          )}
        </div>
        {collapsed ? (
          <ChevronRight size={13} className="text-[#AEAEB2]" />
        ) : (
          <ChevronDown size={13} className="text-[#AEAEB2]" />
        )}
      </button>

      {!collapsed && (
        <div className="max-h-48 overflow-y-auto">
          {favourites.length === 0 ? (
            <div className="py-4 px-3 text-center">
              <p className="text-xs text-[#86868B]">No favourites yet.</p>
              <p className="mt-0.5 text-[11px] text-[#AEAEB2]">
                Star a field below to save it here.
              </p>
            </div>
          ) : (
            <div className="px-2 py-1">
              {favourites.map((fav) => (
                <div
                  key={fav.id}
                  draggable
                  onDragStart={(e) => handleDragStart(e, fav)}
                  className="group flex items-center gap-1.5 py-1.5 px-1 rounded-lg hover:bg-[#F5F5F7] cursor-grab active:cursor-grabbing transition-colors"
                >
                  <GripVertical size={12} className="text-[#C7C7CC] shrink-0" />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1.5">
                      <span className="text-xs font-medium text-[#1D1D1F] truncate">
                        {fav.fieldName}
                      </span>
                      <span
                        className={`shrink-0 text-[10px] font-medium px-1.5 py-0.5 rounded-full ${TYPE_COLOURS[fav.fieldType]}`}
                      >
                        {fav.fieldType}
                      </span>
                    </div>
                    {fav.value && (
                      <p className="text-[11px] text-[#86868B] truncate mt-0.5">{fav.value}</p>
                    )}
                  </div>
                  <button
                    onClick={() => onRemove(fav.id)}
                    className="p-0.5 rounded text-[#C7C7CC] hover:text-red-500 hover:bg-red-50 transition-colors opacity-0 group-hover:opacity-100 shrink-0"
                    aria-label={`Remove ${fav.fieldName} from favourites`}
                  >
                    <X size={11} />
                  </button>
                </div>
              ))}
            </div>
          )}
          {favourites.length > 0 && (
            <p className="px-3 pb-2 text-[10px] text-[#AEAEB2] text-center">
              Drag a favourite onto the fields list to add it
            </p>
          )}
        </div>
      )}
    </div>
  );
}
