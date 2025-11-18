import { Link } from 'react-router-dom'
import ProfessorCalibrationForm from '../components/ProfessorCalibrationForm'

export default function Professor() {
  return (
    <div className="max-w-3xl mx-auto">
      <div className="mb-6">
        <Link to="/" className="text-blue-600 hover:text-blue-800">
          ← Back to Home
        </Link>
      </div>

      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">👨‍🏫 Professor Mode</h1>
        <p className="text-gray-600">
          Set classroom coordinates and acceptable radius for student verification
        </p>
      </div>

      <ProfessorCalibrationForm />
    </div>
  )
}
