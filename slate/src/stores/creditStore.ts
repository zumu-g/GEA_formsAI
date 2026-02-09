import { create } from 'zustand';

interface CreditState {
  balance: number;
  isLoading: boolean;

  setBalance: (balance: number) => void;
  deductCredits: (amount: number) => void;
  addCredits: (amount: number) => void;
  setIsLoading: (loading: boolean) => void;
}

export const useCreditStore = create<CreditState>((set) => ({
  balance: 5,
  isLoading: false,

  setBalance: (balance) => set({ balance }),
  deductCredits: (amount) => set((state) => ({ balance: state.balance - amount })),
  addCredits: (amount) => set((state) => ({ balance: state.balance + amount })),
  setIsLoading: (loading) => set({ isLoading: loading }),
}));
