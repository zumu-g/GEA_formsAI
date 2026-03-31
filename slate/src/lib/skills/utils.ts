import type { SkillDefinition, SkillSection, PdfmeFieldMapping } from '@/types/skill';
import type { DataProfile } from '@/types/profile';

export function applyComputedFields(
  skill: SkillDefinition,
  values: Record<string, string>
): Record<string, string> {
  const result = { ...values };

  for (const computed of skill.computedFields ?? []) {
    if (computed.formula === 'subtract' && computed.operands.length === 2) {
      const a = parseFloat(values[computed.operands[0]]?.replace(/[^0-9.]/g, '') || '0');
      const b = parseFloat(values[computed.operands[1]]?.replace(/[^0-9.]/g, '') || '0');
      const val = a - b;
      result[computed.skillFieldId] = val > 0 ? val.toFixed(2) : '0.00';
    }
  }

  return result;
}

function applyTransform(value: string, transform?: string): string {
  if (!value) return value;

  switch (transform) {
    case 'uppercase':
      return value.toUpperCase();
    case 'lowercase':
      return value.toLowerCase();
    case 'currency_au': {
      const num = parseFloat(value.replace(/[^0-9.]/g, ''));
      if (isNaN(num)) return value;
      return `$${num.toLocaleString('en-AU', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    }
    case 'date_au':
      // Already expect dd/mm/yyyy, just pass through
      return value;
    default:
      return value;
  }
}

export function mapSkillValuesToPdfFields(
  skill: SkillDefinition,
  values: Record<string, string>
): Record<string, string> {
  const result: Record<string, string> = {};

  for (const mapping of skill.fieldMappings) {
    const rawValue = values[mapping.skillFieldId];
    if (rawValue !== undefined && rawValue !== '') {
      // Only include checkbox values that are 'true' (PDF filler expects only checked fields)
      const skillField = skill.sections
        .flatMap(s => s.fields)
        .find(f => f.id === mapping.skillFieldId);
      if (skillField?.type === 'checkbox' && rawValue !== 'true') continue;

      result[mapping.pdfFieldName] = applyTransform(rawValue, mapping.transform);
    }
  }

  return result;
}

export function validateSection(
  section: SkillSection,
  values: Record<string, string>
): Record<string, string> {
  const errors: Record<string, string> = {};

  for (const field of section.fields) {
    const value = values[field.id] ?? '';

    if (field.computed) continue;

    if (field.type === 'checkbox') {
      if (field.required && value !== 'true') {
        errors[field.id] = `${field.label} must be checked.`;
      }
      continue; // Skip other validations for checkboxes
    }

    if (field.required && !value.trim()) {
      errors[field.id] = `${field.label} is required.`;
      continue;
    }

    if (value && field.validation?.pattern) {
      const regex = new RegExp(field.validation.pattern);
      if (!regex.test(value)) {
        errors[field.id] = field.validation.patternMessage ?? 'Invalid format.';
      }
    }

    if (value && field.validation?.minLength && value.length < field.validation.minLength) {
      errors[field.id] = `Minimum ${field.validation.minLength} characters.`;
    }

    if (value && field.validation?.maxLength && value.length > field.validation.maxLength) {
      errors[field.id] = `Maximum ${field.validation.maxLength} characters.`;
    }

    if (field.type === 'date' && value) {
      const dateRegex = /^\d{2}\/\d{2}\/\d{4}$/;
      if (!dateRegex.test(value)) {
        errors[field.id] = 'Please use dd/mm/yyyy format.';
      }
    }
  }

  return errors;
}

export function mapSkillValuesToPdfmeInputs(
  mappings: PdfmeFieldMapping[],
  values: Record<string, string>,
  sections: SkillSection[]
): Record<string, string> {
  const result: Record<string, string> = {};

  for (const mapping of mappings) {
    const rawValue = values[mapping.skillFieldId];
    if (rawValue !== undefined && rawValue !== '') {
      const skillField = sections
        .flatMap((s) => s.fields)
        .find((f) => f.id === mapping.skillFieldId);
      if (skillField?.type === 'checkbox' && rawValue !== 'true') continue;

      result[mapping.schemaName] = applyTransform(rawValue, mapping.transform);
    }
  }

  return result;
}

export function autoFillFromProfile(
  skill: SkillDefinition,
  profile: DataProfile
): Record<string, string> {
  const values: Record<string, string> = {};

  for (const section of skill.sections) {
    for (const field of section.fields) {
      if (field.profileKey && profile.data[field.profileKey]) {
        values[field.id] = profile.data[field.profileKey];
      }
    }
  }

  return values;
}
