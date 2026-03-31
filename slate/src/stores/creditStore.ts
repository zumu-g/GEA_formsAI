import { create } from 'zustand';

interface CreditState {
  balance: number;
  isLoading: boolean;
  hasFetched: boolean;

  setBalance: (balance: number) => void;
  deductCredits: (amount: number) => void;
  addCredits: (amount: number) => void;
  setIsLoading: (loading: boolean) => void;
  fetchBalance: () => Promise<void>;
}

export const useCreditStore = create<CreditState>((set, get) => ({
  balance: 0,
  isLoading: false,
  hasFetched: false,

  setBalance: (balance) => set({ balance }),
  deductCredits: (amount) => set((state) => ({ balance: state.balance - amount })),
  addCredits: (amount) => set((state) => ({ balance: state.balance + amount })),
  setIsLoading: (loading) => set({ isLoading: loading }),

  fetchBalance: async () => {
    // Avoid duplicate fetches
    if (get().isLoading) return;

    set({ isLoading: true });
    try {
      const res = await fetch('/api/credits/balance');
      if (res.ok) {
        const json = await res.json();
        if (json.success) {
          set({ balance: json.data.balance, hasFetched: true });
        }
      }
    } catch (error) {
      console.error('Failed to fetch credit balance:', error);
    } finally {
      set({ isLoading: false });
    }
  },
}));
