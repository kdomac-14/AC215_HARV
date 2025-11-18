import { useState } from 'react'
import { Link } from 'react-router-dom'
import GPSButton from '../components/GPSButton'
import VerifyButtons from '../components/VerifyButtons'
import ManualCoordsForm from '../components/ManualCoordsForm'
import ImageVerifyCard from '../components/ImageVerifyCard'
import { useAppStore } from '../store/appState'

export default function Student() {
  const [verificationMethod, setVerificationMethod] = useState<'gps' | 'ip'>('gps')
  const [showManualForm, setShowManualForm] = useState(false)
  const { gpsData } = useAppStore()

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-6">
        <Link to="/" className="text-blue-600 hover:text-blue-800">
          ← Back to Home
        </Link>
      </div>

      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">🎓 Student Mode</h1>
        <p className="text-gray-600">
          Verify your attendance with location and photo
        </p>
      </div>

      {/* Section 0: Geolocation Verification */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-8">
        <h2 className="text-2xl font-bold mb-4">📍 0) Geolocation-first Auth</h2>
        
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-3">
            Choose verification method:
          </label>
          <div className="space-y-2">
            <label className="flex items-center p-3 bg-gray-50 rounded-lg cursor-pointer hover:bg-gray-100">
              <input
                type="radio"
                name="method"
                value="gps"
                checked={verificationMethod === 'gps'}
                onChange={(e) => setVerificationMethod(e.target.value as 'gps' | 'ip')}
                className="mr-3"
              />
              <div>
                <span className="font-medium">📱 GPS (Accurate 5-50m)</span>
                <p className="text-xs text-gray-600">Uses your device's location for best accuracy</p>
              </div>
            </label>
            
            <label className="flex items-center p-3 bg-gray-50 rounded-lg cursor-pointer hover:bg-gray-100">
              <input
                type="radio"
                name="method"
                value="ip"
                checked={verificationMethod === 'ip'}
                onChange={(e) => setVerificationMethod(e.target.value as 'gps' | 'ip')}
                className="mr-3"
              />
              <div>
                <span className="font-medium">🌐 IP-based (Quick but less accurate)</span>
                <p className="text-xs text-gray-600">Uses your internet connection</p>
              </div>
            </label>
          </div>
        </div>

        {verificationMethod === 'gps' ? (
          <div>
            <div className="mb-4 p-3 bg-blue-50 rounded">
              <p className="text-sm text-blue-900">
                📱 <strong>Embedded GPS Collection:</strong> Click the button below to use your device's GPS. 
                Your browser will ask for permission.
              </p>
            </div>

            <GPSButton />

            {gpsData && (
              <div className="my-4 p-4 bg-gray-50 rounded-lg">
                <p className="text-sm font-medium mb-2">GPS Coordinates:</p>
                <p className="text-sm font-mono">
                  Latitude: {gpsData.lat.toFixed(6)}<br />
                  Longitude: {gpsData.lon.toFixed(6)}<br />
                  Accuracy: ±{Math.round(gpsData.accuracy)}m
                </p>
              </div>
            )}

            <VerifyButtons />

            <div className="mt-6">
              <button
                onClick={() => setShowManualForm(!showManualForm)}
                className="text-sm text-blue-600 hover:text-blue-800"
              >
                {showManualForm ? '▼' : '▶'} Or enter GPS coordinates manually
              </button>
              {showManualForm && (
                <ManualCoordsForm onSubmit={(lat, lon, acc) => {
                  // Handle manual coords - could integrate with verify
                  console.log('Manual coords:', { lat, lon, acc })
                }} />
              )}
            </div>
          </div>
        ) : (
          <div>
            <div className="mb-4 p-3 bg-yellow-50 rounded">
              <p className="text-sm text-yellow-900">
                🌐 <strong>IP-based verification:</strong> This uses your internet connection for location. 
                Less accurate but works without GPS permission.
              </p>
            </div>

            <VerifyButtons />
          </div>
        )}

        <div className="mt-6 p-4 bg-gray-50 rounded-lg">
          <p className="text-xs text-gray-600">
            💡 <strong>Note:</strong> For production use, deploy a mobile app that sends GPS/WiFi data to the backend.
          </p>
        </div>
      </div>

      {/* Section 1: Visual Verification */}
      <ImageVerifyCard />
    </div>
  )
}
