import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface GPSData {
  lat: number
  lon: number
  accuracy: number
}

interface VerifyResult {
  success: boolean
  data: any
  timestamp: number
}

interface AppState {
  gpsData: GPSData | null
  gpsStatus: string | null
  lastVerifyResponse: VerifyResult | null
  setGPSData: (data: GPSData | null) => void
  setGPSStatus: (status: string | null) => void
  setLastVerifyResponse: (result: VerifyResult | null) => void
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      gpsData: null,
      gpsStatus: null,
      lastVerifyResponse: null,
      setGPSData: (data) => set({ gpsData: data }),
      setGPSStatus: (status) => set({ gpsStatus: status }),
      setLastVerifyResponse: (result) => set({ lastVerifyResponse: result }),
    }),
    {
      name: 'harv-app-storage',
      partialize: (state) => ({ lastVerifyResponse: state.lastVerifyResponse }),
    }
  )
)
