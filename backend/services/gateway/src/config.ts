import dotenv from 'dotenv';

dotenv.config();

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
