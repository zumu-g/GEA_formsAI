import { describe, it, expect } from 'vitest';
import { applyComputedFields, addDaysToAuDate } from '@/lib/skills/utils';
import type { SkillDefinition } from '@/types/skill';

function baseSkill(overrides: Partial<SkillDefinition> = {}): SkillDefinition {
  return {
    id: 'test_skill',
    name: 'Test Skill',
    description: '',
    icon: 'file',
    version: '1.0.0',
    documentType: 'test',
    sections: [],
    fieldMappings: [],
    ...overrides,
  };
}

describe('addDaysToAuDate', () => {
  it('adds a day offset to a dd/mm/yyyy date', () => {
    expect(addDaysToAuDate('15/09/2026', 30)).toBe('15/10/2026');
  });

  it('returns undefined for a missing date', () => {
    expect(addDaysToAuDate(undefined, 30)).toBeUndefined();
  });

  it('returns undefined for an invalid date string', () => {
    expect(addDaysToAuDate('not-a-date', 30)).toBeUndefined();
  });
});

describe('applyComputedFields — add_days formula', () => {
  it('computes authorityEndDate as auctionDate + 30 days', () => {
    const skill = baseSkill({
      computedFields: [
        {
          skillFieldId: 'authorityEndDate',
          formula: 'add_days',
          operands: ['auctionDate'],
          days: 30,
          pdfFieldName: 'authority_end_date',
        },
      ],
    });

    const result = applyComputedFields(skill, { auctionDate: '15/09/2026' });
    expect(result.authorityEndDate).toBe('15/10/2026');
  });

  it('leaves the computed field blank when the source date is missing', () => {
    const skill = baseSkill({
      computedFields: [
        {
          skillFieldId: 'authorityEndDate',
          formula: 'add_days',
          operands: ['auctionDate'],
          days: 30,
          pdfFieldName: 'authority_end_date',
        },
      ],
    });

    const result = applyComputedFields(skill, {});
    expect(result.authorityEndDate).toBeUndefined();
  });

  it('does not regress the existing subtract formula (e.g. balance_at_settlement)', () => {
    const skill = baseSkill({
      computedFields: [
        {
          skillFieldId: 'balance',
          formula: 'subtract',
          operands: ['price', 'deposit'],
          pdfFieldName: 'balance',
        },
      ],
    });

    const result = applyComputedFields(skill, { price: '500000', deposit: '50000' });
    expect(result.balance).toBe('450000.00');
  });
});

describe('SkillDefinition.draftStatus', () => {
  it('is optional and does not break an existing skill with no draftStatus set', () => {
    const skill = baseSkill();
    expect(skill.draftStatus).toBeUndefined();
  });
});
