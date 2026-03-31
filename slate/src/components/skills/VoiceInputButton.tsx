'use client';

import { useEffect } from 'react';
import { Mic, MicOff } from 'lucide-react';
import { useVoiceInput } from '@/hooks/useVoiceInput';

interface VoiceInputButtonProps {
  onResult: (transcript: string) => void;
  disabled?: boolean;
}

export function VoiceInputButton({ onResult, disabled }: VoiceInputButtonProps) {
  const { isListening, isSupported, transcript, error, startListening, stopListening } =
    useVoiceInput();

  useEffect(() => {
    if (!isListening && transcript) {
      onResult(transcript);
    }
  }, [isListening, transcript, onResult]);

  if (!isSupported) return null;

  return (
    <button
      type="button"
      onClick={isListening ? stopListening : startListening}
      disabled={disabled}
      title={isListening ? 'Stop listening' : 'Voice input'}
      className={`
        flex items-center justify-center w-9 h-9 rounded-lg border transition-all duration-200
        ${
          isListening
            ? 'bg-red-50 border-red-300 text-red-600 animate-pulse'
            : 'bg-white border-[#E5E5EA] text-[#86868B] hover:text-[#1D1D1F] hover:border-[#C7C7CC]'
        }
        ${disabled ? 'opacity-40 cursor-not-allowed' : 'cursor-pointer'}
      `}
    >
      {isListening ? <MicOff size={16} /> : <Mic size={16} />}
      {error && (
        <span className="sr-only">{error}</span>
      )}
    </button>
  );
}
