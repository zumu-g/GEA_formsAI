export interface FillHistoryEntry {
  id: string;           // UUID
  formName: string;     // filename of uploaded PDF
  instructions: string; // first 120 chars of instructions
  timestamp: number;    // Date.now()
  status: 'complete' | 'error';
  fieldsFilled?: number; // from complete event data.fields_filled
  formId: string;       // original formId (for reference)
}

const KEY = 'slate_fill_history';
const MAX_ENTRIES = 50;

function generateId(): string {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return Math.random().toString(36).slice(2) + Date.now().toString(36);
}

export function addFillEntry(entry: Omit<FillHistoryEntry, 'id'>): void {
  if (typeof window === 'undefined') return;

  const history = getFillHistory();
  const newEntry: FillHistoryEntry = { ...entry, id: generateId() };

  // Prepend newest entry, then cap at MAX_ENTRIES
  const updated = [newEntry, ...history].slice(0, MAX_ENTRIES);

  try {
    localStorage.setItem(KEY, JSON.stringify(updated));
  } catch {
    // Storage may be full — silently ignore
  }
}

export function getFillHistory(): FillHistoryEntry[] {
  if (typeof window === 'undefined') return [];

  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export function clearFillHistory(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(KEY);
}
