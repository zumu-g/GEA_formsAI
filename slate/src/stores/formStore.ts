import { create } from 'zustand';
import type { Form, FormField } from '@/types/form';

interface FormState {
  currentForm: Form | null;
  fields: FormField[];
  selectedFieldId: string | null;
  currentPage: number;
  isDetecting: boolean;
  isFilling: boolean;

  setCurrentForm: (form: Form | null) => void;
  setFields: (fields: FormField[]) => void;
  addField: (field: FormField) => void;
  updateField: (id: string, updates: Partial<FormField>) => void;
  removeField: (id: string) => void;
  selectField: (id: string | null) => void;
  setCurrentPage: (page: number) => void;
  setIsDetecting: (detecting: boolean) => void;
  setIsFilling: (filling: boolean) => void;
  reset: () => void;
}

export const useFormStore = create<FormState>((set) => ({
  currentForm: null,
  fields: [],
  selectedFieldId: null,
  currentPage: 1,
  isDetecting: false,
  isFilling: false,

  setCurrentForm: (form) => set({ currentForm: form }),
  setFields: (fields) => set({ fields }),
  addField: (field) => set((state) => ({ fields: [...state.fields, field] })),
  updateField: (id, updates) =>
    set((state) => ({
      fields: state.fields.map((f) => (f.id === id ? { ...f, ...updates } : f)),
    })),
  removeField: (id) =>
    set((state) => ({ fields: state.fields.filter((f) => f.id !== id) })),
  selectField: (id) => set({ selectedFieldId: id }),
  setCurrentPage: (page) => set({ currentPage: page }),
  setIsDetecting: (detecting) => set({ isDetecting: detecting }),
  setIsFilling: (filling) => set({ isFilling: filling }),
  reset: () =>
    set({
      currentForm: null,
      fields: [],
      selectedFieldId: null,
      currentPage: 1,
      isDetecting: false,
      isFilling: false,
    }),
}));
