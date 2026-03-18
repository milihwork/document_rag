import dotenv from 'dotenv';
import fs from 'fs';
import path from 'path';

// Prefer the repo root `.env` so `make run-gateway` behaves like the Python services.
// When compiled, __dirname points to `.../backend/services/gateway/dist`, so going up 4 levels
// lands in `.../document_rag/`.
const rootEnvPath = path.resolve(__dirname, '../../../..', '.env');
dotenv.config({ path: fs.existsSync(rootEnvPath) ? rootEnvPath : undefined });

const toBaseUrl = (value: string | undefined, fallback: string) =>
  (value ?? fallback).replace(/\/$/, '');

export const config = {
  ingestionUrl: toBaseUrl(process.env.INGESTION_URL, 'http://127.0.0.1:8001'),
  ragUrl: toBaseUrl(process.env.RAG_URL, 'http://127.0.0.1:8004'),
  port: Number(process.env.PORT ?? '8000'),
  corsOrigins: [
    'http://localhost:5173',
    'http://localhost:3000',
    'http://127.0.0.1:5173',
    'http://127.0.0.1:3000',
  ],
};
