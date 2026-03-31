import { vicContractOfSaleOffer } from './vic-contract-of-sale-offer';
import { section32Offer } from './section-32-offer';
import type { SkillDefinition } from '@/types/skill';

export const SKILLS: SkillDefinition[] = [
  vicContractOfSaleOffer,
  section32Offer,
];

export function getSkillById(id: string): SkillDefinition | undefined {
  return SKILLS.find((s) => s.id === id);
}
