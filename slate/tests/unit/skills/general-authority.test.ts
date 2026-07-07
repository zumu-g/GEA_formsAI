import { describe, it, expect } from 'vitest';
import { generalAuthority } from '@/lib/skills/general-authority';

function allFieldIds(): string[] {
  return generalAuthority.sections.flatMap((s) => s.fields.map((f) => f.id));
}

describe('generalAuthority skill definition', () => {
  it('has all required SkillDefinition properties', () => {
    expect(generalAuthority.id).toBe('vic_general_authority');
    expect(generalAuthority.sections.length).toBeGreaterThan(0);
    expect(generalAuthority.fieldMappings.length).toBeGreaterThan(0);
    expect(generalAuthority.draftStatus).toBe('unverified');
  });

  it('has no orphaned fields — every field has a fieldMapping', () => {
    const mappedIds = new Set(generalAuthority.fieldMappings.map((m) => m.skillFieldId));
    for (const id of allFieldIds()) {
      expect(mappedIds.has(id)).toBe(true);
    }
  });

  it('has no orphaned fields in the pdfme mapping', () => {
    const pdfmeIds = new Set((generalAuthority.pdfmeFieldMappings ?? []).map((m) => m.skillFieldId));
    for (const id of allFieldIds()) {
      expect(pdfmeIds.has(id)).toBe(true);
    }
  });

  it('has no computed expiry field (open-ended design intent)', () => {
    expect(generalAuthority.computedFields ?? []).toHaveLength(0);
  });

  it('does not have a soleAgencyClause field (distinct from Exclusive Sale Authority)', () => {
    expect(allFieldIds()).not.toContain('soleAgencyClause');
  });
});
