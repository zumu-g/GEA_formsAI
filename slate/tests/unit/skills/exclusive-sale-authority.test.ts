import { describe, it, expect } from 'vitest';
import { exclusiveSaleAuthority } from '@/lib/skills/exclusive-sale-authority';
import { applyComputedFields } from '@/lib/skills/utils';

function allFieldIds(): string[] {
  return exclusiveSaleAuthority.sections.flatMap((s) => s.fields.map((f) => f.id));
}

describe('exclusiveSaleAuthority skill definition', () => {
  it('has all required SkillDefinition properties', () => {
    expect(exclusiveSaleAuthority.id).toBe('vic_exclusive_sale_authority');
    expect(exclusiveSaleAuthority.sections.length).toBeGreaterThan(0);
    expect(exclusiveSaleAuthority.fieldMappings.length).toBeGreaterThan(0);
    expect(exclusiveSaleAuthority.draftStatus).toBe('unverified');
  });

  it('computes authorityEndDate as startDate + 60 days', () => {
    const result = applyComputedFields(exclusiveSaleAuthority, { startDate: '01/08/2026' });
    expect(result.authorityEndDate).toBe('30/09/2026');
  });

  it('leaves authorityEndDate blank when startDate is missing', () => {
    const result = applyComputedFields(exclusiveSaleAuthority, {});
    expect(result.authorityEndDate).toBeUndefined();
  });

  it('has no orphaned fields — every field has a fieldMapping', () => {
    const mappedIds = new Set(exclusiveSaleAuthority.fieldMappings.map((m) => m.skillFieldId));
    for (const id of allFieldIds()) {
      expect(mappedIds.has(id)).toBe(true);
    }
  });

  it('has no orphaned fields in the pdfme mapping', () => {
    const pdfmeIds = new Set((exclusiveSaleAuthority.pdfmeFieldMappings ?? []).map((m) => m.skillFieldId));
    for (const id of allFieldIds()) {
      expect(pdfmeIds.has(id)).toBe(true);
    }
  });

  it('has a soleAgencyClause field distinguishing it from the General Authority skill', () => {
    expect(allFieldIds()).toContain('soleAgencyClause');
  });
});
