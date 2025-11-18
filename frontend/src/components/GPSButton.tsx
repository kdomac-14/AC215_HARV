import { useState } from 'react'
import { useAppStore } from '../store/appState'
import StatusBanner from './StatusBanner'

interface GPSButtonProps {
  onSuccess?: (lat: number, lon: number, accuracy: number) => void
}

export default function GPSButton({ onSuccess }: GPSButtonProps) {
  const [status, setStatus] = useState<string>('')
  const [statusType, setStatusType] = useState<'success' | 'error' | 'info'>('info')
  const [isLoading, setIsLoading] = useState(false)
  const { setGPSData } = useAppStore()

  const handleGetGPS = () => {
    if (!navigator.geolocation) {
      setStatusType('error')
      setStatus('❌ GPS not supported on this device/browser')
      return
    }

    setIsLoading(true)
    setStatusType('info')
    setStatus('📡 Requesting GPS permission from your device...')

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const lat = position.coords.latitude
        const lon = position.coords.longitude
        const accuracy = position.coords.accuracy

        setStatusType('success')
        setStatus(`✓ GPS acquired! Accuracy: ±${Math.round(accuracy)}m`)

        const gpsData = { lat, lon, accuracy }
        setGPSData(gpsData)

        if (onSuccess) {
          onSuccess(lat, lon, accuracy)
        }

        setIsLoading(false)
      },
      (error) => {
        let errorMsg = ''
        switch (error.code) {
          case error.PERMISSION_DENIED:
            errorMsg = '❌ Permission denied. Please allow location access in your browser settings.'
            break
          case error.POSITION_UNAVAILABLE:
            errorMsg = '❌ GPS unavailable. Try moving outside or near a window.'
            break
          case error.TIMEOUT:
            errorMsg = '❌ GPS timeout. Please try again.'
            break
          default:
            errorMsg = `❌ GPS error: ${error.message}`
        }
        setStatusType('error')
        setStatus(errorMsg)
        setIsLoading(false)
      },
      {
        enableHighAccuracy: true,
        timeout: 15000,
        maximumAge: 0,
      }
    )
  }

  return (
    <div className="my-4">
      <button
        onClick={handleGetGPS}
        disabled={isLoading}
        className="w-full bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white font-semibold py-3 px-6 rounded-lg transition-colors"
      >
        {isLoading ? '📡 Getting GPS...' : '🛰️ Get My GPS Location'}
      </button>

      {status && (
        <StatusBanner
          type={statusType}
          message={status}
        />
      )}
    </div>
  )
}
