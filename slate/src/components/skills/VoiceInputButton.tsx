'use client';

import { useEffect, useRef } from 'react';
import { Mic, MicOff } from 'lucide-react';
import { useVoiceInput } from '@/hooks/useVoiceInput';

interface VoiceInputButtonProps {
  onResult: (transcript: string) => void;
  disabled?: boolean;
}

export function VoiceInputButton({ onResult, disabled }: VoiceInputButtonProps) {
  const { isListening, isSupported, transcript, error, startListening, stopListening } =
    useVoiceInput();

  // Keep ref current so the effect below doesn't need onResult in its deps,
  // which would otherwise cause an infinite re-render loop when the parent
  // re-renders after setValue triggers a Zustand update.
  const onResultRef = useRef(onResult);
  onResultRef.current = onResult;

  useEffect(() => {
    if (!isListening && transcript) {
      onResultRef.current(transcript);
    }
  }, [isListening, transcript]);

  if (!isSupported) return null;

  return (
    <div className="relative shrink-0">
      <button
        type="button"
        onClick={isListening ? stopListening : startListening}
        disabled={disabled}
        aria-label={isListening ? 'Stop voice input' : 'Dictate field value'}
        title={isListening ? 'Stop listening' : 'Dictate field value'}
        className={`
          flex items-center justify-center w-9 h-9 rounded-lg border transition-all duration-200
          ${
            isListening
              ? 'bg-red-50 border-red-300 text-red-600 animate-pulse'
              : 'bg-white border-[#E2E4EA] text-[#767A85] hover:text-[#1B1D24] hover:border-[#C4C8D1]'
          }
          ${disabled ? 'opacity-40 cursor-not-allowed' : 'cursor-pointer'}
        `}
      >
        {isListening ? <MicOff size={16} /> : <Mic size={16} />}
      </button>

      {/* Live transcript preview while recording */}
      {isListening && transcript && (
        <div className="absolute right-0 top-full mt-1 z-10 w-48 px-2.5 py-1.5 rounded-lg bg-[#1B1D24] text-white text-xs shadow-lg leading-relaxed">
          {transcript}
        </div>
      )}

      {/* Voice error — shown after failed recognition */}
      {error && !isListening && (
        <div className="absolute right-0 top-full mt-1 z-10 whitespace-nowrap px-2.5 py-1.5 rounded-lg bg-red-50 border border-red-200 text-xs text-red-700 shadow-sm">
          {error}
        </div>
      )}
    </div>
  );
}
