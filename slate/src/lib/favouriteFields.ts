import type { FieldEntry } from '@/components/fill/FieldsPanel';

export interface FavouriteField {
  id: string;
  fieldName: string;
  fieldType: FieldEntry['fieldType'];
  value: string;
  savedAt: string;
}

const KEY = 'slate_favourite_fields';

export function getFavourites(): FavouriteField[] {
  if (typeof window === 'undefined') return [];
  try {
    const raw = localStorage.getItem(KEY);
    return raw ? (JSON.parse(raw) as FavouriteField[]) : [];
  } catch {
    return [];
  }
}

export function saveFavourite(field: FieldEntry): void {
  const current = getFavourites();
  const normName = field.fieldName.trim().toLowerCase();
  const existing = current.findIndex((f) => f.fieldName.trim().toLowerCase() === normName);
  const entry: FavouriteField = {
    id: existing >= 0 ? current[existing].id : `fav_${Date.now()}`,
    fieldName: field.fieldName.trim(),
    fieldType: field.fieldType,
    value: field.value,
    savedAt: new Date().toISOString(),
  };
  const updated = existing >= 0
    ? current.map((f, i) => (i === existing ? entry : f))
    : [entry, ...current];
  localStorage.setItem(KEY, JSON.stringify(updated));
}

export function removeFavourite(id: string): void {
  const updated = getFavourites().filter((f) => f.id !== id);
  localStorage.setItem(KEY, JSON.stringify(updated));
}

export function isFavourite(fieldName: string): boolean {
  const normName = fieldName.trim().toLowerCase();
  return getFavourites().some((f) => f.fieldName.trim().toLowerCase() === normName);
}
