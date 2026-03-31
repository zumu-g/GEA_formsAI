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
  formula: 'subtract';
  operands: string[];
  pdfFieldName: string;
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
  sections: SkillSection[];
  fieldMappings: SkillFieldMapping[];
  computedFields?: SkillComputedField[];
  pdfmeFieldMappings?: PdfmeFieldMapping[];
}

export interface SkillSession {
  skillId: string;
  currentSectionIndex: number;
  values: Record<string, string>;
  completedSections: string[];
  formId?: string;
  status: 'upload' | 'in_progress' | 'review' | 'filling' | 'complete' | 'error';
}
