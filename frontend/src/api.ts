import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE || '/api'

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

export interface HealthResponse {
  ok: boolean
  model?: string
  geo_provider?: string
}

export interface CalibrationPayload {
  lat: number
  lon: number
  epsilon_m?: number
}

export interface CalibrationResponse {
  ok: boolean
  calibration: {
    lat: number
    lon: number
    epsilon_m: number
    updated_at: number
  }
}

export interface GeoStatusResponse {
  ok: boolean
  calibration: {
    lat: number | null
    lon: number | null
    epsilon_m: number
    updated_at: number | null
  }
}

export interface GeoVerifyPayload {
  client_gps_lat?: number
  client_gps_lon?: number
  client_gps_accuracy_m?: number
}

export interface GeoVerifyResponse {
  ok: boolean
  source?: string
  client_ip?: string
  distance_m?: number
  epsilon_m?: number
  estimated_lat?: number
  estimated_lon?: number
  estimated_accuracy_m?: number
  reason?: string
}

export interface VerifyPayload {
  image_b64: string
}

export interface VerifyResponse {
  ok: boolean
  label?: string
  confidence?: number
  latency_ms?: number
  reason?: string
}

// API Methods
export const getHealth = () => api.get<HealthResponse>('/healthz')

export const calibrate = (payload: CalibrationPayload) =>
  api.post<CalibrationResponse>('/geo/calibrate', payload)

export const getGeoStatus = () => api.get<GeoStatusResponse>('/geo/status')

export const verifyGeo = (payload: GeoVerifyPayload) =>
  api.post<GeoVerifyResponse>('/geo/verify', payload)

export const verifyImage = (payload: VerifyPayload) =>
  api.post<VerifyResponse>('/verify', payload)

export default api
