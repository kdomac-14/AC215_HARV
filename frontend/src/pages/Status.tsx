import { useEffect, useState } from 'react'
import { getHealth, getGeoStatus } from '../api'
import StatusBanner from '../components/StatusBanner'
import JsonViewer from '../components/JsonViewer'

export default function Status() {
  const [healthData, setHealthData] = useState<any>(null)
  const [geoData, setGeoData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadStatus()
  }, [])

  const loadStatus = async () => {
    setLoading(true)
    setError(null)

    try {
      const [healthRes, geoRes] = await Promise.all([
        getHealth(),
        getGeoStatus()
      ])

      setHealthData(healthRes.data)
      setGeoData(geoRes.data)
    } catch (err: any) {
      setError(`Failed to load status: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-3xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">🔍 System Status</h1>
        <p className="text-gray-600">
          Check API health and geolocation configuration
        </p>
      </div>

      {loading && (
        <div className="text-center py-8">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="mt-2 text-gray-600">Loading status...</p>
        </div>
      )}

      {error && (
        <StatusBanner type="error" message={error} />
      )}

      {!loading && !error && healthData && (
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-bold mb-4">API Health</h2>
            {healthData.ok ? (
              <StatusBanner 
                type="success" 
                message="✅ API is healthy and responding"
              />
            ) : (
              <StatusBanner 
                type="error" 
                message="❌ API health check failed"
              />
            )}
            <div className="mt-4 space-y-2">
              <p className="text-sm">
                <strong>Model:</strong> {healthData.model || 'N/A'}
              </p>
              <p className="text-sm">
                <strong>Geo Provider:</strong> {healthData.geo_provider || 'N/A'}
              </p>
            </div>
            <JsonViewer data={healthData} title="Raw Health Data" />
          </div>

          {geoData && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-bold mb-4">Geolocation Configuration</h2>
              {geoData.calibration && geoData.calibration.lat && geoData.calibration.lon ? (
                <>
                  <StatusBanner 
                    type="success" 
                    message="✅ Classroom calibrated"
                  />
                  <div className="mt-4 space-y-2">
                    <p className="text-sm">
                      <strong>Latitude:</strong> {geoData.calibration.lat.toFixed(6)}
                    </p>
                    <p className="text-sm">
                      <strong>Longitude:</strong> {geoData.calibration.lon.toFixed(6)}
                    </p>
                    <p className="text-sm">
                      <strong>Acceptable Radius:</strong> {geoData.calibration.epsilon_m}m
                    </p>
                    {geoData.calibration.updated_at && (
                      <p className="text-sm">
                        <strong>Last Updated:</strong> {new Date(geoData.calibration.updated_at * 1000).toLocaleString()}
                      </p>
                    )}
                  </div>
                </>
              ) : (
                <StatusBanner 
                  type="info" 
                  message="ℹ️ Classroom not calibrated yet"
                />
              )}
              <JsonViewer data={geoData} title="Raw Geo Status" />
            </div>
          )}

          <div className="text-center">
            <button
              onClick={loadStatus}
              className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-6 rounded-lg transition-colors"
            >
              🔄 Refresh Status
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
