import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom'
import Landing from './pages/Landing'
import Professor from './pages/Professor'
import Student from './pages/Student'
import Status from './pages/Status'

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <nav className="bg-white shadow-sm border-b">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex items-center">
                <Link to="/" className="text-xl font-bold text-gray-900">
                  HARV Dashboard
                </Link>
              </div>
              <div className="flex items-center space-x-4">
                <Link 
                  to="/status" 
                  className="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
                >
                  Status
                </Link>
              </div>
            </div>
          </div>
        </nav>

        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Routes>
            <Route path="/" element={<Landing />} />
            <Route path="/professor" element={<Professor />} />
            <Route path="/student" element={<Student />} />
            <Route path="/status" element={<Status />} />
          </Routes>
        </main>
      </div>
    </Router>
  )
}

export default App
