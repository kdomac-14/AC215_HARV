import { useState } from 'react'

interface ManualCoordsFormProps {
  onSubmit: (lat: number, lon: number, accuracy: number) => void
  isLoading?: boolean
}

export default function ManualCoordsForm({ onSubmit, isLoading }: ManualCoordsFormProps) {
  const [lat, setLat] = useState('42.3770')
  const [lon, setLon] = useState('-71.1167')
  const [accuracy, setAccuracy] = useState('20')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit(parseFloat(lat), parseFloat(lon), parseFloat(accuracy))
  }

  return (
    <div className="bg-gray-50 rounded-lg p-4 my-4">
      <h3 className="font-semibold mb-2">📝 Or enter GPS coordinates manually</h3>
      <p className="text-sm text-gray-600 mb-4">
        <strong>Get your coordinates:</strong>
        <br />• <strong>iPhone:</strong> Open Maps → tap blue dot → swipe up → see coordinates
        <br />• <strong>Android:</strong> Open Google Maps → long-press your location → see coordinates at top
        <br />• <strong>Browser:</strong> Visit https://www.latlong.net/
      </p>
      
      <form onSubmit={handleSubmit} className="space-y-3">
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
            Accuracy (meters)
          </label>
          <input
            type="number"
            step="1"
            value={accuracy}
            onChange={(e) => setAccuracy(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          />
          <p className="text-xs text-gray-500 mt-1">GPS: 5-20m, WiFi: 50-100m</p>
        </div>

        <button
          type="submit"
          disabled={isLoading}
          className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-semibold py-2 px-4 rounded-lg transition-colors"
        >
          {isLoading ? 'Verifying...' : '✓ Verify with Manual Coordinates'}
        </button>
      </form>
    </div>
  )
}
