import { Link } from 'react-router-dom'

export default function Landing() {
  return (
    <div className="max-w-4xl mx-auto">
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          HARV Demo Dashboard
        </h1>
        <p className="text-xl text-gray-600">
          Harvard Attendance Recognition and Verification
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <Link
          to="/professor"
          className="block bg-white rounded-lg shadow-md p-8 hover:shadow-lg transition-shadow"
        >
          <div className="text-6xl mb-4 text-center">👨‍🏫</div>
          <h2 className="text-2xl font-bold text-center mb-2">Professor Mode</h2>
          <p className="text-gray-600 text-center">
            Calibrate classroom location and manage settings
          </p>
        </Link>

        <Link
          to="/student"
          className="block bg-white rounded-lg shadow-md p-8 hover:shadow-lg transition-shadow"
        >
          <div className="text-6xl mb-4 text-center">🎓</div>
          <h2 className="text-2xl font-bold text-center mb-2">Student Mode</h2>
          <p className="text-gray-600 text-center">
            Verify your attendance with location and photo
          </p>
        </Link>
      </div>

      <div className="mt-12 bg-blue-50 rounded-lg p-6">
        <h3 className="text-lg font-semibold mb-3">How it works:</h3>
        <ol className="space-y-2 text-gray-700">
          <li><strong>1. Geolocation Verification:</strong> Students must be physically present in the classroom (GPS/IP-based)</li>
          <li><strong>2. Face Recognition:</strong> Visual verification with liveness challenge ("word of the day")</li>
        </ol>
      </div>
    </div>
  )
}
