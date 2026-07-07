import { describe, it, expect } from 'vitest';
import { auctionAuthority } from '@/lib/skills/auction-authority';
import { applyComputedFields } from '@/lib/skills/utils';

function allFieldIds(): string[] {
  return auctionAuthority.sections.flatMap((s) => s.fields.map((f) => f.id));
}

describe('auctionAuthority skill definition', () => {
  it('has all required SkillDefinition properties', () => {
    expect(auctionAuthority.id).toBe('vic_auction_authority');
    expect(auctionAuthority.name).toBeTruthy();
    expect(auctionAuthority.sections.length).toBeGreaterThan(0);
    expect(auctionAuthority.fieldMappings.length).toBeGreaterThan(0);
    expect(auctionAuthority.draftStatus).toBe('unverified');
  });

  it('computes authorityEndDate as auctionDate + 30 days', () => {
    const result = applyComputedFields(auctionAuthority, { auctionDate: '15/09/2026' });
    expect(result.authorityEndDate).toBe('15/10/2026');
  });

  it('leaves authorityEndDate blank when auctionDate is missing', () => {
    const result = applyComputedFields(auctionAuthority, {});
    expect(result.authorityEndDate).toBeUndefined();
  });

  it('has no orphaned fields — every field has a fieldMapping', () => {
    const mappedIds = new Set(auctionAuthority.fieldMappings.map((m) => m.skillFieldId));
    for (const id of allFieldIds()) {
      expect(mappedIds.has(id)).toBe(true);
    }
  });

  it('has no orphaned fields in the pdfme mapping', () => {
    const pdfmeIds = new Set((auctionAuthority.pdfmeFieldMappings ?? []).map((m) => m.skillFieldId));
    for (const id of allFieldIds()) {
      expect(pdfmeIds.has(id)).toBe(true);
    }
  });
});
