import { create } from 'zustand';

interface User {
  id: string;
  name: string;
  role: 'professor' | 'student';
}

interface AppStore {
  user: User | null;
  setUser: (user: User | null) => void;
  
  currentClassCode: string | null;
  setCurrentClassCode: (code: string | null) => void;
  
  lastCheckIn: {
    success: boolean;
    timestamp: Date;
    className?: string;
  } | null;
  setLastCheckIn: (data: any) => void;
}

export const useStore = create<AppStore>((set) => ({
  user: null,
  setUser: (user) => set({ user }),
  
  currentClassCode: null,
  setCurrentClassCode: (code) => set({ currentClassCode: code }),
  
  lastCheckIn: null,
  setLastCheckIn: (data) => set({ lastCheckIn: data }),
}));
