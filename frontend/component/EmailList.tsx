import { Email } from '../types'

interface Props {
  emails: Email[]
  loading: boolean
  selected: Email | null
  onSelect: (email: Email) => void
}

export default function EmailList({ emails, loading, selected, onSelect }: Props) {
  if (loading) {
    return (
      <div className="w-72 border-r bg-white flex items-center justify-center text-gray-400 text-sm flex-shrink-0">
        加载中…
      </div>
    )
  }

  if (emails.length === 0) {
    return (
      <div className="w-72 border-r bg-white flex items-center justify-center text-gray-400 text-sm flex-shrink-0">
        收件箱为空
      </div>
    )
  }

  return (
    <div className="w-72 border-r bg-white overflow-y-auto flex-shrink-0">
      {emails.map((email) => {
        const isSelected = selected?.id === email.id
        const senderName = email.sender.split('<')[0].trim() || email.sender
        return (
          <div
            key={email.id}
            onClick={() => onSelect(email)}
            className={`px-4 py-3 border-b cursor-pointer transition-colors ${
              isSelected
                ? 'bg-blue-50 border-l-4 border-l-blue-500'
                : 'hover:bg-gray-50 border-l-4 border-l-transparent'
            }`}
          >
            <p className="text-sm font-medium text-gray-800 truncate">{senderName}</p>
            <p className="text-sm text-gray-600 truncate mt-0.5">{email.subject}</p>
            <p className="text-xs text-gray-400 truncate mt-1">{email.snippet}</p>
          </div>
        )
      })}
    </div>
  )
}
