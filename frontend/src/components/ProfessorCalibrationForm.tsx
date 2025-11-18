import { useState, useEffect } from 'react'
import { calibrate, getGeoStatus } from '../api'
import StatusBanner from './StatusBanner'
import JsonViewer from './JsonViewer'

export default function ProfessorCalibrationForm() {
  const [lat, setLat] = useState('42.3770')
  const [lon, setLon] = useState('-71.1167')
  const [epsilon, setEpsilon] = useState('60')
  const [isLoading, setIsLoading] = useState(false)
  const [status, setStatus] = useState<{ type: 'success' | 'error' | 'info'; message: string } | null>(null)
  const [currentCalibration, setCurrentCalibration] = useState<any>(null)
  const [response, setResponse] = useState<any>(null)

  useEffect(() => {
    loadCurrentCalibration()
  }, [])

  const loadCurrentCalibration = async () => {
    try {
      const res = await getGeoStatus()
      setCurrentCalibration(res.data.calibration)
      if (res.data.calibration.lat && res.data.calibration.lon) {
        setLat(res.data.calibration.lat.toString())
        setLon(res.data.calibration.lon.toString())
        setEpsilon(res.data.calibration.epsilon_m.toString())
      }
    } catch (error) {
      console.error('Failed to load calibration:', error)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setStatus(null)
    setResponse(null)

    try {
      const res = await calibrate({
        lat: parseFloat(lat),
        lon: parseFloat(lon),
        epsilon_m: parseFloat(epsilon),
      })

      setStatus({
        type: 'success',
        message: '✅ Calibration saved successfully!',
      })
      setResponse(res.data)
      setCurrentCalibration(res.data.calibration)
    } catch (error: any) {
      setStatus({
        type: 'error',
        message: `Failed to save calibration: ${error.message}`,
      })
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-2xl font-bold mb-4">📍 Calibrate Classroom Location</h2>
      
      {currentCalibration && currentCalibration.lat && (
        <div className="mb-4 p-3 bg-blue-50 rounded">
          <p className="text-sm font-medium text-blue-900">Current Calibration:</p>
          <p className="text-sm text-blue-700">
            Lat: {currentCalibration.lat.toFixed(6)}, Lon: {currentCalibration.lon.toFixed(6)}, 
            Radius: {currentCalibration.epsilon_m}m
          </p>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Latitude
          </label>
          <input
            type="number"
            step="0.000001"
            value={lat}
            onChange={(e) => setLat(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Longitude
          </label>
          <input
            type="number"
            step="0.000001"
            value={lon}
            onChange={(e) => setLon(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Acceptable Radius (meters)
          </label>
          <input
            type="number"
            step="10"
            value={epsilon}
            onChange={(e) => setEpsilon(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          />
          <p className="text-xs text-gray-500 mt-1">
            Students must be within this distance from the classroom
          </p>
        </div>

        <button
          type="submit"
          disabled={isLoading}
          className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-semibold py-3 px-6 rounded-lg transition-colors"
        >
          {isLoading ? 'Saving...' : 'Save Calibration'}
        </button>
      </form>

      {status && <StatusBanner type={status.type} message={status.message} />}
      {response && <JsonViewer data={response} title="📊 Calibration Response" />}
    </div>
  )
}
