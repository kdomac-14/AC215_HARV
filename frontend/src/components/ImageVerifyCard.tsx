import { useState } from 'react'
import { verifyImage } from '../api'
import StatusBanner from './StatusBanner'
import JsonViewer from './JsonViewer'

export default function ImageVerifyCard() {
  const [file, setFile] = useState<File | null>(null)
  const [challengeWord, setChallengeWord] = useState(
    import.meta.env.VITE_CHALLENGE_WORD || 'orchid'
  )
  const [isLoading, setIsLoading] = useState(false)
  const [status, setStatus] = useState<{ type: 'success' | 'error' | 'info'; message: string } | null>(null)
  const [response, setResponse] = useState<any>(null)
  const [preview, setPreview] = useState<string | null>(null)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile) {
      setFile(selectedFile)
      const reader = new FileReader()
      reader.onloadend = () => {
        setPreview(reader.result as string)
      }
      reader.readAsDataURL(selectedFile)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!file) return

    setIsLoading(true)
    setStatus(null)
    setResponse(null)

    try {
      // Convert file to base64
      const reader = new FileReader()
      reader.readAsDataURL(file)
      reader.onload = async () => {
        const base64 = reader.result as string
        const base64Data = base64.split(',')[1] // Remove data:image/...;base64, prefix

        try {
          const res = await verifyImage({
            image_b64: base64Data,
            challenge_word: challengeWord,
          })

          if (res.data.ok) {
            setStatus({
              type: 'success',
              message: `✅ <strong>Image Verified!</strong><br>Label: ${res.data.label}<br>Confidence: ${(res.data.confidence! * 100).toFixed(2)}%`,
            })
          } else {
            const reason = res.data.reason || 'unknown'
            if (reason === 'challenge_failed') {
              setStatus({
                type: 'error',
                message: '❌ Challenge word incorrect',
              })
            } else if (reason === 'model_missing') {
              setStatus({
                type: 'error',
                message: '❌ Model not loaded on server',
              })
            } else {
              setStatus({
                type: 'error',
                message: `❌ Verification failed: ${reason}`,
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
    } catch (error: any) {
      setStatus({
        type: 'error',
        message: `File read error: ${error.message}`,
      })
      setIsLoading(false)
    }
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-2xl font-bold mb-4">📷 Image Verification</h2>
      <p className="text-gray-600 mb-4">
        Upload a photo with the challenge word for visual verification.
      </p>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Challenge Word
          </label>
          <input
            type="text"
            value={challengeWord}
            onChange={(e) => setChallengeWord(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          />
          <p className="text-xs text-gray-500 mt-1">
            Default challenge word is "{import.meta.env.VITE_CHALLENGE_WORD || 'orchid'}"
          </p>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Upload Image
          </label>
          <input
            type="file"
            accept="image/*"
            onChange={handleFileChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          />
        </div>

        {preview && (
          <div className="mt-4">
            <img
              src={preview}
              alt="Preview"
              className="max-w-full h-auto rounded-lg border border-gray-300"
              style={{ maxHeight: '300px' }}
            />
          </div>
        )}

        <button
          type="submit"
          disabled={isLoading || !file}
          className="w-full bg-purple-600 hover:bg-purple-700 disabled:bg-gray-400 text-white font-semibold py-3 px-6 rounded-lg transition-colors"
        >
          {isLoading ? 'Verifying...' : 'Verify Photo'}
        </button>
      </form>

      {status && <StatusBanner type={status.type} message={status.message} />}
      {response && <JsonViewer data={response} title="📊 Verification Response" />}
    </div>
  )
}
