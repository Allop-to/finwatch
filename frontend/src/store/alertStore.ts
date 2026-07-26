import { create } from 'zustand';

interface Alert {
  id: string;
  type: string;
  message: string;
  detectionId?: number;
  timestamp: number;
}

interface AlertState {
  alerts: Alert[];
  addAlert: (alert: Omit<Alert, 'id' | 'timestamp'>) => void;
  clearAlerts: () => void;
}

export const useAlertStore = create<AlertState>((set) => ({
  alerts: [],
  addAlert: (alert) => set((s) => ({
    alerts: [{ ...alert, id: crypto.randomUUID(), timestamp: Date.now() }, ...s.alerts].slice(0, 20),
  })),
  clearAlerts: () => set({ alerts: [] }),
}));
