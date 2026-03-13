// In dev, always use relative /api so Vite proxy forwards to the backend; in prod use VITE_API_URL.
const baseUrl = import.meta.env.DEV ? '' : (import.meta.env.VITE_API_URL ?? '');

export type HealthResponse = { status: string };

export async function getHealth(): Promise<HealthResponse> {
  const res = await fetch(`${baseUrl || '/api'}/health`);
  if (!res.ok) throw new Error('Health check failed');
  return res.json();
}

export type IngestResponse = {
  status: string;
  chunks_inserted: number;
  document: string;
  category?: string;
  category_confidence?: number;
};

export async function ingestPdf(file: File): Promise<IngestResponse> {
  const form = new FormData();
  form.append('file', file);
  const res = await fetch(`${baseUrl || '/api'}/ingest/`, {
    method: 'POST',
    body: form,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Upload failed: ${res.status}`);
  }
  return res.json();
}

export type ChatResponse = {
  question: string;
  answer: string;
  sources: string[];
};

export async function chat(question: string): Promise<ChatResponse> {
  const res = await fetch(`${baseUrl || '/api'}/chat/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Chat failed: ${res.status}`);
  }
  return res.json();
}
