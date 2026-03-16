import axios, { AxiosError } from 'axios';
import cors from 'cors';
import express, { type Request, type Response } from 'express';
import FormData from 'form-data';
import multer from 'multer';
import swaggerUi from 'swagger-ui-express';

import { config } from './config';
import { openApiSpec } from './openapi';

type ChatRequestBody = {
  question?: string;
};

export const app = express();
const upload = multer({ storage: multer.memoryStorage() });

app.disable('x-powered-by');
app.use(
  cors({
    origin: config.corsOrigins,
    credentials: true,
    methods: ['GET', 'POST'],
    allowedHeaders: ['Content-Type'],
  }),
);
app.use(express.json());

app.get('/', (_req: Request, res: Response) => {
  res.redirect(302, '/openapi/docs');
});

app.get('/openapi.json', (_req: Request, res: Response) => res.json(openApiSpec));
app.get('/docs/spec', (_req: Request, res: Response) => res.json(openApiSpec));
app.use('/openapi/docs', swaggerUi.serve, swaggerUi.setup(openApiSpec));

const relayAxiosError = (error: unknown, res: Response, fallbackDetail: string) => {
  if (error instanceof AxiosError && error.response) {
    return res.status(error.response.status).send(error.response.data);
  }

  const cause =
    error instanceof AxiosError
      ? [error.code, error.message].filter(Boolean).join(' ') || error.message
      : error instanceof Error
        ? error.message
        : String(error);
  const detail = cause ? `${fallbackDetail}: ${cause}` : fallbackDetail;

  console.error(fallbackDetail, error);
  return res.status(502).json({ detail });
};

app.post('/ingest/', upload.single('file'), async (req: Request, res: Response) => {
  if (!req.file) {
    return res.status(400).json({ detail: 'Missing multipart file field: file' });
  }

  console.info('Gateway: proxying ingest %s', req.file.originalname);

  const form = new FormData();
  form.append('file', req.file.buffer, {
    filename: req.file.originalname || 'document.pdf',
    contentType: req.file.mimetype || 'application/pdf',
  });

  try {
    const upstream = await axios.post(`${config.ingestionUrl}/ingest`, form, {
      headers: form.getHeaders(),
      timeout: 120_000,
    });

    return res.status(upstream.status).json(upstream.data);
  } catch (error) {
    return relayAxiosError(error, res, 'Upstream error while proxying ingest request');
  }
});

app.post(
  '/chat/',
  async (req: Request<Record<string, never>, unknown, ChatRequestBody>, res: Response) => {
    const question = req.body?.question;
    if (typeof question !== 'string' || question.trim() === '') {
      return res.status(400).json({ detail: 'question must be a non-empty string' });
    }

    console.info('Gateway: proxying chat question: %s', question.slice(0, 80));

    try {
      const upstream = await axios.post(
        `${config.ragUrl}/ask`,
        { question },
        {
          headers: { 'Content-Type': 'application/json' },
          timeout: 180_000,
        },
      );

      return res.status(upstream.status).json(upstream.data);
    } catch (error) {
      return relayAxiosError(error, res, 'Upstream error while proxying chat request');
    }
  },
);

app.get('/health', (_req: Request, res: Response) => {
  res.json({ status: 'ok' });
});
