import { useState } from 'react'
import { verifyGeo } from '../api'
import { useAppStore } from '../store/appState'
import StatusBanner from './StatusBanner'
import JsonViewer from './JsonViewer'

export default function VerifyButtons() {
  const [isLoading, setIsLoading] = useState(false)
  const [status, setStatus] = useState<{ type: 'success' | 'error' | 'info'; message: string } | null>(null)
  const [response, setResponse] = useState<any>(null)
  const { gpsData } = useAppStore()

  const handleVerifyGPS = async () => {
    if (!gpsData) {
      setStatus({
        type: 'error',
        message: 'Please get your GPS location first',
      })
      return
    }

    setIsLoading(true)
    setStatus(null)
    setResponse(null)

    try {
      const res = await verifyGeo({
        client_gps_lat: gpsData.lat,
        client_gps_lon: gpsData.lon,
        client_gps_accuracy_m: gpsData.accuracy,
      })

      if (res.data.ok) {
        setStatus({
          type: 'success',
          message: `✅ <strong>Location Verified!</strong><br>Distance: ${Math.round(res.data.distance_m!)}m (within ${Math.round(res.data.epsilon_m!)}m allowed)`,
        })
      } else {
        const reason = res.data.reason || 'unknown'
        if (reason === 'not_calibrated') {
          setStatus({
            type: 'error',
            message: '❌ Classroom not calibrated yet. Ask professor to calibrate first.',
          })
        } else {
          setStatus({
            type: 'error',
            message: `❌ <strong>Too far from classroom</strong><br>Distance: ${Math.round(res.data.distance_m!)}m<br>Allowed: ${Math.round(res.data.epsilon_m!)}m`,
          })
        }
      }

      setResponse(res.data)
    } catch (error: any) {
      setStatus({
        type: 'error',
        message: `Connection error: ${error.message}`,
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleVerifyIP = async () => {
    setIsLoading(true)
    setStatus(null)
    setResponse(null)

    try {
      const res = await verifyGeo({})

      if (res.data.ok) {
        setStatus({
          type: 'success',
          message: `✅ <strong>Location Verified!</strong><br>Method: ${res.data.source}<br>Distance: ${Math.round(res.data.distance_m!)}m (within ${Math.round(res.data.epsilon_m!)}m allowed)`,
        })
      } else {
        const reason = res.data.reason || 'unknown'
        if (reason === 'not_calibrated') {
          setStatus({
            type: 'error',
            message: '❌ Classroom not calibrated yet. Ask professor to calibrate first.',
          })
        } else {
          setStatus({
            type: 'error',
            message: `❌ <strong>Too far from classroom</strong><br>Distance: ${Math.round(res.data.distance_m!)}m<br>Allowed: ${Math.round(res.data.epsilon_m!)}m`,
          })
        }
      }

      setResponse(res.data)
    } catch (error: any) {
      setStatus({
        type: 'error',
        message: `Connection error: ${error.message}`,
      })
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <button
          onClick={handleVerifyGPS}
          disabled={isLoading || !gpsData}
          className="bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white font-semibold py-3 px-6 rounded-lg transition-colors"
        >
          📱 Verify by GPS
        </button>

        <button
          onClick={handleVerifyIP}
          disabled={isLoading}
          className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-semibold py-3 px-6 rounded-lg transition-colors"
        >
          🌐 Verify by IP
        </button>
      </div>

      {status && <StatusBanner type={status.type} message={status.message} />}
      {response && <JsonViewer data={response} title="📊 Verification Response" />}
    </div>
  )
}
