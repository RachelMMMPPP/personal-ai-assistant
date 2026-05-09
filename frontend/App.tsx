import { useEffect, useState } from 'react'
import { fetchEmails, indexEmails } from './api'
import EmailDetail from './components/EmailDetail'
import EmailList from './components/EmailList'
import DraftPanel from './components/DraftPanel'
import { Email } from './types'

export default function App() {
  const [emails, setEmails] = useState<Email[]>([])
  const [selected, setSelected] = useState<Email | null>(null)
  const [loadingEmails, setLoadingEmails] = useState(true)
  const [loadError, setLoadError] = useState('')
  const [indexing, setIndexing] = useState(false)
  const [indexMsg, setIndexMsg] = useState('')

  useEffect(() => {
    fetchEmails()
      .then(setEmails)
      .catch((e: Error) => setLoadError(e.message))
      .finally(() => setLoadingEmails(false))
  }, [])

  const handleIndex = async () => {
    setIndexing(true)
    setIndexMsg('')
    try {
      const { indexed } = await indexEmails()
      setIndexMsg(`已索引 ${indexed} 封邮件`)
    } catch (e: unknown) {
      setIndexMsg(e instanceof Error ? e.message : '索引失败')
    } finally {
      setIndexing(false)
    }
  }

  return (
    <div className="h-screen flex flex-col bg-gray-50 overflow-hidden">
      {/* Header */}
      <header className="bg-white border-b px-6 py-3.5 flex items-center justify-between shadow-sm flex-shrink-0">
        <h1 className="text-lg font-semibold text-gray-800">Gmail × Claude 回复助手</h1>
        <div className="flex items-center gap-3">
          {indexMsg && (
            <span className="text-sm text-gray-500">{indexMsg}</span>
          )}
          <button
            onClick={handleIndex}
            disabled={indexing}
            className="px-4 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg text-gray-700 disabled:opacity-50 transition-colors"
          >
            {indexing ? '索引中…' : '索引邮件'}
          </button>
        </div>
      </header>

      {loadError && (
        <div className="bg-red-50 border-b border-red-200 px-6 py-2 text-sm text-red-700">
          加载失败：{loadError}
        </div>
      )}

      {/* Body */}
      <div className="flex flex-1 overflow-hidden">
        <EmailList
          emails={emails}
          loading={loadingEmails}
          selected={selected}
          onSelect={setSelected}
        />

        {selected ? (
          <div className="flex-1 flex flex-col overflow-hidden">
            <EmailDetail email={selected} />
            {/* key resets DraftPanel state when the user picks a different email */}
            <DraftPanel key={selected.id} email={selected} />
          </div>
        ) : (
          <div className="flex-1 flex items-center justify-center text-gray-400 text-sm">
            ← 选择一封邮件开始
          </div>
        )}
      </div>
    </div>
  )
}
