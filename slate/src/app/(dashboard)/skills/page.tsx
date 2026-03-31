'use client';

import { SKILLS } from '@/lib/skills';
import { SkillCard } from '@/components/skills/SkillCard';
import { Wand2 } from 'lucide-react';

export default function SkillsPage() {
  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex items-center gap-3 mb-8">
        <div className="w-10 h-10 rounded-xl bg-[#5856D6]/10 flex items-center justify-center">
          <Wand2 size={20} className="text-[#5856D6]" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-[#1D1D1F]">Form Filling Skills</h1>
          <p className="text-sm text-[#86868B]">
            Guided wizards for common legal documents. Fill via text or voice.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {SKILLS.map((skill) => (
          <SkillCard key={skill.id} skill={skill} />
        ))}
      </div>
    </div>
  );
}
