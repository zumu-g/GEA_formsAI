import { describe, it, expect } from 'vitest';
import { SKILLS, getSkillById } from '@/lib/skills';

describe('SKILLS registry', () => {
  it('contains exactly 7 entries (4 existing + 3 new)', () => {
    expect(SKILLS).toHaveLength(7);
  });

  it('resolves each of the 3 new skill ids via getSkillById', () => {
    expect(getSkillById('vic_auction_authority')?.name).toBe('Auction Authority');
    expect(getSkillById('vic_exclusive_sale_authority')?.name).toBe('Exclusive Sale Authority');
    expect(getSkillById('vic_general_authority')?.name).toBe('General (Non-Exclusive) Authority');
  });

  it('has no duplicate id values across all entries', () => {
    const ids = SKILLS.map((s) => s.id);
    expect(new Set(ids).size).toBe(ids.length);
  });
});
