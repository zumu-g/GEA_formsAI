import { create } from 'zustand';
import type { SkillSession } from '@/types/skill';
import { getSkillById } from '@/lib/skills';

interface SkillState {
  session: SkillSession | null;
  startSession: (skillId: string) => void;
  setFormId: (formId: string) => void;
  setValue: (fieldId: string, value: string) => void;
  setValues: (values: Record<string, string>) => void;
  goToSection: (index: number) => void;
  nextSection: () => void;
  prevSection: () => void;
  markSectionComplete: (sectionId: string) => void;
  setStatus: (status: SkillSession['status']) => void;
  reset: () => void;
}

export const useSkillStore = create<SkillState>((set, get) => ({
  session: null,

  startSession: (skillId) => {
    set({
      session: {
        skillId,
        currentSectionIndex: 0,
        values: {},
        completedSections: [],
        status: 'upload',
      },
    });
  },

  setFormId: (formId) => {
    const { session } = get();
    if (!session) return;
    set({ session: { ...session, formId, status: 'in_progress' } });
  },

  setValue: (fieldId, value) => {
    const { session } = get();
    if (!session) return;
    set({
      session: {
        ...session,
        values: { ...session.values, [fieldId]: value },
      },
    });
  },

  setValues: (values) => {
    const { session } = get();
    if (!session) return;
    set({
      session: {
        ...session,
        values: { ...session.values, ...values },
      },
    });
  },

  goToSection: (index) => {
    const { session } = get();
    if (!session) return;
    const skill = getSkillById(session.skillId);
    if (!skill) return;
    if (index >= 0 && index < skill.sections.length) {
      set({ session: { ...session, currentSectionIndex: index } });
    }
  },

  nextSection: () => {
    const { session } = get();
    if (!session) return;
    const skill = getSkillById(session.skillId);
    if (!skill) return;
    const next = session.currentSectionIndex + 1;
    if (next < skill.sections.length) {
      set({ session: { ...session, currentSectionIndex: next } });
    }
  },

  prevSection: () => {
    const { session } = get();
    if (!session) return;
    const prev = session.currentSectionIndex - 1;
    if (prev >= 0) {
      set({ session: { ...session, currentSectionIndex: prev } });
    }
  },

  markSectionComplete: (sectionId) => {
    const { session } = get();
    if (!session) return;
    if (!session.completedSections.includes(sectionId)) {
      set({
        session: {
          ...session,
          completedSections: [...session.completedSections, sectionId],
        },
      });
    }
  },

  setStatus: (status) => {
    const { session } = get();
    if (!session) return;
    set({ session: { ...session, status } });
  },

  reset: () => set({ session: null }),
}));
