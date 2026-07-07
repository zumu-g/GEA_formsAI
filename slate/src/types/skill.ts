export interface SkillField {
  id: string;
  label: string;
  type: 'text' | 'date' | 'currency' | 'checkbox' | 'textarea' | 'email' | 'phone';
  placeholder?: string;
  required?: boolean;
  computed?: boolean;
  validation?: {
    pattern?: string;
    patternMessage?: string;
    minLength?: number;
    maxLength?: number;
  };
  helpText?: string;
  defaultValue?: string;
  profileKey?: string;
}

export interface SkillSection {
  id: string;
  title: string;
  description?: string;
  fields: SkillField[];
}

export interface SkillFieldMapping {
  skillFieldId: string;
  pdfFieldName: string;
  transform?: 'uppercase' | 'lowercase' | 'date_au' | 'currency_au';
}

export interface SkillComputedField {
  skillFieldId: string;
  formula: 'subtract' | 'add_days';
  operands: string[];
  pdfFieldName: string;
  /** Day offset used by the 'add_days' formula (operands[0] is the source date field). */
  days?: number;
}

export interface PdfmeFieldMapping {
  skillFieldId: string;
  schemaName: string;
  page: number;
  position: { x: number; y: number };
  width: number;
  height: number;
  type: 'text' | 'checkbox';
  fontSize?: number;
  alignment?: 'left' | 'center' | 'right';
  transform?: 'uppercase' | 'lowercase' | 'date_au' | 'currency_au';
}

export interface SkillDefinition {
  id: string;
  name: string;
  description: string;
  icon: string;
  version: string;
  jurisdiction?: string;
  documentType: string;
  formTemplateUrl?: string; // URL to download a blank version of this form
  sections: SkillSection[];
  fieldMappings: SkillFieldMapping[];
  computedFields?: SkillComputedField[];
  pdfmeFieldMappings?: PdfmeFieldMapping[];
  /** Unverified skills are researched-not-verbatim: field content isn't confirmed against a real signed form. Absent means verified (existing skills). */
  draftStatus?: 'unverified' | 'verified';
}

export interface SkillSession {
  skillId: string;
  currentSectionIndex: number;
  values: Record<string, string>;
  completedSections: string[];
  formId?: string;
  status: 'upload' | 'in_progress' | 'review' | 'filling' | 'complete' | 'error';
}
