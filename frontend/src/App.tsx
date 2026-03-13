import { useEffect, useState } from 'react'
import { getHealth, ingestPdf, chat } from './api'
import './App.css'

function HealthIndicator() {
  const [status, setStatus] = useState<'checking' | 'ok' | 'error'>('checking')

  const check = async () => {
    setStatus('checking')
    try {
      await getHealth()
      setStatus('ok')
    } catch (e) {
      console.warn('Backend health check failed:', e)
      setStatus('error')
    }
  }

  useEffect(() => {
    check()
    const id = setInterval(check, 10000)
    return () => clearInterval(id)
  }, [])

  return (
    <div className="health" data-status={status}>
      Backend: {status === 'checking' ? '…' : status === 'ok' ? 'OK' : 'Offline'}
    </div>
  )
}

function IngestSection() {
  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<string | null>(null)
  const [category, setCategory] = useState<string | null>(null)
  const [categoryConfidence, setCategoryConfidence] = useState<number | null>(null)
  const [error, setError] = useState<string | null>(null)

  const formatCategory = (cat: string) => {
    return cat.charAt(0).toUpperCase() + cat.slice(1)
  }

  const handleUpload = async () => {
    if (!file) return
    setLoading(true)
    setResult(null)
    setCategory(null)
    setCategoryConfidence(null)
    setError(null)
    try {
      const res = await ingestPdf(file)
      setResult(`Uploaded "${res.document}": ${res.chunks_inserted} chunks.`)
      if (res.category) {
        setCategory(res.category)
        setCategoryConfidence(res.category_confidence ?? null)
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Upload failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="panel">
      <h2>Ingest PDF</h2>
      <div className="row">
        <input
          type="file"
          accept=".pdf"
          onChange={(e) => {
            const f = e.target.files?.[0]
            setFile(f ?? null)
            setResult(null)
            setCategory(null)
            setCategoryConfidence(null)
            setError(null)
          }}
        />
        <button onClick={handleUpload} disabled={!file || loading}>
          {loading ? 'Uploading…' : 'Upload'}
        </button>
      </div>
      {result && <p className="result success">{result}</p>}
      {category && (
        <p className="result category">
          Category: {formatCategory(category)}
          {categoryConfidence !== null && ` (${Math.round(categoryConfidence * 100)}% confidence)`}
        </p>
      )}
      {error && <p className="result error">{error}</p>}
    </section>
  )
}

function ChatSection() {
  const [question, setQuestion] = useState('')
  const [loading, setLoading] = useState(false)
  const [answer, setAnswer] = useState<string | null>(null)
  const [sources, setSources] = useState<string[]>([])
  const [error, setError] = useState<string | null>(null)

  const handleAsk = async () => {
    const q = question.trim()
    if (!q) return
    setLoading(true)
    setAnswer(null)
    setSources([])
    setError(null)
    try {
      const res = await chat(q)
      setAnswer(res.answer)
      setSources(res.sources ?? [])
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Request failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="panel">
      <h2>Ask a question</h2>
      <div className="row">
        <input
          type="text"
          placeholder="Your question…"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleAsk()}
        />
        <button onClick={handleAsk} disabled={!question.trim() || loading}>
          {loading ? 'Asking…' : 'Ask'}
        </button>
      </div>
      {answer !== null && (
        <div className="answer">
          <p>{answer}</p>
          {sources.length > 0 && (
            <p className="sources">Sources: {sources.join(', ')}</p>
          )}
        </div>
      )}
      {error && <p className="result error">{error}</p>}
    </section>
  )
}

export default function App() {
  return (
    <div className="app">
      <header>
        <h1>Document RAG</h1>
        <HealthIndicator />
      </header>
      <main>
        <IngestSection />
        <ChatSection />
      </main>
    </div>
  )
}
