'use client';

import { forwardRef, InputHTMLAttributes } from 'react';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, className = '', id, ...props }, ref) => {
    const inputId = id || label?.toLowerCase().replace(/\s+/g, '-');

    return (
      <div className="flex flex-col gap-1.5">
        {label && (
          <label
            htmlFor={inputId}
            className="text-sm font-medium text-[#1D1D1F]"
          >
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={inputId}
          className={`
            h-10 px-3 rounded-xl border border-[#E5E5EA] bg-white
            text-sm text-[#1D1D1F] placeholder:text-[#AEAEB2]
            transition-all duration-200
            hover:border-[#C7C7CC]
            focus:outline-none focus:ring-2 focus:ring-[#5856D6]/20 focus:border-[#5856D6]
            disabled:opacity-50 disabled:cursor-not-allowed disabled:bg-[#F5F5F7]
            ${error ? 'border-[#FF3B30] focus:ring-[#FF3B30]/20 focus:border-[#FF3B30]' : ''}
            ${className}
          `}
          {...props}
        />
        {error && (
          <p className="text-xs text-[#FF3B30]">{error}</p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';
