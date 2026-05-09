import { Email } from './types'

export async function fetchEmails(): Promise<Email[]> {
  const res = await fetch('/api/emails')
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function indexEmails(): Promise<{ indexed: number }> {
  const res = await fetch('/api/index', { method: 'POST' })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

interface DraftCallbacks {
  onRag: (count: number) => void
  onText: (text: string) => void
  onError: (message: string) => void
  onDone: () => void
}

export async function generateDraft(
  email: Email,
  extra: string,
  signal: AbortSignal,
  callbacks: DraftCallbacks,
): Promise<void> {
  const res = await fetch('/api/draft', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      email_id: email.id,
      subject: email.subject,
      sender: email.sender,
      date: email.date,
      snippet: email.snippet,
      body: email.body,
      extra,
    }),
    signal,
  })

  if (!res.ok) throw new Error(await res.text())

  const reader = res.body!.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() ?? ''
    for (const line of lines) {
      if (!line.startsWith('data: ')) continue
      const data = JSON.parse(line.slice(6))
      if (data.type === 'rag') callbacks.onRag(data.count)
      else if (data.type === 'text') callbacks.onText(data.text)
      else if (data.type === 'error') callbacks.onError(data.message)
      else if (data.type === 'done') callbacks.onDone()
    }
  }
}
