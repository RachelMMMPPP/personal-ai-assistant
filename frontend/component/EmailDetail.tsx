import { Email } from '../types'

interface Props {
  email: Email
}

export default function EmailDetail({ email }: Props) {
  const body = email.body || email.snippet
  const preview = body.length > 600 ? body.slice(0, 600) + '…' : body

  return (
    <div className="border-b bg-white px-6 py-4 overflow-y-auto max-h-60 flex-shrink-0">
      <div className="space-y-1.5 mb-3">
        {[
          { label: '发件人', value: email.sender },
          { label: '日期', value: email.date },
          { label: '主题', value: email.subject },
        ].map(({ label, value }) => (
          <p key={label} className="text-sm flex gap-3">
            <span className="text-gray-400 w-10 flex-shrink-0">{label}</span>
            <span className="text-gray-800 truncate">{value}</span>
          </p>
        ))}
      </div>
      <div className="pt-3 border-t text-sm text-gray-700 whitespace-pre-wrap leading-relaxed">
        {preview}
      </div>
    </div>
  )
}
