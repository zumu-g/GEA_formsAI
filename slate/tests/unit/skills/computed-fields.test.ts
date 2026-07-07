import { describe, it, expect } from 'vitest';
import { applyComputedFields, addDaysToAuDate, getDraftBadge } from '@/lib/skills/utils';
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

  it('returns undefined for a calendar-invalid date instead of rolling over', () => {
    // JS Date silently normalizes 31/02 to 3 March — must be rejected, not rolled over.
    expect(addDaysToAuDate('31/02/2026', 30)).toBeUndefined();
  });

  it('crosses a year boundary correctly', () => {
    expect(addDaysToAuDate('20/12/2026', 30)).toBe('19/01/2027');
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

describe('getDraftBadge', () => {
  it('shows "Unverified draft" with a tooltip when draftStatus is unverified', () => {
    const badge = getDraftBadge({ version: '0.1.0', draftStatus: 'unverified' });
    expect(badge).toEqual({
      show: true,
      label: 'Unverified draft',
      title: expect.stringContaining('not yet confirmed'),
    });
  });

  it('shows plain "Draft" (no tooltip) when only the version string signals draft', () => {
    const badge = getDraftBadge({ version: '0.1.0-draft' });
    expect(badge).toEqual({ show: true, label: 'Draft', title: undefined });
  });

  it('shows no badge for a shipped, verified skill', () => {
    const badge = getDraftBadge({ version: '1.0' });
    expect(badge).toEqual({ show: false, label: null, title: undefined });
  });
});
