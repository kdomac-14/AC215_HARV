import { useState } from 'react'

interface JsonViewerProps {
  data: any
  title?: string
}

export default function JsonViewer({ data, title = 'Response' }: JsonViewerProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  if (!data) return null

  return (
    <div className="mt-4">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="text-sm text-blue-600 hover:text-blue-800 font-medium"
      >
        {isExpanded ? '▼' : '▶'} {title}
      </button>
      {isExpanded && (
        <pre className="mt-2 bg-gray-100 rounded-lg p-4 overflow-x-auto text-sm">
          {JSON.stringify(data, null, 2)}
        </pre>
      )}
    </div>
  )
}
