import { ReactNode } from 'react';

type BadgeVariant = 'default' | 'accent' | 'success' | 'warning' | 'error';

interface BadgeProps {
  children: ReactNode;
  variant?: BadgeVariant;
}

const variants: Record<BadgeVariant, string> = {
  default: 'bg-[#F5F5F7] text-[#86868B]',
  accent: 'bg-[#5856D6]/10 text-[#5856D6]',
  success: 'bg-[#34C759]/10 text-[#34C759]',
  warning: 'bg-[#FF9F0A]/10 text-[#FF9F0A]',
  error: 'bg-[#FF3B30]/10 text-[#FF3B30]',
};

export function Badge({ children, variant = 'default' }: BadgeProps) {
  return (
    <span
      className={`
        inline-flex items-center px-2.5 py-0.5 rounded-full
        text-xs font-medium
        ${variants[variant]}
      `}
    >
      {children}
    </span>
  );
}
