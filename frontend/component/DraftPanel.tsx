import { useEffect, useRef, useState } from 'react'
import { generateDraft } from '../api'
import { Email } from '../types'

interface Props {
  email: Email
}

export default function DraftPanel({ email }: Props) {
  const [extra, setExtra] = useState('')
  const [draft, setDraft] = useState('')
  const [loading, setLoading] = useState(false)
  const [ragCount, setRagCount] = useState<number | null>(null)
  const [error, setError] = useState('')
  const abortRef = useRef<AbortController | null>(null)

  // Cancel any in-flight request when the component unmounts (email switch)
  useEffect(() => {
    return () => {
      abortRef.current?.abort()
    }
  }, [])

  const handleGenerate = async () => {
    abortRef.current?.abort()
    abortRef.current = new AbortController()

    setDraft('')
    setError('')
    setRagCount(null)
    setLoading(true)

    try {
      await generateDraft(email, extra, abortRef.current.signal, {
        onRag: (count) => setRagCount(count),
        onText: (text) => setDraft((prev) => prev + text),
        onError: (msg) => setError(msg),
        onDone: () => setLoading(false),
      })
    } catch (err: unknown) {
      if (err instanceof Error && err.name !== 'AbortError') {
        setError(err.message || '请求失败，请检查后端服务是否启动。')
      }
      setLoading(false)
    }
  }

  const handleCopy = () => navigator.clipboard.writeText(draft)

  return (
    <div className="flex-1 flex flex-col overflow-hidden bg-gray-50">
      {/* Controls */}
      <div className="px-6 py-3 bg-white border-b flex items-end gap-3 flex-shrink-0">
        <div className="flex-1">
          <label className="text-xs text-gray-400 block mb-1">额外要求（可选）</label>
          <input
            type="text"
            value={extra}
            onChange={(e) => setExtra(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !loading && handleGenerate()}
            placeholder="例：请用英文回复，语气正式"
            className="w-full text-sm border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400 bg-white"
          />
        </div>
        <button
          onClick={handleGenerate}
          disabled={loading}
          className="px-4 py-2 bg-blue-500 hover:bg-blue-600 active:bg-blue-700 text-white text-sm rounded-lg disabled:opacity-50 whitespace-nowrap transition-colors"
        >
          {loading ? '生成中…' : '生成草稿'}
        </button>
      </div>

      {/* Draft area */}
      <div className="flex-1 overflow-y-auto px-6 py-4">
        {ragCount !== null && (
          <p className="text-xs text-blue-500 mb-3">
            {ragCount > 0
              ? `RAG：找到 ${ragCount} 封相似历史邮件，已加入上下文`
              : 'RAG：未找到相似历史邮件（可运行「索引邮件」后重试）'}
          </p>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg px-4 py-3 text-sm text-red-700 mb-3">
            {error}
          </div>
        )}

        {draft ? (
          <div className="bg-white rounded-xl border shadow-sm p-4">
            <div className="flex justify-between items-center mb-3">
              <p className="text-xs font-medium text-gray-400">回复草稿</p>
              {!loading && (
                <button
                  onClick={handleCopy}
                  className="text-xs text-gray-400 hover:text-gray-600 px-2 py-1 rounded hover:bg-gray-100 transition-colors"
                >
                  复制
                </button>
              )}
            </div>
            <div className="text-sm text-gray-800 whitespace-pre-wrap leading-relaxed">
              {draft}
              {loading && (
                <span className="inline-block w-0.5 h-4 bg-blue-400 animate-pulse ml-0.5 align-text-bottom" />
              )}
            </div>
          </div>
        ) : (
          !loading && !error && (
            <div className="flex items-center justify-center h-full text-gray-400 text-sm">
              点击「生成草稿」开始
            </div>
          )
        )}
      </div>
    </div>
  )
}
