interface StatusBannerProps {
  type: 'success' | 'error' | 'info'
  message: string
  details?: string
}

export default function StatusBanner({ type, message, details }: StatusBannerProps) {
  const colors = {
    success: 'bg-success-light text-success-dark border-green-300',
    error: 'bg-error-light text-error-dark border-red-300',
    info: 'bg-info-light text-info-dark border-blue-300',
  }

  const icons = {
    success: '✅',
    error: '❌',
    info: 'ℹ️',
  }

  return (
    <div className={`${colors[type]} border rounded-lg p-4 my-4`}>
      <div className="flex items-start">
        <span className="text-2xl mr-3">{icons[type]}</span>
        <div className="flex-1">
          <div className="font-semibold" dangerouslySetInnerHTML={{ __html: message }} />
          {details && (
            <div className="mt-2 text-sm opacity-90">{details}</div>
          )}
        </div>
      </div>
    </div>
  )
}
